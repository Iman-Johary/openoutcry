"""Market features, computed in code.

The model never reads a chart. Anything that can be computed from the price series belongs here and
is deliberately kept out of the narrative memory layer, which exists for what numbers cannot hold.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import numpy as np

from ..clock import as_utc
from ..types import AssetFeatures, PriceBar


def _rsi(closes: np.ndarray, period: int = 14) -> float:
    if closes.size < period + 1:
        return 50.0
    diffs = np.diff(closes[-(period + 1) :])
    gains = np.clip(diffs, 0, None).mean()
    losses = -np.clip(diffs, None, 0).mean()
    if losses == 0:
        return 100.0
    rs = gains / losses
    return float(100.0 - 100.0 / (1.0 + rs))


def _ret(closes: np.ndarray, hours: int) -> float:
    if closes.size <= hours:
        return 0.0
    return float(closes[-1] / closes[-1 - hours] - 1.0)


def compute_features(bars: list[PriceBar], cutoff: datetime) -> dict[str, AssetFeatures]:
    cutoff = as_utc(cutoff)
    by_asset: dict[str, list[PriceBar]] = defaultdict(list)
    for b in bars:
        if as_utc(b.ts) <= cutoff:
            by_asset[b.asset].append(b)

    feats: dict[str, AssetFeatures] = {}
    for asset, rows in by_asset.items():
        rows.sort(key=lambda b: b.ts)
        closes = np.array([r.close for r in rows], dtype=float)
        volumes = np.array([r.volume for r in rows], dtype=float)
        if closes.size < 2:
            continue
        hourly = np.diff(np.log(closes))
        window = hourly[-24:] if hourly.size >= 24 else hourly
        vol_24h = float(window.std(ddof=0)) if window.size else 0.0
        recent_v = volumes[-24:] if volumes.size >= 24 else volumes
        base_v = volumes[-168:] if volumes.size >= 168 else volumes
        sd = float(base_v.std(ddof=0))
        volume_z = float((recent_v.mean() - base_v.mean()) / sd) if sd > 0 else 0.0
        feats[asset] = AssetFeatures(
            asset=asset,
            ret_6h=_ret(closes, 6),
            ret_24h=_ret(closes, 24),
            ret_7d=_ret(closes, 24 * 7),
            vol_24h=vol_24h,
            volume_z=volume_z,
            rsi_14=_rsi(closes),
        )
    return feats
