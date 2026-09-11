"""Core data types. Anything crossing a module boundary is one of these."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PriceBar:
    asset: str
    ts: datetime  # bar close time, UTC
    close: float
    volume: float


@dataclass(frozen=True)
class NewsDoc:
    doc_id: str
    asset: str
    published_at: datetime
    title: str
    source: str
    topic: str | None = None


@dataclass(frozen=True)
class AssetFeatures:
    asset: str
    ret_6h: float
    ret_24h: float
    ret_7d: float
    vol_24h: float
    volume_z: float
    rsi_14: float


@dataclass(frozen=True)
class Bundle:
    """Everything a Strategy is allowed to see for one run. Nothing else is reachable from it."""

    as_of: datetime
    assets: tuple[str, ...]
    features: dict[str, AssetFeatures]
    news: dict[str, tuple[NewsDoc, ...]]
    memory_version: str | None = None


@dataclass(frozen=True)
class Prediction:
    as_of: datetime
    strategy_id: str
    horizon_h: int
    ordering: tuple[str, ...]
    predicted_at: datetime
    config_hash: str = ""
    memory_version: str | None = None
    model_versions: dict[str, str] = field(default_factory=dict)
    rationales: dict[str, str] = field(default_factory=dict)
    reason_codes: dict[str, tuple[str, ...]] = field(default_factory=dict)
    input_doc_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Score:
    as_of: datetime
    strategy_id: str
    horizon_h: int
    settled_at: datetime
    n_assets: int
    spearman: float
    ndcg_at_k: float
    precision_at_k: float
    long_short_bps: float
    scorer_version: str
