"""
Poker Advisor — terminal frontend (Smart Champion Continuous Edition).

Thin console wrapper around the shared `poker_advisor` core. All the actual
poker math/decision logic lives in poker_advisor.strategy / .engine.
"""
from poker_advisor import SIM_COUNT, parse_cards, pretty_cards, recommend


# ── console input helpers ──────────────────────────────────────────────────
def parse_cards_input(prompt_text, expected_count=None):
    while True:
        try:
            return parse_cards(input(prompt_text), expected_count)
        except ValueError as exc:
            print(f"  {exc}")


def get_float_input(prompt_text, min_val=0.0, default=None):
    while True:
        user_in = input(prompt_text).strip()
        if not user_in and default is not None:
            return default
        try:
            val = float(user_in)
            if val >= min_val:
                return val
            print(f"  Please enter a value >= {min_val}.")
        except ValueError:
            print("  Invalid number.")


def run_hand(hand_counter, starting_stack, hero_chips):
    """Process a single hand through all streets. Returns updated chip count."""
    print("\n" + "█" * 60)
    print(f"  STARTING HAND #{hand_counter}")
    print("█" * 60)

    active_players = int(get_float_input("Active players in hand: ", min_val=2))
    hero_cards = parse_cards_input("Your 2 hole cards (e.g., As Kd): ", expected_count=2)

    board_cards = []
    streets = ["PRE-FLOP", "FLOP", "TURN", "RIVER"]

    for street in streets:
        print(f"\n========== {street} STREET ==========")

        if street == "FLOP":
            board_cards.extend(parse_cards_input("Enter the 3 FLOP cards (e.g., Jh 9c 2d): ", expected_count=3))
        elif street in ["TURN", "RIVER"]:
            board_cards.extend(parse_cards_input(f"Enter the 1 {street} card (e.g., Qs): ", expected_count=1))

        if board_cards:
            print(f"  Current Board: {pretty_cards(board_cards)}")

        hero_chips = get_float_input(f"Verify your current stack ($) [Press Enter for ${hero_chips:.0f}]: ",
                                     min_val=0, default=hero_chips)
        current_pot = get_float_input("Current total pot size ($): ", min_val=0)
        call_amount = get_float_input("Amount to call you face ($) [0 if checked/betting]: ", min_val=0)

        if board_cards:
            print(f"\n  Running {SIM_COUNT} arena-mode simulation loops...")

        rec = recommend(hero_cards, board_cards, active_players, hero_chips,
                        starting_stack, current_pot, call_amount)

        print("\n  " + "-" * 40)
        print(f"  Calculated Equity : {rec.equity:.1f}%")
        print(f"  Target Call Floor : {rec.min_call_equity:.1f}%")
        print(f"  Target Raise Floor: {rec.min_raise_equity:.1f}%")
        print("  " + "-" * 40)
        if "call" in rec.evs:
            print(f"  Arena EV(Call) : ${rec.evs['call']:.2f}")
            print(f"  Arena EV(Raise): ${rec.evs['raise']:.2f} "
                  f"(Targeting total size: ${rec.sizing['raise_amount']:.0f})")
        else:
            print(f"  Target Bet size: ${rec.sizing['bet_amount']:.0f} (60% Pot)")
            print(f"  Arena EV(Bet)  : ${rec.evs['bet']:.2f}")
            print(f"  Arena EV(Check): ${rec.evs['check']:.2f}")
        print("  " + "-" * 40)
        print(f"  RECOMMENDATION : {rec.action}")
        print(f"  Reasoning Filter: {rec.reason}")
        print("=" * 60)

        if rec.action == "FOLD" or street == "RIVER":
            break

        if input("\nDid this hand end on this street? (y/n) [Default: n]: ").strip().lower() == 'y':
            break

        active_players = int(
            get_float_input(f"How many active players remain in the hand? [Current: {active_players}]: ",
                            min_val=2, default=active_players))

    print(f"\nHand #{hand_counter} finished.")
    return get_float_input("Enter your total chip stack balance now to carry over ($): ",
                           min_val=0, default=hero_chips)


def main():
    print("=" * 60)
    print("  POKER ADVISOR — Smart Champion Continuous Edition")
    print("=" * 60)
    print()

    hero_chips = get_float_input("Your starting chip stack ($): ", min_val=1)
    starting_stack = hero_chips
    hand_counter = 0

    while True:
        hand_counter += 1
        hero_chips = run_hand(hand_counter, starting_stack, hero_chips)

        if input("\nDo you want to process another hand? (y/n) [Default: y]: ").strip().lower() == 'n':
            print("\nSession ended. Final chip stack: ${:,.2f}".format(hero_chips))
            break


if __name__ == "__main__":
    main()
