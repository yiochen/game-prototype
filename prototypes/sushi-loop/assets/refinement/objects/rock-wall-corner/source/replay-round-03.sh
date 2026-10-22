#!/bin/sh
set -eu
CORNER_SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CORNER_BLENDER=${CORNER_BLENDER:-/opt/homebrew/bin/blender}
CORNER_PYTHON=${CORNER_PYTHON:-/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}
"$CORNER_BLENDER" --background --python "$CORNER_SOURCE/round-03.py"
"$CORNER_BLENDER" --background --python "$CORNER_SOURCE/audit-replay-round-03.py"
"$CORNER_PYTHON" "$CORNER_SOURCE/publish-frames-round-03.py"
node "$CORNER_SOURCE/consumer-round-03.mjs"
"$CORNER_PYTHON" "$CORNER_SOURCE/package-round-03.py"
"$CORNER_PYTHON" "$CORNER_SOURCE/measure-sections-round-03.py"
"$CORNER_PYTHON" "$CORNER_SOURCE/package-round-03.py"
