"""Whole-frame independent atlas/source join comparisons and browser contact sheets.
No crop, overlap, image nudge, recolor or repaired image pixels.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib,shutil
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-03';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def residual(a,b):
 diff=ImageChops.difference(a,b);hist=diff.histogram();n=a.width*a.height
 opaque=[tuple(abs(x[k]-y[k]) for k in range(3)) for x,y in zip(a.getdata(),b.getdata()) if x[3]==255 and y[3]==255]
 opaqueNativeAlphas=[y[3] for x,y in zip(a.getdata(),b.getdata()) if x[3]==255]
 return {'size':list(a.size),'maxAbsoluteDeltaRGBA':[max(i for i,c in enumerate(hist[k*256:(k+1)*256]) if c) for k in range(4)],'meanAbsoluteDeltaRGBA':[sum(i*c for i,c in enumerate(hist[k*256:(k+1)*256]))/n for k in range(4)],'changedPixels':sum(1 for p in diff.getdata() if any(p)),'alphaChangedPixels':sum(1 for p in diff.getdata() if p[3]),'alphaBelow255WhereNativeOpaque':sum(v<255 for v in opaqueNativeAlphas),'fullyTransparentPixelsWhereNativeOpaque':sum(v==0 for v in opaqueNativeAlphas),'minimumIndependentAlphaWhereNativeOpaque':min(opaqueNativeAlphas),'bothOpaqueRGB':{'pixels':len(opaque),'maxAbsoluteDelta':[max(v[k] for v in opaque) for k in range(3)],'meanAbsoluteDelta':[sum(v[k] for v in opaque)/len(opaque) for k in range(3)]}}

consumer=json.loads((OUT/'consumer-fixture-evidence.json').read_text());res={};records=[]
referenceNative=BASE/'source/resources/approved-middle-native';referenceNative.mkdir(exist_ok=True)
for d in 'NESW':shutil.copy2(BASE/f'reviews/preparation-v1/canonical-baseline/middle-native-{d}.png',referenceNative/f'native-{d}.png')
roots={'S':{'end':(.5,0),'middle':(-.5,0)},'E':{'end':(0,-.5),'middle':(0,.5)},'N':{'end':(-.5,0),'middle':(.5,0)},'W':{'end':(0,.5),'middle':(0,-.5)}}
for scale in [4,2]:
 dest=OUT/f'independent-{scale}x';dest.mkdir(exist_ok=True)
 for d in 'NESW':
  full=(1280,1920);cell=512;sourceRoot=(384,1024);assemblyRoot=(640,1280)
  order=next(c['order'] for c in consumer['cases'] if c['endDir']==d and c['middleMode']=='same-facing')
  canvas=Image.new('RGBA',full,(0,0,0,0))
  for obj in order:
   if obj=='end':p=OUT/f'native-static-{d}.png'
   else:p=referenceNative/f'native-{d}.png'
   im=Image.open(p).convert('RGBA');r=roots[d][obj];xy=(int(assemblyRoot[0]+r[0]*cell-sourceRoot[0]),int(assemblyRoot[1]+r[1]*cell-sourceRoot[1]));canvas.alpha_composite(im,xy)
  # At published2x independently publish the whole assembled native canvas.
  # This extra comparator is distinct from the actual consumer, which paints
  # independently BOX-published2x atlases into its common2x native canvas.
  joined=Image.open(OUT/f'joined-native-{d}.png').convert('RGBA')
  if scale==2:canvas=canvas.resize((640,960),Image.Resampling.BOX);joined=joined.resize((640,960),Image.Resampling.BOX)
  cp=dest/f'pair-{d}.png';canvas.save(cp);res[f'{scale}x-{d}']=residual(joined,canvas)
  for bg in ['808080','f5f2e9','182231']:
   bgim=Image.new('RGBA',canvas.size,'#'+bg);bgim.alpha_composite(canvas);bgim.convert('RGB').save(dest/f'pair-{d}-{bg}.png')
# Separate actual independently published atlases, using exact native2x integer root placement.
resPublished={};dest=OUT/'independent-published-atlases';dest.mkdir(exist_ok=True)
for d in 'NESW':
 canvas=Image.new('RGBA',(640,960),(0,0,0,0));order=next(c['order'] for c in consumer['cases'] if c['endDir']==d and c['middleMode']=='same-facing')
 for obj in order:
  p=OUT/f'published/static-{d}.png' if obj=='end' else BASE/f'inputs/approved-middle/published-{d}.png';im=Image.open(p).convert('RGBA');r=roots[d][obj];xy=(int(320+r[0]*256-192),int(640+r[1]*256-512));canvas.alpha_composite(im,xy)
 canvas.save(dest/f'pair-{d}.png');direct=Image.open(OUT/f'joined-native-{d}.png').convert('RGBA').resize((640,960),Image.Resampling.BOX);resPublished[d]=residual(direct,canvas)
 for bg in ['808080','f5f2e9','182231']:
  bgim=Image.new('RGBA',canvas.size,'#'+bg);bgim.alpha_composite(canvas);bgim.convert('RGB').save(dest/f'pair-{d}-{bg}.png')
# Browser all4 sheets, screenshots remain whole and at original size.
for pitch in [128,32,47.3]:
 for background in ['808080','f5f2e9','182231'] if pitch==128 else ['808080']:
  modes=['same-facing','reversed-middle'] if background=='808080' else ['same-facing'];items=[]
  for mode in modes:
   for d in 'NESW':
    phase='0.25-0.5' if background=='808080' else '0-0';p=OUT/'consumer'/f'{d}-{mode}-{pitch}-{phase}-{background}.png';items.append((d,mode,p,Image.open(p).convert('RGB')))
  w=max(i[3].width for i in items);h=max(i[3].height for i in items);sheet=Image.new('RGB',(w*4,(h+24)*len(modes)),'#808080');draw=ImageDraw.Draw(sheet)
  for i,(d,mode,p,im) in enumerate(items):
   x=i%4*w;y=i//4*(h+24);sheet.paste(im,(x,y+24));draw.text((x+3,y+5),f'{d} '+('same' if mode=='same-facing' else 'rev')+f' {pitch}',fill='white');records.append({'path':str(p.relative_to(BASE)),'sha256':sha(p),'sheet':f'previews/consumer-{pitch}-{background}.png'})
  sheet.save(PRE/f'consumer-{pitch}-{background}.png')
shutil.copy2(PRE/'consumer-128-808080.png',PRE/'repeated.png')
(OUT/'independent-join-residuals.json').write_text(json.dumps({'scope':'Direct connected native geometry versus independently captured module RGBA placed at exact native root pitch1 using actual consumer order. Caps hidden only in direct connected scene; no added overlap. These residuals describe natural independent AA/cap/filter differences, not repaired pixels.','nativeIndependentlyComposited':res,'independentlyPublishedAtlasPairs':resPublished,'notes':'Native4x independent layers composited then BOX2x is also retained, separately from true independently published2x atlas pairs. Actual browser fixture uses the true atlas pair path.'},indent=2)+'\n')
(OUT/'consumer-sheet-manifest.json').write_text(json.dumps({'method':'Whole retained actual browser screenshots at original pixel size; labels outside screenshot bounds. Repeated alias contains all4 same-facing and all4 reversed-middle diagnostics.','images':records,'viewportScreenshots':[c['viewportScreenshot'] for c in consumer['cases'] if c.get('viewportScreenshot')]},indent=2)+'\n')
print(json.dumps({'independentNativeCases':len(res),'independentPublishedCases':len(resPublished),'consumerSheets':5,'viewportScreenshots':sum(bool(c.get('viewportScreenshot')) for c in consumer['cases'])}))
