"""#28 r3: slice the ImageGen ship-part sheets into tiers, clean their edges and measure anchors.

Run from prototypes/sushi-loop:
  uv run --with pillow --with numpy --with scipy python design/workshop-preview/tools/prepare-ship-parts.py <capture-dir>

Inputs: design/workshop-preview/ship-parts/{hull,harpoon,collector}-sheet-v1.png (keyed RGBA sheets,
three tiers left→right) and the ship-free captures restaurant-dock-empty.png / dive-empty.png.
Outputs in assets/: part-sprite PNGs, backdrops, and ship-layout.json, where every layer is
placed in one shared ship frame (units: hull-sheet pixels) so any tier mix composes exactly.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parents[1]
PARTS, OUT = HERE / "ship-parts", HERE / "assets"


def clean(rgba):
    """Drop keying specks, harden the edge and pull magenta spill out of the rim."""
    a = np.asarray(rgba).astype(np.float32)
    alpha = a[..., 3]
    solid = alpha > 96
    labels, count = ndimage.label(solid)
    sizes = ndimage.sum(solid, labels, range(1, count + 1))
    keep = np.isin(labels, [i + 1 for i, s in enumerate(sizes) if s > 400])
    keep = ndimage.binary_fill_holes(keep)
    soft = ndimage.gaussian_filter(keep.astype(np.float32), 0.7)
    a[..., 3] = np.clip(soft * 255, 0, 255)
    # De-spill: magenta pushes red and blue above green at the rim.
    rim = (soft > 0.02) & (soft < 0.98)
    spill = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    fix = rim & (spill > 0)
    a[..., 0][fix] -= spill[fix] * 0.8
    a[..., 2][fix] -= spill[fix] * 0.8
    a[..., :3][a[..., 3] == 0] = 0
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def tiers(sheet):
    """The three largest connected objects, left to right, each cropped tight."""
    img = clean(Image.open(sheet).convert("RGBA"))
    alpha = np.asarray(img)[..., 3] > 10
    labels, _ = ndimage.label(ndimage.binary_dilation(alpha, iterations=12))
    boxes = sorted(ndimage.find_objects(labels), key=lambda s: -(s[0].stop - s[0].start) * (s[1].stop - s[1].start))[:3]
    boxes.sort(key=lambda s: s[1].start)
    result = []
    for box in boxes:
        crop = img.crop((box[1].start, box[0].start, box[1].stop, box[0].stop))
        result.append(crop.crop(crop.getbbox()))
    return result


def mask(img, test):
    a = np.asarray(img).astype(int)
    return test(a[..., 0], a[..., 1], a[..., 2]) & (a[..., 3] > 200)


def centroid(m):
    ys, xs = np.nonzero(m)
    return float(xs.mean()), float(ys.mean()), float(xs.max() - xs.min() + 1)


def red(r, g, b):
    return (r > 170) & (g < 110) & (b < 110)


def hull_anchors(img):
    w, h = img.size
    m = mask(img, red)
    m[int(h * 0.45):] = False  # nose ring sits in the upper body
    nx, ny, ring = centroid(m)
    alpha = np.asarray(img)[..., 3] > 128
    rows = np.nonzero(alpha.any(1))[0]
    # Side stubs: the widest band of the body (outermost opaque columns around mid-height).
    widths = [(np.nonzero(alpha[y])[0][[0, -1]], y) for y in rows if alpha[y].any()]
    left = min(x[0] for x, _ in widths)
    right = max(x[1] for x, _ in widths)
    band = [y for x, y in widths if x[0] <= left + 3]
    return {"nose": [nx, ny], "ring": ring, "left": [float(left), float(np.mean(band))], "right": [float(right), float(np.mean(band))]}


def harpoon_anchor(img):
    m = mask(img, red)
    m[: int(img.size[1] * 0.78)] = False  # base ring at the bottom end, below any red clamps
    x, y, ring = centroid(m)
    return {"base": [x, y], "ring": ring}


def collector_anchor(img):
    a = np.asarray(img)[..., 3] > 128
    cols = np.nonzero(a.any(0))[0]
    right = cols.max()
    ys = np.nonzero(a[:, right - 6:].any(1))[0]  # the bracket is the rightmost part
    return {"bracket": [float(right), float(ys.mean())]}


def main():
    captures = Path(sys.argv[1])
    layout = {"units": "hull-sheet px", "hull": [], "harpoon": [], "collector": []}
    hulls, harpoons, collectors = tiers(PARTS / "hull-sheet-v1.png"), tiers(PARTS / "harpoon-sheet-v1.png"), tiers(PARTS / "collector-sheet-v1.png")
    ref = hull_anchors(hulls[0])
    for i, img in enumerate(hulls):
        img.save(OUT / f"ship-hull-{i + 1}.png", optimize=True)
        anchors = hull_anchors(img)
        # Every hull tier is centred on its own body; record where its mounts fall.
        layout["hull"].append({"file": f"ship-hull-{i + 1}.png", "size": list(img.size), **anchors})
    # One factor for the whole harpoon sheet (tiers share its scale): tier 1's base ring matches the nose plate.
    scale = ref["ring"] / harpoon_anchor(harpoons[0])["ring"]
    for i, img in enumerate(harpoons):
        anchor = harpoon_anchor(img)
        img.save(OUT / f"ship-harpoon-{i + 1}.png", optimize=True)
        layout["harpoon"].append({"file": f"ship-harpoon-{i + 1}.png", "size": list(img.size), "scale": scale, **anchor})
    # Collectors were drawn at the hull's scale; one shared factor keeps tier sizes relative.
    for i, img in enumerate(collectors):
        img.save(OUT / f"ship-collector-{i + 1}.png", optimize=True)
        layout["collector"].append({"file": f"ship-collector-{i + 1}.png", "size": list(img.size), "scale": 1.0, **collector_anchor(img)})
    # Old 3D ship placement (fitted in registration.json) gives where and how large the new ship sits.
    registration = json.loads((OUT / "registration.json").read_text())
    BODY = (522, 286)  # old frame: body centre y and body height (incl. propeller), frame px
    for name, key in (("restaurant", "restaurant"), ("dive", "dive")):
        p = registration["placement"][key]
        layout.setdefault("placement", {})[name] = {"cx": p["left"] + 320 * p["scale"], "cy": p["top"] + BODY[0] * p["scale"], "hull_height": BODY[1] * p["scale"] * 0.92}
    layout["capture_size"] = registration["capture_size"]
    for src, dst in (("restaurant-dock-empty.png", "restaurant-dock.webp"), ("dive-empty.png", "dive.webp")):
        Image.open(captures / src).convert("RGB").save(OUT / dst, quality=88, method=6)
    (OUT / "ship-layout.json").write_text(json.dumps(layout, indent=2) + "\n")
    print(json.dumps({k: [{kk: vv for kk, vv in t.items() if kk != "file"} for t in layout[k]] for k in ("hull", "harpoon", "collector")}, indent=1))


if __name__ == "__main__":
    main()
