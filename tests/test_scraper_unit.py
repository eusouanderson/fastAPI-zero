# ruff: noqa: E501, PLR6301, PLR2004, PLW0108, PLC0415
import asyncio
import json

from selectolax.parser import HTMLParser

from fastapi_zero.services import scraper as s


def test_parse_price_formats():
    assert s.parse_price("R$ 1.234,56") == (1234.56, "BRL")
    assert s.parse_price("$ 1,234.56") == (1234.56, "USD")
    assert s.parse_price("€ 99,90") == (99.90, "EUR")
    # digits-only interpreted as cents when long enough
    assert s.parse_price("12345") == (123.45, None)


def test_extract_title_priority():
    html = """
    <html><head>
      <meta property="og:title" content="OG Title"/>
      <title>Doc Title</title>
    </head>
    <body><h1>Heading</h1></body></html>
    """
    parser = HTMLParser(html)
    assert s.extract_title(parser) == "OG Title"


def test_extract_title_fallbacks():
    html_h1 = "<html><body><h1>Titulo H1</h1></body></html>"
    assert s.extract_title(HTMLParser(html_h1)) == "Titulo H1"

    html_title = "<html><head><title>Titulo Doc</title></head></html>"
    assert s.extract_title(HTMLParser(html_title)) == "Titulo Doc"

    html_none = "<html><body><div>Sem titulo</div></body></html>"
    assert s.extract_title(HTMLParser(html_none)) is None


def test_extract_price_best_candidate():
    html = """
    <html><head>
      <meta property="og:price:amount" content="199.90"/>
    </head>
    <body>Promoção por R$ 99,90</body></html>
    """
    parser = HTMLParser(html)
    raw, currency, price = s.extract_price(parser, html)
    assert price == 99.0
    assert currency == "USD"
    assert raw is not None


def test_extract_price_unparsable_candidate():
    html = """
    <html><head>
        <meta property="og:price:amount" content="abc"/>
    </head></html>
    """
    parser = HTMLParser(html)
    raw, currency, price = s.extract_price(parser, html)
    assert price is None


def test_extract_from_scripts_jsonld():
    payload = {
        "name": "Produto A",
        "offers": {
            "price": "149.90",
            "priceCurrency": "BRL",
        },
    }
    html = f"""
    <html><head></head><body>
    <script type="application/ld+json">{json.dumps(payload)}</script>
    </body></html>
    """
    parser = HTMLParser(html)
    title, raw, currency, price = s.extract_from_scripts(parser)
    assert title == "Produto A"
    assert raw == "149.90"
    assert currency == "BRL"
    assert price == 149.90


def test_extract_from_scripts_next_data():
    payload = {
        "props": {
            "pageProps": {
                "product": {
                    "name": "Produto B",
                    "price": {"value": "123.45"},
                }
            }
        }
    }
    html = f"""
    <html><body>
    <script id="__NEXT_DATA__">{json.dumps(payload)}</script>
    </body></html>
    """
    parser = HTMLParser(html)
    title, raw, currency, price = s.extract_from_scripts(parser)
    assert title == "Produto B"
    assert price == 123.45
    assert raw == "123.45"


def test_extract_from_scripts_invalid_json():
    html = """
    <html><body>
    <script type="application/ld+json">{invalid}</script>
    </body></html>
    """
    parser = HTMLParser(html)
    title, raw, currency, price = s.extract_from_scripts(parser)
    assert price is None

    html_empty = """
    <html><body>
    <script type="application/ld+json"></script>
    </body></html>
    """
    parser = HTMLParser(html_empty)
    title, raw, currency, price = s.extract_from_scripts(parser)
    assert price is None


def test_extract_from_scripts_invalid_next_data():
    html = """
    <html><body>
    <script id="__NEXT_DATA__">{invalid}</script>
    </body></html>
    """
    parser = HTMLParser(html)
    title, raw, currency, price = s.extract_from_scripts(parser)
    assert price is None


def test_parse_html_prefers_script_price():
    payload = {"name": "Produto C", "offers": {"price": "79.90", "priceCurrency": "BRL"}}
    html = f"""
    <html><head>
      <meta property="og:price:amount" content="199.90"/>
    </head>
    <body>
      <h1>Fallback</h1>
      <script type="application/ld+json">{json.dumps(payload)}</script>
    </body></html>
    """
    item = s.parse_html("https://example.com/p", html)
    assert item.price == 79.90
    assert item.currency == "BRL"
    assert item.title == "Fallback"


def test_normalize_product_name():
    assert s.normalize_product_name("Placa Vídeo!!!  RTX-4060  ") == "placa v deo rtx 4060"


def test_extract_links_with_filters():
    html = """
    <a href="/produto/abc">A</a>
    <a href="/blog">B</a>
    <a href="https://example.com/produto/xyz#frag">C</a>
    """
    include = s._compile_patterns([r"/produto/"])
    exclude = s._compile_patterns([r"/blog"])
    links = s._extract_links(html, "https://example.com", include, exclude)
    assert "https://example.com/produto/abc" in links
    assert "https://example.com/produto/xyz" in links
    assert "https://example.com/blog" not in links


def test_extract_links_skips_invalid():
    html = """
    <a href="">empty</a>
    <a href="javascript:void(0)">js</a>
    <a href="/produto/ok">ok</a>
    """
    include = s._compile_patterns([r"/produto/"])
    links = s._extract_links(html, "https://example.com", include, None)
    assert links == ["https://example.com/produto/ok"]


def test_extract_product_urls_from_html():
    html = """
    <a href="/produto/abc">A</a>
    <a href="https://example.com/produto/xyz">B</a>
    Texto https://example.com/produto/slug-123
    """
    include = s._compile_patterns([r"/produto/"])
    links = s._extract_product_urls_from_html(html, "https://example.com", include, None)
    assert "https://example.com/produto/abc" in links
    assert "https://example.com/produto/xyz" in links
    assert "https://example.com/produto/slug-123" in links


def test_extract_product_urls_from_html_filtered_and_invalid():
    html = """
    <a>no href</a>
    <a href="javascript:void(0)">js</a>
    <a href="/produto/ok">OK</a>
    <a href="/produto/bad">BAD</a>
    Texto https://example.com/produto/excluir
    /produto/excluir2
    """
    include = s._compile_patterns([r"/produto/"])
    exclude = s._compile_patterns([r"/produto/bad", r"/produto/excluir"])
    links = s._extract_product_urls_from_html(html, "https://example.com", include, exclude)
    assert "https://example.com/produto/ok" in links
    assert "https://example.com/produto/bad" not in links
    assert "https://example.com/produto/excluir" not in links
    assert "https://example.com/produto/excluir2" not in links


def test_extract_product_urls_from_html_normalize_none(monkeypatch):
    html = """
    Texto https://example.com/produto/slug-1
    /produto/slug-2
    """

    def fake_normalize(url):
        return None

    monkeypatch.setattr(s, "_normalize_url", fake_normalize)
    include = s._compile_patterns([r"/produto/"])
    links = s._extract_product_urls_from_html(html, "https://example.com", include, None)
    assert links == []


def test_extract_product_urls_from_next_data():
    payload = {
        "items": [
            "/produto/abc",
            {"externalUrl": "https://example.com/produto/xyz"},
            {"code": 123, "friendlyName": "produto-legal"},
        ]
    }
    html = f"""
    <script id="__NEXT_DATA__">{json.dumps(payload)}</script>
    """
    include = s._compile_patterns([r"/produto/"])
    links = s._extract_product_urls_from_next_data(html, "https://example.com", include, None)
    assert "https://example.com/produto/abc" in links
    assert "https://example.com/produto/xyz" in links
    assert "https://example.com/produto/123/produto-legal" in links


def test_extract_product_urls_from_next_data_invalid():
    html_missing = "<html></html>"
    include = s._compile_patterns([r"/produto/"])
    assert s._extract_product_urls_from_next_data(html_missing, "https://example.com", include, None) == []

    html_invalid = "<script id=\"__NEXT_DATA__\">{bad}</script>"
    assert s._extract_product_urls_from_next_data(html_invalid, "https://example.com", include, None) == []


def test_extract_product_urls_from_next_data_filtered():
    payload = {
        "items": [
            {"externalUrl": "produto/sem-esquema"},
            "/produto/ok",
        ]
    }
    html = f"<script id=\"__NEXT_DATA__\">{json.dumps(payload)}</script>"
    include = s._compile_patterns([r"/foo/"])
    links = s._extract_product_urls_from_next_data(html, "https://example.com", include, None)
    assert links == []


def test_extract_product_urls_from_next_data_normalize_none(monkeypatch):
    payload = {
        "items": [
            {"externalUrl": "produto/sem-esquema/produto/abc"},
        ]
    }
    html = f"<script id=\"__NEXT_DATA__\">{json.dumps(payload)}</script>"

    def fake_normalize(url):
        return None

    monkeypatch.setattr(s, "_normalize_url", fake_normalize)
    include = s._compile_patterns([r"/produto/"])
    links = s._extract_product_urls_from_next_data(html, "https://example.com", include, None)
    assert links == []


def test_extract_pagination_links():
    html = """
    <a href="/busca?page=2">2</a>
    <a href="/busca?pagina=3">3</a>
    <a href="/busca?pageNumber=4">4</a>
    <a href="/busca">no</a>
    """
    links = s._extract_pagination_links(html, "https://example.com")
    assert "https://example.com/busca?page=2" in links
    assert "https://example.com/busca?pagina=3" in links
    assert "https://example.com/busca?pageNumber=4" in links


def test_extract_pagination_links_missing_href():
    html = "<a>sem href</a>"
    links = s._extract_pagination_links(html, "https://example.com")
    assert links == []


def test_compile_patterns_none_or_empty():
    assert s._compile_patterns(None) is None
    assert s._compile_patterns([]) is None


def test_parse_sitemap_variants():
    urlset = """
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/a</loc></url>
      <url><loc>https://example.com/b</loc></url>
    </urlset>
    """
    urls, sitemaps = s._parse_sitemap(urlset)
    assert urls == ["https://example.com/a", "https://example.com/b"]
    assert sitemaps == []

    sitemapindex = """
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.com/s1.xml</loc></sitemap>
    </sitemapindex>
    """
    urls, sitemaps = s._parse_sitemap(sitemapindex)
    assert urls == []
    assert sitemaps == ["https://example.com/s1.xml"]

    urls, sitemaps = s._parse_sitemap("<bad>")
    assert urls == []
    assert sitemaps == []


def test_fetch_text_handles_errors():
    class FakeClient:
        async def get(self, url):
            raise RuntimeError("boom")

    text = asyncio.run(s._fetch_text(FakeClient(), "https://example.com"))
    assert text is None


def test_discover_from_sitemap_simple(monkeypatch):
    async def fake_find(client, base_url):
        return ["https://example.com/sitemap.xml"]

    async def fake_fetch(client, url):
        if url.endswith("sitemap.xml"):
            return """
            <urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
              <url><loc>https://example.com/produto/a</loc></url>
            </urlset>
            """
        return None

    monkeypatch.setattr(s, "_find_sitemaps", fake_find)
    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"]),
        exclude_regex=None,
    )
    urls = asyncio.run(
        s._discover_from_sitemap(None, "https://example.com", 10, filters)
    )
    assert urls == ["https://example.com/produto/a"]


def test_discover_from_sitemap_with_index(monkeypatch):
    async def fake_find(client, base_url):
        return ["https://example.com/sitemap_index.xml"]

    async def fake_fetch(client, url):
        if url.endswith("sitemap_index.xml"):
            return """
            <sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
              <sitemap><loc>https://example.com/s1.xml</loc></sitemap>
            </sitemapindex>
            """
        if url.endswith("s1.xml"):
            return """
            <urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
              <url><loc>https://example.com/produto/z</loc></url>
            </urlset>
            """
        return None

    monkeypatch.setattr(s, "_find_sitemaps", fake_find)
    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"]),
        exclude_regex=None,
    )
    urls = asyncio.run(
        s._discover_from_sitemap(None, "https://example.com", 10, filters)
    )
    assert urls == ["https://example.com/produto/z"]


def test_discover_from_sitemap_filters_and_limits(monkeypatch):
    async def fake_find(client, base_url):
        return ["https://example.com/s1.xml", "https://example.com/s1.xml"]

    async def fake_fetch(client, url):
        if url.endswith("s1.xml"):
            return """
            <urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
              <url><loc>https://example.com/produto/a</loc></url>
              <url><loc>/relative</loc></url>
              <url><loc>https://example.com/excluir</loc></url>
              <url><loc>https://example.com/produto/b</loc></url>
            </urlset>
            """
        return None

    monkeypatch.setattr(s, "_find_sitemaps", fake_find)
    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"]),
        exclude_regex=s._compile_patterns([r"/excluir"]),
    )
    urls = asyncio.run(
        s._discover_from_sitemap(None, "https://example.com", 1, filters)
    )
    assert urls == ["https://example.com/produto/a"]


def test_discover_from_sitemap_skips_seen_and_empty(monkeypatch):
    async def fake_find(client, base_url):
        return ["https://example.com/s1.xml", "https://example.com/s1.xml"]

    async def fake_fetch(client, url):
        return None

    monkeypatch.setattr(s, "_find_sitemaps", fake_find)
    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(include_regex=None, exclude_regex=None)
    urls = asyncio.run(
        s._discover_from_sitemap(None, "https://example.com", 10, filters)
    )
    assert urls == []


def test_discover_from_sitemap_invalid_and_filtered(monkeypatch):
    async def fake_find(client, base_url):
        return ["https://example.com/s1.xml"]

    async def fake_fetch(client, url):
        return """
        <urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">
          <url><loc>/relative</loc></url>
          <url><loc>https://example.com/excluir</loc></url>
          <url><loc>https://example.com/produto/a</loc></url>
        </urlset>
        """

    monkeypatch.setattr(s, "_find_sitemaps", fake_find)
    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"]),
        exclude_regex=s._compile_patterns([r"/excluir"]),
    )
    urls = asyncio.run(
        s._discover_from_sitemap(None, "https://example.com", 10, filters)
    )
    assert urls == ["https://example.com/produto/a"]


def test_allowed_by_filters():
    include = s._compile_patterns([r"/produto/"])
    exclude = s._compile_patterns([r"/admin"])
    assert s._allowed_by_filters("https://example.com/produto/x", include, exclude)
    assert not s._allowed_by_filters("https://example.com/admin", include, exclude)
    assert not s._allowed_by_filters("https://example.com/blog", include, exclude)
    assert s._allowed_by_filters("https://example.com/ok", None, None)


def test_normalize_url():
    assert s._normalize_url("https://example.com/path#frag") == "https://example.com/path"
    assert s._normalize_url("/relative") is None
    assert s._strip_ns("{ns}urlset") == "urlset"


def test_find_sitemaps_from_robots(monkeypatch):
    async def fake_fetch(client, url):
        return """User-agent: *\nSitemap: https://example.com/sitemap.xml\n"""

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)
    urls = asyncio.run(s._find_sitemaps(None, "https://example.com"))
    assert "https://example.com/sitemap.xml" in urls
    assert "https://example.com/sitemap_index.xml" in urls


def test_discover_from_links(monkeypatch):
    html = """
    <a href="/produto/a">A</a>
    <a href="/produto/b">B</a>
    <a href="https://other.com/produto/c">C</a>
    """

    async def fake_fetch(client, url):
        return html

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"]),
        exclude_regex=None,
    )
    config = s.DiscoveryConfig(base_url="https://example.com", max_urls=10, max_depth=1, follow_links=True)

    urls = asyncio.run(
        s._discover_from_links(None, "https://example.com", "example.com", config, filters)
    )
    assert "https://example.com/produto/a" in urls
    assert "https://example.com/produto/b" in urls
    assert "https://other.com/produto/c" not in urls


def test_build_client_headers():
    client = s.Scraper()._build_client()
    assert "User-Agent" in client.headers
    assert "Accept" in client.headers
    asyncio.run(client.aclose())


def test_bounded_fetch_success(monkeypatch):
    async def fast_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    class FakeResponse:
        status_code = 200
        text = "<html><body><h1>Produto</h1>R$ 10,00</body></html>"

        def raise_for_status(self):
            return None

    class FakeClient:
        async def get(self, url):
            return FakeResponse()

    scraper = s.Scraper(max_concurrency=1)
    item = asyncio.run(scraper._bounded_fetch(FakeClient(), "https://example.com/p"))
    assert item.title == "Produto"


def test_bounded_fetch_retries_and_fallback(monkeypatch):
    async def fast_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    class FakeResponse:
        status_code = 503
        text = ""

        def raise_for_status(self):
            raise RuntimeError("fail")

    class FakeClient:
        async def get(self, url):
            return FakeResponse()

    scraper = s.Scraper(max_concurrency=1)
    item = asyncio.run(scraper._bounded_fetch(FakeClient(), "https://example.com/p"))
    assert item.price is None


def test_bounded_fetch_retry_then_success(monkeypatch):
    async def fast_sleep(*args, **kwargs):
        return None

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    class Resp503:
        status_code = 429
        text = ""

        def raise_for_status(self):
            return None

    class Resp200:
        status_code = 200
        text = "<html><body><h1>Produto X</h1>R$ 10,00</body></html>"

        def raise_for_status(self):
            return None

    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def get(self, url):
            self.calls += 1
            return Resp503() if self.calls == 1 else Resp200()

    scraper = s.Scraper(max_concurrency=1)
    item = asyncio.run(scraper._bounded_fetch(FakeClient(), "https://example.com/p"))
    assert item.title == "Produto X"


def test_fetch_text_403_404():
    class FakeResponse:
        def __init__(self, status_code, text):
            self.status_code = status_code
            self.text = text

        def raise_for_status(self):
            raise RuntimeError("boom")

    class FakeClient:
        def __init__(self, status_code, text):
            self._status = status_code
            self._text = text

        async def get(self, url):
            return FakeResponse(self._status, self._text)

    text = asyncio.run(s._fetch_text(FakeClient(403, "blocked"), "https://x"))
    assert text == "blocked"
    text = asyncio.run(s._fetch_text(FakeClient(404, "notfound"), "https://x"))
    assert text == "notfound"


def test_extract_from_jsonld_offers_list():
    payload = {
        "name": "Produto Lista",
        "offers": [
            {"price": "10.00", "priceCurrency": "USD"},
            {"price": "9.00", "priceCurrency": "USD"},
        ],
    }
    title, raw, currency, price = s._extract_from_jsonld(payload)
    assert title is None
    assert price == 10.0
    assert currency == "USD"


def test_extract_from_next_price_keys():
    payload = {"pricePix": "88.50", "name": "Produto Pix"}
    title, raw, currency, price = s._extract_from_next(payload)
    assert title == "Produto Pix"
    assert price == 88.50
    assert raw == "88.50"


def test_extract_from_jsonld_list_and_root_price():
    payload = [
        {"name": "A"},
        {"name": "B", "price": "12.34", "priceCurrency": "USD"},
    ]
    title, raw, currency, price = s._extract_from_jsonld(payload)
    assert title == "B"
    assert price == 12.34
    assert currency == "USD"


def test_extract_from_next_skip_invalid_price():
    payload = {"name": "Produto", "pricePix": "N/A", "price": "20.00"}
    title, raw, currency, price = s._extract_from_next(payload)
    assert title == "Produto"
    assert price == 20.00


def test_discover_urls_impl_combines(monkeypatch):
    async def fake_sitemap(client, base_url, max_urls, filters):
        return ["https://example.com/produto/a"]

    async def fake_links(client, base_url, allowed_host, config, filters):
        return ["https://example.com/produto/b"]

    monkeypatch.setattr(s, "_discover_from_sitemap", fake_sitemap)
    monkeypatch.setattr(s, "_discover_from_links", fake_links)

    class DummyContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scraper = s.Scraper()
    monkeypatch.setattr(scraper, "_build_client", lambda: DummyContext())

    config = s.DiscoveryConfig(
        base_url="https://example.com",
        max_urls=10,
        include_patterns=[r"/produto/"],
        follow_links=True,
        use_sitemap=True,
    )
    urls = asyncio.run(scraper._discover_urls_impl(config))
    assert "https://example.com/produto/a" in urls
    assert "https://example.com/produto/b" in urls


def test_discover_search_urls_with_pagination(monkeypatch):
    page1 = """
    <a href="/produto/a">A</a>
    <a href="/busca?page=2">next</a>
    <script id="__NEXT_DATA__">{"items": ["/produto/b"]}</script>
    """
    page2 = """
    <a href="/produto/c">C</a>
    """

    async def fake_fetch(client, url):
        if "page=2" in url:
            return page2
        return page1

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    class DummyContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scraper = s.Scraper()
    monkeypatch.setattr(scraper, "_build_client", lambda: DummyContext())

    urls = asyncio.run(
        scraper.discover_search_urls(
            "https://example.com/busca",
            max_pages=2,
            max_urls=10,
        )
    )
    assert "https://example.com/produto/a" in urls
    assert "https://example.com/produto/b" in urls
    assert "https://example.com/produto/c" in urls


def test_discover_search_urls_branches(monkeypatch):
    page1 = """
    <a href="/produto/a">A</a>
    <a href="/busca?page=1">self</a>
    <a href="/busca?page=2">next</a>
    """

    async def fake_fetch(client, url):
        if "page=2" in url:
            return None
        return page1

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    class DummyContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scraper = s.Scraper()
    monkeypatch.setattr(scraper, "_build_client", lambda: DummyContext())

    urls = asyncio.run(
        scraper.discover_search_urls(
            "https://example.com/busca?page=1",
            max_pages=2,
            max_urls=1,
        )
    )
    assert urls == ["https://example.com/produto/a"]


def test_discover_search_urls_visited(monkeypatch):
    page1 = """
    <a href="/produto/a">A</a>
    <a href="/busca?page=1">self</a>
    """

    async def fake_fetch(client, url):
        return page1

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    class DummyContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scraper = s.Scraper()
    monkeypatch.setattr(scraper, "_build_client", lambda: DummyContext())

    urls = asyncio.run(
        scraper.discover_search_urls(
            "https://example.com/busca?page=1",
            max_pages=3,
            max_urls=10,
        )
    )
    assert "https://example.com/produto/a" in urls


def test_discover_search_urls_duplicate_queue(monkeypatch):
    page1 = """
    <a href="/produto/a">A</a>
    <a href="/busca?page=2">next</a>
    """
    page2 = """
    <a href="/produto/b">B</a>
    """

    async def fake_fetch(client, url):
        if "page=2" in url:
            return page2
        return page1

    def fake_pagination_links(html, base_url):
        return ["https://example.com/busca?page=2", "https://example.com/busca?page=2"]

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)
    monkeypatch.setattr(s, "_extract_pagination_links", fake_pagination_links)

    class DummyContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    scraper = s.Scraper()
    monkeypatch.setattr(scraper, "_build_client", lambda: DummyContext())

    urls = asyncio.run(
        scraper.discover_search_urls(
            "https://example.com/busca?page=1",
            max_pages=3,
            max_urls=10,
        )
    )
    assert "https://example.com/produto/a" in urls
    assert "https://example.com/produto/b" in urls


def test_parse_price_digit_value_error(monkeypatch):
    import builtins

    def fake_float(value):
        raise ValueError("nope")

    monkeypatch.setattr(builtins, "float", fake_float)
    value, currency = s.parse_price("12345")
    assert value is None


def test_discover_from_links_branches(monkeypatch):
    page1 = """
    <a href="">empty</a>
    <a href="javascript:void(0)">js</a>
    <a href="/produto/a">A</a>
    <a href="/produto/bad">Bad</a>
    <a href="/page2">Page2</a>
    """
    page2 = """
    <a href="/page3">Page3</a>
    """

    async def fake_fetch(client, url):
        if url.endswith("/page2"):
            return page2
        if url.endswith("/page3"):
            return None
        return page1

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"])
        ,
        exclude_regex=s._compile_patterns([r"/produto/bad"]),
    )
    config = s.DiscoveryConfig(base_url="https://example.com", max_urls=10, max_depth=1, follow_links=True)

    urls = asyncio.run(
        s._discover_from_links(None, "https://example.com", "example.com", config, filters)
    )
    assert "https://example.com/produto/a" in urls
    assert "https://example.com/produto/bad" not in urls


def test_discover_from_links_depth_and_limits(monkeypatch):
    page1 = """
    <a href="/produto/a">A</a>
    <a href="/page2">Page2</a>
    <a href="/produto/b">B</a>
    """
    page2 = """
    <a href="/page3">Page3</a>
    """

    async def fake_fetch(client, url):
        if url.endswith("/page2"):
            return page2
        if url.endswith("/page3"):
            return None
        return page1

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(
        include_regex=s._compile_patterns([r"/produto/"]),
        exclude_regex=None,
    )
    config = s.DiscoveryConfig(base_url="https://example.com", max_urls=1, max_depth=1, follow_links=True)

    urls = asyncio.run(
        s._discover_from_links(None, "https://example.com", "example.com", config, filters)
    )
    assert urls == ["https://example.com/produto/a"]


def test_discover_from_links_duplicate_and_empty(monkeypatch):
    page1 = """
    <a href="/page2">Page2</a>
    <a href="/page2">Page2b</a>
    """

    async def fake_fetch(client, url):
        if url.endswith("/page2"):
            return None
        return page1

    monkeypatch.setattr(s, "_fetch_text", fake_fetch)

    filters = s.DiscoveryFilters(include_regex=None, exclude_regex=None)
    config = s.DiscoveryConfig(base_url="https://example.com", max_urls=10, max_depth=2, follow_links=True)

    urls = asyncio.run(
        s._discover_from_links(None, "https://example.com", "example.com", config, filters)
    )
    assert "https://example.com/page2" in urls
