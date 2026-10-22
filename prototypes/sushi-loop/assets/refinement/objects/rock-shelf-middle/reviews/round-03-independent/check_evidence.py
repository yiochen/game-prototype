import pathlib, json, hashlib
B = pathlib.Path(__file__).parent
read = lambda name: json.loads((B / name).read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
n = read('evidence/native-inspection.json')
contract = read('resources/root-native-contract.json')
tol = 1e-5
profile = contract['canonicalFinitePorts']['profileYZ']
assert len(n['caps']) == 2
for cap in n['caps']:
    actual = [v[1:] for v in cap['vertices']]
    assert len(actual) == 6
    cycles = [profile[i:] + profile[:i] for i in range(6)]
    reverse = list(reversed(profile))
    cycles += [reverse[i:] + reverse[:i] for i in range(6)]
    assert min(max(abs(x[k] - y[k]) for x, y in zip(actual, cycle) for k in range(2)) for cycle in cycles) < tol
    x = cap['vertices'][0][0]
    assert abs(abs(x) - .5) < tol and all(abs(v[0] - x) < tol for v in cap['vertices'])
    assert abs(cap['normal'][0] - (1 if x > 0 else -1)) < tol
    assert cap['smooth'] is False and cap['materialIndex'] == 1
bounds = n['allBounds']
assert all(bounds[0][k] >= [-.5, -.45, 0][k] - tol and bounds[1][k] <= [.5, .45, .45][k] + tol for k in range(3))
core = next(o for o in n['objects'] if 'sculpted_core' in o['name'])
assert abs(core['bottomArea'] - .9) < tol
assert all(abs(bounds[0][k] - [-.5, -.45, 0][k]) < tol for k in range(3))
assert len(n['endpointBandSamples']) == 75 and all(s['W'] and s['E'] for s in n['endpointBandSamples'])
camera = n['camera']
assert camera['worldMatrix'] == contract['registration']['cameraWorldMatrix']
assert camera['type'] == 'ORTHO' and camera['orthoScale'] == 1.5 and camera['sensorFit'] == 'HORIZONTAL'
assert camera['pixelAspect'] == contract['registration']['pixelAspect'] and camera['frame'] == [768, 1408]
assert all(abs(camera['calibration']['root'][i] - [384, 992][i]) < .001 for i in range(2))
assert n['settings']['engine'] == 'BLENDER_EEVEE' and n['settings']['samples'] == 32
assert n['settings']['filterSize'] == .5 and n['settings']['filmTransparent']
assert n['settings']['image'] == {'format': 'PNG', 'colorMode': 'RGBA', 'depth': '8'}
assert n['settings']['colorManagement'] == {'view': 'Standard', 'look': 'None', 'exposure': 0.0, 'gamma': 1.0}
assert n['settings']['dither'] == 0 and n['settings']['frameStart'] == n['settings']['frameEnd'] == 1 and n['settings']['fps'] == 12
assert not any(n[k] for k in ['libraries', 'imageResources', 'armatures', 'dataActions'])
assert all(not o['shapeKeys'] and not o['action'] and not o['geometryLibrary'] for o in n['objects'])
assert all(not m['action'] and not m['nodeAction'] and not m['linked'] for m in n['materials'])
assert all(o['meshUsers'] == 1 for o in read('evidence/resource-signatures.json')['objects'])
assert all(v['sealedBOXPublishesExactly'] for v in read('evidence/independent-replay-comparison.json').values())
assert all(r['hashMatch'] for r in read('evidence/consumer-bindings.json')['consumerCopies'])
assert read('evidence/consumer-results.json')['errors'] == []
assert read('evidence/frozen-current-consumer-control.json')['allExact']
for group in read('evidence/seam-measurements.json').values():
    for row in group.values():
        assert all(v['assembledAlphaLess255Pixels'] == 0 and v['minAssembledAlphaOnNativeOpaque'] == 255 for v in row['metrics'].values())
preserved = read('evidence/independent-preservation-comparison.json')
assert preserved['commonPrefixPositionMaxResidual'] == preserved['commonPrefixAlbedoMaxResidual'] == preserved['commonPrefixCornerNormalMaxResidual'] == 0
assert preserved['capGraphsEqual'] and preserved['sourceBytesUnchangedAfter']
assert sha(B / 'resources/source.blend') == n['sourceSHA256'] == '3e6c7cbe865a918dbeec5faf1a48af540f6290e7afc41ef4c987162617199422'
result = {'asset': 'rock-shelf-middle', 'round': 'round-03', 'sourceSHA256': n['sourceSHA256'],
          'checks': {'actualFiniteOrderedPorts': True, 'actualFiniteBaseAndEnvelope': True,
                     'registeredCameraAndRoot': True, 'savedCommonSamplingAndStaticFrame': True,
                     'actualPrivateNativeResources': True, 'wholeBOXPublication': True,
                     'currentConsumerMatchesPacket': True, 'allFourNativeOpaqueAssemblyCoverage': True,
                     'measuredCommonCrownAndCutfacePreservation': True},
          'endpointActualMaxResiduals': n['endpointMaxResidual'],
          'meaning': 'Technical/source checks only. Numeric coverage and preservation do not decide art; appearance is independently assessed in the exact packet-bound verdict. All renderer residuals remain recorded.'}
(B / 'evidence/technical-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
