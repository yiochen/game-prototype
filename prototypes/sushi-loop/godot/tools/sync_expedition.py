#!/usr/bin/env python3
"""Copy the expedition art the game draws into the Godot project.

    python3 prototypes/sushi-loop/godot/tools/sync_expedition.py [--check]

Sources stay outside the runtime tree: approved production clips
(assets/production), same-recipe v2 variants (assets/expedition/v2), the v3 portal ring and the
v1 kit's ground-layer beds and gold (assets/expedition/v1). Images are copied
byte for byte; `assets/expedition/pieces.json` records each clip's frame,
root, footprint and atlas rects so the renderer registers sprites exactly
like the HTML review. `--check` verifies the copy without writing.

Issue #76 reef pieces (assets/expedition/v2/reef.py, reef_break.py) are the
exception: their tall capture frames are mostly empty, so each is cropped to
the band every piece draws in (REEF_CROP) with ffmpeg, and the crack/break
sheets are also scaled to the phone's 192 px per cell. pieces.json `reef`
records the crops, roots and source hashes; `--check` compares those hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
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


# Reef crops in capture pixels (256 per cell, root at (192, 832) in a 384x1024 frame).
REEF_CROP_Y = (592, 964)
REEF_STATIC_X = (56, 328)
REEF_BREAK_SCALE = 0.75


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
    # Issue #22 feature pieces (the portal ring) from the v3 Blender capture.
    for entry in json.loads((SUSHI / "assets/expedition/v3/library.json").read_text())["objects"]:
        add(entry, SUSHI / "assets/expedition/v3", ["static"], entry["family"])

    kit = json.loads((SUSHI / "assets/expedition/v1/manifest.json").read_text())
    sprites = {}
    for name, entry in kit["sprites"].items():
        if not name.startswith(("bed-", "gold-")):
            continue
        target = f"kit/{name}.png"
        copies.append((SUSHI / "assets/expedition/v1" / entry["image"], OUT / target))
        sprites[name] = {"image": target, "origin": entry["origin"], "size": entry["size"]}
    manifest = {"format": "sushi-loop-expedition-pieces", "version": 1, "cellSize": 128, "kitCellPixels": kit["cell_pixels"],
                "objects": objects, "kit": sprites, "reef": reef_plan(),
                "sources": {"production": "assets/production/library.json", "v2": "assets/expedition/v2/library.json", "v3": "assets/expedition/v3/library.json", "kit": "assets/expedition/v1/manifest.json"}}
    return manifest, copies


def reef_plan() -> dict:
    """Reef sprites: static piece per mask/pattern, crack+break sheet per piece."""
    v2 = SUSHI / "assets/expedition/v2"
    breaks = json.loads((v2 / "native/reef-break/pieces.json").read_text())
    y0, y1 = REEF_CROP_Y
    x0, x1 = REEF_STATIC_X
    w = round(384 * REEF_BREAK_SCALE)
    h = round((y1 - y0) * REEF_BREAK_SCALE)
    pieces = {}
    for static in sorted(v2.glob("sprites/reef-*/static-S.png")):
        piece = static.parent.name
        sheet = v2 / "sprites/reef-break" / f"{piece}.png"
        pieces[piece] = {"static": f"reef/static/{piece}.png", "staticSha256": sha(static),
                         "break": f"reef/break/{piece}.png" if sheet.exists() else None, "breakSha256": sha(sheet) if sheet.exists() else None}
    return {"static": {"size": [x1 - x0, y1 - y0], "root": [192 - x0, 832 - y0], "pixelsPerCell": 256},
            "break": {"frame": [w, h], "root": [192 * REEF_BREAK_SCALE, (832 - y0) * REEF_BREAK_SCALE], "pixelsPerCell": 256 * REEF_BREAK_SCALE,
                      "frames": breaks["frames"], "crackFrames": 3, "fps": breaks["fps"]},
            "pieces": pieces}


def write_reef(reef: dict) -> None:
    v2 = SUSHI / "assets/expedition/v2"
    y0, y1 = REEF_CROP_Y
    x0, x1 = REEF_STATIC_X
    fw, fh = reef["break"]["frame"]
    n = len(reef["break"]["frames"])
    for piece, entry in reef["pieces"].items():
        target = OUT / entry["static"]
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(v2 / f"sprites/{piece}/static-S.png"),
                        "-vf", f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0},format=rgba", "-frames:v", "1", str(target)], check=True)
        if entry["break"]:
            target = OUT / entry["break"]
            target.parent.mkdir(parents=True, exist_ok=True)
            # Frame by frame, so the scale never bleeds across a frame edge.
            graph = ";".join(f"[0]crop=384:{y1 - y0}:{i * 384}:{y0},scale={fw}:{fh}:flags=lanczos,format=rgba[v{i}]" for i in range(n))
            graph += ";" + "".join(f"[v{i}]" for i in range(n)) + f"hstack={n}"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(v2 / f"sprites/reef-break/{piece}.png"),
                            "-filter_complex", graph, "-frames:v", "1", str(target)], check=True)


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
        for entry in manifest["reef"]["pieces"].values():
            for key in ("static", "break"):
                if entry[key] and not (OUT / entry[key]).exists():
                    problems.append(f"missing {entry[key]}")
        expected = {target.resolve() for _, target in copies} | {(OUT / "pieces.json").resolve()}
        expected |= {(OUT / e[k]).resolve() for e in manifest["reef"]["pieces"].values() for k in ("static", "break") if e[k]}
        for path in OUT.rglob("*.png"):
            if path.resolve() not in expected:
                problems.append(f"unexpected {path.relative_to(GODOT)}")
        for problem in problems:
            print(problem, file=sys.stderr)
        print(f"expedition art: {len(copies)} images, {'OK' if not problems else f'{len(problems)} problems'}")
        return 1 if problems else 0
    for sub in ("pieces", "kit", "reef"):
        if (OUT / sub).exists():
            shutil.rmtree(OUT / sub)
    for source, target in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    write_reef(manifest["reef"])
    (OUT / "pieces.json").write_text(text)
    print(f"synced {len(copies)} images, {len(manifest['objects'])} objects, {len(manifest['kit'])} kit sprites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
