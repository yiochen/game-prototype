"""Whole-frame BOX publication and inspection sheets, no art repair."""
from pathlib import Path
import json,hashlib,shutil,sys
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-04'
def write(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for d in 'NESW':
 native=O/f'native/static/{d}/000.png';im=Image.open(native).convert('RGBA');assert im.size==(768,1408)
 pub=im.resize((384,704),Image.Resampling.BOX);dest=O/f'frames/static/{d}/000.png';dest.parent.mkdir(parents=True,exist_ok=True);pub.save(dest)
 atlas=O/f'atlases/static-{d}.png';atlas.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(dest,atlas)
 records.append({'direction':d,'native':str(native.relative_to(P)),'published':str(dest.relative_to(P)),'nativeSHA256':sha(native),'publishedSHA256':sha(dest),'nativeSize':list(im.size),'publishedSize':list(pub.size),'nativeRoot':[384,992],'publishedRoot':[192,496],'method':'uniform whole-frame BOX, no RGB/alpha edits','alphaBounds':list(pub.getchannel('A').getbbox()),'outerEdgeAlphaMax':max(max(pub.getchannel('A').crop(box).getextrema()) for box in [(0,0,384,1),(0,703,384,704),(0,0,1,704),(383,0,384,704)])})
for name in [f'joins/native-{d}.png' for d in 'NESW']+['context/native-parallel.png']:
 src=O/name;im=Image.open(src);im.resize((im.width//2,im.height//2),Image.Resampling.BOX).save(src.with_name(src.stem+'-published.png'))
cam=json.loads((O/'native-camera.json').read_text());cam['captureScale']=2;cam['publishedFrame']=[384,704];cam['nativeSourceRecord']='native-camera.json';cam['publication']='uniform full-frame BOX4x to2x';cam['calibration']={k:[q/2 for q in v] for k,v in cam['calibration'].items()};write('published-camera.json',cam)
write('publication.json',{'records':records,'nativeFilter':.01,'resampling':'Pillow BOX whole-frame','pillowVersion':Image.__version__,'edits':'none','nativeMeasuredRoots':{q['direction']:q['measuredRoot'] for q in json.loads((O/'native-validation.json').read_text())['views']},'rootToleranceNote':'Actual per-direction roots are retained here and in native-validation.json. Calibrated integer native root384,992 and published192,496 are metadata; no image shift is performed.'})
# Compact shared full-canvas evidence, labels never baked into output art.
bgs=[('light',(239,239,229,255)),('gray',(122,137,148,255)),('dark',(19,27,44,255))]
sheet=Image.new('RGB',(4*208,3*382),(231,235,237));dr=ImageDraw.Draw(sheet)
for row,(label,bg) in enumerate(bgs):
 for col,d in enumerate('NESW'):
  im=Image.open(O/f'frames/static/{d}/000.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);tile=Image.new('RGBA',(192,352),bg);tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(col*208+8,row*382+24));dr.text((col*208+8,row*382+6),f'{d} / {label} / cell128',fill=(15,25,35))
sheet.save(O/'four-view-sheet.png')
comp=Image.new('RGB',(624,382),(221,227,229));dr=ImageDraw.Draw(comp)
for i,(label,path) in enumerate([('Actual original',P/'inputs/original.png'),('Fixed target (aesthetic)',P/'inputs/target.png'),('Native round04 S',O/'frames/static/S/000.png')]):
 im=Image.open(path).convert('RGBA');im.thumbnail((192,352),Image.Resampling.LANCZOS);tile=Image.new('RGBA',(192,352),(239,239,229,255));tile.alpha_composite(im,((192-im.width)//2,(352-im.height)//2));comp.paste(tile.convert('RGB'),(i*208+8,24));dr.text((i*208+8,6),label,fill=(10,20,30))
comp.save(O/'style-comparison.png')
write('preview-notes.json',{'style-comparison':'Each complete source canvas uniformly displayed inside192x352 cell; target is aesthetic only and is not registered. No candidate art was rescaled or shifted for publication.','four-view-sheet':'Published full frames reduced whole-frame BOX to logical1x for inspection on light/gray/dark; no per-view treatment.'})
# Freeze only modules actually imported by this publication driver, with their actual paths/hashes.
loaded=[]
for name,mod in sorted(sys.modules.items()):
 f=getattr(mod,'__file__',None)
 if f and ('/PIL/' in f):
  q=Path(f);loaded.append({'module':name,'path':str(q),'sha256':sha(q),'bytes':q.stat().st_size})
write('python-runtime-used.json',{'executable':sys.executable,'version':sys.version,'modules':loaded,'runtimePolicy':'record exact externally bundled runtime; no application tree copy, no frozen bytecode writes'})
print(json.dumps({'published':4,'nativeRepeatReductions':5,'sheets':2}))
