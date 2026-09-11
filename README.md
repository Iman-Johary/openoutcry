# openoutcry

**Can a language model read the news and work out which crypto will do better than the rest
tomorrow? Probably not. This is me checking, in public, every day.**

---

## What this is

Four times a day, this system reads the news that came out since it last looked, checks how 30 crypto
assets have been behaving, and puts them in order: which it expects to do best over the next 6, 12
and 24 hours, compared to the others.

Then it waits.

When the time is up, it looks at what actually happened, scores the prediction, and adds the result
to a public record. Nothing is edited afterwards. Every prediction is published before the outcome is
known, and it stays there whether it was right or wrong.

The name comes from open outcry, the way trading worked before screens: you called out your bid in
the open, where everyone could hear it. Same idea here.

## What I expect to find

Probably nothing.

Predicting short-term price movements is close to the hardest thing you can ask a model to do, and if
reading the news were enough, someone with a lot more money than me would already be doing it. So the
honest expectation is that this will not beat a simple momentum rule once you account for trading
costs.

That is fine. **The interesting part is not whether it works, it is measuring properly whether it
works,** which is something surprisingly few projects in this space actually do. A clear negative
result is a real result, and it is the one this is built to be able to report.

## The record

📊 **[Live scoreboard](#)** *(coming once the first predictions go out)*

Every strategy is scored on exactly the same data, side by side, including several deliberately
simple ones that use no AI at all.

## How it works

**1. Look.** Collect the news published since the last checkpoint, and calculate how each asset has
been moving. The price maths is done in code. The model never squints at a chart.

**2. Think.** Several small agents each do one job: filter out the noise, summarise what actually
matters for each asset, argue the bull and the bear case, then rank all 30 together.

**3. Commit.** The ranking is written down, timestamped, and published. It can never be changed.

**4. Settle.** Hours later, a separate process checks what really happened and appends the score.

## Three rules I set before starting

**I never test it on the past.** This sounds backwards, but there is a good reason. Any language
model was trained on text that already covers historical events, so asking it to "predict" 2024 is
really asking it to remember 2024. It would look brilliant and mean nothing. The only honest test is
forwards, on days that have not happened yet, which is why this has to run in real time and why the
record gets more useful the longer it goes.

**The simple methods went first.** Before any AI was involved, five basic rules were already running
and being scored: pure momentum, the reverse of momentum, a volume-based rule, and a random shuffle
as a sanity check. If the clever version cannot beat a coin flip and a moving average, that is worth
knowing, and it is much harder to notice if you never measured them.

**I wrote down what counts as success before seeing any results.** What gets measured, which
comparison is the real one, how long it runs. It is all in
[PREREGISTRATION.md](PREREGISTRATION.md), committed before the first prediction, so the git history
shows it was not decided afterwards to fit whatever came out. This is normal practice in clinical
trials and rare in side projects, and the difference is the whole point of the exercise.

## Why I built it

I do research on recommender systems, so ranking things and arguing about whether the ranking is any
good is the part I know best. I wanted to point that at a problem where the answer arrives on its
own, every single day, and where nobody can dispute the correct answer once it has happened. Most
evaluation work involves painstakingly labelling data by hand. Here the world labels it for you
overnight.

The rest of it, running things on a schedule in the cloud without babysitting them, was the part I
had read about more than I had done, and this seemed like a better way to learn it than another
tutorial.

## Status

Early. The machinery works end to end and is tested, the simple strategies are ready, and the live
data source is being wired up now. No real predictions have been made yet. When they start, the
scoreboard link above goes live and the counter starts at day one.

## Running it yourself

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest

python -m openoutcry predict --as-of 2026-01-02T00:00:00Z --config config/config.example.yaml
python -m openoutcry score   --as-of 2026-01-03T00:00:00Z --config config/config.example.yaml
python -m openoutcry report
```

Out of the box it runs on generated test data, so it works offline with no API keys. The numbers it
prints are noise, deliberately.

<details>
<summary><b>What's in the repository</b></summary>

| Path | What it does |
|---|---|
| `src/openoutcry/leakage.py` | Blocks anything published after a prediction's cutoff from reaching it. The most important file here |
| `src/openoutcry/clock.py` | Checkpoints, horizons, and what gets settled when |
| `src/openoutcry/sources/` | Where prices and news come from, behind an interface, plus offline test data |
| `src/openoutcry/strategies/` | The strategy interface and the five simple baselines |
| `src/openoutcry/scoring/` | Ranking metrics and the settlement process |
| `src/openoutcry/store/` | The record itself. SQLite, append-only, enforced by the database |
| `tests/test_leakage_guard.py` | Required to pass before anything can be merged |

Predictions are immutable: the database physically refuses to update or delete them. Scores are
append-only too but carry a version number, so a bug in a metric is fixed by appending corrected
scores rather than quietly editing the old ones. You can see both.

Crypto is where it starts, not where it stops. Prices and news sit behind a small interface, so
adding gold or equities means writing one adapter and changing nothing else.

</details>

## This is not investment advice

Not a recommendation, not personalised, no connection to any broker or exchange account. Nothing here
should be used to make a financial decision, and no real money is traded on any of it. It is a
measurement project that happens to use market data because the market grades your homework for free.

---

Built with Python, LangGraph, Docker, GitHub Actions and Azure Container Apps.
