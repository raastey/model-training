#!/usr/bin/env bash
set -euo pipefail

.venv/bin/pytest -q
.venv/bin/sixai doctor --json
