from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,math
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-03';C=O/'consumer'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def met(a,b):
 d=np.abs(a.astype(float)-b.astype(float));return {'maxChannelDelta':float(d.max()),'meanChannelDelta':float(d.mean()),'pixelsChannelDeltaOver5':int(np.count_nonzero(d.max(axis=2)>5))}
def rgba(p):return np.array(Image.open(p).convert('RGBA'))
def comp(a,bg):
 f=a[...,3:4]/255;return a[...,:3]*f+np.array(bg)*(1-f)
# Exact replay of canonical renders from the final saved source, without running authoring code.
replay={}
for d in 'NESW':
 a=rgba(O/f'native-static-{d}.png');b=rgba(O/'replay'/f'native-static-{d}.png');replay[d]={'exactRGBA':bool(np.array_equal(a,b)),'canonicalRGBAsha256':hashlib.sha256(a.tobytes()).hexdigest(),'replayRGBAsha256':hashlib.sha256(b.tobytes()).hexdigest(),'size':[a.shape[1],a.shape[0]]}
# Native actual connected single mesh vs independently captured native sprites at registration.
native={}
for d in 'NESW':
 a=rgba(O/f'independent-native-{d}.png');b=rgba(O/f'connected-native-{d}.png');alpha=abs(a[...,3].astype(int)-b[...,3].astype(int))
 native[d]={'alphaMaxDelta':int(alpha.max()),'alphaMeanDelta':float(alpha.mean()),'composites':{k:met(comp(a,bg),comp(b,bg)) for k,bg in {'light':(245,242,233),'gray':(128,128,128),'dark':(24,34,49)}.items()}}
# Actual consumer results, all retained as compact metrics; selectively retain only useful screenshot pairs.
records=[];all_evidence=[]
for name in ['cases.json','background-cases.json','alpha-cases.json']:
 data=json.loads((C/name).read_text());all_evidence+=data['evidence']
 for ev in data['evidence']:
  if ev['mode']!='independent':continue
  stem=ev['case'];p=C/(stem+'-independent.png');q=C/(stem+'-connected.png');a=rgba(p);b=rgba(q)
  pitch=ev['pitch'];vertical=ev['direction'] in 'EW'
  # Actual port-projection cut columns for S/N. E/W cuts project whole Y/Z sections; full-image metric retained.
  if not vertical:
   cuts=[(160/128*pitch+ev['phaseX']),(288/128*pitch+ev['phaseX'])]
   masks=[]
   for cut in cuts:
    x=int(math.floor(cut));lo=max(0,x-1);hi=min(a.shape[1],x+2);masks.append((a[:,lo:hi],b[:,lo:hi]))
   aa=np.concatenate([v[0] for v in masks],axis=1);bb=np.concatenate([v[1] for v in masks],axis=1)
  else:cuts=[];aa=a;bb=b
  r={'case':stem,'direction':ev['direction'],'pitch':pitch,'phase':[ev['phaseX'],ev['phaseY']],'background':ev['background'],'size':[a.shape[1],a.shape[0]],'imageDelta':met(comp(a,(128,128,128)),comp(b,(128,128,128))),'joinRegionDelta':met(comp(aa,(128,128,128)),comp(bb,(128,128,128))),'alphaMaxDelta':int(abs(a[...,3].astype(int)-b[...,3].astype(int)).max()),'joinCutColumns':cuts,'independentPNGsha256':sha(p),'connectedPNGsha256':sha(q)}
  records.append(r)
keep=set()
gray=[r for r in records if r['background']=='#808080']
for d in 'NESW':
 for pitch in [128,32]:
  group=[r for r in gray if r['direction']==d and r['pitch']==pitch]
  worst=max(group,key=lambda r:r['joinRegionDelta']['maxChannelDelta']);keep.add(worst['case'])
 keep.add(next(r['case'] for r in gray if r['direction']==d and r['pitch']==128 and r['phase']==[0,0]))
keep.add(max([r for r in gray if r['pitch']==47.3],key=lambda r:r['joinRegionDelta']['maxChannelDelta'])['case'])
for bg in ['#f5f2e9','#182231','transparent']:
 for pitch in ([128,32] if bg=='transparent' else [128]):
  keep.add(max([r for r in records if r['background']==bg and r['pitch']==pitch],key=lambda r:r['joinRegionDelta']['maxChannelDelta'])['case'])
for r in records:r['screenshotsRetained']=r['case'] in keep
# Labeled actual worst browser pair, preserving screenshots and adding only a presentation label.
worst=max(gray,key=lambda r:r['joinRegionDelta']['maxChannelDelta']);wp=worst['case'];a=Image.open(C/(wp+'-independent.png')).convert('RGB');b=Image.open(C/(wp+'-connected.png')).convert('RGB')
sh=Image.new('RGB',(a.width*2,a.height+54),'#f5f2e9');sh.paste(a,(0,54));sh.paste(b,(a.width,54));dr=ImageDraw.Draw(sh);dr.text((10,8),wp+' actual SpriteScene; left independently published / right connected native',fill='#243c52');dr.text((10,28),'Current source-over consumer shows fractional sampling join lines. Pending shared renderer correction.',fill='#963321');sh.save(O/'consumer-worst-comparison.png')
# Four phone actual worst contexts with a nearest-neighbor inspection enlargement.
sh=Image.new('RGB',(960,4*210),'#f5f2e9');dr=ImageDraw.Draw(sh)
for row,d in enumerate('NESW'):
 r=max([r for r in gray if r['direction']==d and r['pitch']==32],key=lambda r:r['joinRegionDelta']['maxChannelDelta']);stem=r['case'];a=Image.open(C/(stem+'-independent.png')).convert('RGB');b=Image.open(C/(stem+'-connected.png')).convert('RGB');yy=row*210
 dr.text((5,yy+4),stem+' left independent / right native; actual 32px cell pitch and 3x inspection enlargement',fill='#243c52')
 sh.paste(a,(10,yy+28));sh.paste(b,(130,yy+28));sh.paste(a.resize((a.width*3,a.height*3),Image.Resampling.NEAREST).crop((0,0,a.width*3,174)),(260,yy+28));sh.paste(b.resize((b.width*3,b.height*3),Image.Resampling.NEAREST).crop((0,0,b.width*3,174)),(610,yy+28))
sh.save(O/'consumer-phone-worst.png')
# A few exact RGB/alpha cut samples, not a universal numeric appearance threshold.
sample=rgba(C/'N-128-0.25-0.5-independent.png');reference=rgba(C/'N-128-0.25-0.5-connected.png')
examples=[{'pixel':[160,y],'independentRGBA':sample[y,160].tolist(),'connectedRGBA':reference[y,160].tolist()} for y in [250,300,350,400,440]]
metrics={'native':native,'replay':replay,'consumer':{'renderer':'actual unchanged SpriteScene/object-review.jsx and sprite-layout.js','coverageCases':len(records),'caseMetrics':records,'retainedScreenshotPairs':len(keep),'worst':worst,'cutSamples':examples,'finding':'Exact butt-joined image coverage is reduced by source-over at fractional SVG sampling; visible 1-pixel join lines in the current browser. Geometry/profile/albedo are not extended or painted to conceal this.','status':'consumer_fix_required_before_approval'},'sourceSHA256':{n:sha(B/'source/consumer-baseline'/n) for n in ['object-review.jsx','sprite-layout.js']}}
(O/'metrics.json').write_text(json.dumps(metrics,indent=2))
# Trim full DOM evidence to representative cases and keep all case parameters/metrics separately.
(C/'retained-dom-evidence.json').write_text(json.dumps([e for e in all_evidence if e['case'] in keep],indent=2))
for p in C.glob('*.png'):
 stem=p.name.rsplit('-',1)[0]
 if stem not in keep:p.unlink()
for name in ['cases.json','background-cases.json','alpha-cases.json']:
 data=json.loads((C/name).read_text());data['evidence']=[{k:v for k,v in e.items() if k not in ['placements','bounds']} for e in data['evidence']];(C/name).write_text(json.dumps(data,indent=2))
print(json.dumps({'replayAllExact':all(x['exactRGBA'] for x in replay.values()),'consumerCases':len(records),'retainedScreenshotPairs':len(keep),'worst':worst},indent=2))
