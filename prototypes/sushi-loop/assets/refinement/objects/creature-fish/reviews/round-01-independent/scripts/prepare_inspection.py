from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-01';packet=json.loads((C/'packet.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):p=P/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
assert sha(C/'packet.json')=='5b11c24968df9117ccc35ee5891031a7f08a8eafe6d0d1149aa111c6b3081365'
# Full packet preview/hero alias binding; visual inspection remains separately explicit.
aliases=[]
for group in ['candidateRenders','previews']:
 for name,r in packet[group].items():
  path=C/r['path'];assert sha(path)==r['sha256'];aliases.append({'group':group,'name':name,'packetPath':r['path'],'sha256':r['sha256'],'objectPath':str(path.relative_to(O))})
save('packet-aliases.json',aliases)
# Lossless inspection panels retain full registered logical frame slots at 1:1.
coverage=json.loads((C/'sheet-coverage.json').read_text());panels=[]
for e in coverage:
 if not e['sheet'].endswith('-logical.png'):continue
 path=O/e['sheet'];im=Image.open(path).convert('RGB');assert im.size==(5376,2120)
 for chunk in range(3):
  box=[chunk*1792,0,(chunk+1)*1792,2120];dst=P/'panels'/path.name.replace('.png',f'-phases-{chunk*4:02d}-{chunk*4+3:02d}.png');dst.parent.mkdir(exist_ok=True);im.crop(box).save(dst)
  cells=[c for c in e['cells'] if box[0]<=c['cell'][0]<box[2]]
  panels.append({'path':str(dst.relative_to(O)),'sourceSheet':e['sheet'],'sourceSHA256':sha(path),'cropBox':box,'scale':1,'sourceCells':cells,'note':'Inspection-only lossless split of registered cell columns, no crop/fit/paint of candidate art. Each whole448x512 logical cell remains present at1:1.'})
save('native-sheet-panel-coverage.json',panels)
# Compact current-playback contact sheets: complete existing decoded compositor sheets,
# lossless top/bottom halves keep the four actors per recorded frame useful at original diagnostic scale.
dec=json.loads((C/'playback-decoded-manifest.json').read_text());media=[]
for r in dec['records']:
 path=O/r['sheet'];im=Image.open(path);assert sha(path)==r['sheetSHA256']
 # Existing tiles are 7columns phone /4columns logical, each 360x388 /896x183.
 # Split in half horizontally and vertically without resizing, covering every decoded frame.
 xparts=[(0,im.width//2),(im.width//2,im.width)]
 yparts=[(0,im.height//2),(im.height//2,im.height)]
 for xi,(x0,x1) in enumerate(xparts):
  for yi,(y0,y1) in enumerate(yparts):
   dst=P/'playback-panels'/path.name.replace('.png',f'-{xi}{yi}.png');dst.parent.mkdir(exist_ok=True);im.crop((x0,y0,x1,y1)).save(dst)
   media.append({'path':str(dst.relative_to(O)),'sourceSheet':r['sheet'],'sourceSheetSHA256':r['sheetSHA256'],'sourceVideo':r['originalVideo'],'sourceVideoSHA256':r['originalVideoSHA256'],'mode':r['mode'],'viewport':r['viewport'],'clip':r['clip'],'decodedFrames':r['decodedFrames'],'cropBox':[x0,y0,x1,y1],'scale':1,'note':'Lossless inspection partition of already decoded sheet; all compositor frame cells jointly covered. No new browser/state Cartesian or video redump.'})
save('playback-panel-coverage.json',media)
# Check every submitted whole native->published frame and exact atlas slot independently.
cat=json.loads((C/'consumer-catalog.json').read_text());cat=cat.get('object',cat) if isinstance(cat,dict) else cat
if 'objects' in cat:cat=next(o for o in cat['objects'] if o['id']=='creature-fish')
checks=[]
for clip in cat['clips']:
 for d,e in clip['directions'].items():
  atlas=Image.open(C/'atlases'/Path(e['image']).name).convert('RGBA') if (C/'atlases'/Path(e['image']).name).exists() else Image.open(C/e['image']).convert('RGBA')
  for i,(x,y,w,h) in enumerate(e['rects']):
   pub=C/'published'/clip['id']/d/f'{i:03d}.png';raw=C/'native'/clip['id']/d/f'{i:03d}.png';p=Image.open(pub).convert('RGBA');n=Image.open(raw).convert('RGBA');assert p.size==(896,1024) and n.size==(1792,2048)
   reduced=n.resize(p.size,Image.Resampling.LANCZOS);assert p.tobytes()==reduced.tobytes(),('reduction',clip['id'],d,i);assert p.tobytes()==atlas.crop((x,y,x+w,y+h)).tobytes(),('atlas',clip['id'],d,i)
   alpha=p.getchannel('A');checks.append({'clip':clip['id'],'direction':d,'index':i,'native':str(raw.relative_to(O)),'nativeSHA256':sha(raw),'published':str(pub.relative_to(O)),'publishedSHA256':sha(pub),'wholeCanvasLANCZOSExact':True,'atlasSlotExact':True,'alphaBBox':alpha.getbbox(),'alphaBorderNonzero':bool(alpha.crop((0,0,896,1)).getbbox() or alpha.crop((0,1023,896,1024)).getbbox() or alpha.crop((0,0,1,1024)).getbbox() or alpha.crop((895,0,896,1024)).getbbox())})
save('independent-publication-checks.json',{'packetSHA256':sha(C/'packet.json'),'records':checks,'total':len(checks)})
print('PREPARED',len(panels),'native panels',len(media),'playback panels',len(checks),'exact publication checks')
