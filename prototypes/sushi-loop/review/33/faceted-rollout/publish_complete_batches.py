"""Publish only whole native IDs already passed by the independent pixel watcher.

Local publication may overlap remaining renders. This driver alone owns manifest
writes; it verifies every selected capture's source receipt/checksum, invokes the
frozen publisher sequentially, and records completed IDs. It never stamps final
approval or pushes/deploys a partial catalog.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".publication-tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def publish_batch(args):
    native = args.export.resolve()
    project_hash = sha(native / "source/sushi-loop-world-library.blend")
    ids = json.loads((native / "source/sushi-loop-world-library.export.json").read_text())["assetIds"]
    progress = json.loads(args.progress.read_text())
    if progress.get("issues"):
        raise RuntimeError("Independent capture watcher has errors; publication stopped")
    complete = set(ids) - set(progress["pendingAssets"])
    state = json.loads(args.state.read_text()) if args.state.exists() else {
        "projectSHA256": project_hash, "publishedIDs": [], "batches": [],
        "scope": "Local audited whole-ID publication; no final approval, push or deployment",
    }
    if state["projectSHA256"] != project_hash:
        raise RuntimeError("Publication tracker belongs to another frozen source")
    selected = args.ids or [aid for aid in ids if aid in complete and aid not in state["publishedIDs"]][:args.batch_size]
    if set(selected) - complete:
        raise RuntimeError("Selected IDs have not all passed independent whole-ID pixel audit")
    if not selected:
        print(json.dumps({"publishedIDs": len(state["publishedIDs"]), "newCompleteIDs": []}))
        return len(state["publishedIDs"]) == len(ids)
    helper_names = {
        "runtime": "capture_runtime.py", "nativeActions": "native_actions.py",
        "worker": "capture_worker.py", "catalogStyle": "catalog_style.py",
        "catalogFaceted": "catalog_faceted.py", "conceptFooting": "concept_decoration_geometry.py",
    }
    helpers = {name: sha(args.helpers / filename) for name, filename in helper_names.items()}
    workers = {}
    verified_frames = 0
    for aid in selected:
        folder = native / "source" / aid
        metadata = json.loads((folder / "asset.json").read_text())
        rig = json.loads((folder / "rig.json").read_text())
        metadata_hashes = {"assetJson": sha(folder / "asset.json"), "rigJson": sha(folder / "rig.json"), "assetId": aid}
        expected_paths = set()
        for clip, recipe in rig["clips"].items():
            for direction in metadata.get("directions", ["N", "E", "S", "W"]):
                for index in range(recipe["frames"]):
                    path = native / "raw-frames" / aid / (clip + "-" + direction) / (str(index).zfill(3) + ".png")
                    expected_paths.add(path)
                    receipt = json.loads(path.with_suffix(".capture.json").read_text())
                    worker = receipt["worker"]
                    if worker not in workers:
                        status = json.loads((native / "capture-workers" / (worker + ".status.json")).read_text())
                        source = status["nativeSource"]
                        if source["blend"] != project_hash or any(source.get(key) != value for key, value in helpers.items()):
                            raise RuntimeError("Worker refers to stale project/helper inputs: " + worker)
                        if source["samples"] != 32 or source["sourceScale"] != "authored":
                            raise RuntimeError("Worker used the wrong capture sampling: " + worker)
                        workers[worker] = source
                    if receipt["nativeVersion"] != digest({**workers[worker], **metadata_hashes}):
                        raise RuntimeError("Stale native metadata receipt: " + str(path))
                    expected = {
                        "state": "complete", "assetId": aid, "clip": clip,
                        "direction": direction, "index": index, "fps": 12,
                        "width": metadata["frame"][0] * metadata["scale"],
                        "height": metadata["frame"][1] * metadata["scale"],
                    }
                    if any(receipt.get(key) != value for key, value in expected.items()):
                        raise RuntimeError("Capture identity, dimensions or timing mismatch: " + str(path))
                    if receipt["sha256"] != sha(path):
                        raise RuntimeError("Capture checksum mismatch: " + str(path))
                    verified_frames += 1
        if set((native / "raw-frames" / aid).rglob("*.png")) != expected_paths:
            raise RuntimeError("Unexpected/missing PNGs in completed object: " + aid)
    print(json.dumps({"verifiedIDs": selected, "verifiedFrames": verified_frames, "projectSHA256": project_hash}), flush=True)
    if args.dry_run:
        return False
    command = [
        sys.executable, str(args.helpers / "publish_captures.py"),
        "--repo", str(args.repo.resolve()), "--native", str(native),
        "--raw-root", str(native / "raw-frames"), "--runtime-scale", "2",
        "--ids", *selected,
    ]
    subprocess.run(command, check=True)
    state["publishedIDs"] = [aid for aid in ids if aid in set(state["publishedIDs"]) | set(selected)]
    state["batches"].append({
        "ids": selected, "frames": verified_frames,
        "publishedAtUTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "pixelWatcherProgressSHA256": sha(args.progress),
    })
    write(args.state, state)
    print(json.dumps({"publishedIDs": len(state["publishedIDs"]), "totalNativeIDs": len(ids)}), flush=True)
    return len(state["publishedIDs"]) == len(ids)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--helpers", type=Path, required=True)
    parser.add_argument("--progress", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--interval", type=float, default=60)
    args = parser.parse_args()
    if args.batch_size < 1 or args.interval < 1 or args.watch and (args.ids or args.dry_run):
        parser.error("Use positive batch/interval values; --watch cannot combine with --ids or --dry-run")
    while True:
        before = len(json.loads(args.state.read_text())["publishedIDs"]) if args.state.exists() else 0
        finished = publish_batch(args)
        if finished or not args.watch:
            return
        after = len(json.loads(args.state.read_text())["publishedIDs"]) if args.state.exists() else 0
        # Drain already validated work immediately. Poll once per minute only
        # when there is no new complete batch, avoiding a queue at render end.
        if after == before:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
