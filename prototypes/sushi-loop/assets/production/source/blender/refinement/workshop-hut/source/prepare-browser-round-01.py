import json,hashlib,shutil
from pathlib import Path
B=Path(__file__).resolve().parents[1];S=B/'source';R=S/'resources';BR=R/'browser';O=B/'candidates/round-01';FIX=S/'browser';FIX.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
root=B.parents[3]
# Exact live modules, not reimplementations; esbuild bundles unchanged copies for static browser proof.
for name in ['sprite-layout.js','world-sprite-raster.js']:shutil.copyfile(root/'wireframe'/name,BR/name)
records={}
for d in 'NESW':
 for asset,round_,clip in [('dock-floor','round-04','static'),('dock-entry','round-06','static')]:
  exact=B.parent/asset/'candidates'/round_/'atlases'/f'{clip}-{d}.png';dest=BR/f'{asset}-{clip}-{d}.png'
  if dest.exists():shutil.move(dest,BR/f'native-context-reference-{asset}-{d}.png')
  shutil.copyfile(exact,dest);records[str(dest.relative_to(B))]={'path':str(exact),'sha256':sha(exact),'role':'exact candidate wholeframe atlas, no rerender'}
 # Standalone reviewed candidate hut bytes.
 p=O/'atlases'/f'static-{d}.png';records[str(p.relative_to(B))]={'sha256':sha(p),'role':'own actual native capture'}
# Own standalone camera vs the derived reference metadata are explicit, not inferred from raster bounds.
objects=[]
for asset,frame,anchor,footprint,clips in [
 ('workshop-hut',[192,448],[96,352],[1,1],['static']),
 ('dock-floor',[448,480],[224,256],[3,3],['static']),
 ('dock-entry',[192,352],[96,248],[1,1],['static']),
 ('submarine-yellow',[320,384],[160,288],[1,1],['dock-ready']),
 ('customer-rosa',[192,320],[96,248],[1,1],['stand']),
 ('dock-cover',[736,704],[368,480],[3,3],['covered','uncover'])]:
 obj={'id':asset,'kind':'prop','footprint':footprint,'frameSize':frame,'root':anchor,'sourceScale':2,'clips':[]}
 for clip in clips:
  dirs={}
  for d in 'NESW':
   image=f'{asset}-{clip}-{d}.png' if asset!='workshop-hut' else f'../../../candidates/round-01/atlases/static-{d}.png'
   dirs[d]={'image':image,'frames':1,'sourceScale':2,'frameSize':frame,'root':anchor,'columns':1,'rows':1,'rects':[[0,0,frame[0]*2,frame[1]*2]]}
  obj['clips'].append({'id':clip,'fps':12,'frames':1,'loop':False,'directions':dirs})
 objects.append(obj)
rosa=json.load(open(B/'inputs/paired-native/customer-rosa-approved-catalog-object.json'))
rosa['clips']=[c for c in rosa['clips'] if c['id']=='stand']
for direction,entry in rosa['clips'][0]['directions'].items():
 exact=root/'assets/production'/entry['image'];dest=BR/f'published-rosa-stand-{direction}.png';shutil.copyfile(exact,dest);entry['image']=dest.name;records[str(dest.relative_to(B))]={'path':str(exact),'sha256':sha(exact),'role':'actual current approved published Rosa stand atlas, original35degree authored projection'}
objects=[rosa if ob['id']=='customer-rosa' else ob for ob in objects]
current=json.load(open(root/'assets/production/library.json'));sub=next(x for x in current['objects'] if x['id']=='submarine-yellow');sub['clips']=[c for c in sub['clips'] if c['id']=='dock-ready']
for direction,entry in sub['clips'][0]['directions'].items():
 exact=root/'assets/production'/entry['image'];dest=BR/f'published-submarine-dock-ready-{direction}.png';shutil.copyfile(exact,dest);entry['image']=dest.name;records[str(dest.relative_to(B))]={'path':str(exact),'sha256':sha(exact),'role':'actual current published submarine atlas; authored projection/sourceScale unchanged; old supportgap diagnostic'}
objects=[sub if ob['id']=='submarine-yellow' else ob for ob in objects]

manifest={'objects':objects,'sources':records,'renderer':{'sprite-layout.js':sha(BR/'sprite-layout.js'),'world-sprite-raster.js':sha(BR/'world-sprite-raster.js')},'nativeSampling':'Whole native regions assembled by actual paintWorldRaster after common sizing, smoothing false; displayed full canvas ordinary filtering.','humanReference':'Actual current published approved Rosa stand atlas, authored35degree character projection, original frame/root/scale unchanged. Native physical context uses exact approved model under environment projection; no body pixel identity claim.','oldCoverFrames':[0,5,11]}
(BR/'inputs.json').write_text(json.dumps(manifest,indent=2));print(manifest['renderer'])
