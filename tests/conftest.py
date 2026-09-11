from __future__ import annotations

from datetime import UTC, datetime

import pytest
import yaml

from openoutcry.config import load_config


@pytest.fixture
def cutoff() -> datetime:
    return datetime(2026, 1, 10, 0, 0, tzinfo=UTC)


@pytest.fixture
def cfg(tmp_path):
    raw = {
        "run": {
            "cutoff_hours": [0, 6, 12, 18],
            "horizons_h": [6, 12, 24],
            "top_k": 3,
            "cost_bps_round_trip": 20,
        },
        "universe": {"assets": ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"]},
        "sources": {"price": "fixture", "news": "fixture"},
        "strategies": [
            "random_permutation@1",
            "momentum_24h@1",
            "momentum_7d@1",
            "reversal_24h@1",
            "volume_change@1",
        ],
        "store": {"path": str(tmp_path / "test.sqlite")},
    }
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return load_config(path)
