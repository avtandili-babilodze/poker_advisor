#!/usr/bin/env bash
# Launcher: makes sure Python is available, sets up a local virtual
# environment, installs requirements if needed, then runs the poker advisor.
#
#   ./run.sh          # launch the desktop GUI (default)
#   ./run.sh cli      # launch the terminal version
#   ./run.sh test     # run the test suite
#
# If Python is missing it tries to install it automatically using the
# system package manager (apt / dnf / pacman / brew). That may prompt for
# your password (sudo). On Windows, use run.bat instead.
set -e

cd "$(dirname "$0")"

VENV_DIR=".venv"


# ── locate a working Python interpreter, into $PYTHON ──────────────────────
find_python() {
    PYTHON="$(command -v python3 || command -v python || true)"
}

# ── try to install Python via whatever package manager exists ──────────────
install_python() {
    echo
    echo "Python was not found. Attempting to install it automatically"
    echo "(this may ask for your password)..."
    echo
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm python python-pip
    elif command -v brew >/dev/null 2>&1; then
        brew install python
    else
        echo "Error: no supported package manager (apt/dnf/pacman/brew) found." >&2
        echo "Please install Python 3 manually from https://www.python.org/downloads/" >&2
        return 1
    fi
}

find_python
if [ -z "$PYTHON" ]; then
    install_python || exit 1
    find_python
    if [ -z "$PYTHON" ]; then
        echo "Error: Python is still not available after the install attempt." >&2
        exit 1
    fi
fi

# ── create the virtual environment on first run ────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR ..."
    if ! "$PYTHON" -m venv "$VENV_DIR" 2>/dev/null; then
        # Debian/Ubuntu/Kali ship venv as a separate package — install and retry.
        if command -v apt-get >/dev/null 2>&1; then
            echo "The venv module is missing; installing python3-venv ..."
            sudo apt-get install -y python3-venv
            "$PYTHON" -m venv "$VENV_DIR"
        else
            echo "Error: could not create a virtual environment (venv module missing)." >&2
            exit 1
        fi
    fi
fi

VENV_PY="$VENV_DIR/bin/python"

# ── install requirements only if 'treys' is missing ────────────────────────
if ! "$VENV_PY" -c "import treys" >/dev/null 2>&1; then
    echo "Installing requirements..."
    "$VENV_PY" -m pip install --upgrade pip >/dev/null
    "$VENV_PY" -m pip install -r requirements.txt
fi

# ── the GUI needs Tkinter (a separate package on Debian/Kali) ──────────────
ensure_tkinter() {
    if "$VENV_PY" -c "import tkinter" >/dev/null 2>&1; then
        return 0
    fi
    echo "Tkinter (needed for the window) is missing; trying to install it ..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get install -y python3-tk
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3-tkinter
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm tk
    fi
    if ! "$VENV_PY" -c "import tkinter" >/dev/null 2>&1; then
        echo "Error: Tkinter is still unavailable. Use the terminal version:" >&2
        echo "    ./run.sh cli" >&2
        exit 1
    fi
}

# ── run the requested frontend ─────────────────────────────────────────────
case "${1:-gui}" in
    cli)  exec "$VENV_PY" cli.py ;;
    test) exec "$VENV_PY" -m pytest -q || "$VENV_PY" tests/test_strategy.py ;;
    gui)  ensure_tkinter; exec "$VENV_PY" gui.py ;;
    *)    echo "Usage: ./run.sh [gui|cli|test]" >&2; exit 1 ;;
esac
