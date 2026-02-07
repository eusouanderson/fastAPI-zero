# ruff: noqa: I001, PLR6301, PLR2004, E501
from unittest.mock import AsyncMock, patch

import pytest

from fastapi_zero.services.scraper import ScrapedItem
from fastapi_zero.services.smart_scraper import SmartScraper


class TestSmartScraper:
    """Testes para SmartScraper com busca otimizada."""

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_with_query(self):
        """Testa scraping e otimização com query."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            # Mock com resultados fora de ordem
            mock.return_value = [
                ScrapedItem(
                    url="https://example.com/1",
                    title="Monitor LG",
                    price=299.99,
                    currency="USD",
                    raw_price="$299.99",
                ),
                ScrapedItem(
                    url="https://example.com/2",
                    title="Gabinete Gamer RGB",
                    price=199.99,
                    currency="USD",
                    raw_price="$199.99",
                ),
                ScrapedItem(
                    url="https://example.com/3",
                    title="Gabinete Preto",
                    price=149.99,
                    currency="USD",
                    raw_price="$149.99",
                ),
            ]

            # Otimiza para busca "gabinete"
            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"],
                query="gabinete"
            )

            # Deve retornar no máximo 2 (rejeita monitor que não tem "gabinete")
            assert len(result) <= 2
            # Ambos devem ter "gabinete" no título
            assert all("gabinete" in r.title.lower() for r in result)

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_without_query(self):
        """Testa scraping sem otimização (sem query)."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            items = [
                ScrapedItem(
                    url="https://example.com/1",
                    title="Product 1",
                    price=99.99,
                    currency="USD",
                    raw_price="$99.99",
                ),
                ScrapedItem(
                    url="https://example.com/2",
                    title="Product 2",
                    price=149.99,
                    currency="USD",
                    raw_price="$149.99",
                ),
            ]
            mock.return_value = items

            # Sem query, retorna como está
            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"]
            )

            assert len(result) == 2
            assert result[0].title == "Product 1"

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_respects_max_results(self):
        """Testa respeito ao limite de resultados."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            # Retorna 5 produtos
            items = [
                ScrapedItem(
                    url=f"https://example.com/{i}",
                    title=f"Gabinete {i}",
                    price=100.0 + i,
                    currency="USD",
                    raw_price=f"${100.0 + i}",
                )
                for i in range(5)
            ]
            mock.return_value = items

            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"],
                query="gabinete",
                max_results=2
            )

            assert len(result) <= 2

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_removes_duplicates(self):
        """Testa remoção de duplicados."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            items = [
                ScrapedItem(
                    url="https://example.com/1",
                    title="Gabinete Gamer RGB",
                    price=199.99,
                    currency="USD",
                    raw_price="$199.99",
                ),
                ScrapedItem(
                    url="https://example.com/2",
                    title="Gabinete Gamer RGB",  # Duplicado
                    price=199.99,
                    currency="USD",
                    raw_price="$199.99",
                ),
            ]
            mock.return_value = items

            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"],
                query="gabinete"
            )

            # Deve remover duplicado
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_filters_no_price(self):
        """Testa filtragem de produtos sem preço."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            items = [
                ScrapedItem(
                    url="https://example.com/1",
                    title="Gabinete Gamer",
                    price=199.99,
                    currency="USD",
                    raw_price="$199.99",
                ),
                ScrapedItem(
                    url="https://example.com/2",
                    title="Gabinete Preto",
                    price=None,  # Sem preço
                    currency=None,
                    raw_price=None,
                ),
            ]
            mock.return_value = items

            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"],
                query="gabinete"
            )

            # Deve manter apenas o com preço
            assert len(result) == 1
            assert result[0].price is not None

    @pytest.mark.asyncio
    async def test_discover_search_urls_optimized(self):
        """Testa descoberta de URLs com otimização."""
        scraper = SmartScraper()

        with patch.object(
            scraper, 'discover_search_urls', new_callable=AsyncMock
        ) as mock:
            mock.return_value = [
                "https://example.com/gabinete/1",
                "https://example.com/gabinete/2",
            ]

            result = await scraper.discover_search_urls_optimized(
                search_url="https://example.com/search?q=gabinete",
                query="gabinete"
            )

            assert len(result) == 2
            assert "gabinete" in result[0]

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_preserves_order(self):
        """Testa que a otimização preserva ordem de relevância."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            items = [
                ScrapedItem(
                    url="https://example.com/3",
                    title="Gabinete",
                    price=99.99,
                    currency="USD",
                    raw_price="$99.99",
                ),
                ScrapedItem(
                    url="https://example.com/1",
                    title="Gabinete Gamer RGB",  # Melhor match
                    price=199.99,
                    currency="USD",
                    raw_price="$199.99",
                ),
                ScrapedItem(
                    url="https://example.com/2",
                    title="Gabinete Preto",
                    price=149.99,
                    currency="USD",
                    raw_price="$149.99",
                ),
            ]
            mock.return_value = items

            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"],
                query="gabinete gamer rgb"
            )

            # Melhor match deve estar primeiro
            assert result[0].title == "Gabinete Gamer RGB"
            assert result[0].url == "https://example.com/1"

    @pytest.mark.asyncio
    async def test_scrape_and_optimize_complex_query(self):
        """Testa com query complexa."""
        scraper = SmartScraper()

        with patch.object(scraper, 'scrape_urls', new_callable=AsyncMock) as mock:
            items = [
                ScrapedItem(
                    url="https://example.com/1",
                    title="Gabinete Gamer RGB 2024",
                    price=299.99,
                    currency="USD",
                    raw_price="$299.99",
                ),
                ScrapedItem(
                    url="https://example.com/2",
                    title="Gabinete para Gaming",
                    price=249.99,
                    currency="USD",
                    raw_price="$249.99",
                ),
                ScrapedItem(
                    url="https://example.com/3",
                    title="Monitor Gamer 144Hz",
                    price=399.99,
                    currency="USD",
                    raw_price="$399.99",
                ),
            ]
            mock.return_value = items

            result = await scraper.scrape_and_optimize(
                urls=["https://example.com"],
                query="gabinete gamer 2024"
            )

            # Deve retornar resultados relevantes
            assert len(result) >= 1
            # Todos devem ter "gabinete" ou serem muito similares
            assert any("gabinete" in r.title.lower() for r in result)
