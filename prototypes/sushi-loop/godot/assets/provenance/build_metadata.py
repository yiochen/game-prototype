"""Measure native sprite regions and registration; production source PNGs stay intact.

Requires Pillow for read-only alpha/bounds checks. Run after bake_belt_frames.gd.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image
from inspect_atlases import components

BASE = Path(__file__).resolve().parent.parent
PRODUCTION = BASE / "production"
PROVENANCE = BASE / "provenance"
manifest = {}
animations = {}
verification = {}


def add(name, sheet, box, anchor=(0.5, 1.0), reference=None):
    left, top, right, bottom = box
    entry = {
        "file": f"res://assets/production/{sheet}.png",
        "region": [left, top, right - left, bottom - top],
        "anchor": list(anchor),
    }
    if reference:
        entry["scale_reference"] = list(reference)
    manifest[name] = entry


def grid_regions(sheet, columns, rows):
    image = Image.open(PRODUCTION / f"{sheet}.png")
    alpha = image.getchannel("A")
    regions = []
    for index in range(columns * rows):
        left = round(index % columns * image.width / columns)
        top = round(index // columns * image.height / rows)
        right = round((index % columns + 1) * image.width / columns)
        bottom = round((index // columns + 1) * image.height / rows)
        mask = alpha.crop((left, top, right, bottom)).point(lambda n: 255 if n > 24 else 0)
        bounds = mask.getbbox()
        if not bounds:
            raise ValueError(f"Empty frame: {sheet} {index}")
        x0, y0, x1, y1 = bounds
        # Register the center of both short shoes, independent of generated
        # cell padding or arm movement. No pixels are moved or resampled.
        shoe_band = max(y0, y1 - round((y1 - y0) * 0.12))
        shoe_box = mask.crop((x0, shoe_band, x1, y1)).getbbox()
        foot_x = x0 + (shoe_box[0] + shoe_box[2]) / 2
        foot_y = y1
        region = (max(left, left + x0 - 3), max(top, top + y0 - 3),
                  min(right, left + x1 + 3), min(bottom, top + y1 + 3))
        anchor = ((left + foot_x - region[0]) / (region[2] - region[0]),
                  (top + foot_y - region[1]) / (region[3] - region[1]))
        regions.append((region, anchor))
    return regions


records = json.loads((PROVENANCE / "visual-revision.json").read_text())
for source in records["images"]:
    if not source.get("animation"):
        continue
    clip = source["key"]
    regions = grid_regions(clip, 3, 2)
    reference = (max(r[0][2] - r[0][0] for r in regions),
                 max(r[0][3] - r[0][1] for r in regions))
    frames = []
    hashes = []
    image = Image.open(PRODUCTION / source["file"])
    for index, (region, anchor) in enumerate(regions):
        key = f"{clip}_{index:02d}"
        add(key, clip, region, anchor, reference)
        frames.append(key)
        hashes.append(hashlib.sha256(image.crop(region).tobytes()).hexdigest())
    assert len(set(hashes)) == 6, f"{clip} must contain six distinct drawings"
    fps = 8 if "_walk_" in clip or "_work_" in clip else 6
    animations[clip] = {"fps": fps, "frames": frames}
    manifest[clip] = dict(manifest[frames[0]])
    verification[clip] = {"native_reference": list(reference), "frame_hashes": hashes,
                          "frames": len(frames), "fps": fps}

for clip in animations:
    if clip.startswith("guest_") and "_walk_" in clip:
        manifest[clip.replace("_walk_", "_")] = dict(manifest[clip])
for alias, clip in {
    "chef_up": "chef_work_up", "chef_down": "chef_work_down",
    "chef_work": "chef_work_down", "chef_hold": "chef_hold_up",
    "guest_a_waiting": "guest_a_waiting_down", "guest_b_waiting": "guest_b_waiting_down",
    "guest_a_eating": "guest_a_eating_down", "guest_b_eating": "guest_b_eating_down",
    "guest_a_seated": "guest_a_waiting_down", "guest_b_seated": "guest_b_waiting_down",
}.items():
    manifest[alias] = dict(manifest[clip])

props = components(PRODUCTION / "props_v2.png", 24)[:8]
props.sort(key=lambda item: (item[1][1] + item[1][3]) / 2)
prop_boxes = []
for row in range(2):
    prop_boxes.extend(box for _, box in sorted(props[row * 4:(row + 1) * 4], key=lambda item: item[1][0]))
for key, region in zip(
    ["stool", "salmon_nigiri", "blackboard", "plant", "barrel", "crate", "lantern", "plant_tall"], prop_boxes,
):
    add(key, "props_v2", region, (0.5, 0.5) if key == "salmon_nigiri" else (0.5, 1.0))

environment = components(PRODUCTION / "environment_v2.png", 24)[:6]
environment.sort(key=lambda item: (item[1][1] + item[1][3]) / 2)
environment_boxes = []
for row in range(3):
    environment_boxes.extend(box for _, box in sorted(environment[row * 2:(row + 1) * 2], key=lambda item: item[1][0]))
for key, region in zip(
    ["entrance", "pile_sofa", "pile_shelf", "pile_cart", "covered_dock", "harbor_tree"], environment_boxes,
):
    add(key, "environment_v2", region)

belt = json.loads((PROVENANCE / "belt-bake.json").read_text())
width, height = belt["frame_size"]
assert width % 4 == 0
tile_width = width // 4
balance = json.loads((BASE.parent / "content/starter.json").read_text())
belt_fps = 6 / (0.5 * float(balance["service"]["belt_seconds_per_cell"]))
for quarter, clip in enumerate(["belt_end_left", "belt_horizontal", "belt_horizontal_b", "belt_end_right"]):
    frames = []
    for phase in range(6):
        key = f"{clip}_{phase:02d}"
        add(key, f"belt_frame_{phase:02d}",
            (quarter * tile_width, 0, (quarter + 1) * tile_width, height), (0.5, 0.5))
        frames.append(key)
    animations[clip] = {"fps": belt_fps, "frames": frames}
    manifest[clip] = dict(manifest[frames[0]])
manifest["belt_endpoint"] = dict(manifest["belt_end_right"])
animations["belt_endpoint"] = dict(animations["belt_end_right"])
floor = Image.open(PRODUCTION / "floor_doodle_v2.png")
add("floor_wood", "floor_doodle_v2", (0, 0, floor.width, floor.height), (0, 0))
icon = Image.open(PRODUCTION / "app_icon.png")
add("app_icon", "app_icon", (0, 0, icon.width, icon.height), (0.5, 0.5))

(PRODUCTION / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(PRODUCTION / "animations.json").write_text(json.dumps(animations, indent=2) + "\n")
atlas_dir = PRODUCTION / "atlas"
atlas_dir.mkdir(exist_ok=True)
for path in atlas_dir.glob("*.tres"):
    path.unlink()
for name, entry in manifest.items():
    values = ", ".join(str(v) for v in entry["region"])
    (atlas_dir / f"{name}.tres").write_text(
        '[gd_resource type="AtlasTexture" load_steps=2 format=3]\n\n'
        f'[ext_resource type="Texture2D" path="{entry["file"]}" id="1"]\n\n'
        f'[resource]\natlas = ExtResource("1")\nregion = Rect2({values})\nfilter_clip = true\n'
    )

for path in PRODUCTION.glob("*.png"):
    image = Image.open(path)
    entry = {"size": list(image.size), "mode": image.mode,
             "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if "A" in image.getbands():
        alpha = image.getchannel("A")
        entry["alpha_range"] = list(alpha.getextrema())
        entry["fully_transparent_fraction"] = alpha.histogram()[0] / (image.width * image.height)
    verification[path.name] = entry
(PROVENANCE / "image-verification.json").write_text(json.dumps(verification, indent=2) + "\n")
print(f"Wrote {len(manifest)} registered native regions and {len(animations)} six-frame clips.")
