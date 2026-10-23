from pathlib import Path
import PIL
PIL.__path__.append(str(Path(__file__).resolve().parent/'python-new/PIL'))
from PIL import Image,ImageChops,ImageStat,ImageDraw
import json,struct,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE.parent/'evidence';C=ROOT/'candidates/round-01'
def delta(a,b):
 d=ImageChops.difference(a.convert('RGBA'),b.convert('RGBA'));hist=d.histogram();return {'maximumChannelDelta':max(i%256 for i,n in enumerate(hist)if n),'differentChannels':sum(n for i,n in enumerate(hist)if i%256)}
proof={'playbacks':{},'wholeFrameReductions':[],'atlasFrames':[],'closure':[],'savedSourceReplay':[],'consumer':[]}
for d in ['N','E','S','W']:
 apng=Image.open(C/f'idle-{d}.png');data=(C/f'idle-{d}.png').read_bytes();at=8;delays=[]
 while at<len(data):
  n=struct.unpack('>I',data[at:at+4])[0];kind=data[at+4:at+8];block=data[at+8:at+8+n]
  if kind==b'fcTL':delays.append(list(struct.unpack('>HH',block[20:24])))
  at+=12+n
 phases=[]
 for i in range(apng.n_frames):
  apng.seek(i);frame=apng.convert('RGBA');target=Image.open(C/f'frames/idle/{d}/{i:03}.png').convert('RGBA');phases.append({'index':i,**delta(frame,target)})
  raw=Image.open(C/f'native/idle/{d}/{i:03}.png').convert('RGBA');proof['wholeFrameReductions'].append({'direction':d,'index':i,**delta(raw.resize(target.size,Image.Resampling.LANCZOS),target)})
  atlas=Image.open(C/f'atlases/idle-{d}.png').convert('RGBA');rect=(i%6*384,i//6*960,(i%6+1)*384,(i//6+1)*960);proof['atlasFrames'].append({'direction':d,'index':i,**delta(atlas.crop(rect),target)})
 proof['playbacks'][d]={'frames':apng.n_frames,'size':apng.size,'loop':apng.info.get('loop'),'exactDelayNumeratorDenominator':delays,'phaseDecodedPixelComparisons':phases}
 proof['closure'].append({'direction':d,**delta(Image.open(C/f'native/idle/{d}/000.png'),Image.open(C/f'native-closure/idle/{d}/012.png'))})
for d in ['S','E']:
 source=OUT.parent/'replay/candidates/round-01/lookdev-v02/native/idle'/d/'000.png';proof['savedSourceReplay'].append({'direction':d,**delta(Image.open(source),Image.open(C/f'native/idle/{d}/000.png'))})
for f in ['phone-detail','thumbnail-control','registered-context']:
 for suffix in ['', '-native-canvas']:
  proof['consumer'].append({'fixture':f,'layer':'nativeCanvas'if suffix else'actualCSS',**delta(Image.open(C/f'consumer-v02/full-chromium-{f}{suffix}.png'),Image.open(C/f'consumer-v02/headless-shell-{f}{suffix}.png'))})
(OUT/'independent-pixel-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
# Actual browser screenshot phase identification, independently compared to each exact APNG source phase.
P=OUT/'playback-actual-css';ledger=json.load(open(P/'actual-css-playback.json'));mapping=[];expected={}
for d in ['N','E','S','W']:
 expected[d]=[]
 for i in range(12):
  frame=Image.open(C/f'frames/idle/{d}/{i:03}.png').convert('RGBA').resize((192,480),Image.Resampling.LANCZOS);back=Image.new('RGBA',frame.size,'#263e43');back.alpha_composite(frame);expected[d].append(back.convert('RGB'))
for r in ledger['samples']:
 im=Image.open(P/r['path']).convert('RGB');row={'path':r['path'],'elapsedMs':r['elapsedMs'],'directions':{}}
 for k,d in enumerate(['N','E','S','W']):
  frame=im.crop((k*192,0,(k+1)*192,480));scores=[sum(ImageStat.Stat(ImageChops.difference(frame,e)).sum)for e in expected[d]];rank=sorted(range(12),key=lambda i:scores[i]);row['directions'][d]={'closestPhase':rank[0],'absoluteRGBError':scores[rank[0]],'secondClosestPhase':rank[1],'secondError':scores[rank[1]],'cropSHA256':hashlib.sha256(frame.tobytes()).hexdigest()}
 mapping.append(row)
summary={d:sorted(set(r['directions'][d]['closestPhase']for r in mapping))for d in ['N','E','S','W']}
(P/'phase-identification.json').write_text(json.dumps({'method':'Closest absoluteRGB difference against each independently decoded registered APNG phase, uniformly LANCZOS logical-sized and composited on same gray background. Browser ordinary CSS filter differs slightly; rank and exact hashes retained.','observedPhases':summary,'samples':mapping},indent=2)+'\n')
sheet=Image.new('RGB',(1536,1024),'#263e43');draw=ImageDraw.Draw(sheet)
for i,r in enumerate(mapping[:16]):
 frame=Image.open(P/r['path']).convert('RGB').resize((768,480),Image.Resampling.LANCZOS);tile=frame.resize((384,240),Image.Resampling.LANCZOS);x=i%4*384;y=i//4*256;sheet.paste(tile,(x,y+16));draw.text((x+3,y+2),f"{r['elapsedMs']} ms N/E/S/W phases"+','.join(str(r['directions'][d]['closestPhase'])for d in ['N','E','S','W']),fill='white')
sheet.save(P/'actual-temporal-filmstrip.png')
print('APNG decoded48 exact',all(x['differentChannels']==0 for d in proof['playbacks'].values()for x in d['phaseDecodedPixelComparisons']))
print('reductions exact',all(x['differentChannels']==0 for x in proof['wholeFrameReductions']),'atlas exact',all(x['differentChannels']==0 for x in proof['atlasFrames']))
print('closures',proof['closure'],'replay',proof['savedSourceReplay'],'actual playback phases',summary)
