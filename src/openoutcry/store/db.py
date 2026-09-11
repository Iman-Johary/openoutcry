"""Append-only SQLite store.

Predictions are immutable: the database itself refuses UPDATE and DELETE on that table, so the
guarantee does not depend on anyone remembering it.

Scores are append-only too, but they carry a scorer_version and computed_at. That is how scoring can
be re-runnable while the record stays immutable: fixing a metric bug appends a new set of score rows
instead of editing the old ones, and the record shows both what was computed and what it was
corrected to. This is also why predict and score are two entrypoints and not one job.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from ..types import Prediction, Score

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    as_of TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    horizon_h INTEGER NOT NULL,
    ordering TEXT NOT NULL,
    predicted_at TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    memory_version TEXT,
    model_versions TEXT NOT NULL,
    rationales TEXT NOT NULL,
    reason_codes TEXT NOT NULL,
    input_doc_ids TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    PRIMARY KEY (as_of, strategy_id, horizon_h)
);

CREATE TRIGGER IF NOT EXISTS predictions_no_update
BEFORE UPDATE ON predictions
BEGIN SELECT RAISE(ABORT, 'predictions is append-only'); END;

CREATE TRIGGER IF NOT EXISTS predictions_no_delete
BEFORE DELETE ON predictions
BEGIN SELECT RAISE(ABORT, 'predictions is append-only'); END;

CREATE TABLE IF NOT EXISTS scores (
    as_of TEXT NOT NULL,
    strategy_id TEXT NOT NULL,
    horizon_h INTEGER NOT NULL,
    settled_at TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    scorer_version TEXT NOT NULL,
    n_assets INTEGER NOT NULL,
    spearman REAL,
    ndcg_at_k REAL,
    precision_at_k REAL,
    long_short_bps REAL,
    PRIMARY KEY (as_of, strategy_id, horizon_h, scorer_version)
);

CREATE TRIGGER IF NOT EXISTS scores_no_update
BEFORE UPDATE ON scores
BEGIN SELECT RAISE(ABORT, 'scores is append-only; append a new scorer_version instead'); END;

CREATE TRIGGER IF NOT EXISTS scores_no_delete
BEFORE DELETE ON scores
BEGIN SELECT RAISE(ABORT, 'scores is append-only'); END;

CREATE TABLE IF NOT EXISTS runs (
    as_of TEXT NOT NULL,
    kind TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    note TEXT,
    PRIMARY KEY (as_of, kind, started_at)
);
"""


def _iso(ts: datetime) -> str:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).isoformat()


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # predictions -----------------------------------------------------------
    def write_prediction(self, p: Prediction, payload_sha256: str) -> None:
        self.conn.execute(
            "INSERT INTO predictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                _iso(p.as_of),
                p.strategy_id,
                p.horizon_h,
                json.dumps(list(p.ordering)),
                _iso(p.predicted_at),
                p.config_hash,
                p.memory_version,
                json.dumps(p.model_versions, sort_keys=True),
                json.dumps(p.rationales, sort_keys=True),
                json.dumps({k: list(v) for k, v in p.reason_codes.items()}, sort_keys=True),
                json.dumps(list(p.input_doc_ids)),
                payload_sha256,
            ),
        )
        self.conn.commit()

    def predictions_for(self, as_of: datetime, horizon_h: int) -> list[tuple[str, tuple[str, ...]]]:
        rows = self.conn.execute(
            "SELECT strategy_id, ordering FROM predictions WHERE as_of=? AND horizon_h=?",
            (_iso(as_of), horizon_h),
        ).fetchall()
        return [(r["strategy_id"], tuple(json.loads(r["ordering"]))) for r in rows]

    def count_predictions(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) c FROM predictions").fetchone()["c"])

    # scores ----------------------------------------------------------------
    def write_score(self, s: Score) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO scores VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                _iso(s.as_of),
                s.strategy_id,
                s.horizon_h,
                _iso(s.settled_at),
                _iso(datetime.now(tz=UTC)),
                s.scorer_version,
                s.n_assets,
                s.spearman,
                s.ndcg_at_k,
                s.precision_at_k,
                s.long_short_bps,
            ),
        )
        self.conn.commit()

    def leaderboard(self, horizon_h: int | None = None) -> list[dict]:
        """Every strategy that has ever been scored, including retired ones.

        PREREGISTRATION.md §6.4: no strategy is ever removed from the leaderboard.
        """
        sql = (
            "SELECT strategy_id, horizon_h, COUNT(*) n, AVG(spearman) spearman, "
            "AVG(ndcg_at_k) ndcg, AVG(precision_at_k) precision_at_k, "
            "AVG(long_short_bps) long_short_bps FROM scores "
        )
        params: tuple = ()
        if horizon_h is not None:
            sql += "WHERE horizon_h=? "
            params = (horizon_h,)
        sql += "GROUP BY strategy_id, horizon_h ORDER BY horizon_h, spearman DESC"
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    # runs ------------------------------------------------------------------
    def record_run(self, as_of: datetime, kind: str, status: str, note: str = "") -> None:
        now = _iso(datetime.now(tz=UTC))
        self.conn.execute(
            "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?)",
            (_iso(as_of), kind, now, now, status, note),
        )
        self.conn.commit()
