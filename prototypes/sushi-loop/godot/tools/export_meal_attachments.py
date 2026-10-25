"""Export native captured meal positions for presentation-only pickup flights."""
from pathlib import Path
import gzip
import hashlib
import json

PROTOTYPE = Path(__file__).resolve().parents[2]
OBJECTS = PROTOTYPE / "assets/refinement/objects"
sources = {}
actors = {}


def read(relative):
    path = OBJECTS / relative
    raw = path.read_bytes()
    sources[path.relative_to(PROTOTYPE).as_posix()] = hashlib.sha256(raw).hexdigest()
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def store(identity, clip, direction, index, corners):
    # Current native frames are 384x640 with root (192,496), 256 px/cell.
    # These are the same registered camera captures used by the body sprites.
    xs, ys = [p[0] for p in corners], [p[1] for p in corners]
    center = [(sum(xs) / len(xs) - 192) / 256,
              (sum(ys) / len(ys) - 496) / 256,
              (max(xs) - min(xs)) / 256]
    frames = actors.setdefault(identity, {}).setdefault(clip, {}).setdefault(direction, [None] * 12)
    frames[index] = center


for name, path, clip in [
    ("customer-rosa", "customer-rosa/candidates/round-05/measurements.json.gz", "eat"),
    ("customer-rosa", "customer-rosa/candidates/round-05/runtimeVariants/measurements.json.gz", "eat-salmon"),
]:
    for row in read(path):
        if row["clip"] == clip:
            store(name, clip, row["direction"], row["frame"], row["projectedFoodCorners"])

for mode, clip in [("main", "eat"), ("runtime", "eat-salmon")]:
    data = read(f"customer-ellis/candidates/round-03/{mode}-native-audit.json")
    for row in data["samples"]:
        if row["clip"] == clip:
            store("customer-ellis", clip, row["direction"], row["frame"] - 1, row["food"]["cornersProjected"])
    data = read(f"customer-samir/candidates/round-01/{mode}/validation-native.json")
    for row in data["clips"][clip]["samples"]:
        store("customer-samir", clip, row["direction"], row["frame"] - 1, row["foodProjectedCorners"])

for row in read("customer-june/candidates/round-02/food-projection-proof-576.v2.json"):
    if (row["mode"], row["clip"]) in [("main", "eat"), ("runtime", "eat-salmon")]:
        store("customer-june", row["clip"], row["direction"], row["index"], row["correctedCanonicalLawCornerPixels"])

for clips in actors.values():
    for directions in clips.values():
        if set(directions) != {"N", "E", "S", "W"} or any(None in frames for frames in directions.values()):
            raise ValueError("Incomplete native meal attachment capture family")

output = PROTOTYPE / "godot/content/meal_attachments.json"
output.write_text(json.dumps({"version": 1, "fps": 12,
    "coordinate_space": "root-relative cells; [center x, center y, full native food width]",
    "source_files": sources, "actors": actors}, indent=2) + "\n")
print(f"Exported {len(actors)} native customer meal attachment families to {output}")
