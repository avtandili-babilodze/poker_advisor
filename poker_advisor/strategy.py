"""
Strategy / decision engine — pure logic, no console I/O.

`recommend()` takes a single decision point (hole cards, board, stacks, pot,
call amount) and returns a Recommendation describing the equity, the EV of
each action, and the advised play. Both the CLI and the GUI call this.

Key ideas (upgraded):
* Equity comes from a real Monte-Carlo simulation on every street.
* Calling is driven by genuine POT ODDS — the "call floor" shown to the user
  is literally the break-even equity for the price they're being offered, plus
  a small premium when a call would commit a big chunk of their stack. No more
  folding hands that are mathematically profitable to call.
* Fold equity for a raise/bet adapts to bet size and the number of opponents
  instead of being a flat constant, which also enables sensible semi-bluffs.
"""
from dataclasses import dataclass, field

from .engine import calculate_odds_sim, SIM_COUNT, DEFAULT_OPP_RANGE

# ── Configuration Constants ────────────────────────────────────────────────
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
    min_call_equity: float      # equity actually needed to call (pot odds + premium)
    min_raise_equity: float     # equity floor to raise for value
    min_bet_equity: float       # equity floor to bet for value
    # Action-tree numbers (whichever branch applied). Unused ones stay None.
    evs: dict = field(default_factory=dict)
    sizing: dict = field(default_factory=dict)


def _fold_equity(bet, pot, opponents):
    """Estimate the chance that EVERY opponent folds to a bet/raise.

    Bigger bets relative to the pot fold more hands out; each extra opponent
    makes a clean blow-through less likely (probabilities multiply).
    """
    ratio = bet / pot if pot > 0 else 1.0
    per_opponent = min(0.15 + 0.25 * ratio, 0.60)
    return per_opponent ** opponents


def recommend(hero_cards, board_cards, active_players, hero_chips,
              starting_stack, current_pot, call_amount,
              simulations=None, opponent_range=DEFAULT_OPP_RANGE,
              big_blind=BIG_BLIND):
    """Evaluate one decision point and return a Recommendation."""
    is_preflop = len(board_cards) == 0

    # Adaptive trial count: pre-flop is cheap and smooth, so fewer trials are
    # enough; a made board gets the full precision run. Callers can still pin
    # an exact number (the tests do).
    if simulations is None:
        simulations = 2500 if is_preflop else SIM_COUNT

    win_pct, tie_pct = calculate_odds_sim(
        hero_cards, board_cards, active_players,
        simulations=simulations, opponent_range=opponent_range)
    equity = win_pct + tie_pct / 2.0
    eq = equity / 100.0

    opponents = max(active_players - 1, 1)
    stack_ratio = hero_chips / starting_stack if starting_stack > 0 else 1.0

    # Value floors for betting/raising: you need to be ahead of MORE hands when
    # more opponents are in, and you tighten up as your stack gets short.
    short_stack_bump = (1.0 - stack_ratio) * 5.0
    min_raise_equity = min(50.0 + 4.0 * (opponents - 1) + short_stack_bump, 90.0)
    min_bet_equity = min(48.0 + 3.0 * (opponents - 1) + short_stack_bump, 88.0)

    evs = {}
    sizing = {}

    if call_amount > 0:
        # ── Facing a bet: pot odds decide the call, EV decides the raise ──
        breakeven = call_amount / (current_pot + call_amount)   # equity needed to call
        min_call_equity = breakeven * 100.0
        commit = call_amount / hero_chips if hero_chips > 0 else 1.0
        if commit > 0.50:                       # don't stack off light
            min_call_equity += 8.0
        elif commit > 0.30:
            min_call_equity += 4.0
        min_call_equity = min(min_call_equity, 100.0)

        call_cost = min(call_amount, hero_chips)
        ev_call = eq * (current_pot + call_cost) - call_cost

        raise_mult = 3.0 if is_preflop else 2.5
        raise_to = min(max(call_amount * raise_mult, call_amount + big_blind), hero_chips)
        fe = _fold_equity(raise_to, current_pot, opponents)
        pot_if_called = current_pot + 2.0 * raise_to
        ev_raise = fe * current_pot + (1.0 - fe) * (eq * pot_if_called - raise_to)

        evs = {"call": ev_call, "raise": ev_raise}
        sizing = {"raise_amount": raise_to, "call_amount": call_cost}

        can_value_raise = equity >= min_raise_equity
        can_semibluff_raise = fe >= 0.50 and ev_raise > 0
        if ev_raise > ev_call and ev_raise > 0 and (can_value_raise or can_semibluff_raise):
            action = f"RAISE to ${raise_to:.0f}"
            if can_value_raise:
                reason = ("Raising has the best EV and your equity clears the value "
                          f"floor ({equity:.0f}% ≥ {min_raise_equity:.0f}%).")
            else:
                reason = ("Raising as a semi-bluff: enough fold equity that pressuring "
                          "now beats just calling.")
        elif ev_call > 0 and equity >= min_call_equity:
            action = f"CALL ${call_cost:.0f}"
            reason = (f"Profitable call: the price needs {min_call_equity:.0f}% equity "
                      f"and you have {equity:.0f}%.")
        else:
            action = "FOLD"
            reason = (f"The price needs {min_call_equity:.0f}% equity but you only have "
                      f"{equity:.0f}% — folding loses the least.")
    else:
        # ── Nobody has bet: choose between betting for value and checking ──
        min_call_equity = 0.0
        bet_amount = min(max(round(current_pot * 0.60 / 10) * 10, big_blind), hero_chips)
        fe = _fold_equity(bet_amount, current_pot, opponents)
        ev_check = eq * current_pot
        pot_if_called = current_pot + 2.0 * bet_amount
        ev_bet = fe * current_pot + (1.0 - fe) * (eq * pot_if_called - bet_amount)

        evs = {"bet": ev_bet, "check": ev_check}
        sizing = {"bet_amount": bet_amount}

        is_value = equity >= min_bet_equity
        is_semibluff = fe >= 0.50 and ev_bet > 0
        if ev_bet > ev_check and (is_value or is_semibluff):
            action = f"BET ${bet_amount:.0f}"
            if is_value:
                reason = ("Betting beats checking on EV and you have enough equity to "
                          "bet for value.")
            else:
                reason = ("Betting as a semi-bluff: good fold equity makes pressure more "
                          "profitable than checking.")
        else:
            action = "CHECK"
            reason = ("Checking is best — not enough edge to bet for value and keeping "
                      "the pot controlled is fine here.")

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
