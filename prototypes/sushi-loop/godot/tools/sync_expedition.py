#!/usr/bin/env python3
"""Copy the expedition art the game draws into the Godot project.

    python3 prototypes/sushi-loop/godot/tools/sync_expedition.py [--check]

Sources stay outside the runtime tree: approved production clips
(assets/production), same-recipe v2 variants (assets/expedition/v2) and the
v1 kit's ground-layer beds and gold (assets/expedition/v1). Images are copied
byte for byte; `assets/expedition/pieces.json` records each clip's frame,
root, footprint and atlas rects so the renderer registers sprites exactly
like the HTML review. `--check` verifies the copy without writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

GODOT = Path(__file__).resolve().parents[1]
SUSHI = GODOT.parent
OUT = GODOT / "assets" / "expedition"

# Production objects and the clip each one plays in the expedition.
PRODUCTION = {
    "floor-underwater": ["scroll"], "decor-background-rock": ["static"], "decor-foreground-rock": ["static"],
    "boulder-underwater": ["static"], "column-broken": ["static"], "decor-ruin-fragment": ["static"],
    "decor-foreground-coral": ["idle"], "decor-midground-coral": ["idle"], "decor-kelp": ["idle"], "decor-starfish": ["static"],
    "decor-background-fish": ["swim"], "decor-light-shafts": ["ambient"],
    "submarine-yellow": ["travel", "impact"],
}
# Facings the scene actually draws; everything else uses all four for variety.
FACINGS = {"floor-underwater": ["S"], "submarine-yellow": ["S"], "decor-light-shafts": ["S"],  "decor-background-fish": ["E", "W"]}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan() -> tuple[dict, list[tuple[Path, Path]]]:
    copies: list[tuple[Path, Path]] = []
    objects: dict = {}

    def add(entry: dict, base: Path, clip_ids: list[str], family: str) -> None:
        clips = []
        for clip_id in clip_ids:
            clip = next(c for c in entry["clips"] if c["id"] == clip_id)
            directions = {}
            for direction, data in clip["directions"].items():
                if direction not in FACINGS.get(entry["id"], [direction]):
                    continue
                target = f"pieces/{entry['id']}/{clip_id}-{direction}.png"
                copies.append((base / data["image"], OUT / target))
                directions[direction] = {"image": target, "rects": data["rects"]}
            clips.append({"id": clip_id, "fps": clip["fps"], "frames": clip["frames"], "frameOrder": clip.get("frameOrder", list(range(clip["frames"]))), "directions": directions})
        objects[entry["id"]] = {"frameSize": entry["frameSize"], "root": entry["root"], "sourceScale": entry["sourceScale"],
                                "footprint": entry.get("footprint", [1, 1]), "family": family, "clips": clips}

    production = json.loads((SUSHI / "assets/production/library.json").read_text())["objects"]
    for object_id, clip_ids in PRODUCTION.items():
        add(next(o for o in production if o["id"] == object_id), SUSHI / "assets/production", clip_ids, "production")
    v2 = json.loads((SUSHI / "assets/expedition/v2/library.json").read_text())["objects"]
    for entry in v2:
        add(entry, SUSHI / "assets/expedition/v2", ["static"], entry["family"])
        objects[entry["id"]].update({k: entry[k] for k in ("height", "span", "solidCells") if k in entry})

    kit = json.loads((SUSHI / "assets/expedition/v1/manifest.json").read_text())
    sprites = {}
    for name, entry in kit["sprites"].items():
        if not name.startswith(("bed-", "gold-")):
            continue
        target = f"kit/{name}.png"
        copies.append((SUSHI / "assets/expedition/v1" / entry["image"], OUT / target))
        sprites[name] = {"image": target, "origin": entry["origin"], "size": entry["size"]}
    manifest = {"format": "sushi-loop-expedition-pieces", "version": 1, "cellSize": 128, "kitCellPixels": kit["cell_pixels"],
                "objects": objects, "kit": sprites,
                "sources": {"production": "assets/production/library.json", "v2": "assets/expedition/v2/library.json", "kit": "assets/expedition/v1/manifest.json"}}
    return manifest, copies


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest, copies = plan()
    text = json.dumps(manifest, indent=1) + "\n"
    problems = []
    if args.check:
        current = OUT / "pieces.json"
        if not current.exists() or current.read_text() != text:
            problems.append("pieces.json is stale")
        for source, target in copies:
            if not target.exists() or sha(source) != sha(target):
                problems.append(f"{target.relative_to(GODOT)} differs from {source.relative_to(SUSHI)}")
        expected = {target.resolve() for _, target in copies} | {(OUT / "pieces.json").resolve()}
        for path in OUT.rglob("*.png"):
            if path.resolve() not in expected:
                problems.append(f"unexpected {path.relative_to(GODOT)}")
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"expedition art: {len(copies)} images, {'OK' if not problems else f'{len(problems)} problems'}")
        return 1 if problems else 0
    for sub in ("pieces", "kit"):
        if (OUT / sub).exists():
            shutil.rmtree(OUT / sub)
    for source, target in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (OUT / "pieces.json").write_text(text)
    print(f"synced {len(copies)} images, {len(manifest['objects'])} objects, {len(manifest['kit'])} kit sprites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
