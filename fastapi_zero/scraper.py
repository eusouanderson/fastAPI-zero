"""Backward compatibility shim - import from services.scraper instead."""

from fastapi_zero.services.scraper import (
    MIN_PRICE_LENGTH,
    PRICE_PATTERNS,
    DiscoveryConfig,
    DiscoveryFilters,
    ScrapedItem,
    Scraper,
)

__all__ = [
    'MIN_PRICE_LENGTH',
    'PRICE_PATTERNS',
    'DiscoveryConfig',
    'DiscoveryFilters',
    'ScrapedItem',
    'Scraper',
]
