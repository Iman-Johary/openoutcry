"""Source protocols.

Adapters are deliberately generic. Crypto is the starting universe, not the scope: an equities or
commodities adapter implements the same two protocols and nothing above this layer changes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ..types import NewsDoc, PriceBar


@runtime_checkable
class PriceSource(Protocol):
    name: str

    def bars(self, assets: tuple[str, ...], start: datetime, end: datetime) -> list[PriceBar]:
        """Hourly bars closing in [start, end]. Never returns a bar closing after end."""


@runtime_checkable
class NewsSource(Protocol):
    name: str

    def docs(self, assets: tuple[str, ...], start: datetime, end: datetime) -> list[NewsDoc]:
        """Documents published in [start, end). The caller still applies the leakage guard."""


_PRICE: dict[str, type] = {}
_NEWS: dict[str, type] = {}


def register_price_source(name: str):
    def deco(cls):
        _PRICE[name] = cls
        return cls

    return deco


def register_news_source(name: str):
    def deco(cls):
        _NEWS[name] = cls
        return cls

    return deco


def get_price_source(name: str) -> PriceSource:
    from . import fixture  # noqa: F401  (registers the built-ins)

    if name not in _PRICE:
        raise KeyError(f"unknown price source {name!r}; known: {sorted(_PRICE)}")
    return _PRICE[name]()


def get_news_source(name: str) -> NewsSource:
    from . import fixture  # noqa: F401

    if name not in _NEWS:
        raise KeyError(f"unknown news source {name!r}; known: {sorted(_NEWS)}")
    return _NEWS[name]()
