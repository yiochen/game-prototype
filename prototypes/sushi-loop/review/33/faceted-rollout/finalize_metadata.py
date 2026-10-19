"""Stage native record provenance and record the user's approved art rollout.

Run only after the complete new native capture batch has been audited and
published. Publication itself deliberately leaves approval pending; this final
step requires matching native/pixel evidence for the newly frozen project.
It never changes a mesh, material, action, raw capture or runtime atlas.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".faceted-metadata-tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def preserve_and_copy(source, destination, history):
    if destination.exists() and sha(source) == sha(destination):
        return
    if destination.exists():
        archive = history / sha(destination)[:16] / destination.name
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            shutil.copy2(destination, archive)
        elif sha(archive) != sha(destination):
            raise RuntimeError("Immutable metadata history collision: " + str(archive))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--native-audit", type=Path, required=True)
    parser.add_argument("--pixel-audit", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, help="Defaults to the new native export's raw-frames directory")
    parser.add_argument("--approval-authorized", action="store_true", required=True)
    parser.add_argument("--evidence", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    production = args.repo.resolve() / "prototypes/sushi-loop/assets/production"
    source = production / "source"
    native = args.native.resolve() / "source"
    blend_hash = sha(native / "sushi-loop-world-library.blend")
    export_report = json.loads((native / "sushi-loop-world-library.export.json").read_text())
    native_audit = json.loads(args.native_audit.read_text())
    pixel_report = json.loads(args.pixel_audit.read_text())
    pixel_audit = pixel_report.get("native", pixel_report)
    ids = export_report["assetIds"]
    if len(ids) != 104 or len(set(ids)) != 104:
        raise RuntimeError("Expected the complete set of 104 active native objects")
    finalization_path = native / "sushi-loop-world-library.finalized.json"
    finalization = json.loads(finalization_path.read_text()) if finalization_path.exists() else None
    if export_report["sha256"] != blend_hash:
        if not finalization or finalization.get("state") != "complete" or finalization.get("sha256") != blend_hash or finalization.get("inputSha256") != export_report["sha256"]:
            raise RuntimeError("Frozen project is not connected to the original MCP export by its finalization receipt")
    if not native_audit.get("passed") or not pixel_audit.get("passed") or not pixel_report.get("passed"):
        raise RuntimeError("Both native and complete capture audits must pass first")
    if native_audit.get("projectSHA256") != blend_hash:
        raise RuntimeError("Native audit does not identify the newly frozen project")
    if set(pixel_audit.get("assets", {})) != set(ids):
        raise RuntimeError("Capture audit does not cover the complete native inventory")
    expected_raw = args.raw_root.resolve() if args.raw_root else args.native.resolve() / "raw-frames"
    if Path(pixel_audit.get("rawRoot", pixel_audit.get("raw", ""))).resolve() != expected_raw:
        raise RuntimeError("Capture audit refers to another raw batch; do not publish an earlier pilot or old production frames")
    if pixel_audit.get("frames") != 9390:
        raise RuntimeError("Expected all 9390 native frame-facing samples")
    manifest_path = production / "library.json"
    manifest = json.loads(manifest_path.read_text())
    by_id = {item["id"]: item for item in manifest["objects"]}
    if len(by_id) != 117:
        raise RuntimeError("Active catalog must retain 104 native and 13 flat entries")
    if manifest["production"]["nativeSourceSHA256"].get("sushi-loop-world-library.blend") != blend_hash:
        raise RuntimeError("Publish the new capture batch before updating final metadata")
    for aid in ids:
        published = by_id[aid]
        if not any(path.endswith("sushi-loop-world-library.blend") and digest == blend_hash
                   for path, digest in published["source"]["hashes"].items()):
            raise RuntimeError("Object still references an older source project: " + aid)
        for clip in published["clips"]:
            for atlas in clip["directions"].values():
                if max(atlas["atlasSize"]) > 8192:
                    raise RuntimeError("Atlas exceeds publication texture cap: " + atlas["image"])
    # Preserve replaced native records independently from published capture records.
    records = source / "native-records"
    index_path = records / "index.json"
    if index_path.exists():
        archive = source / "native-records-history" / "indexes" / sha(index_path)[:16] / "index.json"
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            shutil.copy2(index_path, archive)
    index = {
        "version": 3,
        "status": "native-models-actions-and-faceted-captures-complete",
        "capturedAtUTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "editableProject": "blender/sushi-loop-world-library.blend",
        "nativeExportReport": "blender/sushi-loop-world-library.export.json",
        "sourceBlendSHA256": blend_hash,
        "assetIds": ids, "records": {},
        "scope": "104 native objects and complete Faceted captures. 13 flat entries retain ImageGen/procedural sources. User approval is recorded in the runtime manifest.",
    }
    for aid in ids:
        index["records"][aid] = {}
        for name in ["asset.json", "camera.json", "rig.json"]:
            destination = records / aid / name
            preserve_and_copy(native / aid / name, destination, source / "native-records-history" / aid)
            index["records"][aid][name] = {
                "path": str(destination.relative_to(source)), "sha256": sha(destination),
            }
        by_id[aid]["productionStage"] = "Native Blender · approved Faceted lighting and materials"
        if by_id[aid].get("validation", {}).get("rigEvidence"):
            by_id[aid]["validation"]["rigEvidence"] = "exported; native and complete capture audits passed"
    raw_report_path = native / "sushi-loop-world-library.export.json"
    raw_report_revision = source / "blender/revisions" / sha(raw_report_path)[:16] / raw_report_path.name
    if raw_report_revision.exists() and sha(raw_report_revision) != sha(raw_report_path):
        raise RuntimeError("Immutable raw export report identity collision")
    preserve_and_copy(raw_report_path, raw_report_revision, source / "blender/history")
    raw_project = native / "sushi-loop-world-library-unfinalized.blend"
    raw_project_revision = None
    if raw_project.exists():
        if sha(raw_project) != export_report["sha256"]:
            raise RuntimeError("Retained original MCP project differs from its export report")
        raw_project_revision = source / "blender/revisions" / sha(raw_project)[:16] / "sushi-loop-world-library.blend"
        if raw_project_revision.exists() and sha(raw_project_revision) != sha(raw_project):
            raise RuntimeError("Immutable original MCP project identity collision")
        preserve_and_copy(raw_project, raw_project_revision, source / "blender/history")
    if finalization:
        preserve_and_copy(finalization_path,
                          source / "blender/sushi-loop-world-library.finalized.json",
                          source / "blender/history")
    # The raw MCP library and the subsequently finalized normal startup project
    # are different files. Preserve both identities and the receipt linking them.
    canonical_report = {
        **export_report,
        "path": str(source / "blender/sushi-loop-world-library.blend"),
        "sha256": blend_hash,
        "bytes": (native / "sushi-loop-world-library.blend").stat().st_size,
        "reportRole": "Finalized editable project identity; original MCP export report retained unchanged",
        "originalMCPExportSHA256": export_report["sha256"],
        "originalMCPExportReport": str(raw_report_revision.relative_to(source)),
        "originalMCPProject": str(raw_project_revision.relative_to(source)) if raw_project_revision else None,
        "finalizationReport": "blender/sushi-loop-world-library.finalized.json" if finalization else None,
    }
    args.evidence.mkdir(parents=True, exist_ok=True)
    final_report_path = args.evidence / "finalized-export-report.json"
    write(final_report_path, canonical_report)
    preserve_and_copy(final_report_path,
                      source / "blender/sushi-loop-world-library.export.json",
                      source / "blender/history")
    write(index_path, index)
    for aid, item in by_id.items():
        if aid not in ids:
            item["productionStage"] = item.get("productionStage", "2D artwork/effect").replace(
                "awaiting art approval", "approved artwork/effect")
    manifest["approval"] = {
        "concept": "approved", "finalAssets": "approved", "issue": 33,
        "approvedOn": "2026-10-19",
        "scope": "Faceted native lighting, matte wood, muted-clay conveyor rails and full asset rollout",
    }
    manifest["production"].update(
        visualApproval="approved",
        finish="Faceted matte Principled, native lower-height ramp and 135% sRGB grade",
        maximumAtlasDimension=8192,
    )
    write(manifest_path, manifest)
    evidence = {
        "passed": True, "sourceBlendSHA256": blend_hash, "nativeObjects": len(ids),
        "flatObjectsPreserved": len(by_id) - len(ids),
        "nativeFrames": pixel_audit["frames"],
        "manifestSHA256": sha(manifest_path), "nativeIndexSHA256": sha(index_path),
        "nativeAuditSHA256": sha(args.native_audit), "pixelAuditSHA256": sha(args.pixel_audit),
        "scope": "Metadata finalized after complete native capture publication; browser/build/Godot import checks are recorded separately.",
    }
    write(args.evidence / "publication-metadata.json", evidence)
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
