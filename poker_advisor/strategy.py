"""
Strategy / decision engine — pure logic, no console I/O.

`recommend()` takes a single decision point (hole cards, board, stacks, pot,
call amount) and returns a Recommendation describing the equity, the EV of
each action, and the advised play. Both the CLI and the GUI call this.
"""
from dataclasses import dataclass, field

from .engine import (
    get_preflop_estimated_equity,
    calculate_odds_sim,
    SIM_COUNT,
)

# ── Configuration Constants ────────────────────────────────────────────────
FOLD_EQUITY_EST = 0.12
BIG_BLIND = 50.0


@dataclass
class Recommendation:
    """Result of evaluating one decision point."""
    action: str                 # e.g. "RAISE to $150", "CALL $50", "FOLD"
    reason: str                 # human-readable justification
    equity: float               # combined equity %
    win_pct: float
    tie_pct: float
    is_preflop: bool
    min_call_equity: float
    min_raise_equity: float
    min_bet_equity: float
    # Action-tree numbers (whichever branch applied). Unused ones stay None.
    evs: dict = field(default_factory=dict)
    sizing: dict = field(default_factory=dict)


def recommend(hero_cards, board_cards, active_players, hero_chips,
              starting_stack, current_pot, call_amount, simulations=SIM_COUNT):
    """Evaluate one decision point and return a Recommendation.

    This is the exact Smart Champion logic that used to live inside the
    terminal loop, lifted out so it is reusable and testable.
    """
    is_preflop = len(board_cards) == 0

    if is_preflop:
        equity = get_preflop_estimated_equity(hero_cards, active_players)
        win_pct, tie_pct = equity, 0.0
    else:
        win_pct, tie_pct = calculate_odds_sim(
            hero_cards, board_cards, active_players, simulations=simulations)
        equity = win_pct + (tie_pct / 2)

    eq = equity / 100.0
    stack_ratio = hero_chips / starting_stack if starting_stack > 0 else 1.0

    if is_preflop:
        min_call_equity = 38.0 + (1.0 - stack_ratio) * 6.0
        min_raise_equity = 52.0 + (1.0 - stack_ratio) * 5.0
        min_bet_equity = 50.0
    else:
        min_call_equity = 40.0 + (1.0 - stack_ratio) * 8.0
        min_raise_equity = 55.0 + (1.0 - stack_ratio) * 6.0
        min_bet_equity = 50.0 + (1.0 - stack_ratio) * 5.0

    stack_commit_pct = call_amount / hero_chips if hero_chips > 0 else 1.0
    if stack_commit_pct > 0.50:
        min_call_equity = max(min_call_equity, 58.0)
    elif stack_commit_pct > 0.30:
        min_call_equity = max(min_call_equity, 50.0)

    evs = {}
    sizing = {}

    if call_amount > 0:
        ev_c = eq * (current_pot + call_amount) - call_amount
        raise_multiplier = 3.0 if is_preflop else 2.5
        raise_to = min(call_amount * raise_multiplier, hero_chips)
        raise_amount = min(max(raise_to, call_amount + BIG_BLIND), hero_chips)
        ev_r = eq * (current_pot + raise_amount) - raise_amount + (FOLD_EQUITY_EST * current_pot)

        evs = {"call": ev_c, "raise": ev_r}
        sizing = {"raise_amount": raise_amount, "call_amount": min(call_amount, hero_chips)}

        if ev_r > ev_c and ev_r > 0 and equity >= min_raise_equity:
            action = f"RAISE to ${raise_amount:.0f}"
            reason = "Raise EV is dominant and equity clears the Champion threshold floor."
        elif ev_c > 0 and equity >= min_call_equity:
            action = f"CALL ${min(call_amount, hero_chips):.0f}"
            reason = "Calling is positive EV and hand strength clears the commitment tier rules."
        else:
            action = "FOLD"
            reason = "Hand falls completely below the Champion's mathematical comfort matrix."
    else:
        bet_amount = min(max(round(current_pot * 0.60 / 10) * 10, BIG_BLIND), hero_chips)
        ev_b = eq * (current_pot + bet_amount) - bet_amount + (FOLD_EQUITY_EST * current_pot)
        ev_check = eq * current_pot

        evs = {"bet": ev_b, "check": ev_check}
        sizing = {"bet_amount": bet_amount}

        if ev_b > ev_check and ev_b > 0 and equity >= min_bet_equity:
            action = f"BET ${bet_amount:.0f}"
            reason = "Betting generates cleaner baseline EV projection than checking."
        else:
            action = "CHECK"
            reason = "Checking keeps pot control optimal for this specific tier range."

    return Recommendation(
        action=action,
        reason=reason,
        equity=equity,
        win_pct=win_pct,
        tie_pct=tie_pct,
        is_preflop=is_preflop,
        min_call_equity=min_call_equity,
        min_raise_equity=min_raise_equity,
        min_bet_equity=min_bet_equity,
        evs=evs,
        sizing=sizing,
    )
