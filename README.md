# openoutcry

**A public, leakage-free forward-evaluation record for cross-sectional asset ranking.**

Open outcry was how a bid was declared out loud in the open pit, where everyone heard it at the same
moment. This system announces every prediction publicly before the outcome is known, and settles it
against reality afterwards. The artifact is the record, not the return.

> **This is not investment advice.** It is not a recommendation, it is not personalised, and there is
> no brokerage integration. Nothing here should be used to make a financial decision.

## What it does

At fixed cutoffs (00:00, 06:00, 12:00, 18:00 UTC) the system builds a point-in-time bundle of market
features and news for a fixed basket of assets, and every registered strategy ranks the basket by
expected return *relative to the basket median* at 6h, 12h and 24h horizons. A separate scorer
settles each prediction when its horizon matures and appends the result to an append-only record.

## The three commitments

1. **No backtest, ever.** Any LLM used here was trained on text covering any period that could be
   backtested, so a backtest would measure memory rather than forecasting. Forward-only, with a
   leakage guard enforced by a required CI check.
2. **Baselines go live before the agent.** M1 contains no LLM at all, so the agent is never the first
   thing measured and can never be the only thing measured.
3. **Pre-registration before the first prediction.** See `PREREGISTRATION.md`. The commit history is
   the proof that the metrics and baselines were chosen before any results existed.

## Status

**M0.** Scaffold only. No live data source, no deployment, no predictions. The pipeline runs
end-to-end on deterministic fixture data so that the interfaces, the store, the metrics and the
leakage guard are all exercised by tests.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# one prediction run on fixture data
python -m openoutcry predict --as-of 2026-01-02T00:00:00Z --config config/config.example.yaml

# settle everything that matured at a later cutoff
python -m openoutcry score --as-of 2026-01-03T00:00:00Z --config config/config.example.yaml

# the record
python -m openoutcry report --config config/config.example.yaml
```

## Layout

| Path | What |
|---|---|
| `src/openoutcry/leakage.py` | The point-in-time guard. The most important file in the repo |
| `src/openoutcry/clock.py` | Cutoffs, horizons, and what settles when |
| `src/openoutcry/sources/` | `PriceSource` and `NewsSource` protocols, plus a deterministic fixture implementation |
| `src/openoutcry/strategies/` | The `Strategy` protocol, the registry, and the five non-LLM baselines |
| `src/openoutcry/scoring/` | Metrics (Spearman, nDCG@k, precision@k, long-short) and the scorer |
| `src/openoutcry/store/` | Append-only SQLite store, enforced by triggers |
| `tests/test_leakage_guard.py` | The required CI check |

## Why the store is append-only but scoring is still re-runnable

Predictions are immutable: a row is written once and the database refuses `UPDATE` and `DELETE` on
that table. Scores are also append-only, but they carry a `scorer_version` and a `computed_at`, so
fixing a metric bug means appending a new set of score rows rather than editing the old ones. The
record then shows both what was computed and what it was corrected to.
