"""Recipe reuse must stay scoped, traceable and separate from artistic review."""
import json
from pathlib import Path
import tempfile
import unittest

from acceptance_contract import acceptance, CHECKS, sha


class AcceptanceContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='conveyor-acceptance-')
        self.addCleanup(self.temp.cleanup)
        self.run = Path(self.temp.name)
        self.folder = self.run / 'objects/belt-corner-e-n'
        self.base = self.folder / 'candidates/round-01'
        self.base.mkdir(parents=True)
        self.policy_path = self.folder / 'inputs/policy.json'
        self.policy_path.parent.mkdir()
        self.evidence = self.base / 'native.json'
        self.evidence.write_text('{"passed":true}')
        family_packet = self.run / 'family-packet.json'
        family_packet.write_text('{"asset":"belt-straight-n"}')
        family_review = self.run / 'family-review.json'
        family_review.write_text(json.dumps({'asset': 'belt-straight-n', 'verdict': 'approve',
                                             'blockers': [], 'candidatePacketSHA256': sha(family_packet)}))
        self.policy = {'method': 'recipe-reuse', 'scope': ['belt-corner-e-n'],
                       'authorization': {'source': 'direct user message in current task'},
                       'family': {'straight': {'asset': 'belt-straight-n', 'packet': family_packet.name,
                                  'packetSHA256': sha(family_packet), 'review': family_review.name,
                                  'reviewSHA256': sha(family_review)}}}
        self.policy_path.write_text(json.dumps(self.policy))
        (self.base / 'N.png').write_bytes(b'render fixture')
        (self.base / 'sheet.png').write_bytes(b'sheet fixture')
        self.packet = {'asset': self.folder.name, 'qualityCriteria': {'method': 'established-native-family-recipe',
                        'policy': 'inputs/policy.json', 'policySHA256': sha(self.policy_path)},
                       'files': {'policy': {'path': '../../inputs/policy.json', 'sha256': sha(self.policy_path)},
                                 'audit': {'path': 'native.json', 'sha256': sha(self.evidence)}},
                       'candidateRenders': {'N': {'path': 'N.png', 'sha256': sha(self.base / 'N.png')}},
                       'previews': {'sheet': {'path': 'sheet.png', 'sha256': sha(self.base / 'sheet.png')}}}
        (self.base / 'packet.json').write_text(json.dumps(self.packet))
        self.receipt = {'asset': self.folder.name, 'method': 'recipe-reuse', 'verdict': 'validated',
                        'independentReview': False, 'blockers': [],
                        'candidatePacketSHA256': sha(self.base / 'packet.json'),
                        'policySHA256': sha(self.policy_path), 'family': self.policy['family'],
                        'checks': {name: True for name in CHECKS},
                        'evidence': {'candidates/round-01/native.json': sha(self.evidence)},
                        'inspectedFiles': ['N.png', 'sheet.png']}
        self.receipt_path = self.folder / 'validations/round-01.json'
        self.receipt_path.parent.mkdir()
        self.save_receipt()

    def save_receipt(self):
        self.receipt_path.write_text(json.dumps(self.receipt))

    def test_exact_recipe_receipt(self):
        self.assertEqual(acceptance(self.folder, 'round-01')['method'], 'recipe-reuse')

    def test_reject_fake_independent_approval_or_missing_checks(self):
        for change in ({'verdict': 'approve'}, {'independentReview': True}, {'checks': {}}):
            original = self.receipt.copy()
            try:
                self.receipt.update(change)
                self.save_receipt()
                with self.assertRaises(ValueError):
                    acceptance(self.folder, 'round-01')
            finally:
                self.receipt = original
        self.save_receipt()

    def test_reject_changed_evidence_policy_and_lineage(self):
        for path in (self.evidence, self.policy_path, self.run / 'family-review.json'):
            original = path.read_bytes()
            try:
                path.write_bytes(original + b' ')
                with self.assertRaises(ValueError):
                    acceptance(self.folder, 'round-01')
            finally:
                path.write_bytes(original)

    def test_reject_unscoped_asset_and_incomplete_inspection(self):
        self.policy['scope'] = ['belt-start-n']
        self.policy_path.write_text(json.dumps(self.policy))
        digest = sha(self.policy_path)
        self.packet['qualityCriteria']['policySHA256'] = digest
        self.packet['files']['policy']['sha256'] = digest
        (self.base / 'packet.json').write_text(json.dumps(self.packet))
        self.receipt.update(policySHA256=digest, candidatePacketSHA256=sha(self.base / 'packet.json'))
        self.save_receipt()
        with self.assertRaises(ValueError):
            acceptance(self.folder, 'round-01')
        self.policy['scope'] = [self.folder.name]
        self.policy_path.write_text(json.dumps(self.policy))
        digest = sha(self.policy_path)
        self.packet['qualityCriteria']['policySHA256'] = digest
        self.packet['files']['policy']['sha256'] = digest
        (self.base / 'packet.json').write_text(json.dumps(self.packet))
        self.receipt.update(policySHA256=digest, candidatePacketSHA256=sha(self.base / 'packet.json'), inspectedFiles=['N.png'])
        self.save_receipt()
        with self.assertRaises(ValueError):
            acceptance(self.folder, 'round-01')


if __name__ == '__main__':
    unittest.main()
