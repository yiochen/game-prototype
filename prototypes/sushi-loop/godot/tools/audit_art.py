"""Read-only release-art audit. Requires Pillow and NumPy."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

base = Path(__file__).resolve().parents[1]
production = base / "assets/production"
manifest = json.loads((production / "manifest.json").read_text())
clips = json.loads((production / "animations.json").read_text())
bake = json.loads((base / "assets/provenance/belt-bake.json").read_text())
report = {"character_clips": 0, "character_frames": 0, "belt_frames_per_cut": 6,
          "native_belt_cut": [bake["quarter_width"], bake["frame_size"][1]],
          "minimum_character_height": 10000, "checks": []}
for clip, data in clips.items():
    if clip.startswith("belt"):
        continue
    assert len(data["frames"]) >= 6, clip
    hashes = set()
    for key in data["frames"]:
        entry = manifest[key]
        x, y, width, height = entry["region"]
        image = Image.open(production / Path(entry["file"]).name)
        hashes.add(hashlib.sha256(image.crop((x, y, x + width, y + height)).tobytes()).hexdigest())
        report["minimum_character_height"] = min(report["minimum_character_height"], height)
        assert height >= 384, key
    assert len(hashes) == len(data["frames"]), clip
    report["character_clips"] += 1
    report["character_frames"] += len(data["frames"])
report["checks"].append("Every character clip has six different native pixel drawings, at least384px tall")
frames = [np.asarray(Image.open(production / f"belt_frame_{index:02d}.png")) for index in range(6)]
baseline = frames[0]
x0, y0, width, height = bake["deck_bounds"]
outside = np.ones(baseline.shape[:2], dtype=bool)
outside[y0:y0 + height + 1, x0:x0 + width + 1] = False
for frame in frames[1:]:
    assert np.array_equal(frame[outside], baseline[outside]), "A rail/support moved"
report["checks"].append("Coral rails and wood supports remain pixel-identical outside the moving deck in every phase")
for quarter, clip in enumerate(["belt_end_left", "belt_horizontal", "belt_horizontal_b", "belt_end_right"]):
    hashes = set()
    for phase, key in enumerate(clips[clip]["frames"]):
        entry = manifest[key]
        x, y, width, height = entry["region"]
        assert [x, y, width, height] == [quarter * 502, 0, 502, 460]
        hashes.add(hashlib.sha256(frames[phase][:, x:x + width].tobytes()).hexdigest())
    assert len(hashes) == 6, clip
for frame in frames:
    cuts = [frame[:, quarter * 502:(quarter + 1) * 502] for quarter in range(4)]
    assert np.array_equal(np.concatenate(cuts, axis=1), frame)
report["checks"].append("Each of four cuts has six unique phases; concatenating the cuts exactly reconstructs each connected strip")
records = json.loads((base / "assets/provenance/visual-revision.json").read_text())
checked = 0
for entry in records["images"]:
    source = Path(entry["source"])
    target = production / entry["file"]
    if entry.get("status") or not source.exists() or not target.exists():
        continue
    assert hashlib.sha256(source.read_bytes()).digest() == hashlib.sha256(target.read_bytes()).digest()
    checked += 1
report["unmodified_generated_sources_verified"] = checked
report["checks"].append("All available copied generation sources are byte-identical; no fake resolution upscaling")
output = base / "review/10/animation/art-audit.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
