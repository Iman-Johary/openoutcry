"""The required CI check.

Everything else in this repository can be rebuilt. If these tests stop passing, or stop existing,
the forward record stops meaning anything, because nothing else prevents a document published after
the cutoff from reaching a prediction that claims to predate it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from openoutcry.leakage import (
    LeakageError,
    assert_bars_point_in_time,
    assert_docs_point_in_time,
    assert_memory_version_allowed,
    filter_docs_point_in_time,
)
from openoutcry.pipeline.predict import build_bundle
from openoutcry.types import NewsDoc, PriceBar

CUTOFF = datetime(2026, 1, 10, 0, 0, tzinfo=UTC)


def _doc(minutes: int) -> NewsDoc:
    return NewsDoc(
        doc_id=f"d{minutes}",
        asset="AAA",
        published_at=CUTOFF + timedelta(minutes=minutes),
        title="t",
        source="test",
    )


def test_document_published_after_cutoff_is_rejected():
    with pytest.raises(LeakageError):
        assert_docs_point_in_time([_doc(1)], CUTOFF)


def test_document_published_exactly_at_cutoff_is_rejected():
    # The window is [previous cutoff, cutoff). A document stamped exactly at the cutoff is
    # simultaneous with the price snapshot and is not admissible.
    with pytest.raises(LeakageError):
        assert_docs_point_in_time([_doc(0)], CUTOFF)


def test_document_published_before_cutoff_is_accepted():
    assert_docs_point_in_time([_doc(-1)], CUTOFF)


def test_filter_drops_future_documents_and_keeps_past_ones():
    kept = filter_docs_point_in_time([_doc(-60), _doc(-1), _doc(0), _doc(30)], CUTOFF)
    assert {d.doc_id for d in kept} == {"d-60", "d-1"}


def test_price_bar_closing_at_cutoff_is_allowed_but_later_is_not():
    at = PriceBar(asset="AAA", ts=CUTOFF, close=1.0, volume=1.0)
    later = PriceBar(asset="AAA", ts=CUTOFF + timedelta(hours=1), close=1.0, volume=1.0)
    assert_bars_point_in_time([at], CUTOFF)
    with pytest.raises(LeakageError):
        assert_bars_point_in_time([at, later], CUTOFF)


def test_memory_version_later_than_cutoff_is_rejected():
    assert_memory_version_allowed(CUTOFF - timedelta(days=1), CUTOFF)
    assert_memory_version_allowed(None, CUTOFF)
    with pytest.raises(LeakageError):
        assert_memory_version_allowed(CUTOFF + timedelta(seconds=1), CUTOFF)


def test_built_bundle_contains_no_post_cutoff_documents(cfg, cutoff):
    # The fixture news source deliberately emits a post-cutoff item for every asset.
    bundle = build_bundle(cfg, cutoff)
    for docs in bundle.news.values():
        for d in docs:
            assert d.published_at < cutoff
    assert not any(
        d.doc_id.endswith("future") for docs in bundle.news.values() for d in docs
    )
