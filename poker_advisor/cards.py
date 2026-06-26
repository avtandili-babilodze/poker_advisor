"""
Card parsing helpers.

Pure functions (no console I/O) so any frontend can reuse them. Invalid
input raises ValueError; the caller decides how to surface the error.
"""
from treys import Card


def parse_cards(text, expected_count=None):
    """Parse a string like 'As Kd' into a list of treys card ints.

    Raises ValueError if the token count is wrong or a token is not a
    valid card. An empty string is allowed only when expected_count is None.
    """
    text = (text or "").strip()
    if not text:
        if expected_count in (None, 0):
            return []
        raise ValueError(f"Please enter exactly {expected_count} card(s).")

    tokens = text.split()
    if expected_count is not None and len(tokens) != expected_count:
        raise ValueError(f"Please enter exactly {expected_count} card(s).")

    try:
        return [Card.new(token) for token in tokens]
    except Exception as exc:  # treys raises bare exceptions on bad input
        raise ValueError("Invalid card syntax. Use format like: As Kd Th 2c") from exc


def pretty_cards(cards):
    """Return a colourful terminal-friendly string for a list of card ints."""
    if not cards:
        return ""
    return " ".join(Card.int_to_pretty_str(c) for c in cards)
