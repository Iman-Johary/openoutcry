"""The score entrypoint.

Settles every prediction whose horizon matures at this cutoff, for every strategy, and appends
the result. Runs with no LLM credentials at all, which is one reason it is a separate entrypoint.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from ..clock import as_utc, due_at, floor_to_cutoff
from ..config import Config
from ..scoring.metrics import (
    SCORER_VERSION,
    long_short_bps,
    ndcg_at_k,
    precision_at_k,
    spearman,
)
from ..sources import get_price_source
from ..store import Store
from ..types import Score


def realised_relative_returns(cfg: Config, as_of: datetime, horizon_h: int) -> dict[str, float]:
    price = get_price_source(cfg.raw["sources"]["price"])
    settle = as_of + timedelta(hours=horizon_h)
    bars = price.bars(cfg.assets, as_of - timedelta(hours=1), settle)
    start: dict[str, float] = {}
    end: dict[str, float] = {}
    for b in bars:
        ts = as_utc(b.ts)
        if ts == as_utc(as_of):
            start[b.asset] = b.close
        if ts == as_utc(settle):
            end[b.asset] = b.close
    return {
        a: end[a] / start[a] - 1.0 for a in cfg.assets if a in start and a in end and start[a] > 0
    }


def run_score(cfg: Config, at: datetime) -> int:
    at = floor_to_cutoff(as_utc(at), cfg.cutoff_hours)
    store = Store(cfg.db_path)
    written = 0
    try:
        for as_of, horizon in due_at(at, cfg.horizons_h, cfg.cutoff_hours):
            preds = store.predictions_for(as_of, horizon)
            if not preds:
                continue
            realised = realised_relative_returns(cfg, as_of, horizon)
            if len(realised) < 2:
                continue
            for strategy_id, ordering in preds:
                store.write_score(
                    Score(
                        as_of=as_of,
                        strategy_id=strategy_id,
                        horizon_h=horizon,
                        settled_at=at,
                        n_assets=len(realised),
                        spearman=spearman(ordering, realised),
                        ndcg_at_k=ndcg_at_k(ordering, realised, cfg.top_k),
                        precision_at_k=precision_at_k(ordering, realised, cfg.top_k),
                        long_short_bps=long_short_bps(
                            ordering, realised, cfg.top_k, cfg.cost_bps
                        ),
                        scorer_version=SCORER_VERSION,
                    )
                )
                written += 1
        store.record_run(at, "score", "ok", f"{written} scores")
    finally:
        store.close()
    return written
