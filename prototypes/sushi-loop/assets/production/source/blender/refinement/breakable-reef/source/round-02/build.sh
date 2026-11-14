#!/bin/sh
# Rebuild round-02 evidence: native captures, 2x sprites, assembly, seam sheets, repeat render, validation.
set -e
R=$(cd "$(dirname "$0")" && pwd); EXP=$(cd "$R/../.." && pwd); C=$EXP/candidates/round-02
rm -rf "$R/native" "$R/repeat/r" "$C/native" "$C/sprites"; mkdir -p "$C/native" "$C/sprites" "$R/repeat"
blender -b --factory-startup --python "$R/reef.py" -- --out "$R/native" > "$R/render.log" 2>&1
blender -b --factory-startup --python "$R/reef.py" -- reef-05-a --out "$R/repeat/r" > "$R/repeat.log" 2>&1
cp "$R/native/reef-05-a/project.blend" "$R/reef-05-a.blend"
for d in "$R"/native/reef-*/; do id=$(basename "$d"); cp "$d/static-S.png" "$C/native/$id.png"; mkdir -p "$C/sprites/$id"
  ffmpeg -loglevel error -y -i "$d/static-S.png" -vf scale=384:1024:flags=lanczos,format=rgba -frames:v 1 "$C/sprites/$id/static-S.png"; done
cd "$EXP" && python3 inputs/assemble_snapshot.py "$C/sprites" "$C/assembly.html" >/dev/null
NODE_PATH=/Users/yiouchen/dev/game-prototype/node_modules node inputs/shoot.cjs "$C/assembly.html" "$C/assembly.png"
python3 "$R/seam_sheet.py" "$C/native" "$C/seam-stress-native.png" native
python3 "$R/seam_sheet.py" "$C/sprites" "$C/seam-stress-2x.png" sprites
blender -b --factory-startup --python "$R/validate.py" -- "$C/validation.json" 2>&1 | grep VALIDATION
