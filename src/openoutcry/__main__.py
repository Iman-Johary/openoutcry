"""Two entrypoints, one image: `predict` and `score`. Plus `report` for a local look at the record.

They are deliberately separate. Scoring must be re-runnable and prediction must never be, the scorer
needs no LLM credentials, and the two must fail independently so that an outage costs one thing
rather than two.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime

from .config import load_config
from .pipeline.predict import run_predict
from .pipeline.score import run_score
from .store import Store


def _parse_ts(value: str) -> datetime:
    if value in ("now", "", None):
        return datetime.now(tz=UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openoutcry")
    parser.add_argument("--config", default="config/config.example.yaml")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("predict", help="write predictions for one cutoff")
    p.add_argument("--as-of", default="now")

    s = sub.add_parser("score", help="settle every prediction maturing at this cutoff")
    s.add_argument("--as-of", default="now")

    sub.add_parser("report", help="print the leaderboard")

    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.cmd == "predict":
        n = run_predict(cfg, _parse_ts(args.as_of))
        print(f"wrote {n} predictions")
    elif args.cmd == "score":
        n = run_score(cfg, _parse_ts(args.as_of))
        print(f"wrote {n} scores")
    elif args.cmd == "report":
        store = Store(cfg.db_path)
        rows = store.leaderboard()
        store.close()
        if not rows:
            print("no scores yet")
            return 0
        print(f"{'strategy':<26}{'h':>4}{'n':>6}{'spearman':>11}{'ndcg':>9}{'prec':>8}{'ls_bps':>10}")
        for r in rows:
            print(
                f"{r['strategy_id']:<26}{r['horizon_h']:>4}{r['n']:>6}"
                f"{r['spearman']:>11.4f}{r['ndcg']:>9.4f}"
                f"{r['precision_at_k']:>8.3f}{r['long_short_bps']:>10.1f}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
