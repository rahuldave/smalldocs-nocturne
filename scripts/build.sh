#!/bin/sh
set -eu
ELEGANT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
python3 "$ELEGANT_ROOT/scripts/build.py"
