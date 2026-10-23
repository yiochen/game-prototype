import sys,json,argparse,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'resources/python-pillow'))
from PIL import Image,ImageChops,ImageStat,ImageDraw
ap=argparse.ArgumentParser();ap.add_argument('--variant',required=True);a=ap.parse_args();V=P/a.variant
out=V/'packed';out.mkdir(exist_ok=True)
def summarize(im):
 im=im.convert('RGBA');alpha=im.getchannel('A');data=list(alpha.getdata());w,h=im.size;deficits=[(i%w,i//w,255-v) for i,v in enumerate(data) if v<255];cols={};rows={}
 for x,y,d in deficits:cols[str(x)]=cols.get(str(x),0)+1;rows[str(y)]=rows.get(str(y),0)+1
 border={'left':im.crop((0,0,1,h)),'right':im.crop((w-1,0,w,h)),'top':im.crop((0,0,w,1)),'bottom':im.crop((0,h-1,w,h))}
 return {'size':[w,h],'alphaRange':alpha.getextrema(),'nonOpaqueCount':len(deficits),'deficitBBox':ImageChops.invert(alpha).getbbox(),'deficitRows':rows,'deficitColumns':cols,'firstDeficits':deficits[:20],'lastDeficits':deficits[-20:],'borders':{k:{'rgbaExtrema':v.getextrema(),'rgbaMean':ImageStat.Stat(v).mean} for k,v in border.items()},'rgbaSHA256':hashlib.sha256(im.tobytes()).hexdigest()}
reports=[]
for direction in 'NESW':
 sheet=Image.new('RGBA',(1536,512))
 for phase in (0,3):
  name=direction+'-'+str(phase).zfill(3)+'.png';raw=Image.open(V/'raw-single'/name).convert('RGBA');packed=raw.resize((256,256),Image.Resampling.LANCZOS);packed.save(out/name)
  sheet.paste(packed,(phase%6*256,phase//6*256))
  native=Image.open(V/'raw-native-patch'/name).convert('RGBA');nativePacked=native.resize((768,768),Image.Resampling.LANCZOS);nativePacked.save(out/('native-patch-'+name))
  independent=Image.new('RGBA',(768,768))
  for y in range(3):
   for x in range(3):independent.alpha_composite(packed,(256*x,256*y))
  independent.save(out/('independent-patch-'+name))
  rows={'direction':direction,'phase':phase,'raw':summarize(raw),'packed':summarize(packed),'nativePatch':summarize(nativePacked),'independentPatch':summarize(independent)}
  strips={}
  for axis in ('x','y'):
   for edge in (256,512):
    box=(edge-2,4,edge+2,764) if axis=='x' else (4,edge-2,764,edge+2)
    strips[axis+str(edge)]={'native':summarize(nativePacked.crop(box)),'independent':summarize(independent.crop(box))}
  rows['internalJoinStrips']=strips;reports.append(rows)
 sheet.save(out/('study-scroll-'+direction+'.png'))
canvas=Image.new('RGB',(4*400,2*448),'#eee');draw=ImageDraw.Draw(canvas)
for di,direction in enumerate('NESW'):
 for ri,phase in enumerate((0,3)):
  name=direction+'-'+str(phase).zfill(3)+'.png';im=Image.open(out/('independent-patch-'+name)).convert('RGBA');bg=Image.new('RGBA',im.size,(20,24,30,255));bg.alpha_composite(im);canvas.paste(bg.convert('RGB').resize((384,384),Image.Resampling.LANCZOS),(di*400+8,ri*448+40));draw.text((di*400+8,ri*448+8),a.variant+' '+direction+' phase'+str(phase),fill='black')
canvas.save(out/'independent-overview-dark.png')
(V/'pixel-report.json').write_text(json.dumps({'variant':a.variant,'resampling':'Full512→256 LANCZOS unchanged','samples':reports},indent=2)+'\n')
print(json.dumps({r['direction']+str(r['phase']):{'raw':r['raw']['alphaRange'],'packed':r['packed']['alphaRange'],'packedNonOpaque':r['packed']['nonOpaqueCount'],'independentNonOpaque':r['independentPatch']['nonOpaqueCount'],'nativeInternalJoinNonOpaque':{k:v['native']['nonOpaqueCount'] for k,v in r['internalJoinStrips'].items()}} for r in reports},indent=2))
