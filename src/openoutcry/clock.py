"""Cutoffs, horizons, and what settles when.

The clock is defined by the cutoff, never by wall-clock time at execution. A run that starts late is
still valid: it sees the same evidence window and the same price snapshot it would have seen
on time.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

CUTOFF_HOURS: tuple[int, ...] = (0, 6, 12, 18)
HORIZONS_H: tuple[int, ...] = (6, 12, 24)


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


def as_utc(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC)


def is_cutoff(ts: datetime, cutoff_hours: tuple[int, ...] = CUTOFF_HOURS) -> bool:
    ts = as_utc(ts)
    return ts.hour in cutoff_hours and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0


def floor_to_cutoff(ts: datetime, cutoff_hours: tuple[int, ...] = CUTOFF_HOURS) -> datetime:
    """The most recent cutoff at or before ts."""
    ts = as_utc(ts).replace(minute=0, second=0, microsecond=0)
    for h in sorted(cutoff_hours, reverse=True):
        if ts.hour >= h:
            return ts.replace(hour=h)
    return (ts - timedelta(days=1)).replace(hour=max(cutoff_hours))


def previous_cutoff(ts: datetime, cutoff_hours: tuple[int, ...] = CUTOFF_HOURS) -> datetime:
    """The cutoff strictly before the one at ts. Defines the news window [previous, this)."""
    this = floor_to_cutoff(ts, cutoff_hours)
    return floor_to_cutoff(this - timedelta(seconds=1), cutoff_hours)


def settles_at(as_of: datetime, horizon_h: int) -> datetime:
    return as_utc(as_of) + timedelta(hours=horizon_h)


def due_at(
    cutoff: datetime,
    horizons: tuple[int, ...] = HORIZONS_H,
    cutoff_hours: tuple[int, ...] = CUTOFF_HOURS,
) -> list[tuple[datetime, int]]:
    """(as_of, horizon) pairs whose outcome is known exactly at this cutoff."""
    cutoff = as_utc(cutoff)
    out: list[tuple[datetime, int]] = []
    for h in horizons:
        origin = cutoff - timedelta(hours=h)
        if is_cutoff(origin, cutoff_hours):
            out.append((origin, h))
    return out
