from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,math
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';C=O/'consumer-world-raster'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def arr(p):return np.array(Image.open(p).convert('RGBA'))
def composite(a,bg):
 f=a[...,3:4]/255;return a[...,:3]*f+np.array(bg)*(1-f)
def stats(delta,mask=None):
 v=delta if mask is None else delta[mask]
 if not v.size:return {'pixels':0,'maxChannelDelta':0,'meanChannelDelta':0,'pixelsAnyChannelDeltaOver5':0}
 if v.ndim==3:v=v.reshape(-1,v.shape[2])
 return {'pixels':int(v.shape[0]),'maxChannelDelta':float(v.max()),'meanChannelDelta':float(v.mean()),'p99ChannelDelta':float(np.percentile(v,99)),'pixelsAnyChannelDeltaOver5':int(np.count_nonzero(v.max(axis=1)>5))}
def sample(a,x,y):return a[int(y),int(x)].tolist()
data=json.loads((C/'cases.json').read_text());before=json.loads((B/'candidates/round-03/metrics.json').read_text());old={r['case']:r for r in before['consumer']['caseMetrics']};records=[]
profile=[[-.5,0],[.5,0],[.5,.67],[.45,1.04],[.31,1.15],[-.31,1.15],[-.45,1.04],[-.5,.67]]
for e in data['evidence']:
 if e['mode']!='independent':continue
 stem=e['case'];a=arr(C/(stem+'-independent.png'));b=arr(C/(stem+'-connected.png'));d=e['direction'];pitch=e['pitch'];px,py=e['phaseX'],e['phaseY'];sc=pitch/128
 mask=Image.new('1',(a.shape[1],a.shape[0]),0);draw=ImageDraw.Draw(mask)
 # Locked 3D port planes projected with the registered basis; no alpha-bound fitting.
 cuts=[]
 for cut in [-.5,.5]:
  points=[]
  for y,z in profile:
   wx,wy={'S':(cut,y),'N':(-cut,-y),'E':(-y,cut),'W':(y,-cut)}[d]
   points.append(((224+128*wx)*sc+px,(384-128*wy-89.6*z)*sc+py))
  if d in 'NS':
   x=points[0][0];ys=[p[1] for p in points];draw.rectangle((math.floor(x)-1,math.ceil(min(ys))+2,math.floor(x)+1,math.floor(max(ys))-2),fill=1);cuts.append(x)
  else:draw.polygon(points,fill=1)
 mask=np.asarray(mask).astype(bool);opaque=mask&(b[...,3]>=250)&(a[...,3]>=250)
 # For transparent screenshots, connected opaque reference is authoritative for coverage loss.
 expectedOpaque=mask&(b[...,3]>=250)
 delta=abs(composite(a,(128,128,128))-composite(b,(128,128,128)))
 alphaDelta=abs(a[...,3].astype(int)-b[...,3].astype(int))
 bg=e['background'];bgRGB={'#808080':(128,128,128),'#f5f2e9':(245,242,233),'#182231':(24,34,49)}.get(bg,(0,0,0))
 foreground=(np.max(abs(b[...,:3].astype(int)-np.array(bgRGB)),axis=2)>2) if bg!='transparent' else b[...,3]>0
 r={'case':stem,'direction':d,'pitch':pitch,'phase':[px,py],'background':bg,'size':[a.shape[1],a.shape[0]],'wholeImage':stats(delta),'foreground':stats(delta,foreground),'projectedJoinRegion':stats(delta,mask),'opaqueJoinRegion':stats(delta,opaque),'alphaMaxDelta':int(alphaDelta.max()),'opaqueReferenceJoinAlphaMaxDelta':int(alphaDelta[expectedOpaque].max()) if expectedOpaque.any() else 0,'independentAlphaMinimumAtOpaqueReferenceJoins':int(a[...,3][expectedOpaque].min()) if expectedOpaque.any() else None,'joinCutColumns':cuts,'worldRasterReady':e['worldRaster']['ready'],'worldRasterError':e['worldRaster']['error'],'independentPNGsha256':sha(C/(stem+'-independent.png')),'connectedPNGsha256':sha(C/(stem+'-connected.png')),'priorSourceOverWholeMax':old[stem]['imageDelta']['maxChannelDelta'] if stem in old else None,'priorSourceOverJoinMax':old[stem]['joinRegionDelta']['maxChannelDelta'] if stem in old else None}
 records.append(r)
# Keep actual worst contexts and explicit old regression samples; all cases remain reproducible in the compact metrics.
keep=set(['N-128-0.25-0.5','N-128-0.5-0.75'])
gray=[r for r in records if r['background']=='#808080']
for d in 'NESW':
 for pitch in [128,32]:
  group=[r for r in gray if r['direction']==d and r['pitch']==pitch];keep.add(max(group,key=lambda r:r['opaqueJoinRegion']['maxChannelDelta'])['case'])
 keep.add(next(r['case'] for r in gray if r['direction']==d and r['pitch']==128 and r['phase']==[0,0]))
keep.add(max([r for r in gray if r['pitch']==47.3],key=lambda r:r['wholeImage']['maxChannelDelta'])['case'])
for bg in ['#f5f2e9','#182231','transparent']:
 for pitch in ([128,32] if bg=='transparent' else [128]):
  keep.add(max([r for r in records if r['background']==bg and r['pitch']==pitch],key=lambda r:r['wholeImage']['maxChannelDelta'])['case'])
for r in records:r['screenshotsRetained']=r['case'] in keep
# Fixed old defect reproduction, actual browser screenshots at exact dimensions.
fixed='N-128-0.25-0.5';aa=Image.open(C/(fixed+'-independent.png')).convert('RGB');bb=Image.open(C/(fixed+'-connected.png')).convert('RGB');sh=Image.new('RGB',(aa.width*2,aa.height+44),'#f5f2e9');sh.paste(aa,(0,44));sh.paste(bb,(aa.width,44));dr=ImageDraw.Draw(sh);dr.text((8,7),'Actual updated SpriteScene: N128 phase(.25,.5); independent left / connected native right',fill='#243c52');dr.text((8,24),'Shared world-native raster before final SVG scaling; unchanged native round03 art.',fill='#243c52');sh.save(O/'consumer-fixed-regression.png')
worst=max(gray,key=lambda r:r['wholeImage']['maxChannelDelta']);stem=worst['case'];aa=Image.open(C/(stem+'-independent.png')).convert('RGB');bb=Image.open(C/(stem+'-connected.png')).convert('RGB');sh=Image.new('RGB',(aa.width*2,aa.height+44),'#f5f2e9');sh.paste(aa,(0,44));sh.paste(bb,(aa.width,44));dr=ImageDraw.Draw(sh);dr.text((8,7),stem+' current whole-image worst; independent left / native right',fill='#243c52');dr.text((8,24),'Residuals are measured over the whole comparison, not only the connector columns.',fill='#243c52');sh.save(O/'consumer-whole-worst.png')
# All four actual phone contexts; keep original dimensions and a separate enlargement of the visible object region.
sh=Image.new('RGB',(960,4*240),'#f5f2e9');dr=ImageDraw.Draw(sh)
for row,d in enumerate('NESW'):
 r=max([r for r in gray if r['direction']==d and r['pitch']==32],key=lambda r:r['opaqueJoinRegion']['maxChannelDelta']);stem=r['case'];aa=Image.open(C/(stem+'-independent.png')).convert('RGB');bb=Image.open(C/(stem+'-connected.png')).convert('RGB');yy=row*240;dr.text((8,yy+7),stem+' actual32 cell pitch: independent / native; enlarged object region at right',fill='#243c52');sh.paste(aa,(8,yy+32));sh.paste(bb,(128,yy+32));sh.paste(aa.crop((0,45,112,115)).resize((336,210),Image.Resampling.NEAREST),(256,yy+26));sh.paste(bb.crop((0,45,112,115)).resize((336,210),Image.Resampling.NEAREST),(604,yy+26))
sh.save(O/'consumer-phone-four-view.png')
# RGBA samples at former full-height cut line and transparent coverage proof.
a=arr(C/(fixed+'-independent.png'));b=arr(C/(fixed+'-connected.png'));samples=[{'pixel':[160,y],'independentRGBA':a[y,160].tolist(),'connectedRGBA':b[y,160].tolist()} for y in [250,300,350,400,440]]
provenance=json.loads((O/'provenance.json').read_text());artUnchanged=all(sha(B/r['path'])==r['sha256'] for r in provenance['nativeArt'])
summary={'artUnchanged':artUnchanged,'dependenciesUnchangedDuringCapture':data['dependenciesUnchanged'],'caseCount':len(records),'allWorldRasterReady':all(r['worldRasterReady']=='true' and not r['worldRasterError'] for r in records),'browserErrors':data['errors'],'maxWholeImageChannelDelta':max(r['wholeImage']['maxChannelDelta'] for r in records),'maxOpaqueJoinChannelDelta':max(r['opaqueJoinRegion']['maxChannelDelta'] for r in records),'maxOpaqueReferenceJoinAlphaDelta':max(r['opaqueReferenceJoinAlphaMaxDelta'] for r in records if r['background']=='transparent'),'worstWholeImage':worst,'formerCutLineSamples':samples,'retainedScreenshotPairs':len(keep),'visualAssessment':'Pending direct editor image inspection and independent visual judge. Metrics are supporting evidence, not approval.'}
metrics={'asset':'rock-wall-middle','round':4,'scope':'Evidence only, native art remains exact round03 bytes','sharedRenderer':'Actual current SpriteScene with world-sprite-raster.js; shared canvas composed on authored world-native grid before one browser scaling/pan step. This is changed renderer code, not the retained old SVG source-over path.','dependencies':data['dependencies'],'summary':summary,'caseMetrics':records,'previousMetrics':'../round-03/metrics.json'}
(O/'metrics.json').write_text(json.dumps(metrics,indent=2));(C/'retained-dom-evidence.json').write_text(json.dumps([e for e in data['evidence'] if e['case'] in keep],indent=2))
for p in C.glob('*.png'):
 if p.name.rsplit('-',1)[0] not in keep:p.unlink()
data['evidence']=[{k:v for k,v in e.items() if k not in ['placements','bounds']} for e in data['evidence']];(C/'cases.json').write_text(json.dumps(data,indent=2))
print(json.dumps(summary,indent=2))
