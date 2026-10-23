from pathlib import Path
import json,sys,hashlib,shutil
from PIL import Image,ImageChops,ImageStat,ImageDraw
base=Path(__file__).resolve().parents[2];res=base/'resources';out=base/'evidence'
stat=[];frames={}
for d in ['N','E','S','W']:
 n=Image.open(out/f'source-native-{d}.png').convert('RGBA');p=n.resize((384,704),Image.Resampling.LANCZOS);p.save(out/f'source-published-{d}.png');frames[d]=p
 a=p.getchannel('A');stat.append({'direction':d,'nativeSize':n.size,'publishedSize':p.size,'alphaBounds':a.getbbox(),'alphaTouchesFrame':any([a.getbbox()[0]==0,a.getbbox()[1]==0,a.getbbox()[2]==p.width,a.getbbox()[3]==p.height])})
orig=Image.open(res/'resource-inputs/original.png').convert('RGBA');rep=frames['S'];diff=ImageChops.difference(orig,rep)
# Exact decoded comparison, including alpha and RGB. Report drift honestly.
hist=diff.histogram();rgb=ImageStat.Stat(diff);comparison={'exactDecodedRGBA':not any(v for i,v in enumerate(hist) if i%256),'meanAbsoluteChannelDifference':rgb.mean,'originalSize':orig.size,'replaySize':rep.size,'differingPixels':sum(a!=b for a,b in zip(orig.getdata(),rep.getdata()))}
canvas=Image.new('RGB',(1592,780),(229,232,232));draw=ImageDraw.Draw(canvas)
for i,d in enumerate(['N','E','S','W']):
 draw.text((i*398+7,12),d,fill=(30,35,40));canvas.paste(frames[d],(i*398+7,44),frames[d]);
canvas.save(out/'source-four-view-published-sheet.png')
logical=Image.new('RGB',(824,404),(224,228,228));draw=ImageDraw.Draw(logical)
for i,d in enumerate(['N','E','S','W']):
 f=frames[d].resize((192,352),Image.Resampling.LANCZOS);draw.text((i*206+6,8),d,fill=(30,35,40));logical.paste(f,(i*206+6,32),f)
logical.save(out/'source-four-view-logical-sheet.png')
inputs=[]
for name in ['original.png','target.png','warm-soft-reference.png','family-concept.png']:
 p=res/'resource-inputs'/name;im=Image.open(p);inputs.append({'name':name,'size':im.size,'alphaBounds':im.convert('RGBA').getchannel('A').getbbox(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
# Runtime closure: freeze only modules actually imported from Pillow, no app/runtime tree.
closure=[]
for m in list(sys.modules.values()):
 p=getattr(m,'__file__',None)
 if p and '/PIL/' in p:
  p=Path(p);dst=res/'python-runtime'/p.parent.name/p.name;dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists():shutil.copy2(p,dst)
  closure.append({'path':str(dst.relative_to(base.parents[1])),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'originalPath':str(p)})
(out/'pixel-analysis.json').write_text(json.dumps({'uniformReduction':'Pillow whole-canvas 4x→2x LANCZOS, no alpha/RGB repair or subject fitting','frames':stat,'originalReplayComparison':comparison,'inputs':inputs,'pillowVersion':Image.__version__,'python':sys.version,'actualUsedPillowClosure':closure},indent=2)+'\n')
print(json.dumps(comparison))
