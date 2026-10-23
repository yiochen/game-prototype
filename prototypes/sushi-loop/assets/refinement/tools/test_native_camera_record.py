"""Reject camera metadata that disagrees with approved native registration."""
import copy
import unittest

from native_camera_record import normalize_measured


class NativeCameraRecordTest(unittest.TestCase):
    def setUp(self):
        self.camera = {'matrix': [[1, 0, 0, 0], [0, 1, 0, -8],
                                  [0, 0, 1, 5], [0, 0, 0, 1]],
                       'orthoScale': 1.5, 'shift': [0, .458331],
                       'rootPx': [192, 495.999755859375],
                       'nativeFrame': [384, 640], 'fps': 12}
        self.asset = {'id': 'actor', 'projection': 'character-orthographic',
                      'frame': [192, 320], 'anchor': [96, 248], 'scale': 2}
        self.catalog = {'id': 'actor', 'frameSize': [192, 320],
                        'root': [96, 248], 'sourceScale': 2}

    def translate(self, validation=None):
        return normalize_measured(self.camera, self.asset, self.catalog,
            validation or {'allChecksPassed': True, 'camera': copy.deepcopy(self.camera)})

    def test_native_fields_are_retained_without_reusing_stale_scale4_camera(self):
        normalized = self.translate()
        self.assertEqual(normalized['captureScale'], 2)
        self.assertEqual(normalized['nativeMeasurement'], self.camera)
        self.assertEqual(normalized['camera']['worldMatrix'], self.camera['matrix'])

    def test_camera_not_matching_native_validation_is_rejected(self):
        validation = {'allChecksPassed': True, 'camera': copy.deepcopy(self.camera)}
        self.camera['shift'][0] = .01
        with self.assertRaisesRegex(ValueError, 'match the passing native validation'):
            self.translate(validation)

    def test_wrong_native_resolution_is_rejected_even_if_validation_agrees(self):
        self.camera['nativeFrame'] = [768, 1280]
        with self.assertRaisesRegex(ValueError, 'native frame differs'):
            self.translate()

    def test_shifted_root_is_rejected_even_if_validation_agrees(self):
        self.camera['rootPx'][1] = 497
        with self.assertRaisesRegex(ValueError, 'ground root differs'):
            self.translate()

    def test_asset_from_another_actor_is_rejected(self):
        self.asset['id'] = 'someone-else'
        with self.assertRaisesRegex(ValueError, 'asset registration differs'):
            self.translate()


if __name__ == '__main__':
    unittest.main()
