from http import HTTPStatus

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from fastapi_zero.db.models import PriceRecord, Product
from fastapi_zero.db.session import get_session
from fastapi_zero.schemas import (
    CrawlRequest,
    CrawlResponse,
    ProductBestPrice,
    ScrapedItemPublic,
    ScrapeResult,
    ScrapeUrlsRequest,
    SearchCrawlRequest,
    SearchCrawlResponse,
)
from fastapi_zero.services.scraper import Scraper, normalize_product_name

router = APIRouter(tags=['scraping'])


@router.post(
    '/crawl/urls', status_code=HTTPStatus.OK, response_model=CrawlResponse
)
async def crawl_urls(payload: CrawlRequest):
    scraper = Scraper(max_concurrency=payload.max_concurrency)
    urls = await scraper.discover_urls(
        base_url=str(payload.base_url),
        max_urls=payload.max_urls,
        include_patterns=payload.include_patterns,
        exclude_patterns=payload.exclude_patterns,
        use_sitemap=payload.use_sitemap,
        follow_links=payload.follow_links,
        max_depth=payload.max_depth,
    )
    return CrawlResponse(total_urls=len(urls), urls=urls)


@router.post(
    '/crawl/search',
    status_code=HTTPStatus.OK,
    response_model=SearchCrawlResponse,
)
async def crawl_search(payload: SearchCrawlRequest):
    scraper = Scraper(max_concurrency=payload.max_concurrency)
    urls = await scraper.discover_search_urls(
        search_url=str(payload.search_url),
        max_pages=payload.max_pages,
        max_urls=payload.max_urls,
        include_patterns=payload.include_patterns,
        exclude_patterns=payload.exclude_patterns,
    )
    return SearchCrawlResponse(total_urls=len(urls), urls=urls)


@router.post(
    '/scrape/urls', status_code=HTTPStatus.OK, response_model=ScrapeResult
)
async def scrape_urls(
    payload: ScrapeUrlsRequest, session: Session = Depends(get_session)
):
    scraper = Scraper(max_concurrency=payload.max_concurrency)
    items = await scraper.scrape_urls([str(url) for url in payload.urls])

    product_ids: set[int] = set()
    saved_count = 0

    for item in items:
        if not item.title or item.price is None:
            continue

        normalized = normalize_product_name(item.title)
        product = session.scalar(
            select(Product).where(Product.normalized_name == normalized)
        )

        if not product:
            product = Product(
                display_name=item.title,
                normalized_name=normalized,
                category=payload.category,
            )
            session.add(product)
            session.commit()
            session.refresh(product)

        product_ids.add(product.id)

        price_record = PriceRecord(
            product_id=product.id,
            source_url=item.url,
            price=item.price,
            currency=item.currency,
        )
        session.add(price_record)
        saved_count += 1

    if saved_count:
        session.commit()

    products: list[ProductBestPrice] = []

    if product_ids:
        subquery = (
            select(
                PriceRecord.product_id,
                func.min(PriceRecord.price).label('min_price'),
            )
            .where(PriceRecord.product_id.in_(product_ids))
            .group_by(PriceRecord.product_id)
            .subquery()
        )

        rows = session.execute(
            select(Product, PriceRecord)
            .join(subquery, Product.id == subquery.c.product_id)
            .join(
                PriceRecord,
                (PriceRecord.product_id == subquery.c.product_id)
                & (PriceRecord.price == subquery.c.min_price),
            )
            .where(Product.id.in_(product_ids))
        ).all()

        for product, price_record in rows:
            products.append(
                ProductBestPrice(
                    product_id=product.id,
                    name=product.display_name,
                    category=product.category,
                    lowest_price=price_record.price,
                    currency=price_record.currency,
                    source_url=price_record.source_url,
                )
            )

    return ScrapeResult(
        total_scraped=len(items),
        total_saved=saved_count,
        products=products,
        raw_items=[
            ScrapedItemPublic(
                url=item.url,
                title=item.title,
                price=item.price,
                currency=item.currency,
            )
            for item in items
        ],
    )
