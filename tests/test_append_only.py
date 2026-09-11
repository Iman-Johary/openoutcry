from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from openoutcry.store import Store
from openoutcry.types import Prediction

AS_OF = datetime(2026, 1, 10, 0, 0, tzinfo=UTC)


def _pred() -> Prediction:
    return Prediction(
        as_of=AS_OF,
        strategy_id="momentum_24h@1",
        horizon_h=24,
        ordering=("A", "B", "C"),
        predicted_at=datetime.now(tz=UTC),
        config_hash="deadbeef",
    )


def test_predictions_cannot_be_updated(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.write_prediction(_pred(), "hash")
    with pytest.raises(sqlite3.IntegrityError):
        store.conn.execute("UPDATE predictions SET ordering='[]'")
    store.close()


def test_predictions_cannot_be_deleted(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.write_prediction(_pred(), "hash")
    with pytest.raises(sqlite3.IntegrityError):
        store.conn.execute("DELETE FROM predictions")
    store.close()


def test_the_same_prediction_cannot_be_written_twice(tmp_path):
    store = Store(tmp_path / "t.sqlite")
    store.write_prediction(_pred(), "hash")
    with pytest.raises(sqlite3.IntegrityError):
        store.write_prediction(_pred(), "hash")
    store.close()
