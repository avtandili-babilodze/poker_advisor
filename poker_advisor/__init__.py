"""Poker Advisor — reusable core package.

Exposes the equity engine, card parsing, and the pure decision/strategy
logic so that any frontend (CLI, Tkinter GUI, ...) can share the same brain.
"""
from .engine import (
    SIM_COUNT,
    DEFAULT_OPP_RANGE,
    get_preflop_estimated_equity,
    calculate_odds_sim,
    validate_cards,
)
from .cards import parse_cards, pretty_cards
from .strategy import Recommendation, recommend

__all__ = [
    "SIM_COUNT",
    "DEFAULT_OPP_RANGE",
    "get_preflop_estimated_equity",
    "calculate_odds_sim",
    "validate_cards",
    "parse_cards",
    "pretty_cards",
    "Recommendation",
    "recommend",
]
