#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
CORNER_SOURCE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
CORNER_BLENDER=${CORNER_BLENDER:-/opt/homebrew/bin/blender}
CORNER_PYTHON=${CORNER_PYTHON:-/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}
"$CORNER_BLENDER" --background --python "$CORNER_SOURCE/round-05.py"
"$CORNER_BLENDER" --background --python "$CORNER_SOURCE/audit-replay-round-05.py"
"$CORNER_BLENDER" --background --python "$CORNER_SOURCE/ground-support-audit-round-05.py"
"$CORNER_BLENDER" --background --python "$CORNER_SOURCE/compare-native-round-05.py"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/geometry-comparison-round-05.py"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/publish-frames-round-05.py"
node "$CORNER_SOURCE/consumer-round-05.mjs"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/resource-closure-round-05.py"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/package-round-05.py"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/measure-sections-round-05.py"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/revision-comparison-round-05.py"
"$CORNER_PYTHON" -B "$CORNER_SOURCE/package-round-05.py"
