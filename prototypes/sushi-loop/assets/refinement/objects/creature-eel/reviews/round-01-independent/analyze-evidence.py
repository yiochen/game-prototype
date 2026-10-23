from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageChops,ImageStat,ImageDraw
J=Path(__file__).resolve().parent;O=J.parent.parent;C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(O))
def desc(p):return {'path':rel(p),'sha256':sha(p)}
def save(d,p):p.write_text(json.dumps(d,indent=2)+'\n')
def diff(a,b):
 assert a.size==b.size
 d=ImageChops.difference(a,b);rgb=d.convert('RGB'); ab=a.getchannel('A');bb=b.getchannel('A');mask=ImageChops.lighter(ab,bb).point(lambda x:255 if x else 0)
 st=ImageStat.Stat(rgb,mask);h=mask.histogram();visible=sum(h[1:]);dr=rgb.getextrema(); ar=d.getchannel('A').getextrema();px=sum(1 for p,m in zip(rgb.getdata(),mask.getdata()) if m and max(p))
 return {'exactRGBA':a.tobytes()==b.tobytes(),'RGBDifferenceBBox':rgb.getbbox(),'maxRGBChannelDelta':max(v[1] for v in dr),'maxAlphaDelta':ar[1],'meanVisibleRGBChannelDelta':st.mean,'visibleRGBChangedPixels':px,'visibleUnionPixels':visible}
def sheet(items,out,cols=3):
 # All useful RGBA pixels retained at exact original scale; only empty canvas is cropped.
 crops=[];maps=[];w=0;h=0
 for label,p in items:
  im=Image.open(p).convert('RGBA');box=im.getchannel('A').getbbox();crop=im.crop(box);crops.append((label,crop,p,box));w=max(w,crop.width);h=max(h,crop.height)
 w+=24;h+=34
 canvas=Image.new('RGBA',(w*cols,h*math.ceil(len(crops)/cols)),(142,145,150,255));dr=ImageDraw.Draw(canvas)
 for i,(label,im,p,box) in enumerate(crops):
  x=(i%cols)*w+12;y=(i//cols)*h+26;dr.text(((i%cols)*w+8,(i//cols)*h+5),label,fill='white');canvas.paste(im,(x,y));assert canvas.crop((x,y,x+im.width,y+im.height)).tobytes()==im.tobytes();maps.append({**desc(p),'sourceCrop':box,'sheetRect':[x,y,im.width,im.height],'exactUsefulRGBA':True})
 canvas.save(out);return {**desc(out),'size':canvas.size,'coverage':maps,'resampling':'none; alpha useful-pixel crop and exact RGBA paste'}
for d in ['inspection/canvas','inspection/native','inspection/controls']: (J/d).mkdir(parents=True,exist_ok=True)
a=json.loads((J/'native-audit.json').read_text());report={'candidatePacketSHA256':a['candidatePacketSHA256'],'nativeReplays':[],'controlComparisons':[],'canvasPhaseAliases':[],'canvasSheets':[],'cadence':[]}
for r in a['replays']:
 x=Image.open(O/r['path']).convert('RGBA');y=Image.open(O/r['submittedPath']).convert('RGBA');report['nativeReplays'].append({'replay':desc(O/r['path']),'submitted':desc(O/r['submittedPath']),**diff(x,y)})
for i in range(0,len(a['replays']),4):
 rs=a['replays'][i:i+4];report.setdefault('nativeReplaySheets',[]).append(sheet([(r['clip']+' '+r['direction']+' frame '+str(r['frame']),O/r['path']) for r in rs],J/f'inspection/native/replays-{i//4}.png',2))
controls=sorted((C/'controls').rglob('*.png'))
for p in controls:
 clip=p.parts[-3];target=C/'native'/clip/'S'/('000.png' if a['clips'][clip]['loop'] else '011.png');report['controlComparisons'].append({'control':desc(p),'expected':desc(target),**diff(Image.open(p).convert('RGBA'),Image.open(target).convert('RGBA'))})
for i in range(0,len(controls),7):report.setdefault('controlSheets',[]).append(sheet([(p.parts[-3]+' S frame '+str(int(p.stem)+1),p) for p in controls[i:i+7]],J/f'inspection/controls/controls-{i//7}.png'))
b=json.loads((J/'browser-replay.json').read_text());other={(f['clip'],f['facing'],f['frame']):f for panel in b[1]['panels'] for f in panel['phaseFiles']}
for panel in b[0]['panels']:
 pairs=list(dict.fromkeys((f['clip'],f['facing']) for f in panel['phaseFiles']))
 for clip,facing in pairs:
  fs=sorted([f for f in panel['phaseFiles'] if (f['clip'],f['facing'])==(clip,facing)],key=lambda f:f['frame']);assert [f['frame'] for f in fs]==list(range(12))
  report['canvasSheets'].append(sheet([(clip+' '+facing+' phase '+str(f['frame']+1),O/f['path']) for f in fs],J/f'inspection/canvas/{clip}-{facing}.png'))
 for f in panel['phaseFiles']:
  g=other[(f['clip'],f['facing'],f['frame'])];same=Image.open(O/f['path']).convert('RGBA').tobytes()==Image.open(O/g['path']).convert('RGBA').tobytes();assert same;report['canvasPhaseAliases'].append({'chromium':desc(O/f['path']),'shell':desc(O/g['path']),'decodedRGBAIdentical':same})
for mode in b:
 for panel in mode['panels']:
  for pair in dict.fromkeys((f['clip'],f['facing']) for f in panel['phaseFiles']):
   clip,facing=pair;f0=next(f for f in panel['phaseFiles'] if (f['clip'],f['facing'])==pair);loop=f0['loop'];seq=[(t['seconds'],next(f['frame'] for f in t['frames'] if (f['clip'],f['facing'])==pair)) for t in panel['timeline']];expected=all(frame==(int(max(0,t)*12)%12 if loop else min(11,int(max(0,t)*12))) for t,frame in seq)
   transitions=[{'seconds':t,'frame':f} for n,(t,f) in enumerate(seq) if n==0 or seq[n-1][1]!=f];dwell=[transitions[i+1]['seconds']-transitions[i]['seconds'] for i in range(len(transitions)-1)];boundary=[{'seconds':t['seconds'],'frame':next(f['frame'] for f in t['frames'] if (f['clip'],f['facing'])==pair),'digest':next(f['visiblePositionRGBAFNV32'] for f in t['digests'] if (f['clip'],f['facing'])==pair)} for t in panel['boundary']]
   report['cadence'].append({'mode':mode['id'],'panel':panel['panel'],'clip':clip,'facing':facing,'loop':loop,'RAFCount':len(seq),'actualElapsed':panel['actualElapsed'],'allFramesMatch12fpsRule':expected,'distinctVisiblePhases':len(set(f for _,f in seq)),'transitions':transitions,'minDwell':min(dwell),'maxDwell':max(dwell),'boundary':boundary})
report['nativeResidualInterpretation']='Clean saved-source rerenders, same recipe and exact registered canvas; visible RGB quantization residuals explicitly measured, no bit-exact rerender bar. No geometric or color adjustment was applied.'
report['playbackInterpretation']='Real requestAnimationFrame wall clock progression for 2.2 seconds per panel per actual browser mode, 12 complete canvas phase witnesses per actor, exact decoded aliases across modes; visual sheets inspect all 144 distinct witnesses. Boundary calls supplement full RAF; no APNG drawImage or sparse video claim.'
save(report,J/'evidence-analysis.json')
print(json.dumps({'nativeReplayCount':len(report['nativeReplays']),'nativeMaxRGBDelta':max(x['maxRGBChannelDelta'] for x in report['nativeReplays']),'nativeMaxAlphaDelta':max(x['maxAlphaDelta'] for x in report['nativeReplays']),'controls':len(controls),'controlMaxRGBDelta':max(x['maxRGBChannelDelta'] for x in report['controlComparisons']),'controlMaxAlphaDelta':max(x['maxAlphaDelta'] for x in report['controlComparisons']),'canvasExactModeAliases':len(report['canvasPhaseAliases']),'canvasSheets':len(report['canvasSheets']),'cadenceAllPass':all(x['allFramesMatch12fpsRule'] and x['distinctVisiblePhases']==12 for x in report['cadence'])},indent=2))
