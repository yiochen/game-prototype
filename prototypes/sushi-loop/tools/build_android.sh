#!/usr/bin/env bash
# Credentials stay in the private ignored signing directory, never in arguments.
set -euo pipefail
script_directory="$(cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$script_directory/build_android.py" "$@"
