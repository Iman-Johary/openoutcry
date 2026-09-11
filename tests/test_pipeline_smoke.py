"""End to end on fixture data: predict, settle, and read the record back."""

from __future__ import annotations

from datetime import timedelta

from openoutcry.pipeline.predict import run_predict
from openoutcry.pipeline.score import run_score
from openoutcry.store import Store


def test_predict_then_score_produces_a_leaderboard(cfg, cutoff):
    written = run_predict(cfg, cutoff)
    assert written == len(cfg.strategies) * len(cfg.horizons_h)

    # settle the 24h horizon at the next day's 00:00 cutoff
    scored = run_score(cfg, cutoff + timedelta(hours=24))
    assert scored >= len(cfg.strategies)

    store = Store(cfg.db_path)
    rows = store.leaderboard(horizon_h=24)
    store.close()

    assert {r["strategy_id"] for r in rows} == set(cfg.strategies)
    for r in rows:
        assert r["n"] >= 1
        assert -1.0 <= r["spearman"] <= 1.0


def test_scoring_twice_does_not_duplicate_or_mutate(cfg, cutoff):
    run_predict(cfg, cutoff)
    first = run_score(cfg, cutoff + timedelta(hours=24))
    second = run_score(cfg, cutoff + timedelta(hours=24))
    assert first == second  # idempotent at the same scorer_version

    store = Store(cfg.db_path)
    n = store.conn.execute("SELECT COUNT(*) c FROM scores").fetchone()["c"]
    store.close()
    assert n == first
