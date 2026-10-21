from pathlib import Path
from PIL import Image, ImageChops
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile

B = Path(__file__).resolve().parent.parent
O = B / 'candidates/round-01'
R = B / 'reviews/round-01-inspection'
R.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rgba = lambda p: Image.open(p).convert('RGBA')
files = json.loads((B / 'source/replay-resources.json').read_text())
for entry in files:
    assert sha(B / entry['path']) == entry['sha256']
proof = {'packetSHA256': sha(O / 'packet.json'), 'boundResourceHashesMatch': True,
         'boundResourceCount': len(files), 'productionWrites': False}
with tempfile.TemporaryDirectory(prefix='portable-', dir=R) as temporary:
    dest = Path(temporary) / 'supplement'
    dest.mkdir()
    for entry in files:
        src = B / entry['path']
        target = dest / entry['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
        assert sha(target) == entry['sha256']
    replay = dest / 'judge-native-replay'
    command = ['/opt/homebrew/bin/blender', '--background', str(dest / 'source/round-01.blend'),
               '--python', str(dest / 'source/reopen_goods.py'), '--', '--output-dir', str(replay)]
    subprocess.run(command, capture_output=True, text=True, check=True)
    assert rgba(O / 'goods.png').tobytes() == rgba(replay / 'reopened.png').tobytes()
    proof['portableNativeRGBAPixelsExact'] = True
    proof['portableNativeRGBAPixelSHA256'] = hashlib.sha256(rgba(replay / 'reopened.png').tobytes()).hexdigest()
    python = '/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
    subprocess.run([python, str(dest / 'source/prepare_consumer.py')], capture_output=True, text=True, check=True)
    project = dest / 'source/consumer'
    subprocess.run(['/opt/homebrew/bin/godot', '--headless', '--editor', '--path', str(project), '--import'],
                   capture_output=True, text=True, check=True)
    consumer = dest / 'judge-consumer-replay'
    env = dict(os.environ, GOODS_OUTPUT=str(consumer))
    subprocess.run(['/opt/homebrew/bin/godot', '--path', str(project), '--script', 'res://bench.gd',
                    '--resolution', '64x64', '--position', '-5000,-5000'], env=env,
                   capture_output=True, text=True, check=True)
    count = 0
    for original in sorted((O / 'consumer').glob('*.png')):
        replayed = consumer / original.name
        assert replayed.exists()
        assert rgba(original).tobytes() == rgba(replayed).tobytes(), original.name
        count += 1
    assert count == 54
    proof['portableConsumerExactRGBACount'] = count

record = json.loads((O / 'consumer/render-record.json').read_text())
contexts = {(v['mode'], v['state'], tuple(v['viewportSize'])): v for v in record['contexts']}
pairs = []
for key, candidate in contexts.items():
    mode, state, dimensions = key
    if mode != 'candidate':
        continue
    original = contexts[('original', state, dimensions)]
    a = {k: v for k, v in original.items() if k not in ['mode', 'path']}
    c = {k: v for k, v in candidate.items() if k not in ['mode', 'path']}
    assert a == c, (state, dimensions, 'context properties')
    ai, ci = rgba(O / 'consumer' / original['path']), rgba(O / 'consumer' / candidate['path'])
    difference = ImageChops.difference(ai, ci).convert('RGB')
    bounds = difference.getbbox()
    barrel = next((card for card in candidate['cards'] if card['id'] == 'barrel-wood'), None)
    if barrel:
        x, y, width, height = barrel['fullCanvasDestination']
        allowed = (math.floor(x), math.floor(y), math.ceil(x + width), math.ceil(y + height))
        difference.paste((0, 0, 0), allowed)
        assert difference.getbbox() is None, (state, dimensions, 'UI outside barrel')
    else:
        assert bounds is None
    pairs.append({'state': state, 'viewport': list(dimensions), 'propertiesExact': True,
                  'onlyBarrelPreviewPixelsDiffer': True, 'differenceBounds': bounds})
assert len(pairs) == 15
proof['pairedContextChecks'] = pairs

snapshot = B / 'source/resources/current-consumer'
manifest = json.loads((snapshot / 'assets/ui/editor-goods/manifest.json').read_text())
atlas = rgba(O / 'consumer-atlas.png')
baseline = rgba(snapshot / 'baseline-atlas.png')
checks = {}
for name, entry in manifest['sprites'].items():
    x, y, width, height = entry['region']
    rect = (x, y, x + width, y + height)
    a, c = baseline.crop(rect), atlas.crop(rect)
    if name == 'barrel-wood':
        assert c.tobytes() == rgba(O / 'goods.png').tobytes()
    else:
        assert a.tobytes() == c.tobytes()
    checks[name] = {'unchanged': a.tobytes() == c.tobytes(),
                    'rgbaSHA256': hashlib.sha256(c.tobytes()).hexdigest()}
floor = snapshot / 'floor-cream.png'
assert sha(floor) == '6ded9330f3106d1d4941ac84e94c3e54436f098d261f5f36436d7115af239177'
assert checks['floor-cream']['rgbaSHA256'] == hashlib.sha256(rgba(floor).tobytes()).hexdigest()
proof['atlasCells'] = checks
proof['acceptedFloorFileSHA256'] = sha(floor)
proof['native384RGBA'] = rgba(O / 'goods.png').size == (384, 384)
assert proof['native384RGBA']
proof['complete'] = True
(R / 'portable-and-consumer-checks.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps({'nativeExact': True, 'consumerExactImages': count, 'contextPairsExact': len(pairs),
                  'otherFiveCellsAndFloorExact': True, 'proof': str(R / 'portable-and-consumer-checks.json')}))
