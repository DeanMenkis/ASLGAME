#!/bin/zsh
# Double-click to play. Opens Terminal, which needs camera access the first time.
cd "$(dirname "$0")"
if [[ ! -x .venv/bin/python ]]; then
  echo "Setup needed first: see Running in README.md"
  read -k1 "?Press any key to close."
  exit 1
fi
.venv/bin/python -m aslgame
