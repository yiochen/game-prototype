#!/usr/bin/env python3
"""Fast packaging-boundary tests; no SDK, imports or installed saves are touched."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_android as build


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sushi-android-packaging-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "godot"
        for name in build.ROOT_FILES:
            self.write(name, "[application]\n" if name == "project.godot" else "{}")
        self.write("assets/catalog/manifest.json", '{"objects": []}')
        self.write("assets/catalog/sprites/test/static-s.png", b"approved sprite bytes")
        self.write("assets/ui/app_icon.png", b"wordless icon")
        self.write("scripts/app.gd", "extends Node\n")
        approved = self.root / "assets/production"
        (approved / "sprites/test").mkdir(parents=True)
        (approved / "library.json").write_text('{"approval":{"finalAssets":"approved"}}')
        (approved / "sprites/test/static-s.png").write_bytes(b"approved sprite bytes")

    def write(self, name, value):
        path = self.project / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else value.encode())
        return path

    def test_only_runtime_allowlist_is_staged_without_changing_pixels(self):
        for name in ("assets/production/old.png", "assets/provenance/source.png", "review/10/evidence.png",
                     "tests/fixture.json", "tools/script.gd", ".local/signing/release.json",
                     "assets/audio/audio-verification.json", "assets/catalog/source-provenance.json"):
            self.write(name, b"must not ship")
        audio = self.write("assets/audio/click.wav", b"runtime audio")
        selected, catalog = build.stage_runtime(self.project, self.root / "staged")
        self.assertEqual(catalog["atlas_count"], 1)
        self.assertEqual(selected["assets/audio/click.wav"], build.sha(audio))
        self.assertEqual((self.root / "staged/assets/catalog/sprites/test/static-s.png").read_bytes(), b"approved sprite bytes")
        self.assertEqual(len(selected), 9)
        self.assertFalse((self.root / "staged/.local").exists())
        self.assertFalse((self.root / "staged/assets/production").exists())

    def test_rejects_runtime_reference_to_excluded_legacy_art(self):
        self.write("scripts/app.gd", 'extends Node\nconst OLD = preload("res://assets/production/old.png")\n')
        with self.assertRaisesRegex(ValueError, "excluded old art"):
            build.runtime_sources(self.project)

    def test_rejects_symlink_that_escapes_the_project(self):
        external = self.root / "outside.png"
        external.write_bytes(b"private bytes")
        (self.project / "assets/ui/escape.png").symlink_to(external)
        with self.assertRaisesRegex(ValueError, "outside the project"):
            build.runtime_sources(self.project)

    def test_rejects_changed_native_pixels(self):
        self.write("assets/catalog/sprites/test/static-s.png", b"changed sprite bytes")
        with self.assertRaisesRegex(ValueError, "approved source pixels"):
            build.validate_catalog(self.project, build.runtime_sources(self.project))

    def test_missing_release_signer_does_not_generate_a_replacement(self):
        with self.assertRaisesRegex(ValueError, "Restore the original release"):
            build.signing_credentials(self.project, "release", {}, "/missing/keytool")
        self.assertFalse((self.project / ".local/signing/release.keystore").exists())


class ApkBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sushi-apk-audit-test-")
        self.addCleanup(self.temporary.cleanup)
        self.apk = Path(self.temporary.name) / "game.apk"
        self.fingerprint = "ab" * 32
        self.branding = {"android_package": "example.game", "version_code": 20, "version_name": "0.2.0",
                         "release_signer_sha256": self.fingerprint}
        self.badging = "package: name='example.game' versionCode='20' versionName='0.2.0'\nsdkVersion:'24'\ntargetSdkVersion:'35'\n"
        self.signer = f"Signer #1 certificate SHA-256 digest: {self.fingerprint}\n"

    def archive(self, extra=None):
        with zipfile.ZipFile(self.apk, "w") as archive:
            for name, data in {"lib/arm64-v8a/libgodot_android.so": b"arm", "lib/x86_64/libgodot_android.so": b"x64",
                               "assets/assets/catalog/manifest.json": b'{}', **(extra or {})}.items():
                archive.writestr(name, data)

    def audit(self):
        with patch.object(build, "run", side_effect=lambda command, *_: self.signer if "apksigner" in command[0] else self.badging):
            return build.audit_apk(self.apk, self.branding, "release", Path("/sdk"), {}, "secret-test-password")

    def test_accepts_matching_offline_release_and_both_architectures(self):
        self.archive()
        self.assertEqual(self.audit()["signer_sha256"], self.fingerprint)

    def test_rejects_signing_secret_inside_archive(self):
        self.archive({"assets/runtime.bin": b"prefix secret-test-password suffix"})
        with self.assertRaisesRegex(ValueError, "signing credentials"):
            self.audit()

    def test_rejects_legacy_art_and_authoring_evidence(self):
        self.archive({"assets/assets/production/old.png": b"legacy"})
        with self.assertRaisesRegex(ValueError, "excluded authoring"):
            self.audit()

    def test_rejects_incompatible_certificate(self):
        self.archive()
        self.signer = "Signer #1 certificate SHA-256 digest: " + "cd" * 32
        with self.assertRaisesRegex(ValueError, "pinned update identity"):
            self.audit()

    def test_rejects_unrequested_network_permission(self):
        self.archive()
        self.badging += "uses-permission: name='android.permission.INTERNET'\n"
        with self.assertRaisesRegex(ValueError, "Internet permission"):
            self.audit()


if __name__ == "__main__":
    unittest.main(verbosity=2)
