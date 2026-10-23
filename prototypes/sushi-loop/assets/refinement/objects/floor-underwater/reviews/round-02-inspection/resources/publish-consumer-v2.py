"""Bind unchanged native water art to the verified current consumer, after review01."""
from pathlib import Path
import hashlib
import json
import shutil

RUN = Path(__file__).resolve().parents[2]
OBJECT = RUN / 'objects/floor-underwater'
PROOF = RUN / 'verification/fractional-world-raster-v1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    # This adapter cannot grant art approval. The original judge must first
    # finish the failed packet, and independently review the new packet later.
    previous_review = OBJECT / 'reviews/round-01.json'
    review = read(previous_review)
    assert review['verdict'] == 'needs_evidence', 'Read and reconcile any native/art revision before using this adapter'
    assert review['candidatePacketSHA256'] == sha(OBJECT / 'candidates/round-01/packet.json')
    prior = read(OBJECT / 'candidates/round-01/validation.json')
    assert prior['nativeAndFrozenContractChecksPassed'] is True
    assert prior['projectSHA256'] == sha(OBJECT / 'source/round-01.blend')
    assert sha(OBJECT / 'brief-v2-runtime-grid.json') == 'f92c2dd78dac6a348148510a08e68c961fdd14917b75ce3d99d84f110dfef644'
    proof = read(PROOF / 'root-verification.json')
    for name, record in proof['files'].items():
        assert sha(PROOF / name) == record['sha256'], name
    summary = read(PROOF / 'summary.json')['reports']
    assert {report['backend'] for report in summary} == {'full-chrome', 'headless-shell'}
    assert all(report['cases'] == 1476 and report['alphaFailures'] == 0
               and report['playbackRuns'] == 8 and report['errors'] == [] for report in summary)
    assert proof['productionRenderer']['sha256'] == '570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
    output = OBJECT / 'delivery/runtime-grid-v2'
    assert not output.exists(), 'Never overwrite a technical handoff'
    output.mkdir(parents=True)
    validation = {
        'asset': 'floor-underwater', 'round': 'round-02',
        'status': 'Technical consumer revision; original independent final art/runtime verdict pending',
        'allChecksPassed': True, 'aestheticApproval': 'Pending original independent judge; coordinator cannot grant it',
        'nativeArtUnchanged': True, 'projectSHA256': prior['projectSHA256'],
        'nativeValidation': prior['nativeValidation'],
        'actualMaxFacingAngularErrorRadians': prior['actualMaxFacingAngularErrorRadians'],
        'priorNativeAndFrozenContractChecksPassed': True,
        'previousValidation': {'path': 'candidates/round-01/validation.json', 'sha256': sha(OBJECT / 'candidates/round-01/validation.json')},
        'previousReview': {'path': 'reviews/round-01.json', 'sha256': sha(previous_review)},
        'previousRuntimeFailureRetained': 'FullChrome264/1476 failed; aggregate minimum128. No old report/helper/source/frame altered.',
        'currentConsumerContract': {'path': 'inputs/root-consumer-grid-v2.json', 'sha256': sha(OBJECT / 'inputs/root-consumer-grid-v2.json')},
        'currentConsumerProof': {'path': '../../verification/fractional-world-raster-v1/root-verification.json', 'sha256': sha(PROOF / 'root-verification.json')},
        'checks': {'exactNativeSourceAndRenderedBytesRetained': True, 'bothBackendsAll2952CasesOpaque': True,
                   'all16ActualTwelveFpsPlaybacksVisitEveryPhase': True, 'registrationScaleAndPainterOrderRetained': True,
                   'noSourcePixelRepairGeometryOverlapOrPlacementAdjustment': True},
        'nativeCaptureSummary': prior['nativeCaptureSummary'], 'currentConsumerSummary': summary,
    }
    write(output / 'validation.json', validation)
    delivery = read(OBJECT / 'source/delivery-round01.json')
    delivery['round'] = 'round-02'
    delivery['metadataOnly'] = True
    delivery['validation'] = 'delivery/runtime-grid-v2/validation.json'
    delivery['readiness'] = 'Native art reused exactly. Technical current-consumer evidence passes; independent final judge approval pending.'
    delivery['consumerRevision'] = validation['currentConsumerContract']
    resources = delivery['resources']
    assert isinstance(resources, list)
    for path in sorted(PROOF.rglob('*')):
        if path.is_file():
            resources.append({'path': '../../verification/fractional-world-raster-v1/' + path.relative_to(PROOF).as_posix(),
                              'sha256': sha(path), 'relativeTo': 'object'})
    resources.append({'path': 'reviews/round-01.json', 'sha256': sha(previous_review), 'relativeTo': 'object'})
    resources.append({'path': 'candidates/round-01/packet.json', 'sha256': sha(OBJECT / 'candidates/round-01/packet.json'), 'relativeTo': 'object'})
    resources.append({'path': 'delivery/runtime-grid-v2/validation.json', 'sha256': sha(output / 'validation.json'), 'relativeTo': 'object'})
    # New screenshots are actual current-browser consumer output, not new art.
    for backend in ['full-chrome', 'headless-shell']:
        delivery['previews']['current-consumer-' + backend] = '../../verification/fractional-world-raster-v1/' + backend + '/context-S-0.png'
    write(output / 'delivery.json', delivery)
    shutil.copyfile(output / 'delivery.json', OBJECT / 'delivery-round-02.json')
    files = {path.relative_to(OBJECT).as_posix(): {'sha256': sha(path), 'bytes': path.stat().st_size}
             for path in output.iterdir() if path.is_file()}
    write(output / 'manifest.json', {'asset': 'floor-underwater', 'round': 'round-02', 'scope': 'Consumer evidence only; no art edit or approval',
                                    'projectSHA256': prior['projectSHA256'], 'files': files})
    print(json.dumps({'deliverySHA256': sha(output / 'delivery.json'), 'validationSHA256': sha(output / 'validation.json'),
                      'manifestSHA256': sha(output / 'manifest.json')}))


if __name__ == '__main__':
    main()
