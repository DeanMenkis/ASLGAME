#!/bin/zsh
# Double-click to play. The first run sets everything up, which takes a few minutes.
# Terminal needs camera access the first time.
set -e
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "First run: installing Python and the game's libraries. This only happens once."
  export PATH="$HOME/.local/bin:$PATH"
  if ! command -v uv >/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  fi
  uv venv --python 3.11 .venv
  uv pip install --python .venv/bin/python -r requirements.txt
fi

.venv/bin/python -m aslgame
