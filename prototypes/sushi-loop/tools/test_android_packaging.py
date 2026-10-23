#!/usr/bin/env python3
"""Fast packaging-boundary tests; no SDK, imports or installed saves are touched."""
import json
import hashlib
from pathlib import Path
import shutil
import struct
import zlib
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build_android as build


def make_goods_fixture(root):
    """Independent native-receipt fixture for pixel and packaging boundaries."""
    source = root / build.editor_goods_contract.SOURCE_ROOT
    runtime = root / 'godot/assets/ui/editor-goods'
    runtime.mkdir(parents=True, exist_ok=True)
    source.mkdir(parents=True, exist_ok=True)
    production = root / build.editor_goods_contract.PRODUCTION_BLEND
    production.parent.mkdir(parents=True, exist_ok=True)
    production.write_bytes(b'editable production Blender fixture')
    for relative, data in [('source/editor-goods.blend', b'editable native capture fixture'),
                           ('source/capture_goods.py', b'# native Blender capture fixture\n'),
                           ('source/pack_goods.py', b'# unchanged pixel packing fixture\n')]:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    camera = {'id': 'editor-goods-three-quarter-v1', 'projection': 'ordinary-orthographic-three-quarter',
              'elevation_degrees': 35, 'azimuth_degrees': 35, 'pixel_aspect': [1, 1]}
    provenance = {'source_root': build.editor_goods_contract.SOURCE_ROOT,
                  'method': build.editor_goods_contract.METHOD,
                  'production_blend': build.editor_goods_contract.PRODUCTION_BLEND,
                  'production_blend_sha256': build.sha(production),
                  'blend': 'source/editor-goods.blend', 'recipe': 'source/capture_goods.py',
                  'packing_recipe': 'source/pack_goods.py',
                  'records': 'records/captures.json'}
    for field in ('blend', 'recipe', 'packing_recipe'):
        provenance[f'{field}_sha256'] = build.sha(source / provenance[field])
    dimensions = [1176, 784]
    atlas = bytearray(dimensions[0] * dimensions[1] * 4)
    sprites, captures = {}, {}
    for index, identity in enumerate(sorted(build.editor_goods_contract.SPRITES)):
        frame = bytearray(384 * 384 * 4)
        for y in range(10, 374):
            for x in range(10, 374):
                offset = (y * 384 + x) * 4
                frame[offset:offset + 4] = bytes([index * 30 + 20, 90, 130, 255])
        relative = f'renders/{identity}.png'
        render = source / relative
        render.parent.mkdir(parents=True, exist_ok=True)
        render.write_bytes(RuntimeBoundaryTests.rgba_png([384, 384], frame))
        x, y = index % 3 * 392 + 4, index // 3 * 392 + 4
        for row in range(384):
            start = ((y + row) * dimensions[0] + x) * 4
            atlas[start:start + 384 * 4] = frame[row * 384 * 4:(row + 1) * 384 * 4]
        geometry = hashlib.sha256(identity.encode()).hexdigest()
        sprite = {'region': [x, y, 384, 384], 'source_render': relative, 'source_sha256': build.sha(render),
                  'camera_id': camera['id'], 'source_collection': f'ASSET_{identity}',
                  'geometry_sha256': geometry, 'alpha_bounds': [10, 10, 374, 374],
                  'native_collection': f'CAPTURE_{identity}', 'camera': camera | {'resolution': [384, 384]}}
        capture = {'art_id': identity, 'source_collection': sprite['source_collection'],
                   'native_objects': [identity], 'geometry_origin': 'production mesh copy',
                   'geometry_sha256': geometry, 'source_production_sha256': provenance['production_blend_sha256'],
                   'camera': camera | {'resolution': [384, 384]}, 'source_render': relative,
                   'source_sha256': sprite['source_sha256'], 'native_collection': sprite['native_collection']}
        if identity == 'floor-cream':
            sprite['floor_thickness'] = capture['floor_thickness'] = 0.06
        sprites[identity], captures[identity] = sprite, capture
    records = {key: value for key, value in provenance.items() if key in
               {'method', 'production_blend', 'production_blend_sha256', 'blend', 'blend_sha256', 'recipe', 'recipe_sha256'}}
    records.update(schema_version=1, main_file_preserved=True, original_scene_restored=True, sprites=captures)
    receipt = source / provenance['records']
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(records))
    provenance['records_sha256'] = build.sha(receipt)
    image = runtime / 'atlas.png'
    image.write_bytes(RuntimeBoundaryTests.rgba_png(dimensions, atlas))
    manifest = {'schema_version': 1, 'atlas': 'atlas.png', 'atlas_size': dimensions,
                'padding': 4, 'native_render_size': [384, 384],
                'atlas_sha256': build.sha(image), 'atlas_bytes': image.stat().st_size,
                'camera': camera, 'provenance': provenance, 'sprites': sprites}
    (runtime / 'manifest.json').write_text(json.dumps(manifest))
    return manifest


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sushi-android-packaging-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "godot"
        production_pin = patch.object(build.editor_goods_contract, 'PRODUCTION_BLEND_SHA256', hashlib.sha256(b'editable production Blender fixture').hexdigest())
        production_pin.start()
        self.addCleanup(production_pin.stop)
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
        # Exercise the actual coordinated B atlas, complete ImageGen sheets,
        # accepted composition and references; no UI verifier mocks hide drift.
        shutil.copytree(build.PROJECT / "assets/ui/editor", self.project / "assets/ui/editor")
        shutil.copytree(build.PROJECT / "assets/ui/wood-editor", self.project / "assets/ui/wood-editor")
        wood_source = build.PROJECT.parent / "assets/ui/editor/html-export-v1"
        shutil.copytree(wood_source, self.root / "assets/ui/editor/html-export-v1")
        wood_manifest = json.loads((wood_source / "manifest.json").read_text())
        for relative in wood_manifest["source"]["files"]:
            local = relative.removeprefix("prototypes/sushi-loop/")
            fixture = self.root / local
            fixture.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(build.PROJECT.parent / local, fixture)
        ui_source = Path(build.editor_ui_contract.SOURCE_RECORD).parent
        shutil.copytree(build.PROJECT.parent / ui_source, self.root / ui_source)
        # The current calibration reuses immutable v6 pixels and full-screen
        # provenance; copying the parent keeps this fixture independent of the
        # working checkout during subsequent tamper cases.
        parent_source = Path(build.editor_ui_contract.PARENT_SOURCE_RECORD).parent
        shutil.copytree(build.PROJECT.parent / parent_source, self.root / parent_source)
        historical = Path(build.editor_ui_contract.HISTORICAL_SOURCE_RECORD)
        historical_record = json.loads((build.PROJECT.parent / historical).read_text())
        historical_path = self.root / historical
        historical_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(build.PROJECT.parent / historical, historical_path)
        original_floor = Path(historical_record['entries']['floor']['source'])
        (self.root / original_floor).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(build.PROJECT.parent / original_floor, self.root / original_floor)
        generation = json.loads((self.root / build.editor_ui_contract.SOURCE_RECORD).read_text())
        for record in generation["references"]:
            reference = self.root / record["path"]
            reference.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(build.PROJECT.parent / record["path"], reference)
        make_goods_fixture(self.root)
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

    def test_wood_runtime_tampering_blocks_staging(self):
        (self.project / "assets/ui/wood-editor/shop-normal.png").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "pixels differ"):
            build.validate_catalog(self.project, build.runtime_sources(self.project))

    def test_wood_stale_css_blocks_staging(self):
        css = self.root / "design/editor-dock-preview/shared.css"
        css.write_text(css.read_text() + "/* changed */")
        with self.assertRaisesRegex(ValueError, "fresh HTML export"):
            build.validate_catalog(self.project, build.runtime_sources(self.project))

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
        self.assertEqual(len(selected), 48)
        self.assertEqual(catalog["editor_ui"]["images"], 1)
        source_record = json.loads((self.root / build.editor_ui_contract.SOURCE_RECORD).read_text())
        self.assertEqual(catalog["editor_ui"]["imagegen_sources"], len(source_record['generations']))
        self.assertEqual((catalog["editor_ui"]["styles"], catalog["editor_ui"]["icons"]), (19, 16))
        self.assertEqual(selected["assets/ui/editor/manifest.json"], catalog["editor_ui_manifest_sha256"])
        self.assertEqual({name for name in selected if name.startswith("assets/ui/editor/")},
                         {"assets/ui/editor/manifest.json", "assets/ui/editor/skin.png"})
        self.assertEqual(catalog['editor_goods']['sprites'], 6)
        self.assertEqual({name for name in selected if name.startswith('assets/ui/editor-goods/')},
                         {'assets/ui/editor-goods/manifest.json', 'assets/ui/editor-goods/atlas.png'})
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
        self.assertFalse((self.root / "staged-ui/assets/ui/editor/v5").exists())
        self.assertFalse((self.root / 'staged-ui/assets/ui/editor/v6').exists())
        self.assertFalse((self.root / 'staged-ui/assets/ui/editor/v7').exists())
        self.assertFalse((self.root / 'staged-ui/assets/ui/editor/v8').exists())
        self.assertFalse((self.root / 'staged-ui/assets/ui/editor/goods-v1').exists())
        self.assertFalse((self.root / "staged-ui/assets/production").exists())
        self.assertEqual((self.root / "staged-ui/assets/ui/other-controls.png").read_bytes(), b"runtime control pixels")

    def test_misplaced_raw_editor_source_image_cannot_enter_runtime_payload(self):
        self.write("assets/ui/editor/raw/generated-source.png", b"authoring pixels")
        with self.assertRaisesRegex(ValueError, "staged editor UI payload|Unexpected editor UI image payload"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_missing_editor_ui_manifest_blocks_runtime_staging(self):
        (self.project / "assets/ui/editor/manifest.json").unlink()
        with self.assertRaisesRegex(ValueError, "Required runtime file is missing.*editor/manifest"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_missing_or_changed_runtime_ui_pixels_block_before_staging(self):
        path = self.project / "assets/ui/editor/skin.png"
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
        record = json.loads((self.root / build.editor_ui_contract.SOURCE_RECORD).read_text())
        path = (self.root / build.editor_ui_contract.SOURCE_RECORD).parent / record["generations"][0]["raw"]
        original = path.read_bytes()
        for mutation in ("missing", "changed"):
            with self.subTest(mutation=mutation):
                if mutation == "missing":
                    path.unlink()
                else:
                    path.write_bytes(original + b"changed")
                with self.assertRaisesRegex(ValueError, "editor UI provenance|Editor UI source changed|Editor UI reference changed"):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())
                path.write_bytes(original)

    def test_changed_ui_manifest_or_catalog_reference_is_rejected(self):
        path = self.project / "assets/ui/editor/manifest.json"
        original = path.read_text()
        changes = [lambda m: m["icons"].pop("rotate"),
                   lambda m: m.update(atlas_sha256="0" * 64),
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
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        source = json.loads(path.read_text())
        source["generations"][0]["prompt"] = "Unrelated image"
        path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, "ImageGen prompt record changed"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def mutate_ui_manifest(self, mutate):
        path = self.project / "assets/ui/editor/manifest.json"
        manifest = json.loads(path.read_text())
        mutate(manifest)
        path.write_text(json.dumps(manifest))

    def test_passive_surfaces_cannot_be_omitted_from_the_coordinated_family(self):
        path = self.project / "assets/ui/editor/manifest.json"
        original = path.read_text()
        for identity in ("container-tray", "container-modal", "slot-paper", "toast-error", 'noren-rod', 'noren-dock'):
            with self.subTest(surface=identity):
                self.mutate_ui_manifest(lambda m: m["styles"].pop(identity))
                with self.assertRaisesRegex(ValueError, "active/passive surface"):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())
                path.write_text(original)

    def test_ui_source_slices_edges_and_content_cannot_drift(self):
        path = self.project / "assets/ui/editor/manifest.json"
        original = path.read_text()
        changes = [
            (lambda e: e["slice_px"].__setitem__(2, e["slice_px"][2] + 1), "asymmetric source slices"),
            (lambda e: e["edge"].__setitem__(2, e["edge"][2] + 1), "asymmetric logical edges"),
            (lambda e: e["content"].__setitem__(2, e["content"][2] + 1), "asymmetric content margins"),
            (lambda e: e.update(slice_px=[e["region"][2]] * 4), "no plain stretch spans"),
            (lambda e: e.update(content=[-1, -1, -1, -1]), "Invalid editor UI content margins"),
            (lambda e: e.update(stretch=""), "stretch span documentation"),
            (lambda e: e.update(states={"pressed": {"region": [0, 0, 1, 1]}}), "bypasses calibrated framing"),
            (lambda e: e.update(states={"disabled": {"tint": "invalid"}}), "Invalid editor UI state treatment"),
        ]
        for change, message in changes:
            with self.subTest(failure=message):
                self.mutate_ui_manifest(lambda m: change(m["styles"]["control-wood"]))
                with self.assertRaisesRegex(ValueError, message):
                    build.stage_runtime(self.project, self.root / "staged")
                self.assertFalse((self.root / "staged/project.godot").exists())
                path.write_text(original)

    def test_accepted_b_composition_is_required_not_an_unselected_concept(self):
        path = self.root / build.editor_ui_contract.COMPOSITION
        path.write_bytes(path.read_bytes() + b"changed concept")
        with self.assertRaisesRegex(ValueError, "accepted B composition changed"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_pill_minimum_height_cannot_be_missing_or_under_100(self):
        path = self.project / 'assets/ui/editor/manifest.json'
        original = path.read_text()
        for identity in sorted(build.editor_ui_contract.PILL_STYLES):
            for value in (None, 99):
                with self.subTest(style=identity, minimum_height=value):
                    def change(manifest):
                        if value is None:
                            manifest['styles'][identity].pop('minimum_height', None)
                        else:
                            manifest['styles'][identity]['minimum_height'] = value
                    self.mutate_ui_manifest(change)
                    with self.assertRaisesRegex(ValueError, 'minimum height is missing or invalid|pill minimum height is below 100'):
                        build.stage_runtime(self.project, self.root / 'staged')
                    self.assertFalse((self.root / 'staged/project.godot').exists())
                    path.write_text(original)

    def test_pill_minimum_height_cannot_undershoot_the_uniform_source_height(self):
        # All four corner ratios still agree; the declared minimum must also
        # keep the complete source silhouette tall enough at that scale.
        self.mutate_ui_manifest(lambda m: m['styles']['coin-panel'].update(edge=[100, 100, 100, 100]))
        with self.assertRaisesRegex(ValueError, 'minimum height is below its uniformly scaled source height'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_pill_minimum_height_must_match_its_saved_source_calibration(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        record['entries']['coin-panel']['minimum_height'] = 101
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, 'minimum height differs from its packing record'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_source_region_pixel_proof_survives_updated_record_hash(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        # A hash-only verifier would accept this updated record hash. The crop
        # must still exactly explain the immutable source pixels in the atlas.
        record["entries"]["people"]["source_region"][0] += 1
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, "atlas pixels differ from the ImageGen source crop|source region.*outside"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_old_v5_ui_cannot_replace_the_current_amendment(self):
        self.mutate_ui_manifest(lambda m: m.update(version=2, source_record=build.editor_ui_contract.HISTORICAL_SOURCE_RECORD))
        with self.assertRaisesRegex(ValueError, 'manifest version 4'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_inherited_source_cannot_claim_a_new_prompt_after_record_rehash(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        inherited = next(item for item in record['generations'] if 'inherits' in item)
        inherited['prompt'] += '\nUnrecorded change.'
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, 'inherited v6 generation provenance changed'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_current_source_requires_the_latest_complete_composition(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        current = next((item for item in record['generations'] if 'inherits' not in item), record['generations'][0])
        latest = record['latest_composition']['path']
        current['reference_paths'].remove(latest)
        del current['reference_sha256'][latest]
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, 'does not use the latest B amendment composition|inherited v6 generation provenance changed'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_complete_composition_requires_its_saved_generation_prompt(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        record['composition_generation']['prompt'] = 'Unrecorded composition'
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, 'complete-screen generation provenance is missing'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_inherited_parent_record_cannot_be_rewritten(self):
        path = self.root / build.editor_ui_contract.PARENT_SOURCE_RECORD
        parent = json.loads(path.read_text())
        parent['generations'][0]['prompt'] += '\nUnreviewed source mutation.'
        path.write_text(json.dumps(parent))
        with self.assertRaisesRegex(ValueError, 'historical v6 parent record changed'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_inherited_composition_cannot_claim_new_provenance(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        record['composition_generation']['prompt'] += '\nUnreviewed composition mutation.'
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, 'inherited complete-screen provenance changed'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_inherited_sheet_parent_pin_cannot_be_replaced(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        record['generations'][0]['inherits']['source_record_sha256'] = '0' * 64
        path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(path)))
        with self.assertRaisesRegex(ValueError, 'inherited sheet identity changed'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_visible_face_and_icon_ink_bounds_must_fit_their_regions(self):
        path = self.project / 'assets/ui/editor/manifest.json'
        original = path.read_text()
        for group, identity, field in [('styles', 'coin-panel', 'face_px'), ('icons', 'play', 'ink_px')]:
            for bounds in (None, [-1, 0, 10, 10], [0, 0, 0, 10], [0, 0, 99999, 10], [0, 0, 1.5, 10]):
                with self.subTest(identity=identity, bounds=bounds):
                    def change(manifest):
                        if bounds is None:
                            manifest[group][identity].pop(field, None)
                        else:
                            manifest[group][identity][field] = bounds
                    self.mutate_ui_manifest(change)
                    with self.assertRaisesRegex(ValueError, 'visible face bounds|icon ink bounds|Invalid editor UI provenance'):
                        build.stage_runtime(self.project, self.root / 'staged')
                    self.assertFalse((self.root / 'staged/project.godot').exists())
                    path.write_text(original)

    def test_face_and_ink_bounds_must_match_the_saved_registration(self):
        path = self.project / 'assets/ui/editor/manifest.json'
        original = path.read_text()
        for group, identity, field in [('styles', 'coin-panel', 'face_px'), ('icons', 'play', 'ink_px')]:
            with self.subTest(identity=identity):
                self.mutate_ui_manifest(lambda m: m[group][identity][field].__setitem__(0, m[group][identity][field][0] + 1))
                with self.assertRaisesRegex(ValueError, 'bounds differ from its packing record|bounds.*outside its sheet'):
                    build.stage_runtime(self.project, self.root / 'staged')
                self.assertFalse((self.root / 'staged/project.godot').exists())
                path.write_text(original)

    def test_restored_curtains_must_use_their_exact_v6_source_crops(self):
        manifest_path = self.project / 'assets/ui/editor/manifest.json'
        source_path = self.root / build.editor_ui_contract.SOURCE_RECORD
        original_manifest, original_record = manifest_path.read_text(), source_path.read_text()
        for identity in ('tab-idle', 'tab-active'):
            for mutation in ('offset', 'alternate valid curtain'):
                with self.subTest(identity=identity, mutation=mutation):
                    record = json.loads(original_record)
                    manifest = json.loads(original_manifest)
                    if mutation == 'offset':
                        record['entries'][identity]['source_region'][0] += 1
                    else:
                        other = 'tab-active' if identity == 'tab-idle' else 'tab-idle'
                        record['entries'][identity] = dict(record['entries'][other])
                        manifest['styles'][identity] = dict(manifest['styles'][other])
                    source_path.write_text(json.dumps(record))
                    manifest['source_record_sha256'] = build.sha(source_path)
                    manifest_path.write_text(json.dumps(manifest))
                    with self.assertRaisesRegex(ValueError, 'restored curtain must retain its exact v6 source crop and generation'):
                        build.stage_runtime(self.project, self.root / 'staged')
                    manifest_path.write_text(original_manifest)
                    source_path.write_text(original_record)

    def test_restored_curtains_cannot_claim_new_generation_provenance(self):
        source_path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(source_path.read_text())
        del record['generations'][0]['inherits']
        source_path.write_text(json.dumps(record))
        self.mutate_ui_manifest(lambda m: m.update(source_record_sha256=build.sha(source_path)))
        with self.assertRaisesRegex(ValueError, 'curtain restoration requires unchanged v6 sheets without new generated artwork'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_approved_floor_icon_cannot_be_replaced_by_another_valid_crop(self):
        path = self.root / build.editor_ui_contract.SOURCE_RECORD
        record = json.loads(path.read_text())
        # Reusing another valid source crop and atlas rectangle can pass crop
        # equality; the independent v5 Floor proof must still reject it.
        record['entries']['floor'] = dict(record['entries']['people'])
        path.write_text(json.dumps(record))
        def replace_floor(manifest):
            manifest['icons']['floor'] = dict(manifest['icons']['people'])
            manifest['source_record_sha256'] = build.sha(path)
        self.mutate_ui_manifest(replace_floor)
        with self.assertRaisesRegex(ValueError, 'approved Floor icon pixels changed'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    @staticmethod
    def rgba_png(dimensions, pixels):
        width, height = dimensions
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
        rows = b"".join(b"\0" + pixels[row * width * 4:(row + 1) * width * 4] for row in range(height))
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(rows, 1)) + chunk(b"IEND", b""))

    def test_repainting_atlas_is_rejected_even_with_matching_payload_hash(self):
        manifest = json.loads((self.project / "assets/ui/editor/manifest.json").read_text())
        path = self.project / "assets/ui/editor/skin.png"
        dimensions, original = build.editor_ui_contract._decode_png(path.read_bytes())
        pixels = bytearray(original)
        x, y, _, _ = manifest["icons"]["people"]["region"]
        pixels[((y + 4) * dimensions[0] + x + 4) * 4] ^= 1
        path.write_bytes(self.rgba_png(dimensions, pixels))
        self.mutate_ui_manifest(lambda m: m.update(atlas_sha256=build.sha(path), atlas_bytes=path.stat().st_size))
        with self.assertRaisesRegex(ValueError, "atlas pixels differ from the ImageGen source crop"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_changed_authored_ui_calibration_or_states_block_staging(self):
        path = (self.root / build.editor_ui_contract.SOURCE_RECORD).parent / 'authoring.json'
        authoring = json.loads(path.read_text())
        authoring["assets"][0]["content"][0] += 1
        path.write_text(json.dumps(authoring))
        with self.assertRaisesRegex(ValueError, "authored calibration and states changed"):
            build.stage_runtime(self.project, self.root / "staged")
        self.assertFalse((self.root / "staged/project.godot").exists())

    def test_staged_ui_is_reverified_against_original_imagegen_sources(self):
        original_verify = build.editor_ui_contract.verify_editor_ui
        calls = []
        def verify(project, source_project=None):
            calls.append((project, source_project))
            if source_project is not None:
                path = project / "assets/ui/editor/skin.png"
                path.write_bytes(path.read_bytes() + b"post-copy tamper")
            return original_verify(project, source_project)
        with patch.object(build.editor_ui_contract, "verify_editor_ui", side_effect=verify):
            with self.assertRaisesRegex(ValueError, "Editor UI pixels changed"):
                build.stage_runtime(self.project, self.root / "staged")
        self.assertEqual(calls, [(self.project, None), (self.root / "staged", self.project)])

    def test_staged_goods_are_reverified_against_native_blender_renders(self):
        original_verify = build.editor_goods_contract.verify_editor_goods
        calls = []
        def verify(project, source_project=None):
            calls.append((project, source_project))
            if source_project is not None:
                path = project / 'assets/ui/editor-goods/atlas.png'
                path.write_bytes(path.read_bytes() + b'post-copy tamper')
            return original_verify(project, source_project)
        with patch.object(build.editor_goods_contract, 'verify_editor_goods', side_effect=verify):
            with self.assertRaisesRegex(ValueError, 'Editor goods atlas pixels changed'):
                build.stage_runtime(self.project, self.root / 'staged')
        self.assertEqual(calls, [(self.project, None), (self.root / 'staged', self.project)])

    def test_missing_goods_manifest_blocks_runtime_staging(self):
        (self.project / 'assets/ui/editor-goods/manifest.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Required runtime file is missing.*editor-goods/manifest'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_unregistered_raw_goods_render_cannot_enter_the_runtime(self):
        self.write('assets/ui/editor-goods/raw/source-render.png', b'authoring output')
        with self.assertRaisesRegex(ValueError, 'Unexpected editor goods image payload'):
            build.stage_runtime(self.project, self.root / 'staged')
        self.assertFalse((self.root / 'staged/project.godot').exists())

    def test_build_refuses_staging_inside_source_project(self):
        with self.assertRaisesRegex(ValueError, "outside the source project"):
            build.stage_build(self.project, self.project / "nested-stage", self.branding)
        self.assertFalse((self.project / "nested-stage").exists())


class EditorGoodsBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='sushi-editor-goods-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / 'godot'
        production_pin = patch.object(build.editor_goods_contract, 'PRODUCTION_BLEND_SHA256', hashlib.sha256(b'editable production Blender fixture').hexdigest())
        production_pin.start()
        self.addCleanup(production_pin.stop)
        self.manifest = make_goods_fixture(self.root)
        self.manifest_path = self.project / 'assets/ui/editor-goods/manifest.json'

    def save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest))

    def test_accepts_complete_native_receipts_and_exact_render_pixels(self):
        self.assertEqual(build.editor_goods_contract.verify_editor_goods(self.project)['sprites'], 6)

    def test_repainted_goods_atlas_cannot_pass_with_an_updated_payload_hash(self):
        path = self.project / 'assets/ui/editor-goods/atlas.png'
        dimensions, pixels = build.editor_ui_contract._decode_png(path.read_bytes())
        pixels = bytearray(pixels)
        x, y, _, _ = self.manifest['sprites']['floor-cream']['region']
        pixels[((y + 20) * dimensions[0] + x + 20) * 4] ^= 1
        path.write_bytes(RuntimeBoundaryTests.rgba_png(dimensions, pixels))
        self.manifest.update(atlas_sha256=build.sha(path), atlas_bytes=path.stat().st_size)
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'atlas pixels differ from the native Blender render'):
            build.editor_goods_contract.verify_editor_goods(self.project)

    def test_goods_resizing_is_rejected(self):
        self.manifest['sprites']['floor-cream']['region'][2] -= 1
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'native render was rescaled'):
            build.editor_goods_contract.verify_editor_goods(self.project)

    def test_floor_requires_recorded_native_thickness(self):
        self.manifest['sprites']['floor-cream']['floor_thickness'] = 0
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'no physical thickness'):
            build.editor_goods_contract.verify_editor_goods(self.project)

    def test_capture_geometry_drift_is_rejected_after_receipt_hash_update(self):
        path = self.root / build.editor_goods_contract.SOURCE_ROOT / self.manifest['provenance']['records']
        record = json.loads(path.read_text())
        record['sprites']['floor-cream']['geometry_sha256'] = '0' * 64
        path.write_text(json.dumps(record))
        self.manifest['provenance']['records_sha256'] = build.sha(path)
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'geometry registration changed'):
            build.editor_goods_contract.verify_editor_goods(self.project)

    def test_native_scene_source_cannot_change_silently(self):
        source = self.root / build.editor_goods_contract.SOURCE_ROOT
        (source / self.manifest['provenance']['blend']).write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError, 'blend source hash changed'):
            build.editor_goods_contract.verify_editor_goods(self.project)

    def test_world_source_cannot_be_replaced_by_updating_the_goods_hash(self):
        path = self.root / build.editor_goods_contract.PRODUCTION_BLEND
        path.write_bytes(b'changed production geometry')
        self.manifest['provenance']['production_blend_sha256'] = build.sha(path)
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, 'production Blender source hash changed'):
            build.editor_goods_contract.verify_editor_goods(self.project)


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
                               "assets/assets/ui/editor-goods/manifest.json": b'{}',
                               "assets/assets/ui/editor/manifest.json": b'{}',
                               "assets/assets/ui/wood-editor/manifest.json": b'{}', **(extra or {})}.items():
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

    def test_rejects_missing_native_goods_manifest_in_apk(self):
        self.archive()
        with zipfile.ZipFile(self.apk) as archive:
            entries = {name: archive.read(name) for name in archive.namelist() if name != 'assets/assets/ui/editor-goods/manifest.json'}
        with zipfile.ZipFile(self.apk, 'w') as archive:
            for name, data in entries.items():
                archive.writestr(name, data)
        with self.assertRaisesRegex(ValueError, 'Blender editor goods manifest is missing'):
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
