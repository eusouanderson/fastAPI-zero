"""Backward-compatible models module.

Prefer importing from fastapi_zero.db.models.
"""

from fastapi_zero.db.models import PriceRecord, Product, User, table_registry

__all__ = ['PriceRecord', 'Product', 'User', 'table_registry']
