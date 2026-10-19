"""Authoritative approved-catalog selection and runtime-registration verification.

Shared by the catalog copy CLI and Android packaging. Native source records,
logical roots, complete clip regions and source pixels must all agree.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path

DIRECTIONS = ['N', 'E', 'S', 'W']
SELECTION = {
    'floor-cream': (['static'], ['S']),
    'floor-blue-wave': (['static'], ['S']),
    'entry-finished': (['static'], ['S']),
    'wall-middle': (['static'], ['S', 'E']),
    'wall-inner-corner': (['static'], ['S']),
    'wall-outer-corner': (['static'], ['S']),
    'wall-end': (['static'], ['S']),
    'plant-angular': (['idle'], ['S']),
    'barrel-wood': (['static'], ['S']),
    'crate-wood': (['static'], ['S']),
    'lantern-gold': (['idle'], ['S']),
    'stool-wood': (['static'], DIRECTIONS),
    'belt-start-e': (['running'], ['S']),
    'belt-straight-e': (['running'], ['S']),
    'belt-end-e': (['running'], ['S']),
    'chef-lena': (['idle', 'work', 'hold', 'load'], DIRECTIONS),
    'chef-blackboard': (['idle'], ['S']),
    'coin-pop': (['pop'], ['S']),
    **{identity: (['stand', 'walk', 'seated-wait', 'eat', 'sit-down', 'stand-up'], DIRECTIONS)
       for identity in ['customer-rosa', 'customer-ellis', 'customer-samir', 'customer-june']},
    **{identity: (['static'], ['S']) for identity in ['dish-salmon', 'dish-cucumber', 'dish-eel']},
    **{identity: (['idle'], ['S']) for identity in ['garbage-sofa', 'garbage-car', 'garbage-shelving']},
}



def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(data)
    return value.hexdigest()


def atlas_path(directory: Path, image: str) -> Path:
    relative = Path(image)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:1] != ("sprites",) or relative.suffix != ".png":
        raise ValueError(f"Invalid catalog atlas reference: {image}")
    result = directory / relative
    if not result.resolve().is_relative_to(directory.resolve()):
        raise ValueError(f"Catalog atlas escapes its source directory: {image}")
    if not result.is_file():
        raise ValueError(f"Missing referenced catalog atlas: {image}")
    return result


def make_manifest(source: Path, selection: dict | None = None) -> tuple[dict, set[str]]:
    selection = SELECTION if selection is None else selection
    if not selection:
        raise ValueError("The approved runtime selection cannot be empty.")
    library_file = source / "library.json"
    library = json.loads(library_file.read_text())
    if library.get("approval", {}).get("finalAssets") != "approved":
        raise ValueError("The source scene-art catalog is not approved.")
    originals = library.get("objects")
    if not isinstance(originals, list) or not originals:
        raise ValueError("The approved source catalog has no object records.")
    objects = {entry["id"]: entry for entry in originals}
    if len(objects) != len(originals):
        raise ValueError("The approved source catalog has duplicate object IDs.")
    result = {
        "version": 1, "cellSize": library["cellSize"], "approval": library["approval"],
        "source": {"library": "../assets/production/library.json", "librarySha256": digest(library_file)},
        "policy": "Exact approved atlas bytes; whole authored frames; fixed logical roots; no pose fitting or sprite distortion.",
        "objects": {},
    }
    files = set()
    for identity, (clip_names, directions) in selection.items():
        if identity not in objects:
            raise ValueError(f"Approved catalog object is missing: {identity}")
        original = objects[identity]
        entry = {key: deepcopy(original[key]) for key in ["id", "name", "kind", "footprint", "frameSize", "root", "sourceScale", "projection", "sockets", "ports", "rootCell", "directionRootCells", "directionFootprints", "facingPolicy"] if key in original}
        entry["source"] = {"captureFingerprint": original.get("captureFingerprint"), "blend": original.get("source", {}).get("blend"), "assetRecord": original.get("source", {}).get("assetRecord")}
        entry["clips"] = {}
        for clip in original["clips"]:
            if clip["id"] not in clip_names:
                continue
            selected = {key: deepcopy(clip[key]) for key in ["id", "frames", "fps", "static", "loop", "frameOrder", "frameSize", "root", "sourceScale"] if key in clip}
            selected["directions"] = {}
            for direction in directions:
                if direction not in clip["directions"]:
                    raise ValueError(f"Approved clip facing is missing: {identity}/{clip['id']}/{direction}")
                frame = deepcopy(clip["directions"][direction])
                path = frame["image"]
                frame["sha256"] = digest(atlas_path(source, path))
                selected["directions"][direction] = frame
                files.add(path)
            entry["clips"][clip["id"]] = selected
        if set(entry["clips"]) != set(clip_names):
            raise ValueError(f"Approved clip selection is incomplete: {identity}")
        result["objects"][identity] = entry
    return result, files


def verify_catalog(source: Path, destination: Path, selection: dict | None = None) -> tuple[dict, set[str]]:
    expected, files = make_manifest(source, selection)
    actual = json.loads((destination / "manifest.json").read_text())
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError("Catalog registration/provenance differs from the approved selection; run sync_catalog.py.")
    actual_files = {path.relative_to(destination).as_posix() for path in (destination / "sprites").rglob("*.png")}
    if actual_files != files:
        missing = sorted(files - actual_files)
        extra = sorted(actual_files - files)
        raise ValueError(f"Unexpected or missing runtime atlases (missing={missing}, extra={extra}).")
    for image in sorted(files):
        if digest(atlas_path(source, image)) != digest(atlas_path(destination, image)):
            raise ValueError(f"Runtime atlas differs from approved source pixels: {image}")
    return expected, files
