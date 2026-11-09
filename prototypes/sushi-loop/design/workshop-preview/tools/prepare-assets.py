"""#28 Workshop preview assets, derived only from registered production art.

Run from prototypes/sushi-loop:
  uv run --with pillow --with numpy --with scipy python design/workshop-preview/tools/prepare-assets.py <capture-dir>

<capture-dir> holds restaurant-dock.png and dive.png from the two native capture scripts.
Per-track equipment layers are split from the existing `upgraded-*` submarine clips:
each connected region that differs from the baseline clip belongs to one track.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "assets"
SPRITES = ROOT / "assets/production/sprites"
FRAME = (640, 768)  # submarine-yellow frame at scale 2; root (320, 576)


def frame(clip, index=0):
    sheet = Image.open(SPRITES / f"submarine-yellow/{clip}-S.png").convert("RGBA")
    col, row = index % 6, index // 6
    return sheet.crop((col * FRAME[0], row * FRAME[1], (col + 1) * FRAME[0], (row + 1) * FRAME[1]))


def track_of(box):
    """Classify a differing region by where it sits on the south-facing ship."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if cy > 640:
        return "collector"  # stern intake below the propeller housing
    if y1 - y0 > 70 and x1 - x0 < 40 and cy < 470:
        return "hull"  # paired shoulder plates
    return "harpoon"  # starboard launcher rail


def split_layers(clip):
    base, upgraded = frame(clip), frame("upgraded-" + clip)
    b, u = np.asarray(base).astype(int), np.asarray(upgraded).astype(int)
    changed = np.abs(b - u).sum(-1) > 60
    labels, _ = ndimage.label(ndimage.binary_dilation(changed, iterations=3))
    layers = {name: np.zeros(changed.shape, bool) for name in ("hull", "harpoon", "collector")}
    regions = []
    for index, region in enumerate(ndimage.find_objects(labels)):
        mask = labels == index + 1
        if mask.sum() < 30:
            continue
        box = (region[1].start, region[0].start, region[1].stop, region[0].stop)
        name = track_of(box)
        layers[name] |= ndimage.binary_dilation(mask, iterations=2)
        regions.append({"track": name, "box": box})
    ua = np.asarray(upgraded)
    result = {}
    for name, mask in layers.items():
        layer = np.zeros_like(ua)
        layer[mask] = ua[mask]
        result[name] = Image.fromarray(layer)
    return base, result, regions


def fit(capture, clip, guess, scales):
    """Find where the native renderer drew the baseline frame in a capture."""
    sprite = frame(clip)
    best = None
    for scale in scales:
        w, h = round(FRAME[0] * scale), round(FRAME[1] * scale)
        g = np.asarray(sprite.resize((w, h), Image.LANCZOS)).astype(float)
        opaque = g[..., 3] > 250
        for ox in range(guess[0] - 8, guess[0] + 9):
            for oy in range(guess[1] - 8, guess[1] + 9):
                region = np.asarray(capture.crop((ox, oy, ox + w, oy + h))).astype(float)
                error = np.abs(g[..., :3] - region[..., :3])[opaque].mean()
                if best is None or error < best[0]:
                    best = (error, float(scale), ox, oy)
    return {"error": round(best[0], 2), "scale": round(best[1], 4), "left": best[2], "top": best[3], "width": round(FRAME[0] * best[1], 2), "height": round(FRAME[1] * best[1], 2)}


def locate(capture, clip, window):
    """Coarse guess from the red side pods inside `window` (x0, y0, x1, y1), then the exact fit."""
    a = np.asarray(capture.convert("RGB")).astype(int)
    red = (a[..., 0] > 180) & (a[..., 1] < 90) & (a[..., 2] < 90)
    keep = np.zeros_like(red)
    keep[window[1]:window[3], window[0]:window[2]] = True
    red &= keep
    ys, xs = np.where(red)
    sprite = np.asarray(frame(clip)).astype(int)
    sr = (sprite[..., 0] > 180) & (sprite[..., 1] < 90) & (sprite[..., 2] < 90) & (sprite[..., 3] > 200)
    sy, sx = np.where(sr)
    scale = (xs.max() - xs.min()) / (sx.max() - sx.min())
    guess = (int(xs.min() - sx.min() * scale), int(ys.min() - sy.min() * scale))
    return fit(capture, clip, guess, np.arange(scale - 0.02, scale + 0.02, 0.002))


def crop_icon(name):
    sprite = Image.open(SPRITES / f"{name}/idle-S.png").convert("RGBA").crop((0, 0, 384, 704))
    box = sprite.getbbox()
    pad = 6
    return sprite.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))


def main():
    captures = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"frame": FRAME, "root": [320, 576], "layers": {}, "placement": {}}
    for clip in ("idle", "travel"):
        base, layers, regions = split_layers(clip)
        union = base.getbbox()
        for layer in layers.values():
            box = layer.getbbox()
            union = (min(union[0], box[0]), min(union[1], box[1]), max(union[2], box[2]), max(union[3], box[3]))
        union = (union[0] - 4, union[1] - 4, union[2] + 4, union[3] + 4)
        base.crop(union).save(OUT / f"ship-{clip}-base.png", optimize=True)
        for name, layer in layers.items():
            layer.crop(union).save(OUT / f"ship-{clip}-{name}.png", optimize=True)
        report["layers"][clip] = {"crop": union, "regions": regions}
    dock = Image.open(captures / "restaurant-dock.png").convert("RGB")
    dive = Image.open(captures / "dive.png").convert("RGB")
    report["placement"]["restaurant"] = locate(dock, "idle", (380, 880, 600, 1120))  # the 3x3 dock
    report["placement"]["dive"] = locate(dive, "travel", (250, 1000, 530, 1400))  # the ship lane
    report["capture_size"] = list(dock.size)
    dock.save(OUT / "restaurant-dock.webp", quality=88, method=6)
    dive.save(OUT / "dive.webp", quality=88, method=6)
    for track, name in (("hull", "sub-hull-panels"), ("harpoon", "sub-harpoon-mount"), ("collector", "sub-collector-inlet")):
        crop_icon(name).save(OUT / f"part-{track}.png", optimize=True)
    Image.open(ROOT / "godot/assets/expedition/kit/gold-00.png").save(OUT / "salvage.png")
    Image.open(ROOT / "godot/assets/ui/cash.png").save(OUT / "cash.png")
    (OUT / "registration.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["placement"], indent=2))
    for clip, data in report["layers"].items():
        print(clip, [(r["track"], r["box"]) for r in data["regions"]])


if __name__ == "__main__":
    main()
