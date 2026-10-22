"""Regression coverage for dependency revisions with separate native pose ledgers."""
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest

from audit_directions import audit


class PoseLedgerAuditTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'actor'
        self.round = self.folder / 'candidates' / 'round-02'
        self.round.mkdir(parents=True)
        self.ledger = self.round / 'candidate-phases.json'
        self.records = [{'clip': 'hold', 'direction': facing, 'rootRotationZ': angle}
                        for facing, angle in [('N', math.pi), ('E', math.pi / 2),
                                              ('S', 0), ('W', -math.pi / 2)]]
        (self.round / 'validation.json').write_text(json.dumps({'ok': True}))

    def seal(self):
        self.ledger.write_text(json.dumps(self.records))
        packet = {'capture': {'views': ['N', 'E', 'S', 'W']}, 'files': {
            'nativeValidation': {'path': 'validation.json'},
            'candidateResource:phases': {'path': self.ledger.name,
                'sha256': hashlib.sha256(self.ledger.read_bytes()).hexdigest()}}}
        (self.round / 'packet.json').write_text(json.dumps(packet))

    def test_all_measured_cardinals_pass(self):
        self.seal()
        self.assertEqual(audit(self.folder, 'round-02')['sampleCounts'],
                         {'N': 1, 'E': 1, 'S': 1, 'W': 1})

    def test_wrong_native_rotation_fails_even_with_matching_hash(self):
        self.records[0]['rootRotationZ'] = 0
        self.seal()
        with self.assertRaisesRegex(ValueError, 'differs from publisher'):
            audit(self.folder, 'round-02')

    def test_post_seal_ledger_mutation_fails(self):
        self.seal()
        self.ledger.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'candidate phases changed'):
            audit(self.folder, 'round-02')

    def test_missing_facing_cannot_be_inferred(self):
        self.records.pop()
        self.seal()
        with self.assertRaisesRegex(ValueError, 'missing measured root rotation'):
            audit(self.folder, 'round-02')

    def test_reopened_static_audit_reads_actual_facing_matrices(self):
        self.seal()
        (self.round / 'validation.json').write_text(json.dumps({'facings': {
            row['direction']: {'rootMatrix': [
                [math.cos(row['rootRotationZ']), -math.sin(row['rootRotationZ']), 0, 0],
                [math.sin(row['rootRotationZ']), math.cos(row['rootRotationZ']), 0, 0],
                [0, 0, 1, 0], [0, 0, 0, 1]]} for row in self.records}}))
        self.assertEqual(audit(self.folder, 'round-02')['sampleCounts'],
                         {'N': 1, 'E': 1, 'S': 1, 'W': 1})


if __name__ == '__main__':
    unittest.main()
