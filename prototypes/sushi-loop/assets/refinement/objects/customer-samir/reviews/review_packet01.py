import json,pathlib,hashlib,collections
from PIL import Image,ImageDraw,ImageChops
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir');C=P/'candidates/round-01';R=P/'reviews/round-01-evidence';R.mkdir(exist_ok=True)
a=json.loads((C/'packet.json').read_text());checked={};errors=[]
for group in ['files','candidateRenders','previews']:
 for alias,ref in a[group].items():
  path=(C/ref['path']).resolve()
  if path not in checked:
   checked[path]=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else 'MISSING'
  if checked[path]!=ref['sha256']:errors.append([group,alias,str(path),ref['sha256'],checked[path]])
old=json.loads((C/'delivery.json').read_text());new=json.loads((C/'delivery.snapshot.json').read_text())
print('DELIVERY KEYS',list(old),list(new))
changed=[k for k in set(old)|set(new) if old.get(k)!=new.get(k)];print('DELIVERY CHANGED FIELDS',changed)
frames=[];atlases=[];clips=[]
for mode in ['main','runtime']:
 for atlas in sorted((C/mode/'atlases').glob('*.png')):
  state,dr=atlas.stem.rsplit('-',1);im=Image.open(atlas).convert('RGBA');atlas_errors=[]
  for i in range(12):
   fp=C/mode/'frames'/state/dr/(str(i).zfill(2)+'.png');frame=Image.open(fp).convert('RGBA');rect=(i%6*384,i//6*640,i%6*384+384,i//6*640+640)
   if ImageChops.difference(im.crop(rect),frame).getbbox(alpha_only=False):atlas_errors.append(i)
   frames.append({'path':str(fp),'sha256':checked[fp.resolve()],'frame':i,'state':state,'direction':dr,'mode':mode})
  atlases.append({'path':str(atlas),'size':im.size,'errors':atlas_errors})
 # Every clip sheet contains all12frames at logical size over each background, split to3rowsx4frames when needed.
 for state in sorted(p.name for p in (C/mode/'frames').iterdir() if p.is_dir()):
  for dr in ['S','E','N','W']:
   for bgname,bg in [('gray',(110,110,110)),('light',(244,240,230)),('dark',(24,28,36))]:
    sheet=Image.new('RGB',(6*192,2*330),bg);d=ImageDraw.Draw(sheet)
    for i in range(12):
     fp=C/mode/'frames'/state/dr/(str(i).zfill(2)+'.png');f=Image.open(fp).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);sheet.paste(f,(i%6*192,i//6*330+10),f);d.text((i%6*192+3,i//6*330),f'{state} {dr} {i:02}',fill='white' if bgname!='light' else 'black')
    sheet.save(R/(state+'-'+dr+'-'+bgname+'.jpg'),quality=93)
report={'packetSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'uniqueReferencedFiles':len(checked),'referenceEntries':sum(len(a[k]) for k in ['files','candidateRenders','previews']),'errors':errors,'previewAliases':len(a['previews']),'uniquePreviews':len({v['path'] for v in a['previews'].values()}),'atlasCount':len(atlases),'frameCount':len(frames),'atlases':atlases,'frames':frames,'deliveryAdapterChangedTopLevelFields':changed,'oldDeliverySHA256':hashlib.sha256((C/'delivery.json').read_bytes()).hexdigest(),'snapshotSHA256':hashlib.sha256((C/'delivery.snapshot.json').read_bytes()).hexdigest()}
(R/'packet-byte-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('BYTEAUDIT',report['uniqueReferencedFiles'],'errors',len(errors),'frames',len(frames),'atlases',len(atlases),'atlasPixelErrors',sum(len(v['errors']) for v in atlases))
print('Previewdimensions',[(k,Image.open(C/v['path']).size) for k,v in a['previews'].items() if v['path'].endswith('.png')][-18:])
