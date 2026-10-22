import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parent;E=B/'evidence';reports={be:json.loads((E/(be+'-report.json')).read_text()) for be in ['full-chrome-153','shell-153','full-chrome-155']};summaries=[]
for be,report in reports.items():
 assert len(report['records'])==128 and len(report['controls'])==8
 for c in report['controls']:assert c['discardedVisiblePixels']==0 and c['integerRestoration']['differingPixels']==0
 for policy in ['historical','direct2x-filter001']:
  rows=[r for r in report['records'] if r['policy']==policy]
  summaries.append({'backend':be,'browserVersion':report['browserVersion'],'policy':policy,'cases':len(rows),'actualConsumer':{'maxAlphaDelta':max(r['actualConsumerResidual']['maxAlphaDelta'] for r in rows),'maxOpaqueRGBDelta':max(r['actualConsumerResidual']['maxOpaqueRGBDelta'] for r in rows)},'comparisonOnlyEqualExtents':{'maxAlphaDelta':max(r['comparisonOnlyEqualExtentsResidual']['maxAlphaDelta'] for r in rows),'maxOpaqueRGBDelta':max(r['comparisonOnlyEqualExtentsResidual']['maxOpaqueRGBDelta'] for r in rows),'minimumFinitePortInteriorAlpha':min(r['finitePortInterior']['native-equal-extents-diagnostic']['minIndependentAlpha'] for r in rows)},'casesWhereTransparentPaddingOnlyChangesNativeSampling':sum(r['paddingOnlyNativeSamplingEffect']['differingPixels']>0 for r in rows)})
(E/'summary.json').write_text(json.dumps({'status':'Comparison-only targeted precision calibration; no art/runtime/seam approval','reports':summaries,'calibrationInvariant':'All24 control crops removed0visiblepixels and exact integer restoration changed0pixels; new texture extents match independent group extents derived from registered sprite rectangles, not alpha bounds.','interpretation':['Parent source-kind controls are consistent: PNG versus Canvas at same pixels/extent gives exact results.','Parent padding-only diagnostic is independently consistent with new all4 tests: fullChrome153/155 extent-dependent nearest ties account for a large component of earlier raw native-versus-independent residuals; shell is unaffected by equalizing extents.','Direct2x diagnostic equal extents gives exact whole-frame alpha equality in all64cases perbackend; historical alpha loss remains233 in actual finite-port interiors and global alpha delta55. Calibration does not hide that true source-capture seam deficit.','Original sealed opaqueRGB140 and alpha255 observations remain real actual-consumer results. New diagnostics refine their cause; they do not retract observations or change any prior record.','Remaining RGB differences are retained up to43 for direct2x and37 for historical, including native connected versus independent lighting/context variation. They are not declared universally harmless or a seam pass.','Direct2x/.01 remains unadopted. Current production570a0d0d, assets, logical roots/framing, stylecriteria and native normal/albedo/visible-line requirements are unchanged.']},indent=2)+'\n')
def comp(im,bg):
 c=Image.new('RGBA',im.size,bg);c.alpha_composite(im);return c.convert('RGB')
# Compact full-frame phone comparison, exact worst-case common root/pan, all4/source policies, three backgrounds.
report=reports['full-chrome-155'];kinds=['native-actual','native-equal-extents-diagnostic','independent'];bgs=['#f2eee5','#808080','#182536']
for policy in ['historical','direct2x-filter001']:
 c=Image.new('RGB',(1280,840),'#ddd6cb');dr=ImageDraw.Draw(c)
 for row,d in enumerate('NESW'):
  r=next(r for r in report['records'] if r['policy']==policy and r['direction']==d and r['zoom']==.25 and r['rootPhaseLogical']==.25 and r['panPhaseOutput']==.75)
  for bgindex,bg in enumerate(bgs):
   for ki,kind in enumerate(kinds):
    x=10+bgindex*420+ki*138;y=30+row*200;im=Image.open(E/r['images'][kind]).convert('RGBA');dr.text((x,y-16),f'{d} '+['actual native','calibrated native','independent'][ki],fill='black');c.paste(comp(im,bg),(x,y))
 dr.text((10,825),f'{policy}: phone cell32 complete registered448x608common scene×.25, root.25logical/pan.75output. Comparison only; calibrated native is not production art.',fill='black');c.save(E/f'phone-all4-{policy}.png')
# Magnified concrete residual points plus actual internal profile line. All3 methods/all3 backgrounds.
for policy in ['historical','direct2x-filter001']:
 c=Image.new('RGB',(1410,940),'#ddd6cb');dr=ImageDraw.Draw(c)
 for row,(d,box,label,mag) in enumerate([('E',(252,270,290,338),'Opaque blue/dark side boundary; prior140RGB observation',3),('N',(150,420,185,445),'Outer ground silhouette; prior255alpha observation',3),('E',(190,278,282,328),'Actual first internal cut-profile line; keep source/visible-line requirement',2)]):
  r=next(r for r in report['records'] if r['policy']==policy and r['direction']==d and r['zoom']==1 and r['rootPhaseLogical']==.25 and r['panPhaseOutput']==.75)
  for bgindex,bg in enumerate(bgs):
   x=10+bgindex*465;y=26+row*300
   for ki,kind in enumerate(kinds):
    im=Image.open(E/r['images'][kind]).convert('RGBA').crop(box);im=im.resize((im.width*mag,im.height*mag),Image.Resampling.NEAREST)
    # First2 rows fit3×114wide; last row lower horizontal profile is shown as3stacked slices at exact2×.
    px=x+ki*145 if row<2 else x;py=y if row<2 else y+ki*65
    if row==2:im=im.resize((im.width,60),Image.Resampling.NEAREST) # explicit presentation-only vertical sampling; original full crops in raw case PNGs
    dr.text((px,py-13),['actual native','calibrated native','independent'][ki],fill='black');c.paste(comp(im,bg),(px,py))
   dr.text((x,y+225),label,fill='black')
 dr.text((10,926),f'{policy} fullChrome155 cell128 root.25/pan.75. First2rows ×3nearest; final profile crops×2wide/60px presentation. Raw actual/calibrated cases retained.',fill='black');c.save(E/f'precision-residual-diagnostics-{policy}.png')
print(json.dumps(summaries))
