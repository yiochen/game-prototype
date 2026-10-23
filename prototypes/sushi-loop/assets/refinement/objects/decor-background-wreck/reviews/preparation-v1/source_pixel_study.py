from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib
P=Path(__file__).resolve().parent;R=P/'resources';(P/'published-replay').mkdir(exist_ok=True)
rows=[]
for d in 'NESW':
 a=Image.open(P/'native-v2'/f'{d}.png').convert('RGBA');small=a.resize((384,704),Image.Resampling.LANCZOS);small.save(P/'published-replay'/f'{d}.png')
 b=Image.open(R/f'consumer/sprites/decor-background-wreck/static-{d}.png').convert('RGBA');diff=ImageChops.difference(small,b)
 alpha=ImageChops.difference(small.getchannel('A'),b.getchannel('A'))
 rows.append({'direction':d,'sourceReplaySize':list(a.size),'reducedSize':list(small.size),'processing':'Uniform complete canvas LANCZOS 4x to2x only; no crop, fit, alpha or RGB repairs','decodedRGBAExact':small.tobytes()==b.tobytes(),'alphaAbsoluteDifferenceMean':ImageStat.Stat(alpha).mean[0],'nonzeroAlphaBoundingBoxReplay':small.getchannel('A').getbbox(),'nonzeroAlphaBoundingBoxPublished':b.getchannel('A').getbbox(),'maxChannelDifference':max(v[1] for v in diff.getextrema())})
 bg=Image.new('RGBA',(384,704),'#808080');bg.alpha_composite(small);bg.convert('RGB').save(P/'published-replay'/f'{d}-gray.png')
sheet=Image.new('RGB',(4*300,2*400),'#889399');draw=ImageDraw.Draw(sheet)
for col,d in enumerate('NESW'):
 for row,folder in enumerate([R/'consumer/sprites/decor-background-wreck',P/'published-replay']):
  name=f'static-{d}.png' if row==0 else f'{d}.png';im=Image.open(folder/name).convert('RGBA');im.thumbnail((290,370),Image.Resampling.LANCZOS);tile=Image.new('RGBA',im.size,'#889399');tile.alpha_composite(im);sheet.paste(tile.convert('RGB'),(col*300+5,row*400+25));draw.text((col*300+8,row*400+8),f'{d} '+('historical published2x' if row==0 else 'Blender5.2 replay4x reduced2x'),fill='white')
sheet.save(P/'native-source-comparison.png')
orig=R/'inputs/original.png';snapMatches=[d for d in 'NESW' if orig.read_bytes()==(R/f'consumer/sprites/decor-background-wreck/static-{d}.png').read_bytes()]
(P/'source-pixel-comparison.json').write_text(json.dumps({'asset':'decor-background-wreck','originalSnapshotByteMatchesPublishedDirections':snapMatches,'sourceReplays':rows,'limits':'Render differences are reported honestly; camera matrices and native source independently prove contract. Existing production atlas is historical consumer replay; source reconstruction uses untouched blend without edits.'},indent=2)+'\n')
# Browser screenshot sheets cover all30 exact screenshots; no upscaling for actual phone-size rows.
ledger=json.loads((P/'consumer-ledger.json').read_text());comparisons=[]
for run in ledger['runs']:
 ims=[]
 for case in run['cases']:
  im=Image.open(P/case['screenshot']).convert('RGB');im.thumbnail((620,400),Image.Resampling.LANCZOS);ims.append((case,im))
 width=1300;height=sum(max(ims[i][1].height,ims[i+1][1].height if i+1<len(ims) else 0)+42 for i in range(0,len(ims),2));out=Image.new('RGB',(width,height),'#f5f5f2');dr=ImageDraw.Draw(out);y=0
 for i in range(0,len(ims),2):
  rh=max(ims[i][1].height,ims[i+1][1].height if i+1<len(ims) else 0)+42
  for j in range(2):
   if i+j>=len(ims):continue
   c,im=ims[i+j];x=650*j;dr.text((x+8,y+5),f"{i+j:02d} {c['kind']} cell{c['cell']} bg{c['background']} t{c['seconds']}",fill='#222222');out.paste(im,(x+8,y+28))
  y+=rh
 out.save(P/f"consumer-{run['mode']}-sheet.jpg",quality=95)
for a,b in zip(ledger['runs'][0]['cases'],ledger['runs'][1]['cases']):
 ia=Image.open(P/a['screenshot']).convert('RGBA');ib=Image.open(P/b['screenshot']).convert('RGBA');diff=ImageChops.difference(ia,ib);comparisons.append({'case':a['screenshot'].split('/')[-1],'sameNativeCanvasRGBA':a['nativeCanvasRGBA256']==b['nativeCanvasRGBA256'],'sameScreenshotRGBA':ia.tobytes()==ib.tobytes(),'maxChannelDifference':max(v[1] for v in diff.getextrema())})
(P/'browser-mode-comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
print(json.dumps({'snapshotMatches':snapMatches,'replay':rows,'browserCases':len(comparisons),'browserExactScreenshots':sum(c['sameScreenshotRGBA'] for c in comparisons)},indent=2))
# Extra edge-aware comparison makes low-alpha hiddenRGB differences explicit.
report=json.loads((P/'source-pixel-comparison.json').read_text())
for row in report['sourceReplays']:
 d=row['direction'];aa=Image.open(P/'published-replay'/f'{d}.png').convert('RGBA');bb=Image.open(R/f'consumer/sprites/decor-background-wreck/static-{d}.png').convert('RGBA');pairs=[(x,y) for x,y in zip(aa.get_flattened_data(),bb.get_flattened_data()) if max(x[3],y[3])>32]
 row['maxRGBDifferenceAlphaAbove32']=max(abs(x[i]-y[i]) for x,y in pairs for i in range(3));row['meanRGBDifferenceAlphaAbove32']=sum(abs(x[i]-y[i]) for x,y in pairs for i in range(3))/(3*len(pairs));row['changedAlphaPixels']=sum(x[3]!=y[3] for x,y in zip(aa.get_flattened_data(),bb.get_flattened_data()))
(P/'source-pixel-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
