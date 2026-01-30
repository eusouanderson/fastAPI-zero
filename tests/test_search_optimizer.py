import pytest
from fastapi_zero.services.search_optimizer import (
    SearchOptimizer,
    SearchResult,
    optimize_search_results,
)


class TestSearchOptimizer:
    """Testes para otimização de busca."""

    def test_init_query_parsing(self):
        """Testa parsing da query."""
        optimizer = SearchOptimizer("gabinete gamer RTX")
        assert "gabinete" in optimizer.query_words
        assert "gamer" in optimizer.query_words
        assert "rtx" in optimizer.query_words

    def test_stopwords_removed(self):
        """Testa remoção de stopwords."""
        optimizer = SearchOptimizer("gabinete de gaming para pc")
        # "de", "para" devem ser removidos dos meaningful_words
        assert "de" not in optimizer.meaningful_words
        assert "para" not in optimizer.meaningful_words
        assert "gabinete" in optimizer.meaningful_words
        assert "gaming" in optimizer.meaningful_words

    def test_relevance_exact_match(self):
        """Testa score de relevância com match exato."""
        optimizer = SearchOptimizer("gabinete gamer")
        score = optimizer.calculate_relevance("Gabinete Gamer RGB 12V")
        assert score > 70.0  # Score alto para match exato

    def test_relevance_partial_match(self):
        """Testa score com match parcial."""
        optimizer = SearchOptimizer("gabinete gamer")
        score = optimizer.calculate_relevance("Gabinete Preto")
        assert 30.0 < score < 70.0  # Score médio

    def test_relevance_no_match(self):
        """Testa score sem match."""
        optimizer = SearchOptimizer("gabinete gamer")
        score = optimizer.calculate_relevance("Monitor LG 24 polegadas")
        assert score < 30.0  # Score baixo

    def test_is_likely_product_valid(self):
        """Testa validação de produto válido."""
        optimizer = SearchOptimizer("gabinete")
        result = optimizer.is_likely_product("Gabinete Gamer", 199.99)
        assert result is True

    def test_is_likely_product_no_price(self):
        """Testa rejeição sem preço."""
        optimizer = SearchOptimizer("gabinete")
        result = optimizer.is_likely_product("Gabinete Gamer", None)
        assert result is False

    def test_is_likely_product_too_short(self):
        """Testa rejeição de título muito curto."""
        optimizer = SearchOptimizer("gabinete")
        result = optimizer.is_likely_product("AB", 199.99)
        assert result is False

    def test_is_likely_product_too_long(self):
        """Testa rejeição de título muito longo."""
        optimizer = SearchOptimizer("gabinete")
        long_title = "A" * 300
        result = optimizer.is_likely_product(long_title, 199.99)
        assert result is False

    def test_is_likely_product_navigation_text(self):
        """Testa rejeição de texto de navegação."""
        optimizer = SearchOptimizer("produto")
        result = optimizer.is_likely_product("Menu Principal", 199.99)
        assert result is False

        result = optimizer.is_likely_product("Voltar", 199.99)
        assert result is False

    def test_filter_and_rank_basic(self):
        """Testa filtragem e ordenação básica."""
        optimizer = SearchOptimizer("gabinete")
        results = [
            ("url1", "Gabinete Gamer", 199.99, "USD"),
            ("url2", "Gabinete Preto", 149.99, "USD"),
            ("url3", "Monitor LG", 299.99, "USD"),  # Não match
            ("url4", "Gabinete Branco", 179.99, "USD"),
        ]

        filtered = optimizer.filter_and_rank(results)

        # Deve retornar 3 (rejeita Monitor)
        assert len(filtered) == 3
        # Deve estar ordenado por relevância
        assert filtered[0].title == "Gabinete Gamer"  # Melhor match
        # Todos devem ter relevância > 0
        assert all(r.relevance_score > 0 for r in filtered)

    def test_filter_and_rank_filters_invalid(self):
        """Testa filtragem de produtos inválidos."""
        optimizer = SearchOptimizer("gabinete")
        results = [
            ("url1", "Gabinete", 199.99, "USD"),
            ("url2", "AB", 149.99, "USD"),  # Muito curto
            ("url3", "Gabinete", None, "USD"),  # Sem preço
            ("url4", "Menu", 179.99, "USD"),  # Navegação
        ]

        filtered = optimizer.filter_and_rank(results)

        # Apenas url1 deve passar
        assert len(filtered) == 1
        assert filtered[0].url == "url1"

    def test_deduplicate_exact_duplicates(self):
        """Testa remoção de duplicatas exatas."""
        optimizer = SearchOptimizer("gabinete")
        results = [
            SearchResult("url1", "Gabinete Gamer", 199.99, "USD", 90.0),
            SearchResult("url2", "Gabinete Gamer", 199.99, "USD", 90.0),  # Exato
            SearchResult("url3", "Gabinete Preto", 149.99, "USD", 80.0),
        ]

        deduplicated = optimizer.deduplicate(results)

        # Deve remover duplicata exata
        assert len(deduplicated) == 2
        assert deduplicated[0].url == "url1"
        assert deduplicated[1].url == "url3"

    def test_deduplicate_similar(self):
        """Testa remoção de produtos similares."""
        optimizer = SearchOptimizer("gabinete")
        results = [
            SearchResult("url1", "Gabinete Gamer RGB", 199.99, "USD", 90.0),
            SearchResult(
                "url2", "Gabinete Gamer RGB 12V", 199.99, "USD", 89.0
            ),  # Muito similar
            SearchResult("url3", "Gabinete Preto", 149.99, "USD", 80.0),
        ]

        deduplicated = optimizer.deduplicate(results, similarity_threshold=0.8)

        # url2 é muito similar a url1, deve ser removido
        assert len(deduplicated) == 2

    def test_deduplicate_no_removal(self):
        """Testa deduplicação com threshold alto."""
        optimizer = SearchOptimizer("gabinete")
        results = [
            SearchResult("url1", "Gabinete Gamer", 199.99, "USD", 90.0),
            SearchResult("url2", "Gabinete Preto", 149.99, "USD", 80.0),
        ]

        # Com threshold 0.99, nenhum deve ser removido
        deduplicated = optimizer.deduplicate(results, similarity_threshold=0.99)

        assert len(deduplicated) == 2

    def test_deduplicate_empty(self):
        """Testa deduplicação com lista vazia."""
        optimizer = SearchOptimizer("gabinete")
        deduplicated = optimizer.deduplicate([])
        assert deduplicated == []


class TestOptimizeSearchResults:
    """Testes para função de otimização de busca."""

    def test_optimize_search_results_basic(self):
        """Testa otimização básica."""
        results = [
            ("url1", "Gabinete Gamer", 199.99, "USD"),
            ("url2", "Gabinete Preto", 149.99, "USD"),
            ("url3", "Monitor LG", 299.99, "USD"),
            ("url4", "Gabinete Branco", 179.99, "USD"),
        ]

        optimized = optimize_search_results("gabinete", results)

        assert len(optimized) == 3
        assert optimized[0].title == "Gabinete Gamer"
        assert all(isinstance(r, SearchResult) for r in optimized)

    def test_optimize_respects_max_results(self):
        """Testa limite de resultados."""
        results = [
            (f"url{i}", f"Gabinete {i}", float(100 + i), "USD")
            for i in range(50)
        ]

        optimized = optimize_search_results(
            "gabinete", results, max_results=10
        )

        assert len(optimized) <= 10

    def test_optimize_removes_duplicates(self):
        """Testa remoção de duplicados."""
        results = [
            ("url1", "Gabinete Gamer", 199.99, "USD"),
            ("url2", "Gabinete Gamer", 199.99, "USD"),  # Duplicado
            ("url3", "Gabinete Preto", 149.99, "USD"),
        ]

        optimized = optimize_search_results("gabinete", results)

        # Deve remover duplicado
        assert len(optimized) == 2

    def test_optimize_no_duplicates_removal(self):
        """Testa com remoção de duplicados desativada."""
        results = [
            ("url1", "Gabinete Gamer", 199.99, "USD"),
            ("url2", "Gabinete Gamer", 199.99, "USD"),  # Duplicado
        ]

        optimized = optimize_search_results(
            "gabinete", results, remove_duplicates=False
        )

        # Sem remoção, deve manter ambos
        assert len(optimized) == 2

    def test_optimize_empty_results(self):
        """Testa com resultados vazios."""
        optimized = optimize_search_results("gabinete", [])
        assert optimized == []

    def test_optimize_complex_query(self):
        """Testa com query complexa."""
        results = [
            ("url1", "Gabinete Gamer RGB 2024", 299.99, "USD"),
            ("url2", "Gabinete para Gaming", 249.99, "USD"),
            ("url3", "Case PC Gamer", 199.99, "USD"),
            ("url4", "Gabinete Preto", 149.99, "USD"),
            ("url5", "Monitor Gamer", 499.99, "USD"),
        ]

        optimized = optimize_search_results("gabinete gamer 2024", results)

        assert len(optimized) >= 1
        # Melhor match deve estar primeiro
        assert optimized[0].title == "Gabinete Gamer RGB 2024"


class TestSearchResultModel:
    """Testes para o modelo SearchResult."""

    def test_create_search_result(self):
        """Testa criação de SearchResult."""
        result = SearchResult(
            url="https://example.com/product/1",
            title="Gabinete Gamer",
            price=199.99,
            currency="USD",
            relevance_score=85.5
        )

        assert result.url == "https://example.com/product/1"
        assert result.title == "Gabinete Gamer"
        assert result.price == 199.99
        assert result.currency == "USD"
        assert result.relevance_score == 85.5

    def test_search_result_default_score(self):
        """Testa score padrão de SearchResult."""
        result = SearchResult(
            url="https://example.com/product/1",
            title="Gabinete",
            price=199.99,
            currency="USD"
        )

        assert result.relevance_score == 0.0
