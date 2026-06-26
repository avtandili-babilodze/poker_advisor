"""
Poker Calculation Engine
- Pre-flop equity lookup
- Monte-Carlo simulation for post-flop equity
"""
import random
from treys import Card, Evaluator, Deck

SIM_COUNT = 5000  # High precision for the standalone version


def get_preflop_estimated_equity(cards, active_player_count):
    """The exact pre-flop engine used by the Bot-SmartChampion."""
    r1 = Card.get_rank_int(cards[0])
    r2 = Card.get_rank_int(cards[1])
    s1 = Card.get_suit_int(cards[0])
    s2 = Card.get_suit_int(cards[1])

    is_pair = (r1 == r2)
    is_suited = (s1 == s2)
    high_card = max(r1, r2)
    low_card = min(r1, r2)
    gap = high_card - low_card

    if is_pair:
        base = 65.0 if high_card >= 10 else 52.0
    elif is_suited and gap <= 2:
        base = 45.0 if high_card >= 10 else 35.0
    elif high_card >= 11 and low_card >= 9:
        base = 40.0
    else:
        base = 24.0

    scale_factor = 5.0 / max(active_player_count, 2)
    return min(base * scale_factor, 95.0)


def calculate_odds_sim(hero_cards, board_cards, active_player_count, simulations=SIM_COUNT):
    """The exact simulation and binary tie-handling used in the Arena."""
    if len(board_cards) == 0:
        eq = get_preflop_estimated_equity(hero_cards, active_player_count)
        return eq, 0.0

    evaluator = Evaluator()
    wins = ties = 0
    master_deck = Deck()
    known_cards = hero_cards + board_cards
    for card in known_cards:
        if card in master_deck.cards:
            master_deck.cards.remove(card)

    base_deck = master_deck.cards
    cards_to_deal_board = 5 - len(board_cards)
    opponents_count = active_player_count - 1

    if opponents_count <= 0:
        return 100.0, 0.0

    total_needed = (opponents_count * 2) + cards_to_deal_board

    for _ in range(simulations):
        sim_cards = random.sample(base_deck, total_needed)
        opponents_cards = []
        idx = 0
        for _ in range(opponents_count):
            opponents_cards.append(sim_cards[idx:idx + 2])
            idx += 2

        simulated_board = board_cards + sim_cards[idx:]
        hero_score = evaluator.evaluate(hero_cards, simulated_board)
        hero_won = True
        is_tie = False

        for opp_hand in opponents_cards:
            opp_score = evaluator.evaluate(opp_hand, simulated_board)
            if opp_score < hero_score:
                hero_won = False
                is_tie = False
                break
            elif opp_score == hero_score:
                hero_won = False
                is_tie = True
        if hero_won:
            wins += 1
        elif is_tie:
            ties += 1

    return (wins / simulations) * 100, (ties / simulations) * 100
