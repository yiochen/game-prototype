import sys,json,math,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'dependencies/python-library'))
from PIL import Image,ImageChops,ImageStat,ImageDraw,ImageFilter
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'candidates/round-01';C=OUT/'evidence/consumer'
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Record honest saved-source numerical residual rather than calling it exact.
proof=json.loads((OUT/'publication-proof.json').read_text())
for r in proof['frames']:
 d=r['direction'];a=Image.open(OUT/f'native/static/{d}/000.png').convert('RGBA');b=Image.open(OUT/f'evidence/recapture/native-{d}.png').convert('RGBA');diff=ImageChops.difference(a,b);r.update(savedSourceReplayDiffMax=[v[1] for v in diff.getextrema()],savedSourceReplayDiffMean=ImageStat.Stat(diff).mean,alphaReplayExact=a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),note='Actual ledger is measured during primary capture. Clean saved-source replay has only the retained 8-bit residual shown; no claim of exact RGBA parity.')
for r in proof['frames']:
 d=r['direction'];a=Image.open(OUT/f'native/static/{d}/000.png').convert('RGBA');b=Image.open(OUT/f'evidence/recapture/native-{d}.png').convert('RGBA');diff=ImageChops.difference(a,b).convert('RGB');mask=a.getchannel('A').point(lambda p:255 if p==255 else 0);masked=Image.new('RGB',a.size);masked.paste(diff,mask=mask);r['fullyOpaqueReplayRGBMax']=[e[1] for e in masked.getextrema()];r['compositeReplayRGBMax']={bg:[e[1] for e in ImageChops.difference(Image.alpha_composite(Image.new('RGBA',a.size,bg),a).convert('RGB'),Image.alpha_composite(Image.new('RGBA',b.size,bg),b).convert('RGB')).getextrema()] for bg in ['#eef2ed','#909090','#172539']};r['lowAlphaCaveat']='Raw unpremultiplied RGB can differ more at very low alpha; no RGB/alpha repair applied. Fully opaque and composited residuals are recorded separately.'
dump(OUT/'publication-proof.json',proof)
# Compact browser output review sheets: actual intended size, common crop for all4.
# Fixed family crop x16,y120,w416,h472 is supplemental to full raw/browser canvases.
for fixture in ['L','W','N']:
 sheet=Image.new('RGB',(416*4,3*(472+118+24)),'#909090');dr=ImageDraw.Draw(sheet)
 for row,bg in enumerate(['light','gray','dark']):
  y=row*614;fill={'light':'#eef2ed','gray':'#909090','dark':'#172539'}[bg];dr.rectangle((0,y,1663,y+613),fill=fill)
  for col,d in enumerate('NESW'):
   big=Image.open(C/f'{fixture}-{d}-128-{bg}-integer.png').convert('RGB').crop((16,120,432,592));small=Image.open(C/f'{fixture}-{d}-32-{bg}-integer.png').convert('RGB').crop((4,30,108,148));sheet.paste(big,(col*416,y+18));sheet.paste(small,(col*416+156,y+492));dr.text((col*416+8,y+3),f'{fixture} {d} cell128 / cell32',fill='white' if bg=='dark' else '#172539')
 sheet.save(OUT/f'consumer-{fixture}-all4.png')
# Direct native reference/current consumer comparison, every actual family fixture.
sheet=Image.new('RGB',(1664,6*492),'#909090');dr=ImageDraw.Draw(sheet)
for fi,fixture in enumerate(['L','W','N']):
 for ci,d in enumerate('NESW'):
  for k,kind in enumerate(['native reference','independent consumer']):
   y=(fi*2+k)*492
   if k==0:
    rgba=Image.open(OUT/f'evidence/family/published-{fixture}-{d}.png').convert('RGBA').resize((448,608),Image.Resampling.BOX);bg=Image.new('RGBA',rgba.size,'#909090');im=Image.alpha_composite(bg,rgba).convert('RGB')
   else:im=Image.open(C/f'{fixture}-{d}-128-gray-integer.png').convert('RGB')
   sheet.paste(im.crop((16,120,432,592)),(ci*416,y+20));dr.text((ci*416+8,y+3),f'{fixture} {d} {kind}',fill='#172539')
sheet.save(OUT/'native-vs-consumer-all4.png')
# All actual fractional phases on gray, for every direction at both sizes (L fixture).
phases=['integer','quarter','half','threequarter','fractional-root','fractional-pan','mixed'];sheet=Image.new('RGB',(416*4,len(phases)*(472+118+24)),'#909090');dr=ImageDraw.Draw(sheet)
for row,phase in enumerate(phases):
 y=row*614
 for col,d in enumerate('NESW'):
  big=Image.open(C/f'L-{d}-128-gray-{phase}.png').crop((16,120,432,592));small=Image.open(C/f'L-{d}-32-gray-{phase}.png').crop((4,30,108,148));sheet.paste(big,(col*416,y+18));sheet.paste(small,(col*416+156,y+492));dr.text((col*416+8,y+3),f'{d} {phase}',fill='#172539')
sheet.save(OUT/'consumer-phases-all4.png')
# Native combined versus independently composed current consumer at sourceScale2.
angles={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2};profile=[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)];metrics=[]
def stats(im,mask):
 st=ImageStat.Stat(im,mask);return {'mean':st.mean,'max':[e[1] for e in im.getextrema()]}
for fixture in ['L','W','N']:
 for d in 'NESW':
  independent=Image.open(C/f'nativecanvas-{fixture}-{d}.png').convert('RGBA').crop((1,1,897,1217));native=Image.open(OUT/f'evidence/family/published-{fixture}-{d}.png').convert('RGBA');gray=Image.new('RGBA',native.size,'#909090');aa=Image.alpha_composite(gray,native).convert('RGB');bb=Image.alpha_composite(gray,independent).convert('RGB');diff=ImageChops.difference(aa,bb);opacity=ImageChops.multiply(native.getchannel('A'),independent.getchannel('A')).point(lambda p:255 if p==255 else 0);allmask=Image.new('L',native.size,0);perport={}
  for port in (['W','N'] if fixture=='L' else [fixture]):
   a=angles[d];pts=[]
   for transverse,z in profile:
    x,y=(-.5,transverse) if port=='W' else (-transverse,.5);rx=math.cos(a)*x-math.sin(a)*y;ry=math.sin(a)*x+math.cos(a)*y;pts.append((448+rx*256,752-ry*256-z*.7*256))
   mask=Image.new('L',native.size,0);ImageDraw.Draw(mask).polygon(pts,fill=255);mask=mask.filter(ImageFilter.MaxFilter(5));allmask=ImageChops.lighter(mask,allmask);local=ImageChops.multiply(mask,opacity);na=native.getchannel('A');ia=independent.getchannel('A');bbox=mask.getbbox();under=0;maxloss=0
   for y in range(bbox[1],bbox[3]):
    for x in range(bbox[0],bbox[2]):
     if mask.getpixel((x,y)) and na.getpixel((x,y))==255:
      loss=255-ia.getpixel((x,y));under+=loss>0;maxloss=max(maxloss,loss)
   # Three real transverse traces, sampled from actual raw source-scale compositing.
   traces=[]
   for frac in [.2,.5,.8]:
    px=round(bbox[0]+(bbox[2]-bbox[0])*frac);ys=range(bbox[1],bbox[3]);traces.append({'x':px,'startY':bbox[1],'nativeRGBA':[native.getpixel((px,y)) for y in ys],'independentRGBA':[independent.getpixel((px,y)) for y in ys]})
   perport[port]={'projectedCapPolygon':pts,'maskBounds':bbox,'fullyOpaqueReferencePixelsWithIndependentAlphaLoss':under,'maximumAlphaLoss':maxloss,'localCompositeRGBDifference':stats(diff,local),'traces':traces};mask.save(OUT/f'evidence/family/mask-{fixture}-{d}-{port}.png')
  broad=ImageChops.multiply(opacity,ImageChops.invert(allmask.filter(ImageFilter.MaxFilter(15))));metrics.append({'fixture':fixture,'direction':d,'ports':perport,'broadFiniteLightSourceExtentDifference':stats(diff,broad),'note':'Broad finite-area translated source-extent residual is reported separately. Local seam masks and actual pixels remain independent visual-review gates; aggregate values cannot waive a seam.'})
  # Direct source comparison heatmap, retained as evidence rather than art.
  diff.point(lambda p:min(255,p*8)).save(OUT/f'evidence/family/difference8x-{fixture}-{d}.png')
dump(OUT/'family-comparison.json',{'method':'Actual current consumer native canvas with its one-pixel guard removed for measurement only, versus whole-frame BOX2x native combined reference. No candidate RGB or alpha repairs.','fixtures':metrics})
# Actual module inventory used by the Pillow evidence scripts.
mods=[]
for name,m in sorted(sys.modules.items()):
 p=getattr(m,'__file__',None)
 if p and ('PIL' in name or name in ['json','hashlib','math']):mods.append({'module':name,'path':p,'sha256':sha(Path(p)) if Path(p).is_file() else None})
dump(OUT/'used-python-modules.json',{'python':sys.executable,'modules':mods})
print('FINISH COMPLETE')
