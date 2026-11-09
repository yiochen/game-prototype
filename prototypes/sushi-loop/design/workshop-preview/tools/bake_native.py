"""#28: bake the approved Workshop art for Godot (godot/assets/workshop/).

Run from prototypes/sushi-loop:
  uv run --with pillow --with numpy --with scipy python design/workshop-preview/tools/bake_native.py

- parts/: hull and collector tiers (ImageGen, from design/workshop-preview/assets) at PART_SCALE.
- dock/: the nine hull×collector ships composed in the shared frame with the approved #61 cyan
  outline + glow (ring 10 px / glow 14 px at 256 px per cell, as tools/bake_tip_art.gd), for the
  restaurant dock where the ship is interactable.
- hut-outline.png: the registered workshop-hut frame (384×896) with the same outline.
- room.png, cradle.png: the Workshop room and cradle.
- layout.json: part anchors (scaled) and the compose constants app.js uses, so native code
  composes any tier mix exactly like the prototype.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
SRC = HERE / "assets"
OUT = ROOT / "godot/assets/workshop"
PART_SCALE = 0.75
DOCK_HULL_PX = 240          # dock ships: hull height in baked pixels
DOCK_CELL_PX = 240 / 1.11   # restaurant hull is 1.11 cells tall → px per cell in the dock bake
OUTLINE = (0x19, 0xE3, 0xFF)


def outlined(img, px_per_cell):
    """The approved outline: solid ring outside the silhouette plus a fading glow (bake_tip_art.gd)."""
    k = px_per_cell / 256.0
    ring, glow = 10.0 * k, 14.0 * k
    pad = int(ring + glow + 4)
    src = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad))
    src.alpha_composite(img, (pad, pad))
    a = np.asarray(src).astype(np.float32) / 255
    solid = a[..., 3] > 0.05
    d = ndimage.distance_transform_edt(~solid)
    r = np.clip(ring + 0.5 - d, 0, 1)
    g = 0.9 * np.clip(1 - (d - ring) / glow, 0, 1) ** 2
    oa = np.where((d > 0) & (d <= ring + glow), np.maximum(r, g), 0)
    art_a = a[..., 3]
    out_a = art_a + oa * (1 - art_a)
    col = np.array(OUTLINE, np.float32) / 255
    rgb = (a[..., :3] * art_a[..., None] + col * (oa * (1 - art_a))[..., None]) / np.maximum(out_a, 1e-4)[..., None]
    res = np.dstack([rgb, out_a])
    return Image.fromarray((np.clip(res, 0, 1) * 255).astype(np.uint8)), pad


def main():
    for sub in ("parts", "dock"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    layout = json.loads((SRC / "ship-layout.json").read_text())
    K = layout["compose"]

    def scaled(entry, s):
        e = {k: v for k, v in entry.items() if k != "file"}
        e["size"] = [round(entry["size"][0] * s), round(entry["size"][1] * s)]
        for key in ("nose", "left", "right", "bracket"):
            if key in entry: e[key] = [entry[key][0] * s, entry[key][1] * s]
        return e

    native = {"part_scale": PART_SCALE, "collector_scale": K["collector_scale"], "collector_overlap": K["collector_overlap"] * PART_SCALE,
              "hull": [], "collector": [], "dock": {}}
    for kind in ("hull", "collector"):
        for i, entry in enumerate(layout[kind], 1):
            img = Image.open(SRC / entry["file"]).convert("RGBA")
            img = img.resize((round(img.width * PART_SCALE), round(img.height * PART_SCALE)), Image.LANCZOS)
            img.save(OUT / f"parts/{kind}-{i}.png", optimize=True)
            native[kind].append(scaled(entry, PART_SCALE))

    # Compose in hull-sheet px exactly as app.js shipLayout, then scale to the dock size.
    def compose(h, c, s):
        hull, col = layout["hull"][h - 1], layout["collector"][c - 1]
        cs, ov = K["collector_scale"], K["collector_overlap"]
        hx, hy = -hull["size"][0] / 2, -hull["size"][1] / 2
        ly = hull["left"][1] + hy - col["bracket"][1] * cs
        return [(col["file"], hull["left"][0] + hx + ov - col["bracket"][0] * cs, ly, cs, False),
                (col["file"], hull["right"][0] + hx - ov + (col["bracket"][0] - col["size"][0]) * cs, ly, cs, True),
                (hull["file"], hx, hy, 1.0, False)]

    x0 = y0 = x1 = y1 = 0
    for h in (1, 2, 3):
        for c in (1, 2, 3):
            for f, x, y, s, _ in compose(h, c, 1):
                w, hh = Image.open(SRC / f).size
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x + w * s), max(y1, y + hh * s)
    half = max(-x0, x1)
    frame = (-half, y0, 2 * half, y1 - y0)
    native["frame"] = [frame[0] * PART_SCALE, frame[1] * PART_SCALE, frame[2] * PART_SCALE, frame[3] * PART_SCALE]
    native["hull_height"] = layout["hull"][0]["size"][1] * PART_SCALE

    ds = DOCK_HULL_PX / layout["hull"][0]["size"][1]
    for h in (1, 2, 3):
        for c in (1, 2, 3):
            canvas = Image.new("RGBA", (round(frame[2] * ds), round(frame[3] * ds)))
            for f, x, y, s, flip in compose(h, c, 1):
                im = Image.open(SRC / f).convert("RGBA")
                im = im.resize((round(im.width * s * ds), round(im.height * s * ds)), Image.LANCZOS)
                if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
                canvas.alpha_composite(im, (round((x - frame[0]) * ds), round((y - frame[1]) * ds)))
            out, pad = outlined(canvas, DOCK_CELL_PX)
            out.save(OUT / f"dock/ship-{h}-{c}.png", optimize=True)
    # Hull centre inside a dock image, and the hull height there.
    native["dock"] = {"hull_centre": [(-frame[0]) * ds + pad, (-frame[1]) * ds + pad], "hull_height": DOCK_HULL_PX}

    hut = Image.open(ROOT / "assets/production/sprites/workshop-hut/static-S.png").convert("RGBA")
    out, pad = outlined(hut, 256)
    out.save(OUT / "hut-outline.png", optimize=True)
    native["hut_outline_pad"] = pad

    Image.open(SRC / "workshop-room.webp").convert("RGB").save(OUT / "room.png", optimize=True)
    Image.open(SRC / "workshop-cradle.png").save(OUT / "cradle.png", optimize=True)
    native["room"] = {"size": [853, 1844], "wall_bottom": 540, "door": [45, 290, 210, 530], "sign": [283, 323, 547, 420]}
    (OUT / "layout.json").write_text(json.dumps(native, indent=1) + "\n")
    print(json.dumps({k: native[k] for k in ("frame", "hull_height", "dock", "hut_outline_pad")}, indent=1))


if __name__ == "__main__":
    main()
