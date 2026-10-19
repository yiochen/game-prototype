"""Validate published sprite resources in a disposable Godot project.

Copies only the active manifest and referenced atlas PNGs. Never symlink imported
images into the repository: Godot writes sidecar import files next to sources.
The test checks Godot resource compatibility, not Android hardware or gameplay.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--godot", default=shutil.which("godot") or "godot")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    production = args.repo.resolve() / "prototypes/sushi-loop/assets/production"
    evidence = args.evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    project = args.project.resolve() if args.project else Path(tempfile.mkdtemp(prefix="sushi33-godot-import-"))
    project.mkdir(parents=True, exist_ok=True)
    if any(project.iterdir()):
        raise ValueError("Use an empty isolated Godot validation folder")
    manifest_path = production / "library.json"
    manifest_hash = sha(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    images = sorted({atlas["image"] for asset in manifest["objects"] for clip in asset["clips"] for atlas in clip["directions"].values()})
    image_hashes = {}
    for relative in images:
        source = (production / relative).resolve()
        if not source.is_relative_to(production.resolve()):
            raise ValueError("Atlas path escapes production folder: " + relative)
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        image_hashes[relative] = sha(destination)
    shutil.copy2(manifest_path, project / "library.json")
    shutil.copy2(Path(__file__).with_name("validate_godot_sprites.gd"), project / "validate.gd")
    shutil.copy2(production / "source/2d/world_effects.gd", project / "world_effects.gd")
    (project / "project.godot").write_text(
        'config_version=5\n\n[application]\nconfig/name="Sprite import verification"\n'
        '\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        'renderer/rendering_method.mobile="gl_compatibility"\n')
    receipt = {
        "scope": "Disposable Godot editor import and AtlasTexture/SpriteFrames resource validation",
        "project": str(project), "manifestSHA256": manifest_hash,
        "nativeSourceSHA256": manifest.get("production", {}).get("nativeSourceSHA256", {}),
        "atlasSHA256": image_hashes,
    }
    for name, command in [
        ("godot-import.log", [args.godot, "--headless", "--path", str(project), "--editor", "--import"]),
        ("godot-resources.log", [args.godot, "--headless", "--path", str(project), "--script", "res://validate.gd"]),
    ]:
        with (evidence / name).open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
        receipt[name] = {"exitCode": result.returncode}
        if result.returncode:
            receipt["passed"] = False
            (evidence / "godot-import-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
            raise RuntimeError("Godot validation failed: " + str(evidence / name))
    validation = json.loads((project / "validation.json").read_text())
    if sha(manifest_path) != manifest_hash:
        raise RuntimeError("Published manifest changed during Godot validation")
    receipt["passed"] = bool(validation["passed"])
    shutil.copy2(project / "validation.json", evidence / "godot-sprites.json")
    (evidence / "godot-import-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: validation[key] for key in ["passed", "objects", "uniqueAtlasImages", "frameFacingContexts", "maximumAtlasSize", "errors"]}, indent=2))


if __name__ == "__main__":
    main()
