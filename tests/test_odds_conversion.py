"""
Tests for odds conversion utilities.
Imports from python/calibration/ev_calculator.py.
"""
import sys
import os
import math
import pytest

# Ensure python package is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from python.calibration.ev_calculator import EVCalculator

_calc = EVCalculator()


def decimal_to_implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be > 1.0")
    return _calc.compute_implied_probability(decimal_odds)


def implied_to_decimal(prob: float) -> float:
    if prob <= 0 or prob >= 1:
        raise ValueError("Probability must be in (0, 1)")
    return 1.0 / prob


def de_vig(odds: list) -> list:
    return _calc.de_vig_multiplicative(odds)


def margin(odds: list) -> float:
    return _calc.compute_margin(odds)


def EV(p: float, odds: float) -> float:
    return _calc.compute_ev_binary(p, odds)


def Kelly(p: float, odds: float) -> float:
    # Full Kelly for test assertions
    return _calc.compute_kelly_fraction(p, odds, fraction=1.0)


def test_decimal_to_implied_probability():
    assert decimal_to_implied_probability(2.0) == 0.5
    with pytest.raises(ValueError):
        decimal_to_implied_probability(1.0)


def test_implied_to_decimal():
    assert implied_to_decimal(0.5) == 2.0


def test_de_vig():
    res = de_vig([2.1, 3.5, 3.2])
    assert math.isclose(sum(res), 1.0, abs_tol=0.001)

    sym = de_vig([1.91, 1.91])
    assert math.isclose(sym[0], 0.5, abs_tol=0.001)
    assert math.isclose(sym[1], 0.5, abs_tol=0.001)


def test_margin():
    assert math.isclose(margin([1.91, 1.91]), 0.0471, abs_tol=0.001)


def test_ev():
    assert math.isclose(EV(p=0.6, odds=2.0), 0.2, abs_tol=0.0001)
    assert math.isclose(EV(p=0.4, odds=2.0), -0.2, abs_tol=0.0001)
    assert math.isclose(EV(p=0.5, odds=2.0), 0.0, abs_tol=0.0001)


def test_kelly():
    # Kelly = (p*b - q) / b where b = odds - 1
    # p=0.55, odds=2.0, b=1.0 -> (0.55*1 - 0.45) / 1 = 0.1
    assert math.isclose(Kelly(p=0.55, odds=2.0), 0.1, abs_tol=0.0001)
