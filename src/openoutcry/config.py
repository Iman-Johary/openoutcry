"""Configuration loading, and the config hash that every prediction carries."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any]
    path: Path

    @property
    def cutoff_hours(self) -> tuple[int, ...]:
        return tuple(self.raw["run"]["cutoff_hours"])

    @property
    def horizons_h(self) -> tuple[int, ...]:
        return tuple(self.raw["run"]["horizons_h"])

    @property
    def top_k(self) -> int:
        return int(self.raw["run"]["top_k"])

    @property
    def cost_bps(self) -> float:
        return float(self.raw["run"]["cost_bps_round_trip"])

    @property
    def assets(self) -> tuple[str, ...]:
        return tuple(self.raw["universe"]["assets"])

    @property
    def strategies(self) -> tuple[str, ...]:
        return tuple(self.raw["strategies"])

    @property
    def db_path(self) -> Path:
        return Path(self.raw["store"]["path"])

    @property
    def config_hash(self) -> str:
        blob = json.dumps(self.raw, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()[:16]


def load_config(path: str | Path) -> Config:
    path = Path(path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return Config(raw=raw, path=path)
