# Poker Advisor

A smart poker advisor tool that calculates hand equity and provides strategy recommendations based on the Smart Champion poker algorithm.

## Features

- **Pre-flop equity lookup** - Fast hand strength estimation without simulation
- **Post-flop Monte-Carlo simulation** - High-precision equity calculation with 5000+ simulations
- **Dynamic EV calculation** - Evaluates Call, Raise, Bet, and Check decisions
- **Stack-aware strategy** - Adjusts recommendations based on chip stack depth
- **Interactive session tracking** - Process multiple hands with persistent chip counts

## Quick start

There is a launcher for each platform — `run.sh` for Linux/macOS and `run.bat`
for Windows. On first run it bootstraps everything for you: it makes sure
Python is installed, creates a local virtual environment (the `.venv` folder),
installs the `treys` dependency, and then starts the app. Later runs skip
straight to launching.

**Linux / macOS:**

```bash
./run.sh          # desktop GUI (default)
./run.sh cli      # terminal version
./run.sh test     # run the test suite
```

If Python (or Tkinter, or the `venv` module) is missing, the script installs
it via your package manager (`apt` / `dnf` / `pacman` / `brew`), which may ask
for your `sudo` password.

**Windows:**

Just **double-click `run.bat`** to play. For the terminal version, run
`run.bat cli` from a Command Prompt.

- If Python is not installed, it installs it automatically — via `winget`, or
  by downloading the official installer from python.org (needs an internet
  connection and may ask for permission).
- It then creates the `.venv`, installs `treys`, and opens the window.
- The console window **always pauses before closing**, so if anything goes
  wrong you can read the message instead of it flashing shut.
- Tkinter ships with Python on Windows, so no extra step is needed for the GUI.

## Usage

### Desktop GUI

A Tkinter window: enter your hole cards, the board (leave blank for pre-flop),
players, pot, the amount to call, and your stacks, then click **Get
Recommendation**. The engine shows your equity and the advised play.

### Terminal (CLI)

The interactive session walks you through each hand:
1. Enter your starting chip stack
2. For each hand, provide:
   - Number of active players
   - Your hole cards
   - Board cards as streets appear (Flop, Turn, River)
   - Current pot and call amounts
3. Get equity calculations and action recommendations
4. Continue for multiple hands

### Manual setup (without run.sh)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python gui.py      # or: python cli.py
```

## Card Format

Cards are entered as two-character strings: Rank + Suit

- Ranks: `A`, `K`, `Q`, `J`, `T`, `9`-`2`
- Suits: `s` (spades), `h` (hearts), `d` (diamonds), `c` (clubs)

Example: `As Kd Th 2c`

## Architecture

The poker logic lives in a reusable `poker_advisor` package; each frontend is
a thin layer on top that just gathers input and displays the result.

```
poker_advisor/
├── poker_advisor/        # reusable core (no UI code)
│   ├── engine.py         #   equity: pre-flop estimate + Monte-Carlo sim
│   ├── strategy.py       #   pure decision logic -> Recommendation
│   └── cards.py          #   card parsing / pretty printing
├── gui.py                # Tkinter desktop frontend
├── cli.py                # terminal frontend
├── tests/                # test suite
├── run.sh                # launcher for Linux / macOS (venv + install + run)
└── run.bat               # launcher for Windows  (venv + install + run)
```

- **`engine.py`** — equity calculations (pre-flop lookup & simulation)
- **`strategy.py`** — `recommend(...)` returns the EVs, equity floors and advised play
- **`cards.py`** — card parsing/validation shared by both frontends
- **`gui.py`** / **`cli.py`** — call the same `recommend(...)`, so both give identical advice

## Dependencies

- `treys` - Poker hand evaluation and deck management
