"""Exercise the narrow exception without weakening other catalog contracts."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from catalog_metadata_override import AFTER, BEFORE, RUN, sha, validate_override


class CatalogMetadataOverrideTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.bound = {}
        self.original = {'id': 'dock-cover', **BEFORE}
        self.project = 'a' * 64
        self.authority_path = 'inputs/root-height-reconciliation-v1.json'
        authority = RUN / 'objects/dock-cover' / self.authority_path
        target = self.folder / self.authority_path
        target.parent.mkdir(parents=True)
        target.write_bytes(authority.read_bytes())
        self.bound[target.resolve()] = sha(target)
        phases = [*range(1, 14), *[n + .5 for n in range(1, 13)]]
        self.measurements = {
            'asset': 'dock-cover', 'projectSHA256': self.project,
            'samples': [{'clip': clip, 'direction': direction, 'frame': frame,
                         'bounds': [[-1.49, -1.49, -.01], [1.49, 1.49, 2.187]]}
                        for clip in ['covered', 'uncover'] for direction in 'NESW' for frame in phases]}
        self.receipt = {
            'asset': 'dock-cover', 'before': dict(BEFORE), 'after': dict(AFTER),
            'authority': {'path': self.authority_path, 'sha256': sha(target)}}
        self.delivery = {}
        self.review = {'verdict': 'approve', 'blockers': [], 'independentReview': True}
        self.refresh()

    def save(self, name, value):
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        self.bound[path.resolve()] = sha(path)
        return {'path': name, 'sha256': sha(path)}

    def refresh(self):
        self.receipt['measurements'] = self.save('candidates/final/envelope.json', self.measurements)
        descriptor = self.save('candidates/final/catalog-metadata-override.json', self.receipt)
        self.delivery['catalogMetadataOverride'] = descriptor
        self.review['catalogMetadataOverride'] = {
            'receiptSHA256': descriptor['sha256'], 'approved': True, 'fields': dict(AFTER)}

    def validate(self):
        return validate_override(self.folder, self.original, self.delivery,
                                 self.bound, self.project, self.review)

    def test_accepts_exact_bound_reviewed_cover_evidence(self):
        result = self.validate()
        self.assertEqual(result['fields'], AFTER)
        self.assertEqual(result['nativeSamples'], 200)

    def test_absent_override_preserves_ordinary_objects(self):
        self.assertIsNone(validate_override(self.folder, {'id': 'crate'}, {}, {}, '', {}))

    def test_rejects_other_object_and_changed_historical_fields(self):
        for changes in [{'id': 'crate'}, {'height': 1.9}, {'renderPass': 'overhead'}]:
            with self.subTest(changes=changes):
                self.original = {'id': 'dock-cover', **BEFORE, **changes}
                with self.assertRaises(ValueError):
                    self.validate()

    def test_rejects_additional_metadata_changes(self):
        self.receipt['after']['footprint'] = [4, 4]
        self.refresh()
        with self.assertRaises(ValueError):
            self.validate()

    def test_rejects_stale_source_measurement(self):
        self.measurements['projectSHA256'] = 'b' * 64
        self.refresh()
        with self.assertRaises(ValueError):
            self.validate()

    def test_requires_key_half_frame_and_terminal_coverage(self):
        baseline = copy.deepcopy(self.measurements)
        for frame in [1, 4.5, 12.5, 13]:
            with self.subTest(frame=frame):
                self.measurements = copy.deepcopy(baseline)
                self.measurements['samples'] = [s for s in self.measurements['samples']
                                               if (s['clip'], s['direction'], s['frame']) != ('covered', 'N', frame)]
                self.refresh()
                with self.assertRaises(ValueError):
                    self.validate()

    def test_rejects_outside_or_nonfinite_native_envelope(self):
        for value in [2.21, float('nan')]:
            with self.subTest(value=value):
                self.measurements['samples'][0]['bounds'][1][2] = value
                self.refresh()
                with self.assertRaises(ValueError):
                    self.validate()

    def test_rejects_changed_authority_or_unbound_receipt(self):
        self.receipt['authority']['sha256'] = 'b' * 64
        self.refresh()
        with self.assertRaises(ValueError):
            self.validate()
        self.receipt['authority']['sha256'] = sha(self.folder / self.authority_path)
        self.refresh()
        del self.bound[(self.folder / self.delivery['catalogMetadataOverride']['path']).resolve()]
        with self.assertRaises(ValueError):
            self.validate()

    def test_requires_explicit_judge_approval_of_exact_receipt(self):
        self.review.pop('catalogMetadataOverride')
        with self.assertRaises(ValueError):
            self.validate()


if __name__ == '__main__':
    unittest.main()
