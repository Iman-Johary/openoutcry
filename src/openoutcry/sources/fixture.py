"""Deterministic fixture sources.

No network, no keys, reproducible from (asset, timestamp). They exist so the pipeline, the store,
the metrics and the leakage guard are all exercised end to end before a real venue is chosen, and so
that CI never depends on a third party being up.

The news fixture deliberately emits some documents published *after* the requested window, so the
leakage guard has something real to catch in tests.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

import numpy as np

from ..clock import as_utc
from ..types import NewsDoc, PriceBar
from .base import register_news_source, register_price_source

_TOPICS = ("macro_rates", "regulatory", "protocol_upgrade", "sentiment_shift", "onchain_flow")


def _seed(*parts: str) -> int:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big") % (2**32)


@register_price_source("fixture")
class FixturePriceSource:
    name = "fixture"

    def bars(self, assets: tuple[str, ...], start: datetime, end: datetime) -> list[PriceBar]:
        start, end = as_utc(start), as_utc(end)
        out: list[PriceBar] = []
        for asset in assets:
            rng = np.random.default_rng(_seed("price", asset))
            # one continuous series anchored at a fixed epoch, so repeated calls agree
            epoch = datetime(2026, 1, 1, tzinfo=start.tzinfo)
            total_hours = int((end - epoch).total_seconds() // 3600) + 1
            if total_hours <= 0:
                continue
            steps = rng.normal(0.0, 0.01, size=total_hours)
            path = 100.0 * np.exp(np.cumsum(steps))
            vols = rng.lognormal(mean=10.0, sigma=0.4, size=total_hours)
            for i in range(total_hours):
                ts = epoch + timedelta(hours=i)
                if start <= ts <= end:
                    out.append(PriceBar(asset=asset, ts=ts, close=float(path[i]),
                                        volume=float(vols[i])))
        return out


@register_news_source("fixture")
class FixtureNewsSource:
    name = "fixture"

    def docs(self, assets: tuple[str, ...], start: datetime, end: datetime) -> list[NewsDoc]:
        start, end = as_utc(start), as_utc(end)
        span_h = max(1, int((end - start).total_seconds() // 3600))
        out: list[NewsDoc] = []
        for asset in assets:
            rng = np.random.default_rng(_seed("news", asset, start.isoformat()))
            n = int(rng.integers(0, 4))
            for k in range(n):
                offset = float(rng.uniform(0, span_h))
                published = start + timedelta(hours=offset)
                topic = _TOPICS[int(rng.integers(0, len(_TOPICS)))]
                out.append(
                    NewsDoc(
                        doc_id=f"{asset}-{start:%Y%m%dT%H}-{k}",
                        asset=asset,
                        published_at=published,
                        title=f"[fixture] {topic} item for {asset}",
                        source="fixture",
                        topic=topic,
                    )
                )
            # one item published just after the window, on purpose: the guard must drop it
            out.append(
                NewsDoc(
                    doc_id=f"{asset}-{start:%Y%m%dT%H}-future",
                    asset=asset,
                    published_at=end + timedelta(minutes=1),
                    title=f"[fixture] post-cutoff item for {asset}",
                    source="fixture",
                    topic="sentiment_shift",
                )
            )
        return out
