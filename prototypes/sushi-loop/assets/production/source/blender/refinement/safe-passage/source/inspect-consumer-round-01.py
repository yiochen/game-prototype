"""Measure native-grid/CSS/browser differences honestly and retain complete-frame review sheets."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil,subprocess
import numpy as np
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,value):
 p=OUT/name
 with p.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def diff(a,b):
 x=np.asarray(a,dtype=np.int16);y=np.asarray(b,dtype=np.int16);d=np.abs(x-y)
 return {'differentPixels':int(np.any(d!=0,axis=-1).sum()),'maxChannelDelta':int(d.max()),'meanAbsChannelDelta':float(d.mean()),'alphaExact':bool(np.array_equal(x[:,:,3],y[:,:,3])) if x.shape[2]==4 else None}
manifest=json.loads((OUT/'browser/manifest.json').read_text())
assert len(manifest['records'])==12
assert set(r['browserVersion'] for r in manifest['records'])=={'153.0.8010.12'}
assert all(not r['errors'] and not r['requestFailures'] for r in manifest['records'])
cell_comparisons=[];mode_comparisons=[];css=[]
for direction in 'NESW':
 for index in range(12):
  raw=Image.open(OUT/f'frames/ambient/{direction}/{index:03d}.png').convert('RGBA')
  a=Image.open(OUT/f'browser/chromium/frames/{direction}/{index:03d}.png').convert('RGBA')
  b=Image.open(OUT/f'browser/shell/frames/{direction}/{index:03d}.png').convert('RGBA')
  expected=Image.new('RGBA',(386,706));expected.paste(raw,(1,1))
  assert a.size==b.size==expected.size
  for mode,img in [('chromium',a),('shell',b)]:
   m=diff(expected,img);cell_comparisons.append({'mode':mode,'direction':direction,'index':index,'sourceRect':[1,1,384,704],**m});assert m['alphaExact']
  mode_comparisons.append({'direction':direction,'index':index,**diff(a,b)})
for size in ['logical','phone']:
 for bg in ['light','gray','dark']:
  a=Image.open(OUT/f'browser/chromium/{size}-{bg}.png').convert('RGBA');b=Image.open(OUT/f'browser/shell/{size}-{bg}.png').convert('RGBA')
  css.append({'size':size,'background':bg,'physicalDimensions':list(a.size),**diff(a,b)})
playbacks={}
for mode in ['chromium','shell']:
 p=OUT/f'browser/{mode}/actual-playback.json';data=json.loads(p.read_text());samples=data['samples'];trans=[]
 for s in samples:
  assert len(s['phases'])==4 and len(set(s['phases']))==1
  phase=s['phases'][0]
  if not trans or trans[-1]['phase']!=phase:trans.append({'phase':phase,'atMs':s['timeMs'],'absoluteIndex':s['absoluteIndex']})
 errors=[{'from':a,'to':b} for a,b in zip(trans,trans[1:]) if b['phase']!=(a['phase']+1)%12]
 wraps=[b['atMs'] for a,b in zip(trans,trans[1:]) if a['phase']==11 and b['phase']==0]
 intervals=[b['atMs']-a['atMs'] for a,b in zip(trans,trans[1:])]
 assert data['elapsedMs']>=2200 and len(wraps)>=2 and not errors
 playbacks[mode]={'sampleCount':len(samples),'elapsedMs':data['elapsedMs'],'firstPhase':trans[0]['phase'],'transitions':trans,'wrapTimesMs':wraps,'phaseOrderErrors':errors,'transitionIntervalsMs':intervals,'frameCadenceTargetMs':1000/12,'sourceLog':str(p.relative_to(BASE)),'actualLoopCompleteTwice':True}
 # Complete 25fps source video retained; the time-ordered12fps overview spans the entire video.
 video_rec=next(r for r in manifest['records'] if r['mode']==mode and r.get('video'))
 video=BASE/video_rec['video'];target=OUT/f'sheets/playback-full-{mode}.png'
 subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-i',str(video),'-vf','fps=12,tile=7x6','-frames:v','1',str(target)],check=True)
 partial=OUT/f'sheets/playback-{mode}.png'
 if partial.exists():
  dest=BASE/'source/diagnostics';dest.mkdir(exist_ok=True);shutil.move(partial,dest/f'partial-video-overview-{mode}-v1.png')
 for size in ['logical','phone']:
  rows=[]
  for bg in ['light','gray','dark']:rows.append(Image.open(OUT/f'browser/{mode}/{size}-{bg}.png').convert('RGB'))
  sheet=Image.new('RGB',(rows[0].width,sum(r.height for r in rows)))
  y=0
  for row in rows:sheet.paste(row,(0,y));y+=row.height
  sheet.save(OUT/f'sheets/browser-{mode}-{size}-backgrounds.png')
 # Native-grid canvas contact sheets use each full386x706 canvas reduced uniformly to193x353.
 for direction in 'NESW':
  sheet=Image.new('RGB',(1158,754),'#777777');draw=ImageDraw.Draw(sheet)
  for index in range(12):
   im=Image.open(OUT/f'browser/{mode}/frames/{direction}/{index:03d}.png').convert('RGBA').resize((193,353),Image.Resampling.LANCZOS)
   x=index%6*193;y=index//6*377;bg=Image.new('RGBA',im.size,'#777777');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(x,y+24));draw.text((x+5,y+6),f'{mode} {direction} {index:02d}',fill='#fff')
  sheet.save(OUT/f'sheets/browser-{mode}-{direction}-phases.png')
shutil.copyfile(OUT/'browser/chromium/phone-gray.png',OUT/'previews/phone.png')
apng=[]
for direction in 'NESW':
 p=OUT/f'previews/ambient-{direction}.png';image=Image.open(p);assert image.n_frames==12;dur=[]
 for i in range(12):
  image.seek(i);frame=image.convert('RGBA');expected=Image.open(OUT/f'frames/ambient/{direction}/{i:03d}.png').convert('RGBA')
  assert frame.tobytes()==expected.tobytes();dur.append(image.info.get('duration'))
 apng.append({'path':str(p.relative_to(BASE)),'frames':12,'durationsMs':dur,'totalMs':sum(dur),'decodedEachFrameExactToSubmittedPublishedFrame':True})
report={'asset':'safe-passage','round':'round-01','cellToNativeGridCanvas':cell_comparisons,'betweenModeCanvasFrames':mode_comparisons,'betweenModeCSSScreenshots':css,'playback':playbacks,'APNGPresentationChecks':apng,'nativeSmoothing':{'allCheckedPlansNearestAfterResize':all(not p['nativeSmoothing'] for r in manifest['records'] for p in r['evidence']['plans']),'wholeCanvasCSSImageRendering':sorted({p['cssImageRendering'] for r in manifest['records'] for p in r['evidence']['plans']}),'cssFilter':sorted({p['cssFilter'] for r in manifest['records'] for p in r['evidence']['plans']})},'sourceHelperHashes':manifest['helperHashes'],'limits':['Browser low-alpha RGB premultiplication/encoding can differ from submitted PNG; alpha compared exactly, RGB differences recorded, never repaired.','Whole-frame CSS screenshot differences are separate from native-grid canvas differences.','12fps filmstrips visualize the retained full source video and rAF logs; they do not replace complete sequence cadence/order evidence.','APNG is an optional presentation preview only, never supplied to runtime drawImage.','No Godot/device/full gameplay acceptance or independent aesthetic verdict claimed.']}
write('consumer-comparisons.json',report)
print(json.dumps({'cases':12,'cellAlphaExact':all(r['alphaExact'] for r in cell_comparisons),'betweenModeCanvasExact':all(r['differentPixels']==0 for r in mode_comparisons),'maxNativeRGBDelta':max(r['maxChannelDelta'] for r in cell_comparisons),'css':css,'playback':{k:{x:v[x] for x in ['sampleCount','elapsedMs','wrapTimesMs','phaseOrderErrors']} for k,v in playbacks.items()}}))
