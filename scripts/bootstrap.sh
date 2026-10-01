#!/usr/bin/env bash
set -euo pipefail

# Requires pyenv with the version selected by .python-version. This script does not access Hugging Face.
PYTHON_BIN="$(pyenv which python)"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[dev]'
echo "Environment ready. Next: source .venv/bin/activate && sixai doctor"
