"""Record coordinator checks after inspecting a shared-recipe conveyor's views/context."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from PIL import Image, ImageChops
from acceptance_contract import acceptance, CHECKS, sha, require, inside, read
from audit_directions import audit

RUN = Path(__file__).resolve().parents[1]
PACKET_HELPER = Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py')


def record(asset, inspection_note, notes, supplements):
    folder = RUN / 'objects' / asset
    base = folder / 'candidates/round-01'
    ready = read(base / 'READY.json')
    packet_path = base / 'packet.json'
    require(sha(packet_path) == ready['packetSHA256'], 'READY packet changed')
    subprocess.run(['python3', str(PACKET_HELPER), 'verify', '--packet', str(packet_path)], check=True)
    packet, delivery = read(packet_path), read(base / 'delivery.json')
    require(sha(base / 'delivery.json') == ready['deliverySHA256'], 'READY delivery changed')
    require(sha(folder / delivery['project']) == ready['projectSHA256'], 'READY native project changed')
    require(packet['qualityCriteria']['method'] == 'established-native-family-recipe', 'Not a recipe application')
    policy_path = folder / packet['qualityCriteria']['policy']
    policy = read(policy_path)
    require(asset in policy['scope'], 'Asset outside authorized conveyor scope')
    technical = read(base / 'technical-checks.json')
    for key in ['originalDeckVerticesExactlyEqual', 'originalUVExactlyEqual',
                'originalIntrinsicExactlyEqual', 'originalPhaseExactlyEqual',
                'allOpenFunctionalProfilesUncapped', 'atlasRectanglesExact']:
        require(technical.get(key) is True, f'Native recipe check failed: {key}')
    require(technical['nativeFrameCount'] == 96, 'Incomplete native animation')
    camera = technical['nativeRegistration']
    require(camera['sameCameraWorldMatrix'] and camera['sameProjectionMatrix']
            and camera['frame'] == [384, 704]
            and all(abs(a-b) < .001 for a, b in zip(camera['rootCalibration'], [192, 496])),
            'Native registration changed')
    facing = audit(folder, 'round-01')
    require(facing['sampleCounts'] == {d: 25 for d in 'NESW'}, 'Missing root/closure samples')
    native = read(base / 'validation.json')['frames']
    require(len(native) == 100, 'Incomplete native phase audit')
    phases = {(f['direction'], f['index']): f for f in native}
    require(set(phases) == {(d, i) for d in 'NESW' for i in range(25)}, 'Native phase coverage changed')
    require(all(abs(f['phase'] + 7*f['index']/24) < 1e-6 for f in native), 'Native phase law changed')
    closure = {}
    for direction in 'NESW':
        with Image.open(base / phases[direction, 0]['path']) as first, Image.open(base / phases[direction, 24]['path']) as last:
            delta = ImageChops.difference(first.convert('RGBA'), last.convert('RGBA'))
            maxima = [channel[1] for channel in delta.getextrema()]
            require(max(maxima[:3]) <= 1 and maxima[3] == 0, 'Visible or coverage loop closure difference')
            closure[direction] = {'maximumRGBA': maxima, 'RGBDifferenceBounds': delta.convert('RGB').getbbox()}
    frames = {(f['direction'], f['index']): f for f in delivery['rawFrames']}
    require(len(frames) == len(delivery['rawFrames']) == 96, 'Incomplete published frame set')
    require(len(delivery['atlases']) == 4, 'Incomplete published atlas set')
    for atlas in delivery['atlases']:
        require(atlas['frames'] == 24 and atlas['fps'] == 12 and atlas['loop'] is True
                and atlas['frameOrder'] == list(range(24)), 'Published timing changed')
        with Image.open(folder / atlas['path']) as image:
            for index, rect in enumerate(atlas['rects']):
                x, y, width, height = rect
                with Image.open(folder / frames[atlas['direction'], index]['path']) as raw:
                    require(image.crop((x,y,x+width,y+height)).tobytes() == raw.tobytes(), 'Atlas is not exact whole frame')
    for comparison in technical['nativeContinuity'].values():
        require(comparison['joinMaxRGBA'] <= 1 and comparison['joinDifferentAlphaPixels'] == 0
                and comparison['joinRGBOver1Pixels'] == 0, 'Native port continuity failed')
    consumer = technical['actualCurrentConsumer']
    require(consumer['allReady'] and consumer['errors'] == [] and consumer['cases'] >= 1
            and max(consumer['joinMaxRGBA'][:3]) <= 1 and consumer['joinMaxRGBA'][3] == 0
            and consumer['joinAlphaDifferentPixels'] == 0 and consumer['joinRGBOver1Pixels'] == 0,
            'Actual per-asset consumer check failed')
    extras = {}
    for relative in supplements:
        path = inside(RUN, folder / relative)
        bundle = read(path)
        original = RUN / 'objects' / bundle['asset'] / 'candidates/round-01/packet.json'
        require(bundle['originalPacketSHA256'] == sha(original), 'Supplement refers to changed candidate')
        extras[str(path.relative_to(folder)) if path.is_relative_to(folder) else relative] = sha(path)
        for item in bundle['files'].values():
            resource = inside(RUN, path.parent / item['path'])
            require(sha(resource) == item['sha256'], 'Supplement changed')
            extras[os.path.relpath(resource, folder)] = item['sha256']
    receipt = {'schemaVersion':1, 'asset':asset, 'method':'recipe-reuse', 'verdict':'validated',
               'independentReview':False, 'authority':'Direct user instruction; coordinator technical validation after representative visual inspection.',
               'candidatePacketSHA256':sha(packet_path), 'blockers':[], 'policySHA256':sha(policy_path),
               'family':policy['family'], 'checks':{name:True for name in sorted(CHECKS)},
               'evidence':ready['evidence'], 'supplementalEvidence':extras,
               'inspectedFiles':[item['path'] for item in packet['candidateRenders'].values()]
                                +[packet['previews'][name]['path'] for name in ['four-view-sheet','phone']],
               'inspectionMethod':inspection_note, 'closurePixelResiduals':closure,
               'remainingDifferences':notes,
               'coverage':'Own complete native/phase/atlas and representative current consumer checks. Reused common family/filter/motion coverage is labeled in recipe-equivalence.json; no independent artistic judge is claimed.'}
    output = folder / 'validations/round-01.json'
    require(not output.exists(), 'Preserve existing acceptance; do not overwrite')
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(receipt,indent=2)+'\n')
    try:
        acceptance(folder,'round-01')
    except Exception:
        output.unlink()  # Only this unaccepted, newly created receipt.
        raise
    alias = folder / 'delivery.json'
    if alias.exists():
        require(sha(alias) == ready['deliverySHA256'], 'Existing delivery alias differs')
    else:
        shutil.copyfile(base / 'delivery.json',alias)
    print(json.dumps({'asset':asset,'receiptSHA256':sha(output),'status':'technically-validated','independentReview':False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset')
    parser.add_argument('--inspection-note', required=True, help='Actual coordinator visual inspection performed, not an automatic artistic verdict')
    parser.add_argument('--note', action='append', default=[])
    parser.add_argument('--supplement', action='append', default=[])
    args = parser.parse_args()
    record(args.asset,args.inspection_note,args.note,args.supplement)
