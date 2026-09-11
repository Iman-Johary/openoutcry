"""The point-in-time guard.

This is the most important file in the repository. The entire credibility of the record rests on one
property: nothing that was published at or after a run's cutoff may influence that run.

Three things can violate it:
  1. a news document published at or after the cutoff;
  2. a price bar closing after the cutoff;
  3. a memory version built after the cutoff, loaded because it happened to be "the current one".

The third is the easiest to introduce and the hardest to notice afterwards, which is why it is
asserted here rather than left to discipline.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime

from .clock import as_utc
from .types import NewsDoc, PriceBar


class LeakageError(RuntimeError):
    """Raised when an input could not have been known at the cutoff."""


def filter_docs_point_in_time(docs: Iterable[NewsDoc], cutoff: datetime) -> tuple[NewsDoc, ...]:
    """Drop anything published at or after the cutoff. Use on ingest, before anything else."""
    cutoff = as_utc(cutoff)
    return tuple(d for d in docs if as_utc(d.published_at) < cutoff)


def assert_docs_point_in_time(docs: Sequence[NewsDoc], cutoff: datetime) -> None:
    cutoff = as_utc(cutoff)
    bad = [d.doc_id for d in docs if as_utc(d.published_at) >= cutoff]
    if bad:
        raise LeakageError(
            f"{len(bad)} document(s) published at or after cutoff {cutoff.isoformat()}: "
            f"{bad[:5]}{' ...' if len(bad) > 5 else ''}"
        )


def assert_bars_point_in_time(bars: Sequence[PriceBar], cutoff: datetime) -> None:
    """A bar closing exactly at the cutoff is the cutoff price and is allowed. Later is not."""
    cutoff = as_utc(cutoff)
    bad = [(b.asset, b.ts.isoformat()) for b in bars if as_utc(b.ts) > cutoff]
    if bad:
        raise LeakageError(
            f"{len(bad)} price bar(s) close after cutoff {cutoff.isoformat()}: "
            f"{bad[:5]}{' ...' if len(bad) > 5 else ''}"
        )


def assert_memory_version_allowed(memory_as_of: datetime | None, cutoff: datetime) -> None:
    """A run loads the memory version at or before its own cutoff, never the current one."""
    if memory_as_of is None:
        return
    cutoff = as_utc(cutoff)
    if as_utc(memory_as_of) > cutoff:
        raise LeakageError(
            f"memory version as_of {as_utc(memory_as_of).isoformat()} is later than "
            f"cutoff {cutoff.isoformat()}; a retrospective run must load the pinned version"
        )
