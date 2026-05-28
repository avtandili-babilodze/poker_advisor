"""
Input/Output Handlers
- Card input parsing
- Float input with validation
"""
from treys import Card


def parse_cards_input(prompt_text, expected_count=None):
    """Parse and validate card input from user."""
    while True:
        user_in = input(prompt_text).strip()
        if not user_in and expected_count is None:
            return []
        tokens = user_in.split()
        if expected_count is not None and len(tokens) != expected_count:
            print(f"  Error: Please enter exactly {expected_count} cards.")
            continue
        try:
            card_ints = [Card.new(token) for token in tokens]
            return card_ints
        except Exception:
            print("  Invalid card syntax. Use format: As Kd Th 2c")


def get_float_input(prompt_text, min_val=0.0, default=None):
    """Get validated float input from user."""
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
