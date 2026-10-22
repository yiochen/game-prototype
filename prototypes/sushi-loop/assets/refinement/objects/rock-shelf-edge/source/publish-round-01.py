"""Uniform full-frame publication and compact registered review surfaces."""
from pathlib import Path
import sys,json,hashlib,shutil
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent/'round-01-resources/python-library'))
from PIL import Image,ImageDraw,ImageChops
B=Path(__file__).resolve().parent.parent;S=B/'source';E=B/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof={}
for d in 'NESW':
 raw=Image.open(E/f'native-{d}-4x.png').convert('RGBA');pub=raw.resize((384,704),Image.Resampling.BOX)
 frame=E/f'frames/static/{d}/000.png';frame.parent.mkdir(parents=True,exist_ok=True);pub.save(frame)
 atlas=E/f'atlases/static-{d}.png';atlas.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(frame,atlas)
 for label,wh in [('middle',(384,704)),('strip',(896,1216)),('port-W',(896,1216)),('port-E',(896,1216)),('extended',(1408,1728))]:
  source=E/(f'middle-native-{d}-4x.png' if label=='middle' else f'native-{label}-{d}-4x.png')
  Image.open(source).convert('RGBA').resize(wh,Image.Resampling.BOX).save(E/f'{label}-{d}-2x.png')
 replay=Image.open(E/f'replay-control/native-{d}-4x.png').convert('RGBA')
 def diff(a,b):
  delta=ImageChops.difference(a,b);bands=delta.split();mask=bands[0]
  for bb in bands[1:]:mask=ImageChops.lighter(mask,bb)
  return {'sameDecodedRGBA':a.tobytes()==b.tobytes(),'changedPixels':sum(mask.histogram()[1:]),'maxRGBA':[bb.getextrema()[1] for bb in bands],'bounds':mask.getbbox()}
 proof[d]={'nativeSHA256':sha(E/f'native-{d}-4x.png'),'publishedSHA256':sha(frame),'atlasSHA256':sha(atlas),'wholeFrameBOX':diff(pub,raw.resize((384,704),Image.Resampling.BOX)),'savedSourceNativeReplay':diff(raw,replay),'savedSourcePublishedReplay':diff(pub,replay.resize((384,704),Image.Resampling.BOX)),'assemblies':{}}
 for label in ['strip','port-W','port-E','extended']:
  proof[d]['assemblies'][label]=diff(Image.open(E/f'native-{label}-{d}-4x.png').convert('RGBA'),Image.open(E/f'replay-control/native-{label}-{d}-4x.png').convert('RGBA'))
(E/'publication-replay-proof.json').write_text(json.dumps({'method':'Exact complete RGBA native4x BOX to published2x; no fitting/alpha/RGB changes. One unchanged saved-source replay; all residuals retained.','sourceSHA256':sha(S/'round-01.blend'),'views':proof},indent=2)+'\n')
# Single-file useful source / logical / phone evidence. Rows keep one common scale and crop.
bgsets=[('light','#eef2ed'),('gray','#909090'),('dark','#172539')]
sheet=Image.new('RGB',(1560,2240),'#243044');dr=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
 dr.text((390*i+6,4),d+' published whole frame 384x704',fill='white');im=Image.open(E/f'frames/static/{d}/000.png');back=Image.new('RGBA',im.size,bgsets[0][1]);back.alpha_composite(im);sheet.paste(back.convert('RGB'),(390*i,24))
y=738
for label,bg in bgsets:
 dr.text((6,y),label+' logical128 cell / 192x352 frame',fill='white')
 for i,d in enumerate('NESW'):
  im=Image.open(E/f'frames/static/{d}/000.png').resize((192,352),Image.Resampling.BOX);back=Image.new('RGBA',im.size,bg);back.alpha_composite(im);sheet.paste(back.convert('RGB'),(390*i,y+22))
 y+=382
for label,bg in bgsets:
 dr.text((6,y),label+' phone32 cell / 48x88 frame',fill='white')
 for i,d in enumerate('NESW'):
  im=Image.open(E/f'frames/static/{d}/000.png').resize((48,88),Image.Resampling.BOX);back=Image.new('RGBA',im.size,bg);back.alpha_composite(im);sheet.paste(back.convert('RGB'),(390*i,y+22))
 y+=116
sheet.save(E/'four-view-sheet.png')
# Bind the exact Python files actually loaded, without copying an application runtime.
closure=[]
for mod in list(sys.modules.values()):
 p=Path(getattr(mod,'__file__','') or '.')
 if p.is_file() and 'PIL' in p.parts:
  relative=Path('PIL')/p.name;dest=S/'round-01-resources/python-library'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);closure.append({'module':getattr(mod,'__name__',None),'originalPath':str(p),'path':str(dest.relative_to(B)),'sha256':sha(dest)})
(S/'round-01-resources/python-loaded-modules.json').write_text(json.dumps(closure,indent=2)+'\n')
print(json.dumps({d:v['savedSourceNativeReplay'] for d,v in proof.items()},indent=2))
