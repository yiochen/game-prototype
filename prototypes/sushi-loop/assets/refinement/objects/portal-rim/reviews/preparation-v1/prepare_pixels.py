from PIL import Image,ImageChops,ImageStat,ImageDraw
from pathlib import Path
import json,shutil,hashlib
P=Path(__file__).resolve().parent;objectroot=P.parents[1];prod=objectroot.parents[2]/'production'
# Locate via known repository rather than sibling aesthetic evidence.
prod=P.parents[5]/'production'
prod=Path('prototypes/sushi-loop/assets/production').resolve()
cat=json.loads((P/'resources/inputs/catalog-object.json').read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[];residuals={};stats={}
(P/'published').mkdir();(P/'resources/exported-atlases').mkdir()
for facing in ['N','E','S','W']:
 atlas=Image.new('RGBA',(2304,1536));frames=[];rows=[]
 source=prod/'sprites/portal-rim'/('idle-'+facing+'.png');shutil.copy2(source,P/'resources/exported-atlases'/source.name);published=Image.open(source).convert('RGBA')
 for i in range(12):
  raw=Image.open(P/'raw/idle'/facing/f'{i:03d}.png').convert('RGBA');frame=raw.resize((384,768),Image.Resampling.LANCZOS)
  rect=cat['clips'][0]['directions'][facing]['rects'][i];atlas.paste(frame,tuple(rect[:2]));frames.append(frame)
  orig=published.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));diff=ImageChops.difference(frame,orig);hist=diff.histogram();changed=sum(1 for px in diff.getdata() if any(px));a=frame.getchannel('A')
  rows.append({'frame':i,'decodedRGBAExact':not diff.getbbox(),'changedPixels':changed,'maxPerChannel':list(diff.getextrema()),'meanAbsPerChannel':ImageStat.Stat(diff).mean,'alphaBounds':list(a.getbbox()) if a.getbbox() else None,'alphaAtFrameBorder':max(max(a.crop(b).getextrema()) for b in [(0,0,384,1),(0,767,384,768),(0,0,1,768),(383,0,384,768)])})
 atlas.save(P/'published'/('idle-'+facing+'.png'));residuals[facing]=rows
 # All 12 full logical frames. Uniform complete-frame reduction only.
 sheet=Image.new('RGB',(6*192,2*(384+24)),(128,128,128));draw=ImageDraw.Draw(sheet)
 for i,frame in enumerate(frames):
  logical=frame.resize((192,384),Image.Resampling.LANCZOS);x=(i%6)*192;y=(i//6)*408;sheet.paste(logical,(x,y),logical);draw.text((x+4,y+386),f'{facing} idle {i:02d}',fill='white')
 sheet.save(P/'evidence'/f'native-allframes-{facing}.png')
 records.append({'direction':facing,'path':'published/idle-'+facing+'.png','sha256':sha(P/'published'/('idle-'+facing+'.png')),'size':[2304,1536],'columns':6,'rows':2,'rects':cat['clips'][0]['directions'][facing]['rects']})
(P/'published-atlases.json').write_text(json.dumps({'sourceScale':2,'nativeCaptureScale':4,'frame':[192,384],'root':[96,288],'processing':'One uniform whole-frame LANCZOS reduction 768x1536 to384x768. Full original 6x2 cell layout; no fitting/recolor/warp/alphaRGB repair.','atlases':records},indent=2)+'\n')
(P/'source-replay-residuals.json').write_text(json.dumps({'comparison':'Native replay4x uniformly reduced2x against original exported atlas RGBA cells. Different Blender 5.2.2 runtime and source reconstruction may create true raster residuals. Raw4x and original published inputs retained.','pillowVersion':Image.__version__,'facings':residuals},indent=2)+'\n')
print(json.dumps({f:{'allExact':all(r['decodedRGBAExact'] for r in rs),'maxChangedPixels':max(r['changedPixels'] for r in rs),'maxMeanRGBA':[max(r['meanAbsPerChannel'][a] for r in rs) for a in range(4)]} for f,rs in residuals.items()},indent=2))
