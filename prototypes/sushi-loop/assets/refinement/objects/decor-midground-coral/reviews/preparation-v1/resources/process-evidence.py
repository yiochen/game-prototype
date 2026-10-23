from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageStat
import json,hashlib
BASE=Path(__file__).parent.parent;RES=BASE/'resources';ev=BASE/'evidence';pub=ev/'published';pub.mkdir(exist_ok=True)
report={'comparison':'Native saved-action replay vs frozen historical published atlases; full-frame LANCZOS 4x to 2x; no fitting or channel repairs','directions':{}}
for direction in ('N','E','S','W'):
 sheet=Image.new('RGBA',(2304,1536));frameimgs=[];contact=Image.new('RGB',(6*192,3*384),(32,72,84));draw=ImageDraw.Draw(contact)
 original=Image.open(RES/f'consumer/sprites/decor-midground-coral/idle-{direction}.png').convert('RGBA')
 diffs=[]
 for i in range(13):
  img=Image.open(ev/f'native/{direction}/{i:03}.png').convert('RGBA');fr=img.resize((384,768),Image.Resampling.LANCZOS);frameimgs.append(fr)
  fr.save(pub/f'{direction}-{i:03}.png')
  if i<12:sheet.paste(fr,((i%6)*384,(i//6)*768))
  thumb=fr.resize((192,384),Image.Resampling.LANCZOS);contact.paste(thumb,((i%6)*192,(i//6)*384),thumb);draw.text(((i%6)*192+3,(i//6)*384+3),f'{direction} f{i+1}'+(' closure' if i==12 else ''),fill='white')
  if i<12:
   old=original.crop(((i%6)*384,(i//6)*768,(i%6+1)*384,(i//6+1)*768));diff=ImageChops.difference(fr,old);diffs.append({'frame':i+1,'identical':all(mx==0 for mn,mx in diff.getextrema()),'diffBBox':diff.getbbox(alpha_only=False),'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'nativeAlphaBBox':img.getchannel('A').getbbox(),'publishedAlphaBBox':fr.getchannel('A').getbbox()})
 sheet.save(pub/f'idle-{direction}.png');contact.save(ev/f'source-{direction}-all-phases.png')
 frameimgs[0].save(ev/f'source-{direction}-playback.gif',save_all=True,append_images=frameimgs[1:12],duration=[83,83,84]*4,loop=0,disposal=2)
 closure=ImageChops.difference(frameimgs[0],frameimgs[12]); report['directions'][direction]={'frames':diffs,'closureFrame13Vs1Identical':all(mx==0 for mn,mx in closure.getextrema()),'closureMaxDiff':max(ImageStat.Stat(closure).extrema[c][1] for c in range(4))}
# all facings at true logical sprite canvas and fixed registration
for background,color in [('dark',(20,49,65)),('gray',(130,133,136)),('light',(237,234,221))]:
 sheet=Image.new('RGB',(4*192,384),color);d=ImageDraw.Draw(sheet)
 for i,di in enumerate(('N','E','S','W')):
  img=Image.open(pub/f'{di}-000.png').convert('RGBA').resize((192,384),Image.Resampling.LANCZOS);sheet.paste(img,(i*192,0),img);d.text((i*192+5,5),di,fill='white' if background=='dark' else 'black')
 sheet.save(ev/f'logical-four-views-{background}.png')
# target/source view side by side, equal complete canvases; no fitting
src=Image.open(RES/'input/original.png').convert('RGBA');target=Image.open(RES/'input/target.png').convert('RGBA');pan=Image.new('RGB',(768,768),(35,60,72));pan.paste(src,(0,0),src);target.thumbnail((384,768),Image.Resampling.LANCZOS);pan.paste(target,(384+(384-target.width)//2,0),target);pan.save(ev/'initial-comparison.png')
(BASE/'raster-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({d:{'historicalExactFrames':sum(f['identical'] for f in v['frames']),'closureIdentical':v['closureFrame13Vs1Identical'],'maxMeanDiff':max(max(f['meanAbsoluteRGBA']) for f in v['frames'])} for d,v in report['directions'].items()},indent=2))
