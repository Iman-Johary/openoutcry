"""The predict entrypoint.

Builds one point-in-time bundle, runs every registered strategy over every horizon, and appends the
predictions. This entrypoint never scores anything: see store/db.py for why the two are separate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

from ..clock import as_utc, floor_to_cutoff, previous_cutoff
from ..config import Config
from ..features import compute_features
from ..leakage import (
    assert_bars_point_in_time,
    assert_docs_point_in_time,
    assert_memory_version_allowed,
    filter_docs_point_in_time,
)
from ..sources import get_news_source, get_price_source
from ..store import Store
from ..strategies import get_strategy
from ..strategies.base import validate_ordering
from ..types import Bundle, Prediction


def build_bundle(cfg: Config, as_of: datetime, memory_version: str | None = None) -> Bundle:
    as_of = floor_to_cutoff(as_utc(as_of), cfg.cutoff_hours)
    assets = cfg.assets

    price = get_price_source(cfg.raw["sources"]["price"])
    news = get_news_source(cfg.raw["sources"]["news"])

    bars = price.bars(assets, as_of - timedelta(days=30), as_of)
    assert_bars_point_in_time(bars, as_of)

    window_start = previous_cutoff(as_of, cfg.cutoff_hours)
    raw_docs = news.docs(assets, window_start, as_of)
    docs = filter_docs_point_in_time(raw_docs, as_of)
    assert_docs_point_in_time(docs, as_of)  # belt and braces: the filter must have worked

    assert_memory_version_allowed(None if memory_version is None else as_of, as_of)

    by_asset: dict[str, list] = {a: [] for a in assets}
    for d in docs:
        by_asset.setdefault(d.asset, []).append(d)

    return Bundle(
        as_of=as_of,
        assets=assets,
        features=compute_features(bars, as_of),
        news={a: tuple(v) for a, v in by_asset.items()},
        memory_version=memory_version,
    )


def _payload_hash(p: Prediction) -> str:
    blob = json.dumps(
        {
            "as_of": p.as_of.isoformat(),
            "strategy_id": p.strategy_id,
            "horizon_h": p.horizon_h,
            "ordering": list(p.ordering),
            "config_hash": p.config_hash,
            "memory_version": p.memory_version,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def run_predict(cfg: Config, as_of: datetime) -> int:
    store = Store(cfg.db_path)
    bundle = build_bundle(cfg, as_of)
    written = 0
    try:
        for sid in cfg.strategies:
            strategy = get_strategy(sid)
            for horizon in cfg.horizons_h:
                ordering = strategy.rank(bundle, horizon)
                validate_ordering(ordering, bundle)
                pred = Prediction(
                    as_of=bundle.as_of,
                    strategy_id=sid,
                    horizon_h=horizon,
                    ordering=ordering,
                    predicted_at=datetime.now(tz=UTC),
                    config_hash=cfg.config_hash,
                    memory_version=bundle.memory_version,
                    input_doc_ids=tuple(
                        d.doc_id for docs in bundle.news.values() for d in docs
                    ),
                )
                store.write_prediction(pred, _payload_hash(pred))
                written += 1
        store.record_run(bundle.as_of, "predict", "ok", f"{written} predictions")
    finally:
        store.close()
    return written
