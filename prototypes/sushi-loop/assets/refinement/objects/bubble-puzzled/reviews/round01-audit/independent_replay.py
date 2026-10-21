"""Independent review diagnostics. Never writes sealed source/candidate bytes."""
from pathlib import Path
import json, hashlib, shutil, subprocess, sys, os, math
from PIL import Image

sys.dont_write_bytecode = True
A = Path(__file__).resolve().parent
O = A.parents[1]
ROOT = O.parents[5]
C = O / 'candidates/round01'
clone = A / 'relocated-object'
cwd = A / 'unrelated-working-directory'
cwd.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pixels = lambda p: Image.open(p).convert('RGBA').tobytes()
d = json.loads((C / 'delivery.json').read_text())
manifest = json.loads((C / 'manifest.json').read_text())
original = json.loads((O / 'inputs/catalog-object.json').read_text())
paths = set(d['resources'] + [d['project'], d['recipeScript'], d['recipe'], d['validation'], d['manifest']] + list(d['heroes'].values()) + list(d['previews'].values()) + [r['path'] for r in d['rawFrames'] + d['atlases']])
closure = sorted(p for p in paths if p.startswith('source/round01/'))
before = {p: sha(O / p) for p in paths}
log = []
for p in closure:
    assert not Path(p).is_absolute() and '..' not in Path(p).parts
    dest = clone / p
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(O / p, dest)
for script in ['prepare_sources.py', 'publish.py']:
    done = subprocess.run([sys.executable, str(clone / 'source/round01' / script)], cwd=cwd, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, capture_output=True, text=True, check=True)
    log.append({'script': script, 'stdout': done.stdout, 'stderr': done.stderr, 'returncode': done.returncode})
replayed = {}
for p, h in before.items():
    if p.startswith('candidates/') or p in [d['project'], d['recipe'], 'source/round01/crop.json']:
        assert (clone / p).is_file(), p
        assert sha(clone / p) == h, ('replay', p)
        replayed[p] = h
assert sha(clone / 'delivery.json') == sha(C / 'delivery.json')
assert before == {p: sha(O / p) for p in paths}
assert len(d['rawFrames']) == 144 and len({r['path'] for r in d['rawFrames']}) == 36
assert len(d['atlases']) == 12 and len({r['path'] for r in d['atlases']}) == 3
for r in d['rawFrames'] + d['atlases']:
    assert sha(O / r['path']) == r['sha256']
for a in d['atlases']:
    atlas = Image.open(O / a['path']).convert('RGBA')
    assert atlas.size == (2304, 1280)
    for r in [r for r in d['rawFrames'] if r['clip'] == a['clip'] and r['direction'] == a['direction']]:
        x, y, w, h = a['rects'][r['index']]
        assert atlas.crop((x, y, x+w, y+h)).tobytes() == pixels(O / r['path'])
for key in ['frameSize', 'root', 'sourceScale', 'footprint', 'rootCell', 'directionFootprints', 'directionRootCells', 'projection', 'facingPolicy', 'registration']:
    assert manifest[key] == original[key], key
cut = Image.open(O / d['project']).convert('RGBA').resize((164,147), Image.Resampling.LANCZOS)
unique, apng = {}, {}
for clip in manifest['clips']:
    cid = clip['id']
    assert clip['frames'] == 12 and clip['fps'] == 12 and clip['frameOrder'] == list(range(12)) and clip['loop'] == (cid == 'idle') and not clip['static']
    assert set(clip['directions']) == set('NESW')
    assert len(set(json.dumps(e, sort_keys=True) for e in clip['directions'].values())) == 1
    hashes = []
    for i in range(12):
        image = cut.copy()
        opacity = (i+1)/12 if cid == 'appear' else 1-i/12 if cid == 'fade' else 1
        if cid == 'appear':
            scale = .5 + .5 * math.sin((i+1)/12 * math.pi/2)
            image = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)
        if opacity < 1:
            image.putalpha(image.getchannel('A').point(lambda a: round(a * max(0, opacity))))
        canvas = Image.new('RGBA', (384,640))
        center = (192, (248-52-3*math.sin(i/12*math.tau))*2)
        canvas.alpha_composite(image, (round(center[0]-image.width/2), round(center[1]-image.height/2)))
        actual = C / 'raw' / f'{cid}-S-{i:04d}.png'
        assert canvas.tobytes() == pixels(actual), (cid, i)
        hashes.append(hashlib.sha256(pixels(actual)).hexdigest())
    unique[cid] = len(set(hashes))
    seq = Image.open(C / 'previews' / f'{cid}-S.png')
    assert seq.n_frames == 12
    for i in range(12):
        seq.seek(i)
        assert abs(seq.info['duration'] - 1000/12) < 1e-8
        assert seq.convert('RGBA').tobytes() == pixels(C / 'raw' / f'{cid}-S-{i:04d}.png')
    apng[cid] = {'frames':12, 'fps':12, 'exactRawFrames':True, 'APNGPlays':seq.info.get('loop')}
receipt = json.loads((C / 'native-capture-evidence.json').read_text())
runtime = Image.open(C / 'previews/native-runtime-entrance-wait-playback.png')
rr = next(r for r in receipt['files'] if r['key'] == 'native-runtime-entrance-wait-playback')
assert runtime.n_frames == 48
for i in range(48):
    runtime.seek(i)
    assert abs(runtime.info['duration'] - 1000/12) < 1e-8
    assert hashlib.sha256(runtime.convert('RGBA').tobytes()).hexdigest() == rr['pixelSHA256ByFrame'][i]
for name in ['restaurant_view.gd', 'art_book.gd', 'typography.gd']:
    assert sha(ROOT / 'prototypes/sushi-loop/godot/scripts' / name) == sha(O / 'source/round01/resources/context/runtime-scripts' / name) == sha(C / 'native-context/scripts' / name)
raw = Image.open(O / 'inputs/target.png').convert('RGBA')
assert pixels(O / d['project']) == raw.crop((174,633,798,1194)).tobytes()
assert sha(O / 'inputs/target.png') == sha(O / 'source/round01/resources/target.png')
report = {'asset':'bubble-puzzled', 'candidatePacketSHA256':sha(C/'packet.json'), 'briefSHA256':sha(O/'brief.json'), 'criteriaSHA256':sha(O/'reviews/proposedcriteria.json'), 'sourceClosureFiles':len(closure), 'declaredFileCount':len(paths), 'relocatedOutputFilesByteEqual':len(replayed), 'all144AliasFramesAnd12AtlasEntriesVerified':True, 'actualFrames':36, 'actualAtlases':3, 'uniqueFrames':unique, 'independentOriginalAnimationMathMatchesAll36':True, 'sourceCropExactAndRawTargetUnchanged':True, 'all3ClipAPNGExactRawFramesAt12fps':apng, 'actualGodotAPNG48FramesAt12fpsMatchCaptureReceipt':True, 'copiedRuntimeScriptsByteEqualCurrentProductionScripts':True, 'replayRequiresOnlySourceClosure':not(clone/'inputs').exists() and not(clone/'reviews').exists(), 'sealedSourceCandidateFilesUnmodified':True, 'replayOutputHashMapSHA256':hashlib.sha256(json.dumps(replayed,sort_keys=True,separators=(',',':')).encode()).hexdigest(), 'commands':log}
shutil.rmtree(clone)
cwd.rmdir()
report['temporaryReplayFilesRetained'] = False
(A/'independent-replay.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k != 'commands'},indent=2))
