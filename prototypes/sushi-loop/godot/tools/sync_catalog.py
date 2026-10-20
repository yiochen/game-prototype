#!/usr/bin/env python3
"""Copy the approved #33 restaurant subset without changing sprite pixels.

--check verifies selection, provenance and shipped bytes. Whole authored frames,
logical ground roots and the shared 128px pitch are preserved. The selection
includes all native facings of movable objects used by the restaurant editor.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil

from catalog_contract import make_manifest as approved_manifest, verify_catalog

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT.parent / "assets/production"
DESTINATION = PROJECT / "assets/catalog"


def make_manifest() -> tuple[dict, set[str]]:
    return approved_manifest(SOURCE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        manifest, files = verify_catalog(SOURCE, DESTINATION)
    else:
        manifest, files = make_manifest()
        DESTINATION.mkdir(parents=True, exist_ok=True)
        for path in sorted(files):
            target = DESTINATION / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / path, target)
        (DESTINATION / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"{'Verified' if args.check else 'Copied'} {len(manifest['objects'])} approved objects / {len(files)} exact atlases / {sum((SOURCE / path).stat().st_size for path in files):,} bytes")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise SystemExit(str(error)) from None
