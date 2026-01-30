"""Backward-compatible database module.

Prefer importing from fastapi_zero.db.session.
"""

from fastapi_zero.db.session import engine, get_session

__all__ = ['engine', 'get_session']
