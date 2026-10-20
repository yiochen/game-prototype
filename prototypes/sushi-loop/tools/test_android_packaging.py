#!/usr/bin/env python3
"""Fast packaging-boundary tests; no SDK, imports or installed saves are touched."""
import json
from pathlib import Path
import shutil
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
        self.branding = {"title": "Example", "version_name": "0.4.0", "version_code": 40,
                         "android_package": "example.game", "save_identity": "ExistingSave",
                         "release_signer_sha256": "ab" * 32}
        for name, text in {
            "project.godot": '[application]\nconfig/name="Example"\nconfig/version="0.4.0"\nconfig/custom_user_dir_name="ExistingSave"\n',
            "main.tscn": "{}",
            "branding.json": json.dumps(self.branding, indent=2) + "\n",
            "export_presets.cfg": 'package/name="Example"\npackage/unique_name="example.game"\nversion/name="0.4.0"\nversion/code=40\n',
        }.items():
            self.write(name, text)
        self.write("assets/catalog/sprites/test/static-S.png", b"approved sprite bytes")
        self.write("assets/recipe-variants/manifest.json", '{"fixture": "variant verifier is independently tested"}')
        self.write("assets/recipe-variants/sprites/test/eat-S.png", b"native variant fixture")
        # These cases isolate the base-catalog and packaging boundaries. The
        # recipe verifier independently checks its authored native evidence.
        recipe_verification = patch.object(build.recipe_contract, "verify_recipe_variants", return_value={"objects": 1, "atlases": 1})
        self.recipe_verifier = recipe_verification.start()
        self.addCleanup(recipe_verification.stop)
        self.write("assets/chef-variants/manifest.json", '{"fixture": "chef verifier is independently tested"}')
        self.write("assets/chef-variants/sprites/test/hold-S.png", b"native chef fixture")
        chef_verification = patch.object(build.chef_contract, "verify_chef_variants", return_value={"objects": 1, "atlases": 1})
        self.chef_verifier = chef_verification.start()
        self.addCleanup(chef_verification.stop)
        self.write("assets/feedback-variants/manifest.json", '{"fixture": "feedback verifier is independently tested"}')
        self.write("assets/feedback-variants/sprites/test/smile-S.png", b"2D feedback fixture")
        feedback_verification = patch.object(build.feedback_contract, "verify_feedback_variants", return_value={"objects": 1, "atlases": 1})
        self.feedback_verifier = feedback_verification.start()
        self.addCleanup(feedback_verification.stop)
        self.write("assets/ui/app_icon.png", b"wordless icon")
        # The UI gate uses the exact nine real production PNGs and eight saved
        # ImageGen sources; corruption tests exercise provenance end to end.
        shutil.copytree(build.PROJECT / "assets/ui/editor", self.project / "assets/ui/editor")
        shutil.copytree(build.PROJECT.parent / "assets/ui/editor/v1", self.root / "assets/ui/editor/v1")
        reference = self.root / "design/art-directions/restaurant-item-catalog.png"
        reference.parent.mkdir(parents=True)
        shutil.copyfile(build.PROJECT.parent / "design/art-directions/restaurant-item-catalog.png", reference)
        self.write("scripts/app.gd", "extends Node\n")
        approved = self.root / "assets/production"
        (approved / "sprites/test").mkdir(parents=True)
        original = {
            "id": "test", "name": "Test tile", "kind": "prop", "footprint": [1, 1],
            "frameSize": [128, 192], "root": [64, 160], "sourceScale": 2,
            "projection": "top-down-oblique-square-grid", "rootCell": [0.5, 0.5],
            "sockets": {"S": {"deck": [64, 128]}}, "ports": {},
            "source": {"blend": "source/test.blend", "assetRecord": "records/test.json"},
            "captureFingerprint": "test-capture",
            "clips": [{"id": "static", "frames": 1, "fps": 12, "static": True, "loop": False,
                       "frameOrder": [0], "directions": {"S": {
                           "image": "sprites/test/static-S.png", "columns": 1, "rows": 1,
                           "atlasSize": [256, 384], "rects": [[0, 0, 256, 384]]}}}],
        }
        (approved / "library.json").write_text(json.dumps({"cellSize": 128, "approval": {"finalAssets": "approved"}, "objects": [original]}))
        (approved / "sprites/test/static-S.png").write_bytes(b"approved sprite bytes")
        selection = patch.object(build.catalog_contract, "SELECTION", {"test": (["static"], ["S"])})
        selection.start()
        self.addCleanup(selection.stop)
        manifest, _ = build.catalog_contract.make_manifest(approved)
        self.write("assets/catalog/manifest.json", json.dumps(manifest))

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
        self.assertEqual((self.root / "staged/assets/catalog/sprites/test/static-S.png").read_bytes(), b"approved sprite bytes")
        self.assertEqual(len(selected), 25)
        self.assertEqual(catalog["editor_ui"]["images"], 9)
        self.assertEqual(catalog["editor_ui"]["imagegen_sources"], 8)
        self.assertEqual(selected["assets/ui/editor/manifest.json"], catalog["editor_ui_manifest_sha256"])
        self.assertEqual({name for name in selected if name.startswith("assets/ui/editor/")},
                         {"assets/ui/editor/manifest.json"} | {f"assets/ui/editor/{name}.png" for name in build.editor_ui_contract.ASSETS})
        self.assertIn("assets/recipe-variants/manifest.json", selected)
        self.assertIn("assets/recipe-variants/sprites/test/eat-S.png", selected)
        self.recipe_verifier.assert_any_call(self.root / "staged", source_project=self.project)
        self.chef_verifier.assert_any_call(self.root / "staged", source_project=self.project)
        self.feedback_verifier.assert_any_call(self.root / "staged", source_project=self.project)
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
        self.write("assets/catalog/sprites/test/static-S.png", b"changed sprite bytes")
        with self.assertRaisesRegex(ValueError, "approved source pixels"):
            build.validate_catalog(self.project, build.runtime_sources(self.project))

    def mutate_manifest(self, mutate):
        path = self.project / "assets/catalog/manifest.json"
        manifest = json.loads(path.read_text())
        mutate(manifest)
        path.write_text(json.dumps(manifest))

    def test_rejects_empty_object_registration_even_when_png_bytes_match(self):
        for empty in ({}, []):
            with self.subTest(objects=empty):
                self.mutate_manifest(lambda manifest: manifest.update(objects=empty))
                with self.assertRaisesRegex(ValueError, "registration/provenance"):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())

    def test_rejects_corrupt_ground_root_before_staging(self):
        self.mutate_manifest(lambda manifest: manifest["objects"]["test"].update(root=[64, 159]))
        with self.assertRaisesRegex(ValueError, "registration/provenance"):
            build.stage_runtime(self.project, self.root / "staged")

    def test_rejects_stale_clip_frame_regions(self):
        self.mutate_manifest(lambda manifest: manifest["objects"]["test"]["clips"]["static"]["directions"]["S"].update(rects=[[0, 0, 255, 384]]))
        with self.assertRaisesRegex(ValueError, "registration/provenance"):
            build.validate_catalog(self.project, build.runtime_sources(self.project))

    def test_rejects_missing_referenced_png(self):
        selected = build.runtime_sources(self.project)
        (self.project / "assets/catalog/sprites/test/static-S.png").unlink()
        with self.assertRaisesRegex(ValueError, "missing runtime atlases"):
            build.validate_catalog(self.project, selected)

    def test_rejects_metadata_type_change_that_compares_equal_in_python(self):
        self.mutate_manifest(lambda manifest: manifest["objects"]["test"].update(footprint=[True, 1]))
        with self.assertRaisesRegex(ValueError, "registration/provenance"):
            build.validate_catalog(self.project, build.runtime_sources(self.project))

    def test_missing_release_signer_does_not_generate_a_replacement(self):
        with self.assertRaisesRegex(ValueError, "Restore the original release"):
            build.signing_credentials(self.project, "release", {}, "/missing/keytool")
        self.assertFalse((self.project / ".local/signing/release.keystore").exists())

    def test_stale_native_recipe_variant_evidence_blocks_staging(self):
        self.recipe_verifier.side_effect = ValueError("Stale native meal variant evidence")
        with self.assertRaisesRegex(ValueError, "Stale native meal"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_stale_native_chef_variant_evidence_blocks_staging(self):
        self.chef_verifier.side_effect = ValueError("Stale native chef variant evidence")
        with self.assertRaisesRegex(ValueError, "Stale native chef"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_stale_imagegen_feedback_evidence_blocks_staging(self):
        self.feedback_verifier.side_effect = ValueError("Stale ImageGen feedback evidence")
        with self.assertRaisesRegex(ValueError, "Stale ImageGen"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_review_packages_keep_identical_runtime_and_separate_app_sandboxes(self):
        self.write("content/starter.json", '{"same_runtime": true, "coins": 120}')
        self.write("assets/ui/other-controls.png", b"ImageGen-derived runtime controls")
        original = {name: build.sha(path) for name, path in build.runtime_sources(self.project).items()}
        normal, normal_variant = build.resolve_branding(self.branding)
        normal_source, normal_staged, _ = build.stage_build(self.project, self.root / "normal", normal)
        packages = {normal["android_package"]}
        self.assertEqual(normal_variant["kind"], "normal")
        for scene, issue, label in (("customer-visits", 11, "Customer Visits"),
                                    ("restaurant-editor", 12, "Restaurant Editor")):
            with self.subTest(scene=scene):
                review, variant = build.resolve_branding(self.branding, review_scene=scene)
                review_source, staged, _ = build.stage_build(self.project, self.root / scene, review)
                self.assertEqual(normal_source, review_source)
                self.assertEqual(review["android_package"], f"example.game.review{issue}")
                self.assertNotIn(review["android_package"], packages)
                packages.add(review["android_package"])
                self.assertEqual(review["title"], f"Example · {label}")
                self.assertEqual(review["save_identity"], normal["save_identity"])
                self.assertEqual(review["release_signer_sha256"], normal["release_signer_sha256"])
                self.assertEqual((review["version_name"], review["version_code"]), ("0.4.0", 40))
                self.assertEqual((variant["kind"], variant["scene"], variant["issue"]), ("review", scene, issue))
                self.assertEqual(set(variant["staged_branding_overrides"]), {"title", "android_package"})
                changed = {name for name in normal_staged if normal_staged[name] != staged[name]}
                self.assertEqual(changed, {"project.godot", "export_presets.cfg", "branding.json"})
                self.assertEqual((self.root / scene / "content/starter.json").read_bytes(),
                                 (self.root / "normal/content/starter.json").read_bytes())
                self.assertEqual((self.root / scene / "assets/ui/other-controls.png").read_bytes(),
                                 b"ImageGen-derived runtime controls")
                self.assertNotEqual(build.fingerprint(normal_staged), build.fingerprint(staged))
        self.assertEqual(normal["android_package"], "example.game")
        self.assertEqual(original, {name: build.sha(path) for name, path in build.runtime_sources(self.project).items()})
        _, normal_again, _ = build.stage_build(self.project, self.root / "normal-again", normal)
        self.assertEqual(normal_staged, normal_again)

    def test_review_identity_cannot_be_overridden_into_normal_package(self):
        for scene in ("customer-visits", "restaurant-editor"):
            for options in ({"package_id": "example.game"}, {"title": "Example"}):
                with self.subTest(scene=scene, options=options), self.assertRaisesRegex(ValueError, "isolated title/package"):
                    build.resolve_branding(self.branding, review_scene=scene, **options)

    def test_unknown_review_scene_is_rejected_without_touching_source_identity(self):
        original = dict(self.branding)
        with self.assertRaisesRegex(ValueError, "Unknown isolated review scene"):
            build.resolve_branding(self.branding, review_scene="unapproved-scene")
        self.assertEqual(self.branding, original)

    def test_imagegen_controls_ship_without_source_prompts_or_reference_art(self):
        self.write("assets/ui/other-controls.png", b"runtime control pixels")
        self.write("assets/ui/editor/imagegen.json", b"exact authoring prompt")
        self.write("assets/production/source/ui/editor/reference.png", b"catalog reference")
        files, _ = build.stage_runtime(self.project, self.root / "staged-ui")
        self.assertIn("assets/ui/other-controls.png", files)
        self.assertNotIn("assets/ui/editor/imagegen.json", files)
        self.assertIn("assets/ui/editor/manifest.json", files)
        self.assertFalse((self.root / "staged-ui/assets/ui/editor/imagegen.json").exists())
        self.assertFalse((self.root / "staged-ui/assets/ui/editor/v1").exists())
        self.assertFalse((self.root / "staged-ui/assets/production").exists())
        self.assertEqual((self.root / "staged-ui/assets/ui/other-controls.png").read_bytes(), b"runtime control pixels")

    def test_misplaced_raw_editor_source_image_cannot_enter_runtime_payload(self):
        self.write("assets/ui/editor/raw/generated-source.png", b"authoring pixels")
        with self.assertRaisesRegex(ValueError, "staged editor UI payload"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_missing_editor_ui_manifest_blocks_runtime_staging(self):
        (self.project / "assets/ui/editor/manifest.json").unlink()
        with self.assertRaisesRegex(ValueError, "Required runtime file is missing.*editor/manifest"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_missing_or_changed_runtime_ui_pixels_block_before_staging(self):
        path = self.project / "assets/ui/editor/people.png"
        original = path.read_bytes()
        for mutation in ("missing", "changed"):
            with self.subTest(mutation=mutation):
                if mutation == "missing":
                    path.unlink()
                else:
                    path.write_bytes(original + b"changed")
                with self.assertRaisesRegex(ValueError, "editor UI provenance|Editor UI pixels changed"):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())
                path.write_bytes(original)

    def test_missing_or_changed_imagegen_source_blocks_before_staging(self):
        path = self.root / "assets/ui/editor/v1/raw/people.png"
        original = path.read_bytes()
        for mutation in ("missing", "changed"):
            with self.subTest(mutation=mutation):
                if mutation == "missing":
                    path.unlink()
                else:
                    path.write_bytes(original + b"changed")
                with self.assertRaisesRegex(ValueError, "editor UI provenance|Editor UI source changed"):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())
                path.write_bytes(original)

    def test_changed_ui_manifest_or_catalog_reference_is_rejected(self):
        path = self.project / "assets/ui/editor/manifest.json"
        original = path.read_text()
        changes = [lambda m: m["assets"].pop("rotate"),
                   lambda m: m["assets"]["people"].update(sha256="0" * 64),
                   lambda m: m.update(reference="design/art-directions/other.png")]
        for change in changes:
            with self.subTest(change=change):
                manifest = json.loads(original)
                change(manifest)
                path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "Editor UI"):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())
                path.write_text(original)

    def test_changed_saved_imagegen_prompt_record_is_rejected(self):
        path = self.root / "assets/ui/editor/v1/imagegen.json"
        source = json.loads(path.read_text())
        source["assets"][0]["prompt"] = "Unrelated image"
        path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, "ImageGen prompt record changed"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_staged_ui_is_reverified_against_original_imagegen_sources(self):
        original_verify = build.editor_ui_contract.verify_editor_ui
        calls = []
        def verify(project, source_project=None):
            calls.append((project, source_project))
            if source_project is not None:
                path = project / "assets/ui/editor/people.png"
                path.write_bytes(path.read_bytes() + b"post-copy tamper")
            return original_verify(project, source_project)
        with patch.object(build.editor_ui_contract, "verify_editor_ui", side_effect=verify):
            with self.assertRaisesRegex(ValueError, "Editor UI pixels changed"):
                build.stage_runtime(self.project, self.root / "staged")
        self.assertEqual(calls, [(self.project, None), (self.root / "staged", self.project)])

    def test_build_refuses_staging_inside_source_project(self):
        with self.assertRaisesRegex(ValueError, "outside the source project"):
            build.stage_build(self.project, self.project / "nested-stage", self.branding)
        self.assertFalse((self.project / "nested-stage").exists())


class ApkBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sushi-apk-audit-test-")
        self.addCleanup(self.temporary.cleanup)
        self.apk = Path(self.temporary.name) / "game.apk"
        self.fingerprint = "ab" * 32
        self.branding = {"title": "Example", "android_package": "example.game", "version_code": 20, "version_name": "0.2.0",
                         "release_signer_sha256": self.fingerprint}
        self.badging = "package: name='example.game' versionCode='20' versionName='0.2.0'\napplication-label:'Example'\nsdkVersion:'24'\ntargetSdkVersion:'35'\n"
        self.signer = f"Signer #1 certificate SHA-256 digest: {self.fingerprint}\n"

    def archive(self, extra=None):
        with zipfile.ZipFile(self.apk, "w") as archive:
            for name, data in {"lib/arm64-v8a/libgodot_android.so": b"arm", "lib/x86_64/libgodot_android.so": b"x64",
                               "assets/assets/catalog/manifest.json": b'{}',
                               "assets/assets/recipe-variants/manifest.json": b'{}',
                               "assets/assets/chef-variants/manifest.json": b'{}',
                               "assets/assets/feedback-variants/manifest.json": b'{}',
                               "assets/assets/ui/editor/manifest.json": b'{}', **(extra or {})}.items():
                archive.writestr(name, data)

    def audit(self):
        with patch.object(build, "run", side_effect=lambda command, *_: self.signer if "apksigner" in command[0] else self.badging):
            return build.audit_apk(self.apk, self.branding, "release", Path("/sdk"), {}, "secret-test-password")

    def test_accepts_matching_offline_release_and_both_architectures(self):
        self.archive()
        self.assertEqual(self.audit()["signer_sha256"], self.fingerprint)

    def test_rejects_missing_ui_manifest_in_apk(self):
        self.archive()
        with zipfile.ZipFile(self.apk) as archive:
            entries = {name: archive.read(name) for name in archive.namelist() if name != "assets/assets/ui/editor/manifest.json"}
        with zipfile.ZipFile(self.apk, "w") as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        with self.assertRaisesRegex(ValueError, "ImageGen editor UI manifest is missing"):
            self.audit()

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

    def test_rejects_wrong_launcher_label_even_when_package_and_version_match(self):
        self.archive()
        self.badging = self.badging.replace("application-label:'Example'", "application-label:'Other demo'")
        with self.assertRaisesRegex(ValueError, "app label"):
            self.audit()


if __name__ == "__main__":
    unittest.main(verbosity=2)
