"""Supplemental evidence may use object, manifest or enclosing-review paths."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from verify_staged_object import resolve_supplemental_path


class SupplementalPathsTest(unittest.TestCase):
    def test_all_supported_path_bases_reach_the_same_real_evidence(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            review = folder / 'reviews'
            manifest_directory = review / 'round-01-independent'
            manifest_directory.mkdir(parents=True)
            evidence = manifest_directory / 'native.png'
            evidence.write_bytes(b'exact evidence')
            for path in ('reviews/round-01-independent/native.png',
                         'round-01-independent/native.png', 'native.png'):
                with self.subTest(path=path):
                    self.assertEqual(resolve_supplemental_path(
                        folder, manifest_directory, review, path), evidence.resolve())

    def test_a_second_existing_location_remains_ambiguous(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            review = folder / 'reviews'
            manifest_directory = review / 'round-01-independent'
            manifest_directory.mkdir(parents=True)
            (folder / 'native.png').write_bytes(b'wrong evidence')
            (manifest_directory / 'native.png').write_bytes(b'exact evidence')
            with self.assertRaisesRegex(AssertionError, 'ambiguous'):
                resolve_supplemental_path(folder, manifest_directory, review, 'native.png')

    def test_absent_evidence_is_rejected(self):
        with TemporaryDirectory() as temporary:
            folder = Path(temporary)
            with self.assertRaisesRegex(AssertionError, 'Missing'):
                resolve_supplemental_path(folder, folder / 'reviews/round',
                                          folder / 'reviews', 'absent.png')


if __name__ == '__main__':
    unittest.main()
