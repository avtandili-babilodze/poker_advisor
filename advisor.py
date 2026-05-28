"""
Poker Advisor — Smart Champion Continuous Edition
Main game loop and strategy recommendation engine
"""
from treys import Card
from calc_engine import get_preflop_estimated_equity, calculate_odds_sim, SIM_COUNT
from io_handler import parse_cards_input, get_float_input


# ── Configuration Constants ────────────────────────────────────────────────
FOLD_EQUITY_EST = 0.12
BIG_BLIND = 50.0


def run_hand(hand_counter, starting_stack, hero_chips):
    """
    Process a single hand through all streets with dynamic strategy recommendations.
    Returns updated hero chip count.
    """
    print("\n" + "█" * 60)
    print(f"  STARTING HAND #{hand_counter}")
    print("█" * 60)

    active_players = int(get_float_input("Active players in hand: ", min_val=2))
    hero_cards = parse_cards_input("Your 2 hole cards (e.g., As Kd): ", expected_count=2)

    board_cards = []
    streets = ["PRE-FLOP", "FLOP", "TURN", "RIVER"]

    for street in streets:
        print(f"\n========== {street} STREET ==========")

        # 1. Gather new cards based on the betting round
        if street == "FLOP":
            flop_cards = parse_cards_input("Enter the 3 FLOP cards (e.g., Jh 9c 2d): ", expected_count=3)
            board_cards.extend(flop_cards)
        elif street in ["TURN", "RIVER"]:
            card_name = "TURN" if street == "TURN" else "RIVER"
            next_card = parse_cards_input(f"Enter the 1 {card_name} card (e.g., Qs): ", expected_count=1)
            board_cards.extend(next_card)

        # Display total board texture up to this point
        if board_cards:
            print("  Current Board: ", end="")
            Card.print_pretty_cards(board_cards)

        # 2. Update financial parameters dynamically
        hero_chips = get_float_input(f"Verify your current stack ($) [Press Enter for ${hero_chips:.0f}]: ",
                                     min_val=0, default=hero_chips)
        current_pot = get_float_input("Current total pot size ($): ", min_val=0)
        call_amount = get_float_input("Amount to call you face ($) [0 if checked/betting]: ", min_val=0)

        # 3. Process Strategic Matrices
        is_preflop = (street == "PRE-FLOP")
        if is_preflop:
            equity = get_preflop_estimated_equity(hero_cards, active_players)
            win_pct, tie_pct = equity, 0.0
        else:
            print(f"\n  Running {SIM_COUNT} arena-mode simulation loops...")
            win_pct, tie_pct = calculate_odds_sim(hero_cards, board_cards, active_players)
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

        print("\n  " + "-" * 40)
        print(f"  Calculated Equity : {equity:.1f}%")
        print(f"  Target Call Floor : {min_call_equity:.1f}%")
        print(f"  Target Raise Floor: {min_raise_equity:.1f}%")
        print("  " + "-" * 40)

        # 4. Action Tree Evaluation
        if call_amount > 0:
            ev_c = eq * (current_pot + call_amount) - call_amount
            raise_multiplier = 3.0 if is_preflop else 2.5
            raise_to = min(call_amount * raise_multiplier, hero_chips)
            raise_amount = min(max(raise_to, call_amount + BIG_BLIND), hero_chips)
            ev_r = eq * (current_pot + raise_amount) - raise_amount + (FOLD_EQUITY_EST * current_pot)

            print(f"  Arena EV(Call) : ${ev_c:.2f}")
            print(f"  Arena EV(Raise): ${ev_r:.2f} (Targeting total size: ${raise_amount:.0f})")
            print("  " + "-" * 40)

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

            print(f"  Target Bet size: ${bet_amount:.0f} (60% Pot)")
            print(f"  Arena EV(Bet)  : ${ev_b:.2f}")
            print(f"  Arena EV(Check): ${ev_check:.2f}")
            print("  " + "-" * 40)

            if ev_b > ev_check and ev_b > 0 and equity >= min_bet_equity:
                action = f"BET ${bet_amount:.0f}"
                reason = "Betting generates cleaner baseline EV projection than checking."
            else:
                action = "CHECK"
                reason = "Checking keeps pot control optimal for this specific tier range."

        print(f"  RECOMMENDATION : {action}")
        print(f"  Reasoning Filter: {reason}")
        print("=" * 60)

        # If the recommended decision or your chosen path was a fold, or if we completed the River
        if action == "FOLD" or street == "RIVER":
            break

        # Check if an opponent forced an early end to the hand
        end_hand_early = input("\nDid this hand end on this street? (y/n) [Default: n]: ").strip().lower()
        if end_hand_early == 'y':
            break

        # Dynamically handle table structure modifications
        active_players = int(
            get_float_input(f"How many active players remain in the hand? [Current: {active_players}]: ",
                            min_val=2, default=active_players))

    # End of current hand
    print(f"\nHand #{hand_counter} finished.")
    hero_chips = get_float_input(f"Enter your total chip stack balance now to carry over ($): ", min_val=0,
                                 default=hero_chips)
    return hero_chips


def main():
    """Main advisor execution loop."""
    print("=" * 60)
    print("  POKER ADVISOR — Smart Champion Continuous Edition")
    print("=" * 60)
    print()

    # Stack sizes are preserved across hands
    hero_chips = get_float_input("Your starting chip stack ($): ", min_val=1)
    starting_stack = hero_chips  # Baseline used for stack ratio calculations
    hand_counter = 0

    while True:
        hand_counter += 1
        hero_chips = run_hand(hand_counter, starting_stack, hero_chips)

        play_again = input("\nDo you want to process another hand? (y/n) [Default: y]: ").strip().lower()
        if play_again == 'n':
            print("\nSession ended. Final chip stack: ${:,.2f}".format(hero_chips))
            break


if __name__ == "__main__":
    main()
