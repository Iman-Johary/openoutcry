# Pre-registration

**Status: DRAFT. Fields marked `TBD` must be filled before the first prediction is written.**
Once the first prediction exists, this file is not edited. Changes become a new dated section below,
and the original series keeps running.

Committed before any results exist. The commit history of this file is the evidence.

---

## 1. Universe

- Size: 30 assets.
- Selection: `TBD` (exact query, source and snapshot date, recorded verbatim).
- Rebalance rule: quarterly, same query, decided in advance.
- Delisted assets are retained in the record as delisted and never removed.

## 2. Venue and data

- Price venue: `TBD`. Fallback venue: `TBD`.
- News sources: `TBD` (GDELT plus one asset-news API).

## 3. Clock

- Cutoffs: 00:00, 06:00, 12:00, 18:00 UTC.
- Horizons: 6h, 12h, 24h from each cutoff.
- Every input must satisfy `published_at < cutoff`. Price bars may close exactly at the cutoff.

## 4. Targets

- **Primary target:** cross-sectional rank by realised return relative to the basket median.
- **Secondary target:** market direction, reported on its own tab with its own required-n disclosure.

## 5. The primary cell and the primary strategy

- **Primary cell:** the 00:00 run at the 24h horizon, cross-sectional target.
- **Primary strategy:** the full agent with **all nodes enabled** (news, structured and narrative
  memory, bull/bear debate, judge, grounding critic, cross-sectional ranker), in its default
  configuration at first run.
- Every other strategy, cell and target is **exploratory** and is labelled as such wherever it is
  reported.

## 6. Strategy versioning

Improvements to a strategy do not edit it. They are registered as a new version with a new
`strategy_id`, and the rules are:

1. A new version must be **announced in this file, committed, before its first run**. A version
   introduced after seeing results is not admissible.
2. Each version starts its **own clock**. Its 90-day window begins at its own first prediction.
3. Earlier versions **keep running** where cost allows, so no series is ever truncated by the arrival
   of a successor.
4. **No strategy is ever removed from the leaderboard.** Retired versions stay visible and are
   labelled retired, with their full record intact. This is the guard against selecting a flattering
   subset of one's own strategies after the fact.
5. Multiplicity correction is applied across **all** registered strategies and versions, not across
   the currently interesting ones.

### Version log

| Strategy id | Announced (UTC) | First run | Status | What changed |
|---|---|---|---|---|
| `TBD` | | | | |

## 7. Metrics

- **Primary metric:** Spearman rank correlation between predicted and realised ordering.
- **Secondary metrics:** nDCG@5, precision@5 (share of the predicted top 5 finishing above median).
- **Economic secondary:** long top 5 / short bottom 5, equal weight, **20 bps round-trip cost**,
  with a sensitivity run at 40 bps.
- Every reported number carries its `n` and, where cells overlap in time, its effective `n`.

## 8. Baselines

Registered before the first agent prediction, and run from the first day of the record:

1. `random_permutation@1` (seeded deterministically from the cutoff, so it is reproducible)
2. `momentum_24h@1`
3. `momentum_7d@1`
4. `reversal_24h@1`
5. `volume_change@1`

## 9. Ablations

Each is a configuration flag, and every run records its config hash:

- `news_off`
- `news_topic_macro_only`, `news_minus_social`, `news_minus_price_commentary`
- `memory_off`, `memory_structured_only`
- `debate_off`
- `critic_off`
- `features_off`

## 10. Analysis rules

- Bootstrap confidence intervals on every rolling metric. No bare point estimates.
- Block bootstrap wherever cells overlap in time and across days generally, because the memory layer
  carries state forward and correlates errors between consecutive runs.
- Permutation tests against each baseline.
- Benjamini-Hochberg at q = 0.10 across the strategy-by-cell grid and across the reasoning ledger.
  The corrected column is the one quoted anywhere outside this repository.
- Reason-code combinations: **pairs only**, minimum cell size declared in advance, and any
  combination finding stays exploratory until it survives a later hold-out window.

## 11. Run length and stopping rule

- 90 days on the primary cell before any claim is made.
- No metric, universe, horizon or cutoff changes mid-flight.
- Everything measured is reported, including strategies and ablations that lose.

## 12. Reason-code vocabulary

Frozen before the first run. `TBD`, starting from:

`macro_rates`, `regulatory`, `listing_delisting`, `protocol_upgrade`, `security_incident`,
`funding_partnership`, `institutional_flow`, `onchain_flow`, `technical_breakout`,
`volatility_regime`, `sentiment_shift`, `sector_rotation`, `no_signal`

## 13. Expected outcome

The single most likely honest outcome is that **no strategy beats momentum after costs**. That is a
result, it will be reported as the headline, and this document exists so that it cannot be quietly
turned into something else.
