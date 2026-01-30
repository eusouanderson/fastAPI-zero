import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi_zero.app import app
from fastapi_zero.schemas import (
    ScrapeUrlsRequest,
    ScrapeResult,
    CrawlRequest,
    CrawlResponse,
)


client = TestClient(app)


class TestScrapeEndpoints:
    """Testes para endpoints de scraping."""

    def test_scrape_urls_success(self):
        """Testa POST /scrape/urls com sucesso."""
        with patch("fastapi_zero.api.routes.scrape.Scraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            # Mock do resultado assíncrono
            async def mock_scrape(*args, **kwargs):
                from fastapi_zero.services.scraper import ScrapedItem

                return [
                    ScrapedItem(
                        url="https://example.com/1",
                        title="Product 1",
                        price=99.99,
                        currency="USD",
                        raw_price="$99.99",
                    )
                ]

            mock_scraper.scrape_urls = mock_scrape

            payload = {
                "urls": ["https://example.com/1"],
                "max_concurrency": 20,
            }

            response = client.post("/scrape/urls", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "total" in data or "products" in data or "urls" in data

    def test_scrape_urls_empty_list(self):
        """Testa POST /scrape/urls com lista vazia."""
        with patch("fastapi_zero.api.routes.scrape.Scraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            async def mock_scrape(*args, **kwargs):
                return []

            mock_scraper.scrape_urls = mock_scrape

            payload = {"urls": [], "max_concurrency": 20}

            response = client.post("/scrape/urls", json=payload)
            assert response.status_code == 200

    def test_scrape_urls_invalid_json(self):
        """Testa POST /scrape/urls com JSON inválido."""
        response = client.post("/scrape/urls", json={"invalid": "data"})
        assert response.status_code == 422

    def test_scrape_urls_missing_urls(self):
        """Testa POST /scrape/urls sem campo urls."""
        response = client.post("/scrape/urls", json={"max_concurrency": 20})
        assert response.status_code == 422

    def test_crawl_urls_success(self):
        """Testa POST /crawl/urls com sucesso."""
        with patch("fastapi_zero.api.routes.scrape.Scraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            async def mock_discover(*args, **kwargs):
                return [
                    "https://example.com/produto/1",
                    "https://example.com/produto/2",
                ]

            mock_scraper.discover_urls = mock_discover

            payload = {
                "base_url": "https://example.com",
                "max_urls": 100,
                "use_sitemap": True,
            }

            response = client.post("/crawl/urls", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert "total_urls" in data or "urls" in data

    def test_crawl_urls_with_patterns(self):
        """Testa POST /crawl/urls com patterns."""
        with patch("fastapi_zero.api.routes.scrape.Scraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            async def mock_discover(*args, **kwargs):
                return []

            mock_scraper.discover_urls = mock_discover

            payload = {
                "base_url": "https://example.com",
                "max_urls": 100,
                "include_patterns": ["/produto/"],
                "exclude_patterns": ["/admin/"],
            }

            response = client.post("/crawl/urls", json=payload)
            assert response.status_code == 200

    def test_crawl_urls_missing_base_url(self):
        """Testa POST /crawl/urls sem base_url."""
        response = client.post("/crawl/urls", json={"max_urls": 100})
        assert response.status_code == 422

    def test_crawl_search_success(self):
        """Testa POST /crawl/search com sucesso."""
        with patch("fastapi_zero.api.routes.scrape.Scraper") as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper

            async def mock_search(*args, **kwargs):
                return ["https://example.com/produto/1"]

            mock_scraper.discover_search_urls = mock_search

            payload = {
                "search_url": "https://example.com/busca/gpu",
                "max_pages": 3,
            }

            response = client.post("/crawl/search", json=payload)
            assert response.status_code == 200

    def test_crawl_search_missing_url(self):
        """Testa POST /crawl/search sem search_url."""
        response = client.post("/crawl/search", json={"max_pages": 3})
        assert response.status_code == 422

    def test_ui_endpoint(self):
        """Testa GET /ui."""
        response = client.get("/ui")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_docs_endpoint(self):
        """Testa GET /docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_endpoint(self):
        """Testa GET /openapi.json."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["openapi"]
