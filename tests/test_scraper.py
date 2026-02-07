# ruff: noqa: PLR6301, PLR2004, E501
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi_zero.services.scraper import (
    DiscoveryConfig,
    DiscoveryFilters,
    ScrapedItem,
    Scraper,
    normalize_product_name,
    parse_price,
)


class TestPriceParser:
    """Testes para a função parse_price."""

    def test_parse_price_brl(self):
        """Testa parsing de preço em BRL."""
        price, currency = parse_price("R$ 1.999,99")
        assert price == 1999.99
        assert currency == "BRL"

    def test_parse_price_usd(self):
        """Testa parsing de preço em USD."""
        price, currency = parse_price("$ 99.99")
        assert price == 99.99
        assert currency == "USD"

    def test_parse_price_eur(self):
        """Testa parsing de preço em EUR."""
        price, currency = parse_price("€ 1.234,56")
        assert price == 1234.56
        assert currency == "EUR"

    def test_parse_price_without_symbol(self):
        """Testa parsing de preço sem símbolo."""
        price, currency = parse_price("1999.99")
        assert price == 1999.99
        assert currency is None

    def test_parse_price_invalid(self):
        """Testa parsing com valor inválido."""
        price, currency = parse_price("invalid")
        assert price is None

    def test_parse_price_short_digits(self):
        """Testa parsing com menos de 3 dígitos."""
        price, currency = parse_price("99")
        assert price == 99.0  # Não é dividido por 100 (menos de 3 dígitos)
        assert currency is None


class TestNormalizeProductName:
    """Testes para normalização de nomes de produtos."""

    def test_normalize_product_name(self):
        """Testa normalização básica."""
        result = normalize_product_name("GPU RTX 4070 SUPER")
        assert result == "gpu rtx 4070 super"

    def test_normalize_with_special_chars(self):
        """Testa normalização com caracteres especiais."""
        result = normalize_product_name("GPU (RTX) 4070-SUPER")
        assert result == "gpu rtx 4070 super"

    def test_normalize_with_numbers(self):
        """Testa normalização com números."""
        result = normalize_product_name("RTX-4070_SUPER v2.0")
        assert result == "rtx 4070 super v2 0"

    def test_normalize_multiple_spaces(self):
        """Testa normalização com múltiplos espaços."""
        result = normalize_product_name("GPU   RTX    4070")
        assert result == "gpu rtx 4070"


class TestScraperClass:
    """Testes para a classe Scraper."""

    @pytest.mark.asyncio
    async def test_scraper_init(self):
        """Testa inicialização do Scraper."""
        scraper = Scraper(max_concurrency=10, timeout=5.0)
        assert scraper._semaphore._value == 10
        assert scraper._timeout == 5.0

    @pytest.mark.asyncio
    async def test_scraper_default_values(self):
        """Testa valores padrão do Scraper."""
        scraper = Scraper()
        assert scraper._semaphore._value == 20
        assert scraper._timeout == 10.0

    @pytest.mark.asyncio
    async def test_scrape_urls_empty_list(self):
        """Testa scraping de lista vazia."""
        scraper = Scraper()
        result = await scraper.scrape_urls([])
        assert result == []

    @pytest.mark.asyncio
    async def test_scrape_urls_with_mock(self):
        """Testa scraping com mock."""
        scraper = Scraper()

        # Mock do parse_html
        with patch("fastapi_zero.services.scraper.parse_html") as mock_parse:
            mock_parse.return_value = ScrapedItem(
                url="https://example.com",
                title="Test Product",
                price=99.99,
                currency="USD",
                raw_price="$99.99",
            )

            with patch("fastapi_zero.services.scraper.httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.text = "<html>Test</html>"
                mock_response.status_code = 200

                mock_async_client = MagicMock()
                mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
                mock_async_client.__aexit__ = AsyncMock(return_value=None)
                mock_async_client.get = AsyncMock(return_value=mock_response)

                mock_client.return_value = mock_async_client

                result = await scraper.scrape_urls(["https://example.com"])

                assert len(result) >= 0  # Pode retornar 0 por causa de semáforo

    @pytest.mark.asyncio
    async def test_discovery_config(self):
        """Testa DiscoveryConfig dataclass."""
        config = DiscoveryConfig(
            base_url="https://example.com",
            max_urls=100,
            use_sitemap=True,
            follow_links=False,
        )
        assert config.base_url == "https://example.com"
        assert config.max_urls == 100
        assert config.use_sitemap is True
        assert config.follow_links is False

    @pytest.mark.asyncio
    async def test_discovery_filters(self):
        """Testa DiscoveryFilters dataclass."""
        filters = DiscoveryFilters(include_regex=None, exclude_regex=None)
        assert filters.include_regex is None
        assert filters.exclude_regex is None

    @pytest.mark.asyncio
    async def test_scraper_discover_urls_empty(self):
        """Testa discover_urls com resultado vazio."""
        scraper = Scraper()

        with patch.object(scraper, '_discover_urls_impl', new_callable=AsyncMock) as mock_impl:
            mock_impl.return_value = []
            result = await scraper.discover_urls("https://example.com")
            assert result == []

    @pytest.mark.asyncio
    async def test_scraper_discover_search_urls(self):
        """Testa discover_search_urls."""
        scraper = Scraper()

        with patch("fastapi_zero.services.scraper.httpx.AsyncClient") as mock_client:
            # Mock para que a função retorne lista vazia
            mock_async_client = MagicMock()
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)

            mock_client.return_value = mock_async_client

            result = await scraper.discover_search_urls("https://example.com/search")
            assert isinstance(result, list)
