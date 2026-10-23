from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageStat
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metrics(a,b):
 d=ImageChops.difference(a,b);return {'maxRGBA':[x[1] for x in d.getextrema()],'changedPixels':sum(any(p) for p in d.get_flattened_data()),'meanAbsRGBA':list(ImageStat.Stat(d).mean)}
def comp(im,c):
 b=Image.new('RGBA',im.size,c);return Image.alpha_composite(b,im)
res=[]
for d in ['N','E','S','W']:
 for i in range(12):
  a=Image.open(H/f'native/{d}/{i:03d}.png').convert('RGBA');b=Image.open(C/f'native/enter/{d}/{i:03d}.png').convert('RGBA');aa=a.resize((384,768),Image.Resampling.LANCZOS);bb=Image.open(C/f'frames/enter/{d}/{i:03d}.png').convert('RGBA');alpha=ImageChops.lighter(a.getchannel('A'),b.getchannel('A'));diff=ImageChops.difference(a,b);where=[(p[3],q[3]) for p,q,z in zip(a.get_flattened_data(),b.get_flattened_data(),diff.get_flattened_data()) if any(z)]
  opaque=ImageChops.darker(a.getchannel('A'),b.getchannel('A')).point(lambda x:255 if x==255 else 0);od=Image.new('RGBA',a.size);od.paste(diff,(0,0),opaque)
  res.append({'direction':d,'index':i,'rawDifferingPixelAlphaPairs':sorted(set(where)),'rawChangedPixels':len(where),'rawOpaqueDifference':{'maxRGBA':[x[1] for x in od.getextrema()]},'publishedComposites':{name:metrics(comp(aa,color),comp(bb,color)) for name,color in [('light','#f3eee4'),('gray','#777777'),('dark','#132033')]}})
native=json.loads((H/'native-measurements.json').read_text());fixed=[o['name'] for o in native['views'][0]['supportSections']];stable={name:all(next(s['rootRelativeMatrix'] for s in r['supportSections'] if s['name']==name)==next(s['rootRelativeMatrix'] for s in native['views'][0]['supportSections'] if s['name']==name) for r in native['views']) for name in fixed}
report=json.loads((H/'consumer-report.json').read_text());canvas=[];screenshotcomparisons=[]
for b in report['browserModes']:
 for r in b['nativeCanvas']:
  actual=Image.open(H/r['path']).convert('RGBA');assert actual.size==(386,770);frame=Image.open(C/f"frames/enter/{r['direction']}/{r['frame']:03d}.png").convert('RGBA');expected=Image.new('RGBA',(386,770));expected.paste(frame,(1,1));delta=ImageChops.difference(actual,expected);opaque=ImageChops.darker(actual.getchannel('A'),expected.getchannel('A')).point(lambda x:255 if x==255 else 0);od=Image.new('RGBA',actual.size);od.paste(delta,(0,0),opaque)
  canvas.append({'mode':b['id'],'direction':r['direction'],'index':r['frame'],'actualCanvas':r['path'],'sha256':sha(H/r['path']),'smoothing':r['smoothing'],'fullCanvasDecodedSHA256':hashlib.sha256(actual.tobytes()).hexdigest(),'maxRGBA':[x[1] for x in delta.getextrema()],'opaqueMaxRGBA':[x[1] for x in od.getextrema()],'alphaExact':actual.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),'fullFrameRegistration':'Fixed expected frame is at native guard offset1,1; no silhouette fit.'})
 for r in b['screenshots']:
  a=Image.open(H/'consumer'/r['file']).convert('RGBA');submitted=Image.open(C/'consumer'/r['file']).convert('RGBA');screenshotcomparisons.append({'mode':b['id'],'path':'consumer/'+r['file'],'submitted':'candidates/round-01/consumer/'+r['file'],'metrics':metrics(a,submitted),'viewport':r['viewport'],'dpr':r['dpr']})
(H/'evidence-analysis.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'sourceSHA256':sha(O/'source/round-01.blend'),'rendererResiduals':res,'supportStableAll48WithinFloatTolerance':stable,'all48ApertureRaysClear':all(q['hit'] is None for r in native['views'] for q in r['apertureRays']),'all48FiniteSupportAreaPositive':all(q['xyConvexHullArea']>0 for r in native['views'] for q in r['supportSections']),'all48RimSupportIntersections':all(q['continuousRimIntersectionPairs']>0 for r in native['views'] for q in r['supportRimIntersections']),'independentActualRAFCanvas':canvas,'independentCSSVsSubmittedSameMode':screenshotcomparisons,'currentConsumerErrorScope':{b['id']:b['errors'] for b in report['browserModes']},'limits':'Native source/capture replay and current utility fixture; not full React/Godot/device or a physical access mechanism. All exact raw differences retained; no RGB/alpha repairs or dither changes.'},indent=2)+'\n')
print('VISIBLE_COMPOSITE_REPLAY_MAX', [max(r['publishedComposites'][bg]['maxRGBA'][i] for r in res for bg in ['light','gray','dark']) for i in range(4)])
print('RAW_REPLAY_CHANGED_RANGE',min(r['rawChangedPixels'] for r in res),max(r['rawChangedPixels'] for r in res),'ALPHA_PAIRS',sorted(set(p for r in res for p in map(tuple,r['rawDifferingPixelAlphaPairs']))))
print('RAF_CANVAS_COUNT',len(canvas),'ALPHAEXACT',all(r['alphaExact'] for r in canvas),'OPAQUE_MAX',[max(r['opaqueMaxRGBA'][i] for r in canvas) for i in range(4)],'ALLRGB_MAX',[max(r['maxRGBA'][i] for r in canvas) for i in range(4)])
print('SUPPORT_STABLE',stable,'CSS_DIFFERENCES',[(r['path'],r['metrics']['maxRGBA']) for r in screenshotcomparisons]);print('ERRORS',report['browserModes'][0]['errors'],report['browserModes'][1]['errors'])
