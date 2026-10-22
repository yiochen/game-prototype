import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parent;E=BASE/'evidence';BGS={'light':'#f2eee5','gray':'#808080','dark':'#182536'}
def comp(im,bg):
 c=Image.new('RGBA',im.size,bg);c.alpha_composite(im);return c.convert('RGB')
reports={be:json.loads((E/('direct2x-'+be+'-report.json')).read_text()) for be in ['full-chrome','headless-shell']};summary=[]
for be,report in reports.items():
 corrected=[]
 for r in report['records']:
  a=Image.open(E/r['images']['independent']).convert('RGBA');n=Image.open(E/r['images']['native']).convert('RGBA');d=r['direction'];z=r['zoom'];
  boxes=([(166,350,178,420),(294,350,306,420)] if d in 'NS' else [(196,278,276,328),(196,406,276,456)]) if z==1 else ([(47,101,57,115),(79,101,89,115)] if d in 'NS' else [(58,79,78,91),(58,111,78,123)])
  vals=[];rgb=[];excluded=0
  for box in boxes:
   for y in range(box[1],box[3]):
    for x in range(box[0],box[2]):
     # Exclude a1output-pixel neighborhood of actual native silhouette filtering, not internal seams.
     if any(n.getpixel((xx,yy))[3]!=255 for yy in range(y-1,y+2) for xx in range(x-1,x+2)):excluded+=1;continue
     aa=a.getpixel((x,y));bb=n.getpixel((x,y));vals.append(aa[3]);rgb.append(max(abs(aa[k]-bb[k]) for k in range(3)))
  corrected.append({'policy':r['policy'],'direction':d,'zoom':z,'rootPhaseLogical':r['rootPhaseLogical'],'panPhaseOutput':r['panPhaseOutput'],'finiteInteriorBoxes':boxes,'geometricInteriorAndNativeOpaqueSamples':len(vals),'excludedNativeSilhouetteNeighborhoodSamples':excluded,'minIndependentAlpha':min(vals) if vals else None,'deficientAlphaSamples':sum(v<255 for v in vals),'maxRGBDelta':max(rgb) if rgb else None,'rawPortBandMetrics':r['finitePortInterior'],'wholeFrameResiduals':r['residual']})
 (E/('direct2x-'+be+'-corrected-interior.json')).write_text(json.dumps({'explanation':'Original raw finitePortInterior field was only a projected port BAND, including outer silhouette pixels. Corrected interior limits remove known top/bottom/side silhouette neighborhood from actual finite profile, then exclude every pixel with any native nonopaque neighbor. Raw reports/PNG/outer-light-filter residuals retained unchanged. This separates true internal alpha seam loss from legitimate edge antialiasing.','records':corrected},indent=2)+'\n')
 for policy in ['direct2x-filter001']:
  rr=[r for r in corrected if r['policy']==policy];summary.append({'backend':be,'policy':policy,'cases':len(rr),'interiorMinAlpha':min(r['minIndependentAlpha'] for r in rr),'casesWithInteriorAlphaDeficit':sum(r['deficientAlphaSamples']>0 for r in rr),'maxWholeFrameAlphaDelta':max(r['wholeFrameResiduals']['maxAlphaDelta'] for r in rr),'maxLocalRGBDelta':max(r['maxRGBDelta'] for r in rr),'minMeanWholeFrameRGBDelta':min(r['wholeFrameResiduals']['meanRGBDelta'] for r in rr),'maxMeanWholeFrameRGBDelta':max(r['wholeFrameResiduals']['meanRGBDelta'] for r in rr)})
  # Readable compact visual subset: first actual internal port band, both rendered methods, every root/pan case. Other port is in full-strip/raw/technical proof.
  cases=[(0,0),(.25,0),(.5,0),(.75,0),(0,.25),(0,.5),(0,.75),(.25,.75)]
  canvas=Image.new('RGB',(1450,920),'#ddd6cb');draw=ImageDraw.Draw(canvas)
  for row,(d,z) in enumerate((d,z) for z in [1,.25] for d in 'NESW'):
   for col,(root,pan) in enumerate(cases):
    r=next(r for r in report['records'] if r['policy']==policy and r['direction']==d and r['zoom']==z and r['rootPhaseLogical']==root and r['panPhaseOutput']==pan);x=8+col*180;y=8+row*112
    draw.text((x,y),f'{d} {int(128*z)} r{root} p{pan}',fill='black');draw.text((x,y+12),'native / independent',fill='black')
    box=((166,350,178,420) if d in 'NS' else (198,284,270,318)) if z==1 else ((47,101,57,115) if d in 'NS' else (59,80,77,90))
    for k,kind in enumerate(['native','independent']):
     crop=Image.open(E/r['images'][kind]).convert('RGBA').crop(box)
     if z==.25:crop=crop.resize((crop.width*3,crop.height*3),Image.Resampling.NEAREST)
     off=(crop.width+6)*k;canvas.paste(comp(crop,'#808080'),(x+off,y+28))
  draw.text((8,907),f'{policy} {be}: fixed actual first-port interior/profile crops. phone×3nearest. Full both-port source strips/rawRGBA/outer residuals retained.',fill='black');canvas.save(E/f'fractional-{be}-{policy}.png')
# Control visible all4 singles plus native/independent full3module strips on3backgrounds, both use scales.
report=reports['full-chrome']
c=Image.new('RGB',(1180,910),'#ddd6cb');draw=ImageDraw.Draw(c)
for j,d in enumerate('NESW'):
 im=Image.open(E/f'study-direct2x-filter001/packed/single-{d}/sheet.png').convert('RGBA')
 for k,(bn,bg) in enumerate(BGS.items()):
  x=10+j*294;y=30+k*290;draw.text((x,y-16),f'direct2x .01 {d} {bn}:128 /32',fill='black');c.paste(comp(im.resize((192,352),Image.Resampling.LANCZOS).crop((0,110,192,352)),bg),(x,y));c.paste(comp(im.resize((48,88),Image.Resampling.LANCZOS),bg),(x+202,y+100))
draw.text((10,900),'Source-only direct native2x .01filter control, no reduction; unadopted. Same native geometry/materials/lighting/camera/roots.',fill='black');c.save(E/'direct2x-single-all4-use-size.png')
for d in 'NESW':
 c=Image.new('RGB',(1420,740),'#ddd6cb');draw=ImageDraw.Draw(c);rect=(12,282,460,462) if d in 'NS' else (162,162,310,582)
 for bi,(bn,bg) in enumerate(BGS.items()):
  x=10+bi*470;draw.text((x,8),f'direct2x .01 {d} {bn} r0p0 native / independent',fill='black')
  for zi,z in enumerate([1,.25]):
   r=next(r for r in report['records'] if r['policy']=='direct2x-filter001' and r['direction']==d and r['zoom']==z and r['rootPhaseLogical']==0 and r['panPhaseOutput']==0)
   for ki,kind in enumerate(['native','independent']):
    im=Image.open(E/r['images'][kind]).convert('RGBA');im=im.crop(rect) if z==1 else im
    px=x+(ki*160 if d in 'EW' and z==1 else ki*150 if z==.25 else 0);py=30+(0 if d in 'EW' else ki*200) if z==1 else 500
    c.paste(comp(im,bg),(px,py))
 draw.text((10,715),'UNADOPTED source-only sampling control. Geometry unchanged. Top logical128 native/independent. Bottom phone32 same order.',fill='black');c.save(E/f'direct2x-connection-{d}-use-size.png')
(E/'direct2x-summary.json').write_text(json.dumps({'status':'source-only controls and bounded consumer proof; no adoption/art/seam approval','reports':summary,'evidenceInterpretation':'BothBOX controls must retain E/W visible RGB cut-profile lines as unresolved native-authoring requirement. Corrected alpha samples exclude legitimate outer silhouette AA; wholeframe residuals remain raw.'},indent=2)+'\n');print(json.dumps(summary))
