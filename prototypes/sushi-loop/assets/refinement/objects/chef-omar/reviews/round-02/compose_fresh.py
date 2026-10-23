from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
R=Path(__file__).resolve().parent;C=R.parents[1]/'candidates/round-02';records=[]
def bg(im):
 b=Image.new('RGBA',im.size,'#e5e2d8');b.alpha_composite(im);return b.convert('RGB')
def sheet(name,cases):
 out=Image.new('RGB',(1536,680*((len(cases)+3)//4)),'#e5e2d8');dr=ImageDraw.Draw(out)
 for j,(p,label) in enumerate(cases):out.paste(bg(Image.open(p).convert('RGBA')),(j%4*384,j//4*680+28));dr.text((j%4*384+5,j//4*680+7),label,fill='#20343c')
 out.save(R/(name+'.png'))
for food,hold,load in [('salmon','hold','load'),('cucumber','hold-cucumber','load-cucumber')]:
 rr=json.loads((R/f'fresh-{food}-candidate.json').read_text());sheet('fresh-'+food+'-holds',[(R/r['path'],f'fresh native {hold} {r["direction"]}05') for r in rr if r['clip']==hold and r['angle'] is None]);sheet('fresh-'+food+'-other',[(R/r['path'],f'fresh native {r["clip"]} {r["direction"]}{r["index"]:02d}') for r in rr if r['clip']!=hold]);sheet('fresh-'+food+'-turn',[(R/r['path'],f'fresh native {food} {r["angle"]:+g}degrees') for r in rr if r['angle'] is not None])
 for r in rr:
  if r['angle'] is not None:continue
  p=C/('runtimeVariants' if food=='cucumber' else '')/'frames'/f'{r["clip"]}-{r["direction"]}'/f'{r["index"]:03d}.png';a=np.asarray(Image.open(R/r['path'])).astype(np.int16);b=np.asarray(Image.open(p)).astype(np.int16);records.append({'fresh':r['path'],'shipping':str(p.relative_to(C)),'maxRGBAChannelDifference255':int(np.abs(a-b).max()),'differentPixels':int(np.any(a!=b,axis=2).sum())})
 cases=[]
 for mode in ['approved','candidate']:
  pp=R/'fresh'/food/mode
  for d in ['N','S']:cases.append((pp/f'{hold}-{d}-005.png',f'{food} {mode} {d}05'))
 sheet('fresh-'+food+'-approved-vs-candidate',cases)
(R/'fresh-rgba-comparison.json').write_text(json.dumps(records,indent=2)+'\n');print('fresh comparisons',len(records),'maxRGBA',max(r['maxRGBAChannelDifference255'] for r in records))
