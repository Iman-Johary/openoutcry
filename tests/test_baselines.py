from __future__ import annotations

from openoutcry.pipeline.predict import build_bundle
from openoutcry.strategies import REGISTRY, get_strategy
from openoutcry.strategies.base import validate_ordering


def test_all_five_baselines_are_registered():
    expected = {
        "random_permutation@1",
        "momentum_24h@1",
        "momentum_7d@1",
        "reversal_24h@1",
        "volume_change@1",
    }
    assert expected <= set(REGISTRY)


def test_every_baseline_returns_a_valid_permutation(cfg, cutoff):
    bundle = build_bundle(cfg, cutoff)
    for sid in cfg.strategies:
        for horizon in cfg.horizons_h:
            ordering = get_strategy(sid).rank(bundle, horizon)
            validate_ordering(ordering, bundle)


def test_no_baseline_uses_an_llm(cfg):
    for sid in cfg.strategies:
        assert get_strategy(sid).uses_llm is False


def test_random_baseline_is_reproducible(cfg, cutoff):
    bundle = build_bundle(cfg, cutoff)
    a = get_strategy("random_permutation@1").rank(bundle, 24)
    b = get_strategy("random_permutation@1").rank(bundle, 24)
    assert a == b


def test_reversal_is_the_exact_inverse_of_momentum(cfg, cutoff):
    bundle = build_bundle(cfg, cutoff)
    mom = get_strategy("momentum_24h@1").rank(bundle, 24)
    rev = get_strategy("reversal_24h@1").rank(bundle, 24)
    assert mom == tuple(reversed(rev))
