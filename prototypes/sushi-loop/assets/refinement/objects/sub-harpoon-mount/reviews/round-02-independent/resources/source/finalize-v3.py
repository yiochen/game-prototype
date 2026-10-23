"""Final immutable disclosure adapter. No source or rendered pixel changes."""
import pathlib,json,copy,hashlib
P=pathlib.Path(__file__).resolve().parent;E=P.parent.parent;C=E/'candidates/round-02';D=E/'delivery/v3';D.mkdir(parents=True,exist_ok=True)
assert not (D/'delivery.json').exists()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
r=copy.deepcopy(json.loads((E/'delivery/v2/replay-disclosure.json').read_text()));old=r['qualification'];r['qualification']='45/52 replay frames contain sparse native RGB rounding residuals of1–2/255 in at most9pixels/frame; maximum wholeframe channel RMS .0027199634. All52 alpha channels and registered silhouette bounds are exact. Original delivered native/published frames are unchanged; no repair or warping.';dump(D/'replay-disclosure.json',r)
cam=json.loads((C/'camera-native.json').read_text());original=json.loads((E/'inputs/source-camera.json').read_text());ledger=json.loads((C/'standalone-audit.json').read_text())
camera_precision={'sourceCameraMatrixMaximumError':max(abs(a-b) for x,y in zip(cam['camera']['worldMatrix'],original['camera']['worldMatrix']) for a,b in zip(x,y)),'sourceProjectionMatrixMaximumError':max(abs(a-b) for x,y in zip(cam['camera']['projectionMatrix'],original['camera']['projectionMatrix']) for a,b in zip(x,y)),'actualMeasuredNativeRoot':ledger['renders'][0]['projectedRootPixels'],'originalMeasuredNativeRoot':original['calibration']['root'],'nativeRootMaximumErrorPixels':max(abs(a-b) for a,b in zip(ledger['renders'][0]['projectedRootPixels'],original['calibration']['root'])),'qualification':'No fitted camera or root correction. The saved registered camera uses the source world matrix, own fixed ortho scale and source pixel aspect; Blender matrix/Euler roundtrip and calibrated shift differ only at native floating precision. Actual matrix/projection/root measurements are retained.'}
dump(D/'camera-precision.json',camera_precision)
v=copy.deepcopy(json.loads((E/'delivery/v2/validation.json').read_text()));v['replayDisclosure']='delivery/v3/replay-disclosure.json';v['cameraPrecision']='delivery/v3/camera-precision.json';v['limitations']=[x for x in v['limitations'] if x!=old];v['limitations'] += [r['qualification'],camera_precision['qualification']];dump(D/'validation.json',v)
a=copy.deepcopy(json.loads((E/'delivery/v2/native-audit.json').read_text()));a['validation']='delivery/v3/validation.json';a['replayDisclosure']='delivery/v3/replay-disclosure.json';a['cameraPrecision']='delivery/v3/camera-precision.json';dump(D/'native-audit.json',a)
d=copy.deepcopy(json.loads((E/'delivery/v2/delivery.json').read_text()));d['version']=3;d['supersedes']='delivery/v2/delivery.json';d['validation']='delivery/v3/validation.json';d['nativeRecords']['audit']='delivery/v3/native-audit.json';d['limitations']=v['limitations'];d['replayDisclosure']='delivery/v3/replay-disclosure.json';d['cameraPrecision']='delivery/v3/camera-precision.json'
paths={x['path'] for x in d['resources']}
for folder in [E/'source',E/'delivery/v2']:
 for f in folder.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts:paths.add(str(f.relative_to(E)))
for n in ['replay-disclosure.json','camera-precision.json','validation.json','native-audit.json']:paths.add(str((D/n).relative_to(E)))
d['resources']=[{'path':s,'sha256':sha(E/s)} for s in sorted(paths)];dump(D/'delivery.json',d)
m={'asset':'sub-harpoon-mount','round':'round-02','deliveryVersion':3,'project':{'path':d['project'],'sha256':sha(E/d['project'])},'delivery':{'path':'delivery/v3/delivery.json','sha256':sha(D/'delivery.json')},'validation':{'path':'delivery/v3/validation.json','sha256':sha(D/'validation.json')},'canonicalNeutralResourceSHA256':d['mainAdoption']['canonicalNeutralResourceFingerprint'],'resourceCount':len(d['resources']),'resources':d['resources'],'approval':False,'nextStep':'Root seals exact round-02 with this delivery/v3 JSON, then original independent judge reviews. No helper delivery.snapshot.json was created by editor.'};dump(D/'handoff-manifest.json',m)
assert all(sha(E/x['path'])==x['sha256'] for x in d['resources'])
assert all((E/x['path']).stat().st_size<100_000_000 for x in d['resources'])
print(json.dumps({'sourceSHA256':m['project']['sha256'],'deliverySHA256':m['delivery']['sha256'],'validationSHA256':m['validation']['sha256'],'evidenceManifestSHA256':sha(D/'handoff-manifest.json'),'canonicalNeutralResourceSHA256':m['canonicalNeutralResourceSHA256'],'resourceCount':m['resourceCount'],'cameraPrecision':camera_precision},indent=2))
