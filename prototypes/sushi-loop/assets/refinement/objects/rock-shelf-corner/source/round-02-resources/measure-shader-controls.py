import sys,json,math
from pathlib import Path
RES=Path(__file__).resolve().parent;BASE=RES.parent;sys.path.insert(0,str(BASE/'dependencies/python-library'))
from PIL import Image,ImageChops,ImageStat,ImageDraw
OUT=BASE.parent/'candidates/round-02';E=OUT/'evidence/collar-shader-controls';rows=[]
for port in ['W','N']:
 for d in 'NESW':
  for edge in [1,2,3,4,5]:
   for mode in ['albedo','normal']:
    a=Image.open(E/f'{port}-{d}-edge{edge}-reference-{mode}.png').convert('RGBA');b=Image.open(E/f'{port}-{d}-edge{edge}-candidate-{mode}.png').convert('RGBA');mask=ImageChops.multiply(a.getchannel('A').point(lambda p:255 if p==255 else 0),b.getchannel('A').point(lambda p:255 if p==255 else 0));diff=ImageChops.difference(a,b);rgb=diff.convert('RGB');masked=Image.new('RGB',a.size);masked.paste(rgb,mask=mask);rows.append({'port':port,'direction':d,'edge':edge,'field':mode,'interiorPixels':sum(p==255 for p in mask.getdata()),'maxInteriorRGBDifference':[v[1] for v in masked.getextrema()],'meanInteriorRGBDifference':ImageStat.Stat(rgb,mask).mean})
# Actual all-root shader field controls, reference/candidate side by side.
for mode in ['albedo','normal']:
 sheet=Image.new('RGB',(128*10,148*8),'#909090');dr=ImageDraw.Draw(sheet)
 for ri,(port,d) in enumerate((p,d) for p in ['W','N'] for d in 'NESW'):
  for ci,edge in enumerate([1,2,3,4,5]):
   for k,role in enumerate(['reference','candidate']):
    im=Image.open(E/f'{port}-{d}-edge{edge}-{role}-{mode}.png').convert('RGBA');sheet.paste(im,((ci*2+k)*128,ri*148+20),im)
   dr.text((ci*256+4,ri*148+3),f'{port} {d} edge{edge} ref / candidate',fill='#172539')
 sheet.save(OUT/f'collar-shader-{mode}-all-roots.png')
summary={mode:{'maxInteriorRGBDifference':max(max(r['maxInteriorRGBDifference']) for r in rows if r['field']==mode),'maxMeanInteriorRGBDifference':max(max(r['meanInteriorRGBDifference']) for r in rows if r['field']==mode)} for mode in ['albedo','normal']}
(OUT/'collar-shader-control-results.json').write_text(json.dumps({'method':'Decoded actual rendered controls from linked normalized shader Normal or actual Base Color. Compare only shared fully opaque pixel interiors, preserving edge/mask files separately. W/N, five exposed profile segments, every root rotation. Whole full-collar native sample audit is collar-fields.json.','summary':summary,'samples':rows},indent=2)+'\n');print(summary)
