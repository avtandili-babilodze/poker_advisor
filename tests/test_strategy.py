"""Smoke tests for the shared core."""
from poker_advisor import parse_cards, recommend


def test_parse_cards_valid():
    cards = parse_cards("As Kd", expected_count=2)
    assert len(cards) == 2


def test_parse_cards_wrong_count():
    try:
        parse_cards("As", expected_count=2)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_preflop_premium_hand_recommends_action():
    hero = parse_cards("As Ah", expected_count=2)
    rec = recommend(hero, [], active_players=2, hero_chips=1000,
                    starting_stack=1000, current_pot=100, call_amount=50)
    assert rec.is_preflop
    assert rec.action != "FOLD"          # pocket aces should never fold pre
    assert "call" in rec.evs


def test_postflop_runs_simulation():
    hero = parse_cards("As Ks", expected_count=2)
    board = parse_cards("Qs Js Ts")      # royal flush — must dominate
    rec = recommend(hero, board, active_players=2, hero_chips=1000,
                    starting_stack=1000, current_pot=100, call_amount=0,
                    simulations=200)
    assert not rec.is_preflop
    assert rec.equity > 90


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
    print("All tests passed.")
