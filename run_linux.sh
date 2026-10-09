#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it using your distribution's package manager."
  exit 1
fi
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "Python Tkinter is missing. On Ubuntu/Linux Mint/Debian, run:"
  echo "  sudo apt install python3-tk python3-venv"
  exit 1
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-linux.txt
exec .venv/bin/python image_converter.py
