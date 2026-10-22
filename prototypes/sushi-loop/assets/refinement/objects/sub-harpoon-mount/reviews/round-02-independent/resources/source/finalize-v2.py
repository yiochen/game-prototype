"""Immutable v2 delivery adapter: explicit native replay residual and all4 main view alias.
Leaves v1 and every source/render byte intact.
"""
from PIL import Image,ImageChops,ImageStat,ImageDraw
import pathlib,json,hashlib,copy,sys,PIL,subprocess
P=pathlib.Path(__file__).resolve().parent;E=P.parent.parent;C=E/'candidates/round-02';D=E/'delivery/v2';D.mkdir(parents=True,exist_ok=True)
assert not (D/'delivery.json').exists(),'Versioned immutable handoff already exists'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
replay=json.loads((C/'decoded-replay-audit.json').read_text());rows=[]
for r in replay['renders']:
 a=Image.open(E/r['path']).convert('RGBA');b=Image.open(E/r['original']).convert('RGBA');dif=ImageChops.difference(a,b);ext=dif.getextrema()
 rows.append({'clip':r['clip'],'direction':r['direction'],'sourceFrame':r['sourceFrame'],'exactRGBA':r['exactRGBA'],'exactAlpha':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'maxChannelDifference':[x[1] for x in ext],'changedPixels':sum(1 for px in dif.getdata() if any(px)),'differenceRMS':r['differenceRMS'],'alphaBoundsReplay':r['alphaBoundsReplay'],'alphaBoundsOriginal':r['alphaBoundsOriginal']})
disclosure={'method':'Full52 replay from reopened editable standalone source with the same native recipe. No builders, source changes, image correction or warp. Compare decoded native RGBA channel bytes, not only PNG file hashes.','exactRGBACount':sum(r['exactRGBA'] for r in rows),'totalFrames':52,'allAlphaBytesExact':all(r['exactAlpha'] for r in rows),'allAlphaBoundsExact':all(r['alphaBoundsReplay']==r['alphaBoundsOriginal'] for r in rows),'maximumNativeChannelDifference':[max(r['maxChannelDifference'][i] for r in rows) for i in range(4)],'maximumChangedPixelsPerFrame':max(r['changedPixels'] for r in rows),'maximumWholeFrameChannelRMS':max(max(r['differenceRMS']) for r in rows),'qualification':'45/52 replay frames have sparse1/255 RGB rounding residuals; all52 alpha channels and registered silhouettes are exact. Original delivered native/published frames remain unchanged. This is retained renderer replay residual, not repaired imagery.','frames':rows}
dump(D/'replay-disclosure.json',disclosure)
sheet=Image.new('RGB',(1280,414),'#9ca7ac');dr=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
 dr.text((i*320+8,8),d+' neutral · static preliminary main',fill='#243645');dr.text((i*320+8,21),'Other upgrades PROVISIONAL',fill='#243645');fr=Image.open(C/'mounted'/f'idle-{d}'/'000.png').resize((320,384),Image.Resampling.LANCZOS);sheet.paste(fr,(i*320,30),fr)
sheet.save(D/'mounted-neutral-all4.png')
env={'python':sys.version,'Pillow':PIL.__version__,'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0],'nativeExecutable':'/opt/homebrew/bin/blender','nativeVersion':'5.2.2 LTS','browserRuntime':'Exact snapshotted package records under reviews/preparation/resources/runtime; bundled consumer-bundle.js is self-contained and copied exact source layout/raster modules are retained.'}
dump(D/'runtime-environment.json',env)
v=copy.deepcopy(json.loads((E/'delivery/v1/validation.json').read_text()));v['replayDisclosure']='delivery/v2/replay-disclosure.json';v['checks']['all52ReplayAlphaBytesExact']=disclosure['allAlphaBytesExact'];v['checks']['all52ReplayAlphaBoundsExact']=disclosure['allAlphaBoundsExact'];v['checks']['maximumNativeReplayChannelDifference']=disclosure['maximumNativeChannelDifference'];v['checks']['maximumNativeReplayChangedPixelsPerFrame']=disclosure['maximumChangedPixelsPerFrame'];v['checks']['maximumNativeReplayWholeFrameChannelRMS']=disclosure['maximumWholeFrameChannelRMS'];v['limitations'].append(disclosure['qualification']);dump(D/'validation.json',v)
audit=copy.deepcopy(json.loads((E/'delivery/v1/native-audit.json').read_text()));audit['validation']='delivery/v2/validation.json';audit['replayDisclosure']='delivery/v2/replay-disclosure.json';dump(D/'native-audit.json',audit)
d=copy.deepcopy(json.loads((E/'delivery/v1/delivery.json').read_text()));d['version']=2;d['supersedes']='delivery/v1/delivery.json';d['validation']='delivery/v2/validation.json';d['nativeRecords']['audit']='delivery/v2/native-audit.json';d['previews']['native-mounted-all4']='delivery/v2/mounted-neutral-all4.png';d['limitations']=v['limitations'];d['replayDisclosure']='delivery/v2/replay-disclosure.json'
paths={r['path'] for r in d['resources']}
for folder in [E/'source',E/'candidates',E/'inputs',E/'delivery/v1']:
 for f in folder.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts and f.name not in ['packet.json','delivery.snapshot.json']:paths.add(str(f.relative_to(E)))
for n in ['replay-disclosure.json','validation.json','native-audit.json','runtime-environment.json','mounted-neutral-all4.png']:paths.add(str((D/n).relative_to(E)))
d['resources']=[{'path':s,'sha256':sha(E/s)} for s in sorted(paths)]
assert all((E/r['path']).stat().st_size<100_000_000 for r in d['resources'])
dump(D/'delivery.json',d)
manifest={'asset':'sub-harpoon-mount','round':'round-02','deliveryVersion':2,'project':{'path':d['project'],'sha256':sha(E/d['project'])},'delivery':{'path':'delivery/v2/delivery.json','sha256':sha(D/'delivery.json')},'validation':{'path':'delivery/v2/validation.json','sha256':sha(D/'validation.json')},'canonicalNeutralResourceSHA256':d['mainAdoption']['canonicalNeutralResourceFingerprint'],'resourceCount':len(d['resources']),'resources':d['resources'],'approval':False,'nextStep':'Root copies exact versioned delivery JSON into a root-owned versioned delivery filename accepted by seal_object, seals round-02 and sends exact packet to original independent judge. No helper delivery.snapshot.json precreated.'}
dump(D/'handoff-manifest.json',manifest)
print(json.dumps({'projectSHA256':manifest['project']['sha256'],'deliverySHA256':manifest['delivery']['sha256'],'validationSHA256':manifest['validation']['sha256'],'evidenceManifestSHA256':sha(D/'handoff-manifest.json'),'nativeCanonicalResourceSHA256':manifest['canonicalNeutralResourceSHA256'],'resources':manifest['resourceCount'],'replayDisclosure':{k:v for k,v in disclosure.items() if k!='frames'}},indent=2))
