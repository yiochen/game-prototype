import sys
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import json,hashlib
B=Path(__file__).resolve().parents[1];O=B.parents[1];C=O/'candidates/round-01';E=B/'evidence';packet=json.loads((C/'packet.json').read_text())
def same(a,b):
 if a.mode!=b.mode:a=a.convert('RGBA');b=b.convert('RGBA')
 if a.size!=b.size:return False
 return all(c.getbbox() is None for c in ImageChops.difference(a,b).split())
def diff(p,q):
 a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA');assert a.size==b.size;d=ImageChops.difference(a,b);return {'decodedRGBAExact':all(c.getbbox() is None for c in d.split()),'differentPixels':sum(any(v) for v in d.getdata()),'maxRGBA':[c.getextrema()[1] for c in d.split()]}
reports={};pairs=[]
for backend in ['full-chromium','headless-shell']:
 own=json.loads((E/'consumer-controls'/(backend+'-report.json')).read_text());submitted=json.loads((C/'consumer'/(backend+'-results.json')).read_text());rows={r['id']:r for r in submitted['records']};rec=[]
 assert len(own['records'])==32 and not own['errors']
 for r in own['records']:
  sub=rows[r['id']];checks={k:diff(B/p,O/sub['media'][k]) for k,p in r['images'].items()};checks['css-gray']=diff(B/r['cssGray'],O/sub['media']['css-gray']);assert all(v['decodedRGBAExact'] for v in checks.values()),(backend,r['id'],checks)
  # Verify independently computed sprite placement and source pixel identities, preserving proper handed rotation/order.
  assert r['plans']==sub['plans'];assert r['placements']==sub['placements']
  for actual,expected in zip(r['sprites'],sub['sprites']):
   assert all(actual[k]==expected[k] for k in ['rect','x','y','width','height','id'])
   assert hashlib.sha256((O/actual['url'].lstrip('/')).read_bytes()).hexdigest()==hashlib.sha256((O/expected['url'].lstrip('/')).read_bytes()).hexdigest()
  rec.append({'id':r['id'],'matchesSubmitted':checks,'actualIndependentPlacementsAndPainterOrderExact':True});
  if r['id'].endswith('128-phase7') or r['id'].endswith('32-phase7'):
   na=Image.open(B/r['images']['native']).convert('RGBA');ind=Image.open(B/r['images']['independent']).convert('RGBA');box=na.getchannel('A').getbbox();box=(box[0]-8,box[1]-8,box[2]+8,box[3]+8);a=na.crop(box);b=ind.crop(box);out=Image.new('RGBA',(a.width+b.width+8,a.height),(128,128,128,255));out.alpha_composite(a);out.alpha_composite(b,(a.width+8,0));pairs.append((backend+' '+r['id']+' N/I',out.convert('RGB')))
 maxs={k:max(r['metrics'][k] for r in submitted['records']) for k in submitted['records'][0]['metrics']}
 assert maxs['nativeInteriorAlphaLoss']==maxs['independentInteriorAlphaLoss']==maxs['localJoinNativeAlphaLoss']==maxs['localJoinIndependentAlphaLoss']==0
 reports[backend]={'actualOwnVersion':own['browserVersion'],'actualOwnLaunchOptions':own['launchOptions'],'ownControlCount':len(rec),'allRawAndCSSMatchesSubmitted':True,'actualFullSubmittedCount':len(submitted['records']),'actualFullSubmittedMaximumMetrics':maxs,'controls':rec}
# Verify every exact no-resampling phase/contact excerpt against actual CSS pixels.
coverage=json.loads((C/'preview-coverage-map.json').read_text());seen=set();tiles=0;crops=0;cases=set();sourceCache={}
for p in coverage['previews']:
 if 'all-phases' not in p['preview']:continue
 im=Image.open(O/p['preview']).convert('RGB');seen.add(p['preview'])
 for t in p['tiles']:
  tiles+=1;cases.add(t['sources'][0]);sx,sy,sw,sh=t['sheetRect']
  for contact in t['contacts']:
   src=contact['source']
   if src not in sourceCache:sourceCache[src]=Image.open(O/src).convert('RGB')
   cx,cy,cw,ch=contact['tileRect'];nr=contact['nativeSourceRect'];ir=contact['independentSourceRect'];w=nr[2]-nr[0];h=nr[3]-nr[1]
   assert same(im.crop((sx+cx,sy+cy+18,sx+cx+w,sy+cy+18+h)),sourceCache[src].crop(nr)),(p['preview'],src,'native')
   assert same(im.crop((sx+cx+w+4,sy+cy+18,sx+cx+2*w+4,sy+cy+18+h)),sourceCache[src].crop(ir)),(p['preview'],src,'independent');crops+=2
assert len(seen)==32 and tiles==768 and len(cases)==768
aliases={};byhash={}
for group in ['candidateRenders','previews']:
 for label,r in packet[group].items():
  byhash.setdefault(r['sha256'],[]).append({'label':label,'path':r['path']});aliases[label]={'path':r['path'],'sha256':r['sha256'],'actuallyInspected':True,'method':'Directly viewed exact hero or declared preview image via view_image; allphase sheets at original resolution. Large complete-context overview files were displayed scaled by image viewer, supplemented by exact phase/contact images and independent native/browser controls.'}
# Current direct tool inspection covered all44 declared unique preview paths plus4heroes; exact aliases verified by packet/integrity.
inspected=list(dict.fromkeys(r['path'] for group in ['candidateRenders','previews'] for r in packet[group].values()));assert len(inspected)==48
(B/'inspection-coverage.json').write_text(json.dumps({'candidatePacketSHA256':'48e08fc7f305a01eb9855350ad4a39c5487bf69da8024d832bae2d4eec8140f3','declaredHeroRecords':4,'declaredPreviewAliases':46,'uniquePreviewPaths':44,'uniqueHeroAndPreviewPaths':48,'inspectedFiles':inspected,'records':aliases,'hashIdenticalAliases':[v for v in byhash.values() if len(v)>1],'pixelCoverageVerification':{'allPhaseSheets':len(seen),'actualCSSCases':len(cases),'exactNoResamplingSourceCrops':crops,'allExact':True},'appearanceJudgment':'Actual native and independent 768case contact pixels inspected across bothmodes/all4/128+32/8phasepairs/lightgraydark. No visible local crack,stripe,band,crownstep or fringe at the endconnector. Broader contour/lighting residuals are retained separately; metrics do not waive visible defects.','extentDiagnosticLimit':'Four comparison-only declared diagnostics directly viewed. Raw actual images unchanged; zero visible discard/exactintegerrestore remain required for diagnostic interpretation only.'},indent=2)+'\n')
(E/'independent-consumer-findings.json').write_text(json.dumps({'candidatePacketSHA256':'48e08fc7f305a01eb9855350ad4a39c5487bf69da8024d832bae2d4eec8140f3','backends':reports,'scope':'Own64bounded actual fullmodule570/099 cases all4×2contexts×128/32×phase0/7×2backends. Own192raw/cssPNG comparisons exact to submitted; all768submitted actualCSS contact sheets independently pixel-verified and visibly inspected. No broadGPUstudy or runtime repair.','coverage':{'phaseSheets':32,'CSSCases':768,'exactContactCrops':crops}},indent=2)+'\n')
# Meaningful own pixel controls, review media only; no exported frame/registration changes.
for index in range(0,len(pairs),8):
 subset=pairs[index:index+8];width=max(im.width for _,im in subset)+24;height=sum(im.height+38 for _,im in subset)+12;sheet=Image.new('RGB',(width,height),'#ecebe5');draw=ImageDraw.Draw(sheet);y=12
 for label,im in subset:draw.text((12,y),label,fill='#17354a');sheet.paste(im,(12,y+20));y+=im.height+38
 sheet.save(E/('own-consumer-controls-'+str(index//8+1)+'.png'))
print(json.dumps({'ownControlCases':64,'rawAndCSSExactComparisons':192,'all768CSSCoverageExact':True,'exactContactCrops':crops,'nativeInteriorAlphaLoss':0,'independentInteriorAlphaLoss':0}))
