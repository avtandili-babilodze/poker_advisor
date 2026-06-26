# Poker Calculator

A smart poker advisor tool that calculates hand equity and provides strategy recommendations based on the Smart Champion poker algorithm.

## Features

- **Pre-flop equity lookup** - Fast hand strength estimation without simulation
- **Post-flop Monte-Carlo simulation** - High-precision equity calculation with 5000+ simulations
- **Dynamic EV calculation** - Evaluates Call, Raise, Bet, and Check decisions
- **Stack-aware strategy** - Adjusts recommendations based on chip stack depth
- **Interactive session tracking** - Process multiple hands with persistent chip counts

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python advisor.py
```

Then follow the prompts:
1. Enter your starting chip stack
2. For each hand, provide:
   - Number of active players
   - Your hole cards
   - Board cards as streets appear (Flop, Turn, River)
   - Current pot and call amounts
3. Get equity calculations and action recommendations
4. Continue for multiple hands

## Card Format

Cards are entered as two-character strings: Rank + Suit

- Ranks: `A`, `K`, `Q`, `J`, `T`, `9`-`2`
- Suits: `s` (spades), `h` (hearts), `d` (diamonds), `c` (clubs)

Example: `As Kd Th 2c`

## Architecture

- **`advisor.py`** - Main game loop and strategy recommendations
- **`calc_engine.py`** - Equity calculations (pre-flop & simulation)
- **`io_handler.py`** - Input validation and card parsing

## Dependencies

- `treys` - Poker hand evaluation and deck management
