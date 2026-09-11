"""Ranking metrics.

Implemented directly rather than pulled from scipy, so the definitions used in the published record
are visible in the repository and cannot drift with a dependency upgrade.
"""

from __future__ import annotations

import numpy as np

SCORER_VERSION = "1"


def _ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks, 1-based, ties shared."""
    order = values.argsort()
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(values) + 1, dtype=float)
    # average tied ranks
    uniq, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    for idx, c in enumerate(counts):
        if c > 1:
            mask = inverse == idx
            ranks[mask] = ranks[mask].mean()
    return ranks


def spearman(predicted_order: tuple[str, ...], realised: dict[str, float]) -> float:
    """Spearman correlation between the predicted ordering and realised returns.

    predicted_order is best-first, so predicted rank 1 is the best. Realised returns are ranked
    descending so that the two agree in direction.
    """
    assets = [a for a in predicted_order if a in realised]
    n = len(assets)
    if n < 2:
        return float("nan")
    pred_rank = np.arange(1, n + 1, dtype=float)
    real_rank = _ranks(-np.array([realised[a] for a in assets], dtype=float))
    pm, rm = pred_rank.mean(), real_rank.mean()
    num = float(((pred_rank - pm) * (real_rank - rm)).sum())
    den = float(np.sqrt(((pred_rank - pm) ** 2).sum() * ((real_rank - rm) ** 2).sum()))
    return num / den if den else float("nan")


def _gains(realised: dict[str, float], assets: list[str]) -> dict[str, float]:
    """Graded relevance: how many assets this one beat, 0..n-1."""
    vals = np.array([realised[a] for a in assets], dtype=float)
    ranks_desc = _ranks(-vals)
    return {a: float(len(assets) - r) for a, r in zip(assets, ranks_desc, strict=True)}


def ndcg_at_k(predicted_order: tuple[str, ...], realised: dict[str, float], k: int = 5) -> float:
    assets = [a for a in predicted_order if a in realised]
    if not assets:
        return float("nan")
    k = min(k, len(assets))
    gains = _gains(realised, assets)
    disc = 1.0 / np.log2(np.arange(2, k + 2))
    dcg = float(sum(gains[a] * d for a, d in zip(assets[:k], disc, strict=True)))
    ideal = sorted(gains.values(), reverse=True)[:k]
    idcg = float(sum(g * d for g, d in zip(ideal, disc, strict=True)))
    return dcg / idcg if idcg else float("nan")


def precision_at_k(
    predicted_order: tuple[str, ...], realised: dict[str, float], k: int = 5
) -> float:
    """Share of the predicted top k that finished above the cross-sectional median."""
    assets = [a for a in predicted_order if a in realised]
    if not assets:
        return float("nan")
    k = min(k, len(assets))
    median = float(np.median([realised[a] for a in assets]))
    hits = sum(1 for a in assets[:k] if realised[a] > median)
    return hits / k


def long_short_bps(
    predicted_order: tuple[str, ...],
    realised: dict[str, float],
    k: int = 5,
    cost_bps_round_trip: float = 20.0,
) -> float:
    """Equal-weight long top k, short bottom k, net of an assumed round-trip cost.

    The cost is charged on both legs, which is why it is subtracted once per leg rather than once
    per basket. The assumption is stated rather than hidden: see PREREGISTRATION.md §7.
    """
    assets = [a for a in predicted_order if a in realised]
    if len(assets) < 2 * k:
        k = max(1, len(assets) // 2)
    longs = [realised[a] for a in assets[:k]]
    shorts = [realised[a] for a in assets[-k:]]
    gross = float(np.mean(longs) - np.mean(shorts))
    return gross * 10_000.0 - 2.0 * cost_bps_round_trip
