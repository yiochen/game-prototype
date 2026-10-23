"""Bind the final editor handoff without creating a review or sealing packet."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-01'
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
delivery=read(OBJ/'delivery-round01-editor.json');groups={};records=[]
for name,path in delivery['previews'].items():
    p=OBJ/path;h=sha(p);groups.setdefault(h,[]).append(path);records.append({'name':name,'path':path,'sha256':h,'size':list(Image.open(p).size)})
write(OUT/'visual-preview-map.json',{'pathBase':'object folder','records':records,'hashIdenticalAliases':[{'sha256':h,'paths':ps} for h,ps in groups.items() if len(ps)>1],'inspectionClaim':'Technical path/hash mapping only. The original independent judge must actually inspect every distinct image and truthfully list every packet-relative declared path.'})
ledger=read(OUT/'consumer/capture-ledger.json');pairs=[]
for a,b in zip(ledger['modes'][0]['captures'],ledger['modes'][1]['captures']):
    assert (a['direction'],a['size'],a['phase'],a['background'])==(b['direction'],b['size'],b['phase'],b['background'])
    aa=np.asarray(Image.open(OUT/a['screenshot']['path'])).astype(int);bb=np.asarray(Image.open(OUT/b['screenshot']['path'])).astype(int);diff=np.abs(aa-bb)
    pairs.append({'full':a['screenshot'],'shell':b['screenshot'],'decodedDifferentPixels':int(np.any(diff>0,axis=2).sum()),'maxChannelDifference':int(diff.max())})
local=read(OUT/'local-join-measurements.json');modeLocal=[]
for rec in local['actualCSSBackgroundComparisons']:
    if rec['mode']!='full-chromium':continue
    di,sz,ph=rec['direction'],rec['cell'],rec['phase'];paths=[]
    for mode in ledger['modes']:
        r=next(r for r in mode['captures'] if r['direction']==di and r['size']==sz and r['phase']==ph and r['background']=='#f2f0e8');paths.append(r['screenshot']['path'])
    aa,bb=[np.asarray(Image.open(OUT/p).convert('RGB')).astype(int) for p in paths];pick=np.asarray(Image.open(OUT/rec['mask']))==255;diff=np.abs(aa-bb)
    modeLocal.append({'direction':di,'cell':sz,'phase':ph,'port':rec['port'],'mask':rec['mask'],'pixels':int(pick.sum()),'maxRGBDifference':int(diff[pick].max()),'meanRGBDifference':float(diff[pick].mean()),'changedPixels':int((np.any(diff>0,axis=2)&pick).sum()),'screenshots':paths})
write(OUT/'consumer/mode-comparison.json',{'comparison':'All actual paired full Chromium and headless-shell CSS screenshots; no controls or repaired pixels.','pairs':pairs,'totalChangedPixels':sum(p['decodedDifferentPixels'] for p in pairs),'finiteLocalNeighborhoodComparisons':modeLocal,'maxLocalRGBDifference':max(r['maxRGBDifference'] for r in modeLocal),'limits':'Actual mode differences retained, including large fractional outer/silhouette precision deltas and broad color rounding. Separate actual CSS light/dark finite-local tests record background-independent opaque interiors. No equal-extent control, render repair or runtime helper change. Visual seam assessment remains independent.'})
replay=read(OUT/'saved-source-replay-comparison.json');residual=[]
for rec in replay['comparisons']:
    if not rec['decodedDifferentPixels']:continue
    aa=np.asarray(Image.open(OUT/rec['path'])).astype(int);bb=np.asarray(Image.open(OUT/rec['sourceReplay'])).astype(int);ys,xs=np.where(np.any(aa!=bb,axis=2))
    residual.extend({'path':rec['path'],'pixel':[int(x),int(y)],'submittedRGBA':aa[y,x].tolist(),'replayRGBA':bb[y,x].tolist()} for y,x in zip(ys,xs))
validation=read(OUT/'validation.json');top=read(OUT/'native-topology.json')
validation['measurements']['finiteExteriorEvaluatedVertexCount']=top['finiteExteriorContainment']['evaluatedVertices'];validation['measurements']['finiteExteriorOverhangVertices']=top['finiteExteriorContainment']['count']
validation['consumerModeComparison']='candidates/round-01/consumer/mode-comparison.json'
validation['observedResiduals']={'savedNativeReplay':residual,'nativeIndependentLocalRGBMax':max(r['nativeIndependentRGBMax'] for r in local['nativeVsIndependent']),'browserModesLocalRGBMax':max(r['maxRGBDifference'] for r in modeLocal),'browserModesWholeScreenshotRGBMax':max(r['maxChannelDifference'] for r in pairs),'handling':'Raw files retained unchanged. No local visual defect waiver or editor approval is issued.'}
write(OUT/'validation.json',validation)
delivery['resources']=[{'path':str(p.relative_to(OBJ)),'sha256':sha(p)} for p in sorted(BASE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
write(OBJ/'delivery-round01-editor.json',delivery)
files=[]
for folder in [BASE,OUT]:
    for p in sorted(folder.rglob('*')):
        if p.is_file() and p.name not in ['editor-handoff-manifest.json','packet.json'] and '__pycache__' not in p.parts:files.append(p)
files.append(OBJ/'delivery-round01-editor.json')
assert all(p.stat().st_size<100_000_000 for p in files)
assert all(sha(OBJ/r['path'])==r['sha256'] for r in delivery['resources'])
manifest={'asset':'reef-corner','round':'round-01','status':'Immutable editor handoff awaiting root seal and original independent judge','pathBase':'object folder','sourceSHA256':sha(BASE/'round-01.blend'),'delivery':{'path':'delivery-round01-editor.json','sha256':sha(OBJ/'delivery-round01-editor.json')},'frozenInputs':{'brief.json':sha(OBJ/'brief.json'),'inputs/root-native-contract.json':sha(OBJ/'inputs/root-native-contract.json'),'inputs/target.png':sha(OBJ/'inputs/target.png'),'source/resources/canonical-middle.blend':sha(BASE/'resources/canonical-middle.blend')},'files':[{'path':str(p.relative_to(OBJ)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files],'fileCount':len(files),'totalBytes':sum(p.stat().st_size for p in files),'maxFileBytes':max(p.stat().st_size for p in files),'previewCount':len(delivery['previews']),'editorSelfApproval':False,'nextStep':'Root may seal these exact bytes using delivery-round01-editor.json; original independent judge inspects all declared candidate and preview paths. No production/family approval is inferred.'}
write(OUT/'editor-handoff-manifest.json',manifest)
print(json.dumps({'manifestSHA256':sha(OUT/'editor-handoff-manifest.json'),'deliverySHA256':sha(OBJ/'delivery-round01-editor.json'),'sourceSHA256':sha(BASE/'round-01.blend'),'files':len(files),'bytes':manifest['totalBytes'],'maxFileBytes':manifest['maxFileBytes'],'observedResiduals':validation['observedResiduals']},indent=2))
