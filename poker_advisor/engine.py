"""
Poker Calculation Engine
- Monte-Carlo equity for ANY street (pre-flop through river)
- Optional opponent hand-range modelling (opponents don't play random junk)
- Input validation so bad/duplicate cards fail loudly instead of silently

The old version estimated pre-flop equity from a tiny 4-bucket lookup table
that was badly miscalibrated (it capped almost every hand near 95% heads-up).
Pre-flop now runs the same real simulation as every other street.
"""
import itertools
import random

from treys import Card, Evaluator

SIM_COUNT = 5000               # default Monte-Carlo trials for a made board
DEFAULT_OPP_RANGE = 0.5        # opponents play roughly their strongest 50% of hands

_EVALUATOR = Evaluator()

# Build the full 52-card deck once, as treys ints.
_FULL_DECK = [Card.new(rank + suit) for rank in "23456789TJQKA" for suit in "shdc"]


# ── opponent hand-range modelling ──────────────────────────────────────────
def _rank_value(card):
    """Return 2..14 (Ace high) for a treys card int."""
    return Card.get_rank_int(card) + 2


def _chen_score(c1, c2):
    """Bill Chen pre-flop hand strength — used only to model opponent ranges."""
    v1, v2 = _rank_value(c1), _rank_value(c2)
    hi, lo = max(v1, v2), min(v1, v2)
    suited = Card.get_suit_int(c1) == Card.get_suit_int(c2)

    base = {14: 10.0, 13: 8.0, 12: 7.0, 11: 6.0}.get(hi, hi / 2.0)

    if v1 == v2:                                  # pocket pair
        return max(base * 2.0, 5.0)

    score = base + (2.0 if suited else 0.0)
    gap = hi - lo - 1
    score -= {0: 0, 1: 1, 2: 2, 3: 4}.get(gap, 5)
    if gap <= 1 and hi < 12:                      # connected & below Q: straight bonus
        score += 1.0
    return score


# Pre-compute every starting hand's Chen score once, sorted high→low, so a
# "range fraction" can be converted into a minimum-score threshold cheaply.
_ALL_SCORES = sorted(
    (_chen_score(a, b) for a, b in itertools.combinations(_FULL_DECK, 2)),
    reverse=True,
)


def _range_threshold(range_fraction):
    """Minimum Chen score an opponent's hand must have to be 'in range'."""
    if range_fraction >= 1.0:
        return float("-inf")                      # opponents play everything
    range_fraction = max(range_fraction, 0.01)
    idx = min(int(range_fraction * len(_ALL_SCORES)), len(_ALL_SCORES) - 1)
    return _ALL_SCORES[idx]


def _deal_opponents(pool, opponents, threshold, max_tries=24):
    """Deal `opponents` 2-card hands from pool, biased toward 'in range' hands.

    Rejection sampling: redraw a hand a few times until it clears the Chen
    threshold; if it never does (very tight range / thin deck) we keep the last
    draw so this can never loop forever.
    """
    pool = list(pool)
    hands = []
    for _ in range(opponents):
        hand = random.sample(pool, 2)
        for _ in range(max_tries):
            if _chen_score(hand[0], hand[1]) >= threshold:
                break
            hand = random.sample(pool, 2)
        hands.append(hand)
        chosen = set(hand)
        pool = [c for c in pool if c not in chosen]
    return hands


# ── validation ─────────────────────────────────────────────────────────────
def validate_cards(hero_cards, board_cards):
    """Raise ValueError on impossible inputs (wrong counts or duplicate cards)."""
    if len(hero_cards) != 2:
        raise ValueError("You must have exactly 2 hole cards.")
    if len(board_cards) not in (0, 3, 4, 5):
        raise ValueError("The board must have 0, 3, 4 or 5 cards.")
    all_cards = list(hero_cards) + list(board_cards)
    if len(set(all_cards)) != len(all_cards):
        raise ValueError("Duplicate card detected — every card must be unique.")


# ── equity ──────────────────────────────────────────────────────────────────
def calculate_odds_sim(hero_cards, board_cards, active_player_count,
                       simulations=SIM_COUNT, opponent_range=DEFAULT_OPP_RANGE):
    """Monte-Carlo equity for any street. Returns ``(win_pct, tie_pct)``.

    Works pre-flop (empty board) too: the engine simply deals all five
    community cards each trial instead of guessing from a lookup table.

    ``opponent_range`` (0..1) tightens opponents toward stronger hands:
    1.0 = fully random opponents (the old behaviour), 0.5 = they only show up
    with roughly their top half of hands, which is far more realistic.
    """
    validate_cards(hero_cards, board_cards)

    opponents = active_player_count - 1
    if opponents <= 0:
        return 100.0, 0.0

    known = set(hero_cards) | set(board_cards)
    deck = [c for c in _FULL_DECK if c not in known]

    cards_to_deal_board = 5 - len(board_cards)
    needed = opponents * 2 + cards_to_deal_board
    if needed > len(deck):
        raise ValueError("Too many players for the cards remaining in the deck.")

    threshold = _range_threshold(opponent_range)
    hero = list(hero_cards)
    wins = ties = 0

    for _ in range(simulations):
        board_extra = random.sample(deck, cards_to_deal_board)
        sim_board = board_cards + board_extra
        leftover = [c for c in deck if c not in set(board_extra)]
        opp_hands = _deal_opponents(leftover, opponents, threshold)

        hero_score = _EVALUATOR.evaluate(hero, sim_board)
        hero_won = True
        is_tie = False
        for opp in opp_hands:
            opp_score = _EVALUATOR.evaluate(opp, sim_board)
            if opp_score < hero_score:               # lower is better in treys
                hero_won = False
                is_tie = False
                break
            if opp_score == hero_score:
                hero_won = False
                is_tie = True

        if hero_won:
            wins += 1
        elif is_tie:
            ties += 1

    return (wins / simulations) * 100.0, (ties / simulations) * 100.0


def get_preflop_estimated_equity(cards, active_player_count,
                                 simulations=2000, opponent_range=DEFAULT_OPP_RANGE):
    """Pre-flop equity as a single combined percentage (win + tie/2).

    Kept for backward compatibility; now backed by a real (fast) simulation
    instead of the old lookup table.
    """
    win_pct, tie_pct = calculate_odds_sim(
        cards, [], active_player_count,
        simulations=simulations, opponent_range=opponent_range)
    return win_pct + tie_pct / 2.0
