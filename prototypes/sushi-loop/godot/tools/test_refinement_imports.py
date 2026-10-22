"""Integration regressions for approved-byte imports, in isolated temp projects.

Run with Pillow available. Source assets and the working game's art stay intact.
"""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from pack_refined_goods import pack
from sync_refined_feedback import sync
from verify_editor_goods import verify_editor_goods
from verify_feedback_variants import verify_feedback_variants

PROTOTYPE = Path(__file__).resolve().parents[2]
SOURCE = PROTOTYPE / 'godot'


class RefinementImports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='sushi-refinement-import-tests-')
        cls.project = Path(cls.temp.name)
        cls.goods = cls.project / 'assets/ui/editor-goods'
        pack(PROTOTYPE, cls.goods)
        cls.feedback = cls.project / 'assets/feedback-variants'
        sync(PROTOTYPE, cls.feedback)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def mutate_manifest(self, directory, verifier, change):
        path = directory / 'manifest.json'
        original = path.read_bytes()
        manifest = json.loads(original)
        change(manifest)
        try:
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                verifier(self.project, SOURCE)
        finally:
            path.write_bytes(original)

    def test_exact_approved_payloads(self):
        self.assertEqual(verify_editor_goods(self.project, SOURCE)['approved_native_captures'], 5)
        self.assertEqual(verify_feedback_variants(self.project, SOURCE)['frames'], 48)

    def test_goods_reject_registration_and_approval_changes(self):
        def shift(manifest):
            manifest['sprites']['plant-angular']['region'][0] += 1

        def wrong_review(manifest):
            manifest['provenance']['approvals']['crate-wood']['reviewSHA256'] = '0' * 64

        for change in (shift, wrong_review):
            self.mutate_manifest(self.goods, verify_editor_goods, change)

    def test_goods_reject_changed_floor_and_gutters_even_with_new_atlas_hash(self):
        from PIL import Image
        atlas, metadata = self.goods / 'atlas.png', self.goods / 'manifest.json'
        original_atlas, original_metadata = atlas.read_bytes(), metadata.read_bytes()
        for coordinate in ((950, 560), (0, 0)):
            with self.subTest(coordinate=coordinate):
                try:
                    image = Image.open(atlas).convert('RGBA')
                    image.putpixel(coordinate, (200, 0, 0, 255))
                    image.save(atlas)
                    manifest = json.loads(original_metadata)
                    manifest.update(atlas_sha256=hashlib.sha256(atlas.read_bytes()).hexdigest(),
                                    atlas_bytes=atlas.stat().st_size)
                    metadata.write_text(json.dumps(manifest))
                    with self.assertRaises(ValueError):
                        verify_editor_goods(self.project, SOURCE)
                finally:
                    atlas.write_bytes(original_atlas)
                    metadata.write_bytes(original_metadata)

    def test_smile_reject_registration_freshness_and_approval_changes(self):
        def shift(manifest):
            manifest['objects']['bubble-happy']['root'][1] += 1

        def stale(manifest):
            manifest['baseLibrarySha256'] = '0' * 64

        def wrong_review(manifest):
            manifest['refinement']['reviewSHA256'] = '0' * 64

        for change in (shift, stale, wrong_review):
            self.mutate_manifest(self.feedback, verify_feedback_variants, change)

    def test_smile_reject_changed_atlas(self):
        atlas = next((self.feedback / 'sprites').rglob('*.png'))
        original = atlas.read_bytes()
        try:
            atlas.write_bytes(original[:-1] + bytes([original[-1] ^ 1]))
            with self.assertRaises(ValueError):
                verify_feedback_variants(self.project, SOURCE)
        finally:
            atlas.write_bytes(original)

    def test_legacy_formats_remain_supported(self):
        self.assertEqual(verify_editor_goods(SOURCE, SOURCE)['sprites'], 6)
        # Catalog rollout intentionally leaves the current runtime overlay on
        # its previous library. Refresh only that field in a temporary fixture
        # to exercise the original legacy source/pixel checks without cutover.
        with tempfile.TemporaryDirectory(prefix='sushi-legacy-feedback-') as directory:
            project = Path(directory)
            runtime = project / 'assets/feedback-variants'
            shutil.copytree(SOURCE / 'assets/feedback-variants', runtime)
            metadata = runtime / 'manifest.json'
            manifest = json.loads(metadata.read_text())
            manifest['baseLibrarySha256'] = hashlib.sha256(
                (PROTOTYPE / 'assets/production/library.json').read_bytes()).hexdigest()
            metadata.write_text(json.dumps(manifest))
            self.assertEqual(verify_feedback_variants(project, SOURCE)['frames'], 48)


if __name__ == '__main__':
    unittest.main()
