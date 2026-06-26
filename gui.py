"""
Poker Advisor — Tkinter desktop GUI.

A thin window on top of the shared `poker_advisor` core. Enter the current
state of the hand, click "Get Recommendation", and the Smart Champion engine
returns equity + the advised play. The Monte-Carlo simulation runs on a
background thread so the window stays responsive.
"""
import threading
import tkinter as tk
from tkinter import ttk

from poker_advisor import parse_cards, recommend

# ── colour palette (poker-table feel) ──────────────────────────────────────
BG = "#0b3d2e"        # felt green
PANEL = "#13503c"
ACCENT = "#f5c542"    # gold
TEXT = "#f0f0f0"
GOOD = "#5ad17a"
BAD = "#e06c6c"
NEUTRAL = "#e0c060"


class PokerAdvisorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Poker Advisor — Smart Champion")
        self.configure(bg=BG)
        self.minsize(520, 600)

        self._build_styles()
        self._build_widgets()

    # ── styling ─────────────────────────────────────────────────────────
    def _build_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("Panel.TFrame", background=PANEL)
        style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("Header.TLabel", background=BG, foreground=ACCENT,
                        font=("Segoe UI", 18, "bold"))
        style.configure("Field.TLabel", background=PANEL, foreground=TEXT, font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 12, "bold"), padding=8)
        style.configure("TEntry", padding=4)

    # ── layout ──────────────────────────────────────────────────────────
    def _build_widgets(self):
        ttk.Label(self, text="♠ POKER ADVISOR ♥", style="Header.TLabel").pack(pady=(16, 4))
        ttk.Label(self, text="Smart Champion equity & decision engine").pack(pady=(0, 12))

        form = ttk.Frame(self, style="Panel.TFrame", padding=16)
        form.pack(fill="x", padx=16)

        self.vars = {}
        rows = [
            ("hole", "Your hole cards (e.g. As Kd)", "As Kd"),
            ("board", "Board cards (blank = pre-flop)", ""),
            ("players", "Active players", "2"),
            ("pot", "Current pot ($)", "100"),
            ("call", "Amount to call ($, 0 = checked)", "0"),
            ("stack", "Your current stack ($)", "1000"),
            ("start", "Starting stack ($)", "1000"),
        ]
        for i, (key, label, default) in enumerate(rows):
            ttk.Label(form, text=label, style="Field.TLabel").grid(
                row=i, column=0, sticky="w", pady=5, padx=(0, 10))
            var = tk.StringVar(value=default)
            ttk.Entry(form, textvariable=var, width=22).grid(row=i, column=1, sticky="e", pady=5)
            self.vars[key] = var
        form.columnconfigure(0, weight=1)

        self.button = ttk.Button(self, text="Get Recommendation", command=self.on_calculate)
        self.button.pack(pady=16)

        # ── results panel ───────────────────────────────────────────────
        self.result_frame = ttk.Frame(self, style="Panel.TFrame", padding=16)
        self.result_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.action_label = tk.Label(self.result_frame, text="—", bg=PANEL, fg=ACCENT,
                                     font=("Segoe UI", 22, "bold"))
        self.action_label.pack(pady=(4, 8))

        self.detail = tk.Text(self.result_frame, height=10, bg=PANEL, fg=TEXT,
                              relief="flat", font=("Consolas", 10), wrap="word",
                              highlightthickness=0, borderwidth=0)
        self.detail.pack(fill="both", expand=True)
        self.detail.configure(state="disabled")

    # ── actions ─────────────────────────────────────────────────────────
    def on_calculate(self):
        """Validate inputs, then run the (possibly slow) engine off-thread."""
        try:
            hero = parse_cards(self.vars["hole"].get(), expected_count=2)
            board = parse_cards(self.vars["board"].get())  # 0/3/4/5 allowed below
            if len(board) not in (0, 3, 4, 5):
                raise ValueError("Board must be 0, 3, 4 or 5 cards.")
            players = int(float(self.vars["players"].get()))
            if players < 2:
                raise ValueError("Need at least 2 players.")
            pot = float(self.vars["pot"].get())
            call = float(self.vars["call"].get())
            stack = float(self.vars["stack"].get())
            start = float(self.vars["start"].get())
            if min(pot, call, stack, start) < 0:
                raise ValueError("Amounts cannot be negative.")
            if stack <= 0 or start <= 0:
                raise ValueError("Stacks must be greater than 0.")
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self.button.configure(state="disabled", text="Calculating…")
        self.action_label.configure(text="…", fg=NEUTRAL)
        self._set_detail("Running Monte-Carlo simulation…" if board else "Evaluating…")

        args = (hero, board, players, stack, start, pot, call)
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _worker(self, *args):
        try:
            rec = recommend(*args)
            self.after(0, lambda: self._show_result(rec))
        except Exception as exc:  # surface any engine failure in the UI
            self.after(0, lambda: self._show_error(f"Engine error: {exc}"))

    # ── rendering ───────────────────────────────────────────────────────
    def _show_result(self, rec):
        self.button.configure(state="normal", text="Get Recommendation")

        verb = rec.action.split()[0]
        colour = {"RAISE": GOOD, "BET": GOOD, "CALL": NEUTRAL,
                  "CHECK": NEUTRAL, "FOLD": BAD}.get(verb, ACCENT)
        self.action_label.configure(text=rec.action, fg=colour)

        lines = [
            f"Street          : {'Pre-flop' if rec.is_preflop else 'Post-flop (simulated)'}",
            f"Calculated equity: {rec.equity:.1f}%   (win {rec.win_pct:.1f}% / tie {rec.tie_pct:.1f}%)",
            f"Call floor       : {rec.min_call_equity:.1f}%",
            f"Raise floor      : {rec.min_raise_equity:.1f}%",
            "-" * 46,
        ]
        if "call" in rec.evs:
            lines.append(f"EV(Call)  : ${rec.evs['call']:.2f}")
            lines.append(f"EV(Raise) : ${rec.evs['raise']:.2f}  "
                         f"(to ${rec.sizing['raise_amount']:.0f})")
        else:
            lines.append(f"Bet size  : ${rec.sizing['bet_amount']:.0f}  (60% pot)")
            lines.append(f"EV(Bet)   : ${rec.evs['bet']:.2f}")
            lines.append(f"EV(Check) : ${rec.evs['check']:.2f}")
        lines.append("-" * 46)
        lines.append(rec.reason)
        self._set_detail("\n".join(lines))

    def _show_error(self, msg):
        self.button.configure(state="normal", text="Get Recommendation")
        self.action_label.configure(text="Input error", fg=BAD)
        self._set_detail(msg)

    def _set_detail(self, text):
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", text)
        self.detail.configure(state="disabled")


def main():
    PokerAdvisorApp().mainloop()


if __name__ == "__main__":
    main()
