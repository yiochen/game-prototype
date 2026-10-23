from pathlib import Path
import json,hashlib,shutil,math
from PIL import Image,ImageChops,ImageStat,ImageDraw
HERE=Path(__file__).resolve().parent; PROD=HERE.parents[4]/'production'
# Directory ancestry is explicit; all publication reads are immutable original atlas inputs.
PROD=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
asset=json.loads((HERE/'resources/inputs/catalog-object.json').read_text());clip=asset['clips'][0]
published=HERE/'published';published.mkdir(exist_ok=True);atlasdir=HERE/'resources/consumer/atlases';atlasdir.mkdir(exist_ok=True)
replaydir=HERE/'resources/consumer/replay-atlases';replaydir.mkdir(exist_ok=True)
results=[]
for d,entry in clip['directions'].items():
 src=PROD/entry['image'];shutil.copy2(src,atlasdir/f'{d}.png');orig=Image.open(src).convert('RGBA');replay=Image.new('RGBA',tuple(entry['atlasSize']))
 folder=published/d;folder.mkdir(exist_ok=True)
 for i,rect in enumerate(entry['rects']):
  raw=Image.open(HERE/'native'/d/f'{i:03d}.png').convert('RGBA');im=raw.resize((384,768),Image.Resampling.LANCZOS);im.save(folder/f'{i:03d}.png');replay.paste(im,(rect[0],rect[1]));old=orig.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));diff=ImageChops.difference(im,old)
  extrema=diff.getextrema();changed=sum(1 for p in diff.getdata() if any(p));mean=list(ImageStat.Stat(diff).mean)
  alpha=im.getchannel('A');bbox=alpha.getbbox();edge={s:sum(1 for v in pixels if v) for s,pixels in [('left',list(alpha.crop((0,0,1,768)).getdata())),('right',list(alpha.crop((383,0,384,768)).getdata())),('top',list(alpha.crop((0,0,384,1)).getdata())),('bottom',list(alpha.crop((0,767,384,768)).getdata()))]}
  results.append({'direction':d,'index':i,'publishedPath':str((folder/f'{i:03d}.png').relative_to(HERE)),'rawSize':list(raw.size),'publishedSize':list(im.size),'replayVsOriginal':{'changedPixels':changed,'maxRGBA':[x[1] for x in extrema],'meanAbsRGBA':mean},'alphaBounds':bbox,'nonzeroAlphaAtEdges':edge,'decodedOriginalSHA256':hashlib.sha256(old.tobytes()).hexdigest(),'decodedReplaySHA256':hashlib.sha256(im.tobytes()).hexdigest()})
 replay.save(replaydir/f'{d}.png')
# Native all48 contact sheet: one whole-frame, uniform reduction to96x192 per cell.
sheet=Image.new('RGB',(12*96,4*212),'#737373');draw=ImageDraw.Draw(sheet)
for row,d in enumerate(['N','E','S','W']):
 for i in range(12):
  im=Image.open(HERE/'native'/d/f'{i:03d}.png').convert('RGBA').resize((96,192),Image.Resampling.LANCZOS);sheet.paste(im,(i*96,row*212),im);draw.text((i*96+2,row*212+194),f'{d} {i}',fill='white')
sheet.save(HERE/'native-all48-sheet.png')
# Source snapshot comparison is exact extraction only.
snapshot=Image.open(HERE/'resources/inputs/original.png').convert('RGBA');sorig=Image.open(atlasdir/'S.png').convert('RGBA').crop((1920,0,2304,768))
measure=json.loads((HERE/'native-measurements.json').read_text())
geom={}
for d in ['N','E','S','W']:
 rows=[r for r in measure['views'] if r['direction']==d]
 geom[d]={}
 for k in ['rawAuthoredWorldBounds','evaluatedWorldBounds']:
  bs=[o[k] for r in rows for o in r['objects'] if o[k]]
  geom[d][k]={'min':[min(b['min'][a] for b in bs) for a in range(3)],'max':[max(b['max'][a] for b in bs) for a in range(3)]}
write(HERE/'replay-analysis.json',{'resampling':'one complete768x1536 RGBA native4x canvas to384x768 published2x using Pillow LANCZOS; no crop/fitting/recolor/alpha repair','pillowVersion':Image.__version__,'sourceSnapshotDecodedExact':snapshot.tobytes()==sorig.tobytes(),'originalAtlasHashes':{d:sha(atlasdir/f'{d}.png') for d in ['N','E','S','W']},'perFrame':results,'allFramesFacingGeometryEnvelope':geom})
