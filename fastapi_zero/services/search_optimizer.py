"""
Módulo de busca inteligente para produtos.
Fornece filtragem precisa e validação de resultados.
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class SearchResult:
    """Resultado de busca com score de relevância."""
    url: str
    title: str | None
    price: float | None
    currency: str | None
    relevance_score: float = 0.0


class SearchOptimizer:
    """Otimiza resultados de busca com filtragem e relevância."""

    def __init__(self, query: str):
        self.query = query.lower()
        self.query_words = set(re.findall(r'\w+', self.query))
        # Palavras que não agregam valor
        self.stopwords = {
            'de', 'o', 'a', 'em', 'para', 'com', 'por', 'que', 'e', 'ou',
            'um', 'uma', 'os', 'as', 'nos', 'nas', 'ao', 'à', 'essa',
            'esse', 'este', 'esse', 'esses', 'essas', 'este', 'esta',
            'este', 'estão', 'estou'
        }
        self.meaningful_words = self.query_words - self.stopwords

    def calculate_relevance(self, title: str) -> float:
        """
        Calcula score de relevância (0-100) baseado no título.
        
        Critérios:
        - Palavras-chave presentes (peso alto)
        - Ordem das palavras (peso médio)
        - Comprimento do título (weight baixo)
        """
        if not title:
            return 0.0

        title_lower = title.lower()
        title_words = set(re.findall(r'\w+', title_lower))

        # 1. Quantas palavras-chave significativas estão presentes
        matching_words = len(self.meaningful_words & title_words)
        if not self.meaningful_words:
            word_match_score = 0.0
        else:
            word_match_score = matching_words / len(self.meaningful_words)

        # 2. Similaridade de sequência (ordem importa)
        sequence_matcher = SequenceMatcher(None, self.query, title_lower)
        sequence_score = sequence_matcher.ratio()

        # 3. Query aparece como substring contíguo (bonus)
        substring_bonus = 0.0
        if self.query in title_lower:
            substring_bonus = 0.2

        # Score final (0-100)
        final_score = (
            (word_match_score * 50) +      # 50% peso para palavras-chave
            (sequence_score * 40) +        # 40% peso para sequência
            (substring_bonus * 10)         # 10% bonus para substring
        )

        return min(100.0, final_score)

    def is_likely_product(self, title: str, price: float | None) -> bool:
        """
        Verifica se é provável que seja um produto válido.
        
        Critérios:
        - Tem preço
        - Não é muito curto (mínimo 3 caracteres)
        - Não é muito longo (máximo 200 caracteres)
        """
        if price is None:
            return False

        if not title or len(title) < 3 or len(title) > 200:
            return False

        # Evita títulos que parecem ser cabeçalhos/navegação
        navigation_patterns = [
            r'^home$', r'^menu', r'^back', r'^voltar',
            r'^mais', r'^carrinho', r'^conta', r'^sair',
            r'^entrar', r'^login', r'^registr'
        ]
        title_lower = title.lower().strip()
        for pattern in navigation_patterns:
            if re.match(pattern, title_lower):
                return False

        return True

    def filter_and_rank(
        self,
        results: list[tuple[str, str | None, float | None, str | None]]
    ) -> list[SearchResult]:
        """
        Filtra e ordena resultados por relevância.
        
        Input: lista de (url, title, price, currency)
        Output: lista de SearchResult ordenada por relevância
        """
        filtered = []

        for url, title, price, currency in results:
            # Validação básica
            if not self.is_likely_product(title, price):
                continue

            # Calcula relevância
            score = self.calculate_relevance(title or "")

            # Filtra por score mínimo (ajustável)
            if score < 10.0:
                continue

            filtered.append(SearchResult(
                url=url,
                title=title,
                price=price,
                currency=currency,
                relevance_score=score
            ))

        # Ordena por relevância (decrescente)
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)

        return filtered

    def deduplicate(
        self,
        results: list[SearchResult],
        similarity_threshold: float = 0.85
    ) -> list[SearchResult]:
        """
        Remove resultados duplicados/muito similares.
        
        Usa SequenceMatcher para comparar títulos.
        """
        if not results:
            return []

        deduplicated = [results[0]]

        for current in results[1:]:
            is_duplicate = False

            for existing in deduplicated:
                # Compara títulos
                if existing.title and current.title:
                    similarity = SequenceMatcher(
                        None,
                        existing.title.lower(),
                        current.title.lower()
                    ).ratio()

                    if similarity >= similarity_threshold:
                        is_duplicate = True
                        break

            if not is_duplicate:
                deduplicated.append(current)

        return deduplicated


def optimize_search_results(
    query: str,
    results: list[tuple[str, str | None, float | None, str | None]],
    max_results: int = 100,
    remove_duplicates: bool = True
) -> list[SearchResult]:
    """
    Otimiza resultados de busca aplicando todos os filtros.
    
    Args:
        query: termo de busca
        results: lista de (url, title, price, currency)
        max_results: número máximo de resultados
        remove_duplicates: se deve remover duplicados
        
    Returns:
        Lista de SearchResult ordenada por relevância
    """
    optimizer = SearchOptimizer(query)

    # Filtra e ordena por relevância
    ranked = optimizer.filter_and_rank(results)

    # Remove duplicados se configurado
    if remove_duplicates:
        ranked = optimizer.deduplicate(ranked)

    # Limita ao máximo solicitado
    return ranked[:max_results]
