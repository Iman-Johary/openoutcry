from __future__ import annotations

import math

from openoutcry.scoring.metrics import long_short_bps, ndcg_at_k, precision_at_k, spearman

REALISED = {"A": 0.05, "B": 0.03, "C": 0.01, "D": -0.02, "E": -0.04}
PERFECT = ("A", "B", "C", "D", "E")
WORST = ("E", "D", "C", "B", "A")


def test_spearman_perfect_and_inverted():
    assert math.isclose(spearman(PERFECT, REALISED), 1.0, abs_tol=1e-9)
    assert math.isclose(spearman(WORST, REALISED), -1.0, abs_tol=1e-9)


def test_ndcg_bounds():
    assert math.isclose(ndcg_at_k(PERFECT, REALISED, 3), 1.0, abs_tol=1e-9)
    assert 0.0 <= ndcg_at_k(WORST, REALISED, 3) < 1.0


def test_precision_at_k_counts_above_median():
    # median is 0.01; A and B beat it, C does not
    assert math.isclose(precision_at_k(PERFECT, REALISED, 3), 2 / 3, abs_tol=1e-9)
    assert math.isclose(precision_at_k(WORST, REALISED, 2), 0.0, abs_tol=1e-9)


def test_long_short_is_net_of_stated_cost():
    gross_bps = ((0.05 + 0.03) / 2 - (-0.02 + -0.04) / 2) * 10_000
    assert math.isclose(
        long_short_bps(PERFECT, REALISED, k=2, cost_bps_round_trip=20.0),
        gross_bps - 40.0,
        abs_tol=1e-6,
    )


def test_metrics_are_symmetric_under_a_shared_market_move():
    # Adding the same return to every asset is a pure market move and must not change the ranking
    # metrics. This is the whole reason the target is cross-sectional.
    shifted = {k: v + 0.10 for k, v in REALISED.items()}
    assert math.isclose(spearman(PERFECT, REALISED), spearman(PERFECT, shifted), abs_tol=1e-9)
    assert math.isclose(
        ndcg_at_k(PERFECT, REALISED, 3), ndcg_at_k(PERFECT, shifted, 3), abs_tol=1e-9
    )
