from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';C=O/'consumer-world-raster';M=O/'metrics.json';m=json.loads(M.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Retain the actual worst full-image alpha case as well as opaque join residuals.
for r in m['caseMetrics']:
 if r['case']=='E-128-0.25-0.5-transparent':
  for mode in ['independent','connected']:
   p=C/(r['case']+'-'+mode+'.png');assert sha(p)==r[mode+'PNGsha256']
  r['screenshotsRetained']=True
m['summary']['retainedScreenshotPairs']=sum(r['screenshotsRetained'] for r in m['caseMetrics'])
m['summary']['visualAssessment']='Editor directly inspected all four actual 32px repeated contexts and enlarged object regions, the four 128px contexts, fixed N128 regression and current whole-image worst. No continuous connector line is visible after the shared renderer correction. Remaining pixel differences are localized stone-crease/outer-silhouette samples; independent judge approval is pending.'
m['summary']['residualInterpretation']={'wholeRGB':'Maximum19 channel levels across7 pixels in N128 phase(.25,.5), at x82/210/338,y346–347. These are periodic stone-crease pixels away from cut columns160/288. Whole-image p99 delta1.','projectedJoin':'S/N true cut-column band max2 in the regression; the maximum14 broad E/W projected profile region is2 isolated pixels in W47.3, not a continuous cut line.','alpha':'Maximum opaque-reference projected-join alpha difference1. Maximum full-image alpha difference10 occurs in E128 transparency at a silhouette edge; retain this case separately. No old48–51 alpha-level full-height join coverage loss is observed.'}
# All four actual logical-size contexts in one sheet; source screenshot dimensions are preserved.
for mode in ['independent','connected']:
 sh=Image.new('RGB',(896,2*608+54),'#f5f2e9');dr=ImageDraw.Draw(sh)
 for n,d in enumerate('NESW'):
  r=max([r for r in m['caseMetrics'] if r['direction']==d and r['pitch']==128 and r['background']=='#808080'],key=lambda r:r['opaqueJoinRegion']['maxChannelDelta']);im=Image.open(C/(r['case']+'-'+mode+'.png')).convert('RGB');x=n%2*448;y=n//2*608+54;sh.paste(im,(x,y));dr.text((x+7,y+7),r['case']+' '+mode,fill='#eceae3')
 dr.text((7,8),'Actual current SpriteScene; all four facings at128px cell pitch, unchanged round03 art.',fill='#243c52');dr.text((7,28),'Shared world-native raster is composed before final browser fit/pan sampling.',fill='#243c52');sh.save(O/f'consumer-four-view-128-{mode}.png')
# Exact full-image alpha residual locations; RGBA values retain the distinction from opaque join coverage.
stem='E-128-0.25-0.5-transparent';a=np.array(Image.open(C/(stem+'-independent.png')).convert('RGBA'));b=np.array(Image.open(C/(stem+'-connected.png')).convert('RGBA'));diff=abs(a[...,3].astype(int)-b[...,3].astype(int));inds=np.argwhere(diff==diff.max());r={'case':stem,'alphaMaximumDelta':int(diff.max()),'maximumLocations':[{'pixel':[int(x),int(y)],'independentRGBA':a[y,x].tolist(),'connectedRGBA':b[y,x].tolist()} for y,x in inds[:20]],'note':'Full-image alpha maximum; projected opaque-reference join alpha delta is separately recorded as0 for this E128 case.'};(O/'alpha-residual-locations.json').write_text(json.dumps(r,indent=2))
M.write_text(json.dumps(m,indent=2));print(json.dumps(m['summary'],indent=2))
