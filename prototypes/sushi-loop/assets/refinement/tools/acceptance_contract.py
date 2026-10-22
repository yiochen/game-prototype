"""Distinguish independent art approval from user-authorized conveyor recipe reuse."""
import argparse
import hashlib
import json
from pathlib import Path

RECIPE_METHOD = 'established-native-family-recipe'
CHECKS = {'nativeRegistration', 'originalClipsAndCadence', 'familyRecipeAndMaterials',
          'portsAndPhase', 'nativeContinuity', 'publishedPixelsAndResourceClosure',
          'intendedSizeInspection'}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, path):
    path = Path(path).resolve()
    require(path.is_relative_to(Path(root).resolve()), 'Acceptance resource escapes experiment')
    return path


def acceptance(folder, round_name, packet=None):
    folder = Path(folder).resolve()
    run = folder.parent.parent
    packet_path = folder / 'candidates' / round_name / 'packet.json'
    packet = packet or read(packet_path)
    recipe = packet['qualityCriteria'].get('method') == RECIPE_METHOD
    path = folder / ('validations' if recipe else 'reviews') / f'{round_name}.json'
    receipt = read(path)
    require(packet.get('asset') == folder.name
            and receipt.get('asset', packet['asset']) == folder.name
            and receipt.get('candidatePacketSHA256') == sha(packet_path)
            and receipt.get('blockers') == [], 'Acceptance binds wrong or blocked candidate')
    if recipe:
        require(receipt.get('asset') == folder.name, 'Recipe receipt must name the asset')
        require(folder.name.startswith(('belt-corner-', 'belt-start-', 'belt-end-')),
                'Recipe reuse is authorized only for remaining conveyors')
        require(receipt.get('method') == 'recipe-reuse' and receipt.get('verdict') == 'validated'
                and receipt.get('independentReview') is False,
                'Recipe receipt must identify technical validation, not independent art approval')
        policy_path = inside(folder, folder / packet['qualityCriteria']['policy'])
        expected = packet['qualityCriteria']['policySHA256']
        require(sha(policy_path) == expected == receipt.get('policySHA256'), 'Recipe policy changed')
        policy = read(policy_path)
        require(policy.get('method') == 'recipe-reuse' and folder.name in policy['scope']
                and policy.get('authorization', {}).get('source') == 'direct user message in current task',
                'Asset lacks direct user recipe authorization')
        bound = {(packet_path.parent / item['path']).resolve(): item['sha256']
                 for group in ['files', 'candidateRenders', 'previews'] for item in packet[group].values()}
        require(bound.get(policy_path) == expected, 'Recipe policy is outside sealed packet')
        require(receipt.get('checks') == {name: True for name in CHECKS},
                'Recipe registration/phase/continuity/inspection checks are incomplete')
        require(receipt.get('family') == policy['family'], 'Recipe family lineage differs')
        for reference in policy['family'].values():
            family_packet = inside(run, run / reference['packet'])
            family_review = inside(run, run / reference['review'])
            require(sha(family_packet) == reference['packetSHA256']
                    and sha(family_review) == reference['reviewSHA256'], 'Approved family lineage changed')
            review = read(family_review)
            require(read(family_packet).get('asset') == reference['asset']
                    and review.get('asset') == reference['asset'], 'Recipe family identity differs')
            require(review.get('verdict') == 'approve' and review.get('blockers') == []
                    and review.get('candidatePacketSHA256') == reference['packetSHA256'],
                    'Recipe family lacks independent original approval')
        evidence = receipt.get('evidence')
        require(isinstance(evidence, dict) and evidence, 'Missing measured recipe evidence')
        for name, digest in evidence.items():
            resource = inside(run, folder / name)
            require(bound.get(resource) == digest == sha(resource), 'Recipe evidence is not exact packet-bound bytes')
        method = 'recipe-reuse'
    else:
        require(receipt.get('verdict') == 'approve', 'Independent art approval required')
        method = 'independent-review'
    expected_views = {record['path'] for group in ['candidateRenders', 'previews']
                      for record in packet[group].values()}
    inspected = receipt.get('inspectedFiles')
    require(isinstance(inspected, list) and all(isinstance(value, str) for value in inspected)
            and expected_views <= set(inspected), 'Acceptance lacks required visual inspection coverage')
    return {'method': method, 'path': path, 'sha256': sha(path), 'receipt': receipt}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--round', required=True)
    args = parser.parse_args()
    result = acceptance(Path(__file__).resolve().parents[1] / 'objects' / args.asset, args.round)
    print(json.dumps({'asset': args.asset, 'method': result['method'], 'sha256': result['sha256']}))
