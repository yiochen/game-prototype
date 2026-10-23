import json,hashlib,shutil,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;GAME=OBJ.parents[3]; PROD=GAME/'assets/production'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=[];alpha=[];motion={};closures={}
capture=json.loads((HERE/'capture-records.json').read_text());bydir={d:[] for d in 'NESW'}
for r in capture['captureRecords']:bydir[r['direction']].append(r)
(HERE/'published').mkdir(exist_ok=True);(HERE/'sheets').mkdir(exist_ok=True)
cat=json.loads((HERE/'resources/catalog-object.json').read_text());clip=cat['clips'][0]
for direction,records in bydir.items():
 sheet=Image.new('RGB',(1152,736),'#777777');draw=ImageDraw.Draw(sheet)
 atlas=Image.new('RGBA',(2304,1408));frames=[];current=Image.open(PROD/clip['directions'][direction]['image']).convert('RGBA')
 for r in records:
  i=r['index'];raw=Image.open(HERE/r['path']).convert('RGBA');frame=raw.resize((384,704),Image.Resampling.LANCZOS)
  out=HERE/'published'/direction/f'{i:03}.png';out.parent.mkdir(exist_ok=True);frame.save(out)
  rect=clip['directions'][direction]['rects'][i];atlas.alpha_composite(frame,(rect[0],rect[1]));old=current.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
  diff=ImageChops.difference(frame,old);stat=ImageStat.Stat(diff);nz=diff.convert('RGB').getbbox()
  results.append({'direction':direction,'index':i,'replayPublishedSHA256':sha(out),'productionCellSHA256':hashlib.sha256(old.tobytes()).hexdigest(),'sameDecodedRGBA':frame.tobytes()==old.tobytes(),'meanAbsoluteRGBA':stat.mean,'maxAbsoluteRGBA':[x[1] for x in diff.getextrema()],'differenceBBoxRGB':nz})
  a=frame.getchannel('A');bb=a.getbbox();alpha.append({'direction':direction,'index':i,'alphaBounds':bb,'frame':[384,704],'edgeAlphaMax':max(max(a.crop((0,0,384,1)).getdata()),max(a.crop((0,703,384,704)).getdata()),max(a.crop((0,0,1,704)).getdata()),max(a.crop((383,0,384,704)).getdata()))})
  tile=frame.resize((192,352),Image.Resampling.LANCZOS);x=i%6*192;y=i//6*368;sheet.paste(tile,(x,y+16),tile);draw.text((x+4,y+2),f'{direction} frame {i}',fill='white');frames.append(frame)
 atlas.save(HERE/'published'/f'ambient-{direction}.png');sheet.save(HERE/'sheets'/f'all-frames-{direction}.png')
 deltas=[]
 for i in range(12):
  diff=ImageChops.difference(frames[i],frames[(i+1)%12]);deltas.append({'from':i,'to':(i+1)%12,'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'bbox':diff.convert('RGB').getbbox()})
 motion[direction]={'uniqueRGBAFrames':len({hashlib.sha256(x.tobytes()).hexdigest() for x in frames}),'adjacentPixelDifferences':deltas}
 first=records[0]['geometry'];close=capture['closureFrame13'][direction]['geometry'];worst=0
 for a,b in zip(first['objects'],close['objects']):
  for ar,br in zip(a['matrixWorld'],b['matrixWorld']):worst=max(worst,max(abs(x-y) for x,y in zip(ar,br)))
 closures[direction]={'maxObjectMatrixAbsDeltaFrame1To13':worst,'geometryBoundsEqual':first['rawAuthoredBounds']==close['rawAuthoredBounds']}
# All facing comparison, complete registered frames on three backgrounds at logical size.
for bg,label in [('#eeeeee','light'),('#777777','gray'),('#121820','dark')]:
 canvas=Image.new('RGB',(768,376),bg);dr=ImageDraw.Draw(canvas)
 for j,d in enumerate('NESW'):
  im=Image.open(HERE/'published'/d/'006.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);canvas.paste(im,(j*192,24),im);dr.text((j*192+8,8),d,fill='white' if label!='light' else 'black')
 canvas.save(HERE/'sheets'/f'four-view-{label}.png')
write(HERE/'replay-residuals.json',{'method':'Native original 768x1408 RGBA reduced complete frame to384x704 with Pillow LANCZOS, matching recorded publisher method. No crop/fit/repair/recolor. Compare exact published original catalog cells. Renderer version/sample defaults may differ from historical capture.','records':results})
write(HERE/'alpha-motion-measurements.json',{'alphaRecords':alpha,'motion':motion,'loopClosure':closures})
# Freeze actual-used consumer and source records, not unrelated assets.
for f in ['world-sprite-raster.js','sprite-layout.js']:shutil.copy2(GAME/'wireframe'/f,HERE/'resources'/f)
for f in ['world_components.py','publish_captures.py']:shutil.copy2(PROD/'source/blender'/f,HERE/'resources'/f)
for d in 'NESW':shutil.copy2(PROD/clip['directions'][d]['image'],HERE/'resources'/f'original-ambient-{d}.png')
print(json.dumps({'replayFrames':len(results),'sameDecoded':sum(r['sameDecodedRGBA'] for r in results),'worstMean':max(max(r['meanAbsoluteRGBA']) for r in results),'closure':closures},indent=2))
