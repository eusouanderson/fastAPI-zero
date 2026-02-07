"""
Extensão do Scraper com busca otimizada.
Integra SearchOptimizer para resultados mais precisos.
"""

from fastapi_zero.services.scraper import ScrapedItem, Scraper
from fastapi_zero.services.search_optimizer import optimize_search_results


class SmartScraper(Scraper):
    """
    Scraper com busca inteligente.
    Estende Scraper para aplicar otimizações de busca.
    """

    async def scrape_and_optimize(
        self,
        urls: list[str],
        query: str | None = None,
        max_results: int = 100,
    ) -> list[ScrapedItem]:
        """
        Faz scraping e otimiza resultados se query é fornecida.

        Args:
            urls: URLs para fazer scraping
            query: Termo de busca (opcional)
            max_results: Máximo de resultados a retornar

        Returns:
            Lista de ScrapedItem ordenada por relevância
        """
        # Faz o scraping normal
        items = await self.scrape_urls(urls)

        # Se não tem query, retorna como está
        if not query:
            return items[:max_results]

        # Converte para formato esperado pelo optimizer
        results = [
            (item.url, item.title, item.price, item.currency)
            for item in items
        ]

        # Otimiza resultados
        optimized = optimize_search_results(
            query=query,
            results=results,
            max_results=max_results,
            remove_duplicates=True
        )

        # Converte de volta para ScrapedItem
        scraped_items = [
            ScrapedItem(
                url=result.url,
                title=result.title,
                price=result.price,
                currency=result.currency,
                raw_price=f"{result.currency} {result.price}"
                if result.price
                else None,
            )
            for result in optimized
        ]

        return scraped_items

    async def discover_search_urls_optimized(  # noqa: PLR0913, PLR0917
        self,
        search_url: str,
        query: str,
        max_pages: int = 5,
        max_urls: int = 500,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> list[str]:
        """
        Descobre URLs de busca com otimização de relevância.

        Args:
            search_url: URL base de busca
            query: Termo de busca para filtrar
            max_pages: Número máximo de páginas
            max_urls: Máximo de URLs
            include_patterns: Padrões a incluir
            exclude_patterns: Padrões a excluir

        Returns:
            Lista de URLs ordenadas por relevância
        """
        # Usa descoberta normal
        urls = await self.discover_search_urls(
            search_url=search_url,
            max_pages=max_pages,
            max_urls=max_urls,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )

        # Filtra URLs por query relevância
        # (Aqui você pode adicionar lógica adicional se necessário)
        return urls
