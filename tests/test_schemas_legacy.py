# ruff: noqa: E501, PLR2004, PT018
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError


def _load_legacy_schemas():
    path = Path(__file__).resolve().parents[1] / "fastapi_zero" / "schemas.py"
    spec = importlib.util.spec_from_file_location("fastapi_zero.schemas_legacy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


schemas = _load_legacy_schemas()


def test_message_schema():
    msg = schemas.Message(message="ok")
    assert msg.message == "ok"


def test_user_schema_validates_email():
    user = schemas.UserSchema(username="u", email="u@example.com", password="p")
    assert user.email == "u@example.com"

    with pytest.raises(ValidationError):
        schemas.UserSchema(username="u", email="invalid", password="p")


def test_user_public_from_attributes():
    class Obj:
        def __init__(self):
            self.username = "u"
            self.email = "u@example.com"
            self.id = 1

    obj = Obj()
    model = schemas.UserPublic.model_validate(obj)
    assert model.id == 1


def test_scrape_urls_request_bounds():
    with pytest.raises(ValidationError):
        schemas.ScrapeUrlsRequest(urls=["https://example.com"], max_concurrency=0)

    req = schemas.ScrapeUrlsRequest(urls=["https://example.com"], max_concurrency=20)
    assert req.max_concurrency == 20


def test_scraped_item_public():
    item = schemas.ScrapedItemPublic(
        url="https://example.com/p",
        title="Produto",
        price=10.5,
        currency="BRL",
    )
    assert item.price == 10.5


def test_product_best_price():
    model = schemas.ProductBestPrice(
        product_id=1,
        name="Produto",
        category=None,
        lowest_price=9.9,
        currency="BRL",
        source_url="https://example.com/p",
    )
    assert model.lowest_price == 9.9


def test_scrape_result():
    result = schemas.ScrapeResult(
        total_scraped=1,
        total_saved=1,
        products=[
            schemas.ProductBestPrice(
                product_id=1,
                name="Produto",
                category="x",
                lowest_price=9.9,
                currency="BRL",
                source_url="https://example.com/p",
            )
        ],
        raw_items=[
            schemas.ScrapedItemPublic(
                url="https://example.com/p",
                title="Produto",
                price=9.9,
                currency="BRL",
            )
        ],
    )
    assert result.total_saved == 1


def test_crawl_request_defaults_and_bounds():
    with pytest.raises(ValidationError):
        schemas.CrawlRequest(base_url="https://example.com", max_depth=10)

    req = schemas.CrawlRequest(base_url="https://example.com")
    assert req.use_sitemap is True


def test_search_crawl_request_bounds():
    with pytest.raises(ValidationError):
        schemas.SearchCrawlRequest(search_url="https://example.com", max_pages=0)

    req = schemas.SearchCrawlRequest(search_url="https://example.com")
    assert req.max_pages == 5
