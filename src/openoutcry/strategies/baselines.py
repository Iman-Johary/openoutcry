"""The five pre-registered baselines. No LLM, no network, fully deterministic.

These go live before the agent so that the record can never consist of the agent alone.
"""

from __future__ import annotations

import hashlib

import numpy as np

from ..types import Bundle
from .base import register_strategy


def _sorted_by(bundle: Bundle, key, reverse: bool = True) -> tuple[str, ...]:
    def value(asset: str) -> float:
        return key(bundle.features[asset]) if asset in bundle.features else 0.0

    return tuple(sorted(bundle.assets, key=value, reverse=reverse))


@register_strategy("random_permutation@1")
class RandomPermutation:
    uses_llm = False

    def rank(self, bundle: Bundle, horizon_h: int) -> tuple[str, ...]:
        digest = hashlib.sha256(f"{bundle.as_of.isoformat()}|{horizon_h}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big") % (2**32))
        assets = list(bundle.assets)
        rng.shuffle(assets)
        return tuple(assets)


@register_strategy("momentum_24h@1")
class Momentum24h:
    uses_llm = False

    def rank(self, bundle: Bundle, horizon_h: int) -> tuple[str, ...]:
        return _sorted_by(bundle, lambda f: f.ret_24h, reverse=True)


@register_strategy("momentum_7d@1")
class Momentum7d:
    uses_llm = False

    def rank(self, bundle: Bundle, horizon_h: int) -> tuple[str, ...]:
        return _sorted_by(bundle, lambda f: f.ret_7d, reverse=True)


@register_strategy("reversal_24h@1")
class Reversal24h:
    uses_llm = False

    def rank(self, bundle: Bundle, horizon_h: int) -> tuple[str, ...]:
        return _sorted_by(bundle, lambda f: f.ret_24h, reverse=False)


@register_strategy("volume_change@1")
class VolumeChange:
    uses_llm = False

    def rank(self, bundle: Bundle, horizon_h: int) -> tuple[str, ...]:
        return _sorted_by(bundle, lambda f: f.volume_z, reverse=True)
