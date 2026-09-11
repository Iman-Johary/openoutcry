"""The Strategy protocol and its registry.

Baselines, the single-call ranker, the full agent and every ablation are all strategies behind one
interface, registered by id and scored identically. Adding a ranking idea is a module and one
registry line, never a fork of the pipeline.

Strategy ids are versioned (`name@version`). A change to a strategy is a new id, never an edit to an
existing one: see PREREGISTRATION.md §6.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..types import Bundle


@runtime_checkable
class Strategy(Protocol):
    id: str
    uses_llm: bool

    def rank(self, bundle: Bundle, horizon_h: int) -> tuple[str, ...]:
        """Return every asset in the bundle, best expected relative return first."""


REGISTRY: dict[str, type] = {}


def register_strategy(strategy_id: str):
    def deco(cls):
        if strategy_id in REGISTRY:
            raise ValueError(f"strategy id {strategy_id!r} already registered")
        cls.id = strategy_id
        REGISTRY[strategy_id] = cls
        return cls

    return deco


def get_strategy(strategy_id: str) -> Strategy:
    if strategy_id not in REGISTRY:
        raise KeyError(f"unknown strategy {strategy_id!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[strategy_id]()


def validate_ordering(ordering: tuple[str, ...], bundle: Bundle) -> None:
    if set(ordering) != set(bundle.assets):
        missing = set(bundle.assets) - set(ordering)
        extra = set(ordering) - set(bundle.assets)
        raise ValueError(
            f"ordering must be a permutation of the universe; missing={missing} extra={extra}"
        )
    if len(ordering) != len(set(ordering)):
        raise ValueError("ordering contains duplicates")
