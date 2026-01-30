import asyncio
import json
import re
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from selectolax.parser import HTMLParser

MIN_PRICE_LENGTH = 3

PRICE_PATTERNS = [
    re.compile(r'R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?'),
    re.compile(r'\d{1,3}(?:\.\d{3})*(?:,\d{2})?\s*R\$'),
    re.compile(r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'),
    re.compile(r'€\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?'),
    re.compile(r'\d{1,3}(?:\.\d{3})*,\d{2}'),
    re.compile(r'\d{1,3}(?:,\d{3})*\.\d{2}'),
]


@dataclass(slots=True)
class DiscoveryConfig:
    base_url: str
    max_urls: int = 1000
    include_patterns: list[str] | None = None
    exclude_patterns: list[str] | None = None
    use_sitemap: bool = True
    follow_links: bool = False
    max_depth: int = 1


@dataclass(slots=True)
class DiscoveryFilters:
    include_regex: list[re.Pattern[str]] | None = None
    exclude_regex: list[re.Pattern[str]] | None = None


@dataclass(slots=True)
class ScrapedItem:
    url: str
    title: str | None
    price: float | None
    currency: str | None
    raw_price: str | None


class Scraper:
    def __init__(self, max_concurrency: int = 20, timeout: float = 10.0):
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._timeout = timeout

    async def scrape_urls(self, urls: Iterable[str]) -> list[ScrapedItem]:
        async with self._build_client() as client:
            tasks = [self._bounded_fetch(client, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[ScrapedItem] = []
        for result in results:
            if isinstance(result, ScrapedItem):
                items.append(result)
        return items

    async def discover_urls(
        self,
        base_url: str,
        max_urls: int = 1000,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **kwargs: bool,
    ) -> list[str]:
        use_sitemap = kwargs.get('use_sitemap', True)
        follow_links = kwargs.get('follow_links', False)
        max_depth = kwargs.get('max_depth', 1)

        config = DiscoveryConfig(
            base_url=base_url,
            max_urls=max_urls,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            use_sitemap=use_sitemap,
            follow_links=follow_links,
            max_depth=max_depth,
        )
        return await self._discover_urls_impl(config)

    async def _discover_urls_impl(self, config: DiscoveryConfig) -> list[str]:
        base_url = config.base_url.rstrip('/')
        allowed_host = urlparse(base_url).netloc

        filters = DiscoveryFilters(
            include_regex=_compile_patterns(config.include_patterns),
            exclude_regex=_compile_patterns(config.exclude_patterns),
        )
        discovered: set[str] = set()

        async with self._build_client() as client:
            if config.use_sitemap:
                sitemap_urls = await _discover_from_sitemap(
                    client, base_url, config.max_urls, filters
                )
                discovered.update(sitemap_urls)

            if config.follow_links and len(discovered) < config.max_urls:
                link_urls = await _discover_from_links(
                    client, base_url, allowed_host, config, filters
                )
                discovered.update(link_urls)

        return list(discovered)[: config.max_urls]

    async def discover_search_urls(
        self,
        search_url: str,
        max_pages: int = 5,
        max_urls: int = 500,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> list[str]:
        if include_patterns is None:
            include_patterns = [r'/produto/']

        include_regex = _compile_patterns(include_patterns)
        exclude_regex = _compile_patterns(exclude_patterns)
        discovered: set[str] = set()
        visited_pages: set[str] = set()
        page_queue = deque([search_url])

        async with self._build_client() as client:
            while page_queue and len(visited_pages) < max_pages:
                page_url = page_queue.popleft()
                if page_url in visited_pages:
                    continue
                visited_pages.add(page_url)

                html = await _fetch_text(client, page_url)
                if not html:
                    continue

                product_links = _extract_product_urls_from_html(
                    html,
                    base_url=page_url,
                    include_regex=include_regex,
                    exclude_regex=exclude_regex,
                )
                product_links.extend(
                    _extract_product_urls_from_next_data(
                        html,
                        base_url=page_url,
                        include_regex=include_regex,
                        exclude_regex=exclude_regex,
                    )
                )
                for link in product_links:
                    if link not in discovered:
                        discovered.add(link)
                        if len(discovered) >= max_urls:
                            break

                if len(visited_pages) >= max_pages:
                    break

                for next_page in _extract_pagination_links(
                    html,
                    base_url=page_url,
                ):
                    if next_page not in visited_pages:
                        page_queue.append(next_page)

        return list(discovered)[:max_urls]

    def _build_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            headers={
                'User-Agent': (
                    'Mozilla/5.0 (X11; Linux x86_64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/122.0 Safari/537.36'
                ),
                'Accept': (
                    'text/html,application/xhtml+xml,application/xml;'
                    'q=0.9,image/avif,image/webp,*/*;q=0.8'
                ),
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Upgrade-Insecure-Requests': '1',
            },
            follow_redirects=True,
        )

    async def _bounded_fetch(self, client: httpx.AsyncClient, url: str):
        async with self._semaphore:
            for attempt in range(3):
                try:
                    response = await client.get(url)
                    if response.status_code in {403, 429, 503}:
                        await asyncio.sleep(0.6 * (attempt + 1))
                        continue
                    response.raise_for_status()
                    return parse_html(url, response.text)
                except Exception:
                    await asyncio.sleep(0.4 * (attempt + 1))

            return ScrapedItem(
                url=url,
                title=None,
                price=None,
                currency=None,
                raw_price=None,
            )


def parse_html(url: str, html: str) -> ScrapedItem:
    parser = HTMLParser(html)
    title = extract_title(parser)
    raw_price, currency, price = extract_price(parser, html)

    script_title, script_raw, script_currency, script_price = (
        extract_from_scripts(parser)
    )
    title = title or script_title
    if script_price is not None:
        raw_price = script_raw
        currency = script_currency or currency
        price = script_price

    return ScrapedItem(
        url=url,
        title=title,
        price=price,
        currency=currency,
        raw_price=raw_price,
    )


def extract_title(parser: HTMLParser) -> str | None:
    og_title = parser.css_first('meta[property="og:title"]')
    if og_title and og_title.attributes.get('content'):
        return og_title.attributes['content'].strip()

    h1 = parser.css_first('h1')
    if h1 and h1.text():
        return h1.text().strip()

    title_tag = parser.css_first('title')
    if title_tag and title_tag.text():
        return title_tag.text().strip()

    return None


def extract_price(
    parser: HTMLParser,
    html: str,
) -> tuple[str | None, str | None, float | None]:
    candidates: list[str] = []

    for selector in (
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
        'meta[name="twitter:data1"]',
    ):
        tag = parser.css_first(selector)
        if tag and tag.attributes.get('content'):
            candidates.append(tag.attributes['content'].strip())

    body_text = parser.text()
    for pattern in PRICE_PATTERNS:
        candidates.extend(pattern.findall(body_text))

    candidates.extend(extract_price_from_raw_html(html))

    best_price = None
    best_raw = None
    best_currency = None

    for value in candidates:
        parsed, currency = parse_price(value)
        if parsed is None:
            continue
        if best_price is None or parsed < best_price:
            best_price = parsed
            best_raw = value
            best_currency = currency

    return best_raw, best_currency, best_price


def extract_price_from_raw_html(html: str) -> list[str]:
    candidates: list[str] = []
    for pattern in PRICE_PATTERNS:
        candidates.extend(pattern.findall(html))
    return candidates


def extract_from_scripts(
    parser: HTMLParser,
) -> tuple[str | None, str | None, str | None, float | None]:
    title = None
    raw_price = None
    currency = None
    price = None

    for script in parser.css('script[type="application/ld+json"]'):
        if not script.text():
            continue
        try:
            payload = json.loads(script.text())
        except json.JSONDecodeError:
            continue
        title, raw_price, currency, price = _extract_from_jsonld(payload)
        if price is not None:
            return title, raw_price, currency, price

    next_data = parser.css_first('script#__NEXT_DATA__')
    if next_data and next_data.text():
        try:
            payload = json.loads(next_data.text())
            title, raw_price, currency, price = _extract_from_next(payload)
        except json.JSONDecodeError:
            pass

    return title, raw_price, currency, price


def _extract_from_jsonld(
    payload: object,
) -> tuple[str | None, str | None, str | None, float | None]:
    title = None
    raw_price = None
    currency = None
    price = None

    if isinstance(payload, list):
        for item in payload:
            t, r, c, p = _extract_from_jsonld(item)
            if p is not None:
                return t, r, c, p
    elif isinstance(payload, dict):
        name_value = payload.get('name')
        title = name_value if isinstance(name_value, str) else None
        offers = payload.get('offers')
        if isinstance(offers, list):
            for offer in offers:
                t, r, c, p = _extract_from_jsonld(offer)
                if p is not None:
                    return t, r, c, p
        elif isinstance(offers, dict):
            raw = offers.get('price')
            curr = offers.get('priceCurrency')
            if raw is not None:
                parsed, _ = parse_price(str(raw))
                return title, str(raw), curr, parsed

        if 'price' in payload:
            raw = payload.get('price')
            curr = payload.get('priceCurrency')
            if raw is not None:
                parsed, _ = parse_price(str(raw))
                raw_price = str(raw)
                currency = curr
                price = parsed

    return title, raw_price, currency, price


def _extract_from_next(
    payload: object,
) -> tuple[str | None, str | None, str | None, float | None]:
    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield key, value
                yield from walk(value)
        elif isinstance(obj, list):
            for item in obj:
                yield from walk(item)

    title = None
    best_price = None
    best_raw = None
    best_currency = None

    price_keys = {
        'price',
        'bestPrice',
        'priceValue',
        'salePrice',
        'spotPrice',
        'pricePix',
        'pricePIX',
        'priceFrom',
        'priceTo',
        'priceWithDiscount',
        'priceWithOffer',
        'priceFinal',
        'cashPrice',
        'pixPrice',
    }

    for key, value in walk(payload):
        if title is None and key in {'name', 'productName', 'title'}:
            if isinstance(value, str):
                title = value
        if key in price_keys:
            if isinstance(value, dict):
                for sub_key in ('value', 'amount', 'current', 'price'):
                    if sub_key in value:
                        value = value[sub_key]  # noqa: PLW2901
                        break
            parsed, curr = parse_price(str(value))
            if parsed is None:
                continue
            if best_price is None or parsed < best_price:
                best_price = parsed
                best_raw = str(value)
                best_currency = curr

    return title, best_raw, best_currency, best_price


def parse_price(raw: str) -> tuple[float | None, str | None]:
    raw = raw.strip()
    currency = None

    if 'R$' in raw:
        currency = 'BRL'
    elif '€' in raw:
        currency = 'EUR'
    elif '$' in raw:
        currency = 'USD'

    cleaned = (
        raw.replace('R$', '')
        .replace('€', '')
        .replace('$', '')
        .replace(' ', '')
    )

    if ',' in cleaned and '.' in cleaned:
        if cleaned.rfind(',') > cleaned.rfind('.'):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        cleaned = cleaned.replace('.', '').replace(',', '.')

    if cleaned.isdigit() and len(cleaned) >= MIN_PRICE_LENGTH:
        try:
            return float(cleaned) / 100, currency
        except ValueError:
            return None, currency

    try:
        return float(cleaned), currency
    except ValueError:
        return None, currency


def normalize_product_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', ' ', name)
    return ' '.join(name.split())


def _compile_patterns(patterns: list[str] | None):
    if not patterns:
        return None
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def _allowed_by_filters(
    url: str,
    include_regex: list[re.Pattern[str]] | None,
    exclude_regex: list[re.Pattern[str]] | None,
) -> bool:
    if include_regex and not any(r.search(url) for r in include_regex):
        return False
    if exclude_regex and any(r.search(url) for r in exclude_regex):
        return False
    return True


def _normalize_url(url: str) -> str | None:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    normalized = parsed._replace(fragment='')
    return urlunparse(normalized)


def _extract_links(
    html: str,
    base_url: str,
    include_regex: list[re.Pattern[str]] | None,
    exclude_regex: list[re.Pattern[str]] | None,
) -> list[str]:
    parser = HTMLParser(html)
    links: list[str] = []
    for anchor in parser.css('a'):
        href = anchor.attributes.get('href')
        if not href:
            continue
        absolute = urljoin(base_url, href)
        normalized = _normalize_url(absolute)
        if not normalized:
            continue
        if not _allowed_by_filters(normalized, include_regex, exclude_regex):
            continue
        links.append(normalized)
    return links


def _extract_product_urls_from_html(
    html: str,
    base_url: str,
    include_regex: list[re.Pattern[str]] | None,
    exclude_regex: list[re.Pattern[str]] | None,
) -> list[str]:
    parser = HTMLParser(html)
    links: set[str] = set()

    for anchor in parser.css('a'):
        href = anchor.attributes.get('href')
        if not href:
            continue
        absolute = urljoin(base_url, href)
        normalized = _normalize_url(absolute)
        if not normalized:
            continue
        if not _allowed_by_filters(normalized, include_regex, exclude_regex):
            continue
        links.add(normalized)

    for match in re.findall(r"https?://[^\s\"'>]+/produto/[^\s\"'>]+", html):
        normalized = _normalize_url(match)
        if not normalized:
            continue
        if not _allowed_by_filters(normalized, include_regex, exclude_regex):
            continue
        links.add(normalized)

    for match in re.findall(r"/produto/[^\s\"'>]+", html):
        absolute = urljoin(base_url, match)
        normalized = _normalize_url(absolute)
        if not normalized:
            continue
        if not _allowed_by_filters(normalized, include_regex, exclude_regex):
            continue
        links.add(normalized)

    return list(links)


def _extract_product_urls_from_next_data(
    html: str,
    base_url: str,
    include_regex: list[re.Pattern[str]] | None,
    exclude_regex: list[re.Pattern[str]] | None,
) -> list[str]:
    parser = HTMLParser(html)
    node = parser.css_first('script#__NEXT_DATA__')
    if not node or not node.text():
        return []
    try:
        payload = json.loads(node.text())
    except json.JSONDecodeError:
        return []

    urls: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                yield value
                yield from walk(value)
        elif isinstance(obj, list):
            for item in obj:
                yield item
                yield from walk(item)

    def add_url(candidate: str):
        normalized = _normalize_url(candidate)
        if not normalized:
            return
        if not _allowed_by_filters(normalized, include_regex, exclude_regex):
            return
        urls.add(normalized)

    for value in walk(payload):
        if isinstance(value, str) and '/produto/' in value:
            if value.startswith('/'):
                add_url(urljoin(base_url, value))
            else:
                add_url(value)

        if isinstance(value, dict):
            code = value.get('code')
            friendly = value.get('friendlyName')
            external = value.get('externalUrl')
            if isinstance(external, str) and '/produto/' in external:
                add_url(external)
            if isinstance(code, int) and isinstance(friendly, str):
                candidate = urljoin(base_url, f'/produto/{code}/{friendly}')
                add_url(candidate)

    return list(urls)


def _extract_pagination_links(html: str, base_url: str) -> list[str]:
    parser = HTMLParser(html)
    links: list[str] = []
    for anchor in parser.css('a'):
        href = anchor.attributes.get('href')
        if not href:
            continue
        if (
            'page=' not in href
            and 'pagina=' not in href
            and 'page_number=' not in href
            and 'pageNumber=' not in href
        ):
            continue
        absolute = urljoin(base_url, href)
        normalized = _normalize_url(absolute)
        if normalized:
            links.append(normalized)
    return list(dict.fromkeys(links))


async def _discover_from_sitemap(
    client: httpx.AsyncClient,
    base_url: str,
    max_urls: int,
    filters: DiscoveryFilters,
) -> list[str]:
    sitemap_candidates = await _find_sitemaps(client, base_url)
    seen_sitemaps: set[str] = set()
    discovered: list[str] = []

    queue = deque(sitemap_candidates)
    while queue and len(discovered) < max_urls:
        sitemap_url = queue.popleft()
        if sitemap_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sitemap_url)

        content = await _fetch_text(client, sitemap_url)
        if not content:
            continue

        urls, sitemaps = _parse_sitemap(content)
        for loc in urls:
            normalized = _normalize_url(loc)
            if not normalized:
                continue
            if not _allowed_by_filters(
                normalized, filters.include_regex, filters.exclude_regex
            ):
                continue
            if normalized not in discovered:
                discovered.append(normalized)
                if len(discovered) >= max_urls:
                    break

        for loc in sitemaps:
            normalized = _normalize_url(loc)
            if normalized and normalized not in seen_sitemaps:
                queue.append(normalized)

    return discovered


async def _find_sitemaps(
    client: httpx.AsyncClient, base_url: str
) -> list[str]:
    candidates = []
    robots_url = urljoin(base_url + '/', 'robots.txt')
    robots = await _fetch_text(client, robots_url)
    if robots:
        for line in robots.splitlines():
            if line.lower().startswith('sitemap:'):
                sitemap = line.split(':', 1)[1].strip()
                if sitemap:
                    candidates.append(sitemap)

    for fallback in ('sitemap.xml', 'sitemap_index.xml'):
        candidates.append(urljoin(base_url + '/', fallback))

    return list(dict.fromkeys(candidates))


async def _discover_from_links(
    client: httpx.AsyncClient,
    base_url: str,
    allowed_host: str,
    config: DiscoveryConfig,
    filters: DiscoveryFilters,
) -> list[str]:
    discovered: set[str] = set()
    visited: set[str] = set()
    queue = deque([(base_url, 0)])

    while queue and len(discovered) < config.max_urls:
        current, depth = queue.popleft()
        if current in visited or depth > config.max_depth:
            continue
        visited.add(current)

        html = await _fetch_text(client, current)
        if not html:
            continue

        parser = HTMLParser(html)
        for anchor in parser.css('a'):
            href = anchor.attributes.get('href')
            if not href:
                continue
            absolute = urljoin(current, href)
            normalized = _normalize_url(absolute)
            if not normalized:
                continue
            parsed = urlparse(normalized)
            if parsed.netloc != allowed_host:
                continue
            if not _allowed_by_filters(
                normalized, filters.include_regex, filters.exclude_regex
            ):
                continue
            if normalized not in discovered:
                discovered.add(normalized)
                if len(discovered) >= config.max_urls:
                    break
            if depth + 1 <= config.max_depth and normalized not in visited:
                queue.append((normalized, depth + 1))

    return list(discovered)


async def _fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
        if response.status_code in {403, 404}:
            return response.text or None
        response.raise_for_status()
        return response.text
    except Exception:
        return None


def _parse_sitemap(content: str) -> tuple[list[str], list[str]]:
    urls: list[str] = []
    sitemaps: list[str] = []
    try:
        root = ET.fromstring(content)
    except ET.ParseError:
        return urls, sitemaps

    tag = _strip_ns(root.tag)
    if tag == 'sitemapindex':
        for sitemap in root.findall('.//{*}loc'):
            if sitemap.text:
                sitemaps.append(sitemap.text.strip())
    elif tag == 'urlset':
        for loc in root.findall('.//{*}loc'):
            if loc.text:
                urls.append(loc.text.strip())
    return urls, sitemaps


def _strip_ns(tag: str) -> str:
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag
