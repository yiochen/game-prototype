from pathlib import Path
import json,hashlib,shutil,math,sys
from PIL import Image,ImageDraw
import numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';R=B/'source/resources';D=B/'delivery/round-04';D.mkdir(parents=True,exist_ok=True);A=O/'atlases';A.mkdir(exist_ok=True);P=O/'previews';P.mkdir(exist_ok=True)
DIR={'N':180,'E':90,'S':0,'W':-90};bgs={'light':(244,244,244,255),'gray':(144,149,156,255),'dark':(23,33,44,255)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(B).as_posix()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def flatten(im,bg):back=Image.new('RGBA',im.size,bg);back.alpha_composite(im);return back.convert('RGB')
raw=[];native=[];atl=[];reproduction={};alpha={}
for d in DIR:
 p=O/f'native-static-{d}.png';im=Image.open(p).convert('RGBA');assert im.size==(768,1408);pub=im.resize((384,704),Image.Resampling.BOX);pp=O/f'published-static-{d}.png';pub.save(pp);shutil.copy2(pp,A/f'static-{d}.png')
 raw.append({'clip':'static','direction':d,'index':0,'path':rel(pp),'sha256':sha(pp)});native.append({'clip':'static','direction':d,'index':0,'path':rel(p),'sha256':sha(p),'nativeCaptureScale':4,'size':[768,1408]});atl.append({'clip':'static','direction':d,'path':rel(A/f'static-{d}.png'),'sha256':sha(A/f'static-{d}.png'),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]],'fps':12,'loop':False,'frameOrder':[0]})
 rp=O/'replay'/p.name;aa=np.asarray(im).astype(int);bb=np.asarray(Image.open(rp).convert('RGBA')).astype(int);reproduction[d]={'nativeDecodedMaxDifference':int(np.abs(aa-bb).max()),'nativeDecodedDifferentPixels':int(np.any(aa!=bb,axis=2).sum()),'original':rel(p),'replay':rel(rp),'originalSHA256':sha(p),'replaySHA256':sha(rp)}
 arr=np.asarray(pub);mask=arr[:,:,3]>0;ys,xs=np.where(mask);alpha[d]={'publishedSize':[384,704],'alphaBBox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'outerFrameAlphaMax':int(max(arr[0,:,3].max(),arr[-1,:,3].max(),arr[:,0,3].max(),arr[:,-1,3].max())),'transparentOutside':True}
# Full registered standalone frames at their exact native publication size on all backgrounds.
for bg,c in bgs.items():
 sheet=Image.new('RGB',(384*4,736),c[:3]);dr=ImageDraw.Draw(sheet)
 for i,d in enumerate(DIR):sheet.paste(flatten(Image.open(O/f'published-static-{d}.png').convert('RGBA'),c),(i*384,28));dr.text((i*384+12,8),f'{d} - complete published 384x704',fill='white' if bg=='dark' else 'black')
 sheet.save(P/f'standalone-all4-{bg}.png')
# Independently captured canonical middle/corner assemblies at exact projected roots, no overlap or fit.
assemblies={};cross=[];metric={}
for d,deg in DIR.items():
 canvas=Image.new('RGBA',(896,1216));r=math.radians(deg);co=math.cos(r);si=math.sin(r)
 placements=[('N-middle',0,1,['S','E','N','W'][(1+['S','E','N','W'].index(d))%4]),('W-middle',-1,0,d),('corner',0,0,d)]
 ps=[]
 for name,x,y,fd in placements:
  xx=co*x-si*y;yy=si*x+co*y;ps.append((name,xx,yy,fd))
 # Same ground-depth stable order as snapshotted consumer orderPlacements.
 ps.sort(key=lambda p:-p[2])
 for name,x,y,fd in ps:
  im=Image.open(O/f'published-static-{fd}.png' if name=='corner' else R/f'approved-middle/published-{fd}.png').convert('RGBA');canvas.alpha_composite(im,(round(448+256*x-192),round(768-256*y-512)))
 assembly=O/f'independent-published-joined-{d}.png';canvas.save(assembly);assemblies[d]=canvas
 nim=Image.open(O/f'native-joined-{d}.png').convert('RGBA').resize((896,1216),Image.Resampling.BOX);nim.save(O/f'published-native-joined-{d}.png');na=np.asarray(nim).astype(int);ia=np.asarray(canvas).astype(int)
 metric[d]={'wholeFrameMaxRGBAResidual':int(np.abs(na-ia).max()),'meanAbsoluteRGBAResidual':float(np.abs(na-ia).mean()),'nativeOpaqueIndependentAlphaBelow250':int(((na[:,:,3]>=254)&(ia[:,:,3]<250)).sum()),'nativeVsIndependentNotAssumedIdentical':'Independent alpha-composited captures retain terminal surfaces and per-frame alpha boundaries. Canonical middle native relief exceeds side nominal plane by ~.005; exact port cuts remain fixed. Raw residuals are shown, never repaired.'}
 for port,v in [('W',(-.5,0,1.15)),('N',(0,.5,1.15))]:
  x=co*v[0]-si*v[1];y=si*v[0]+co*v[1];cx=round(448+256*x);cy=round(768-256*y-179.20008*v[2]);normal=(co, -si) if port=='W' else (-si,-co)
  samples=[]
  for off in range(-8,9):
   px=round(cx+off*normal[0]);py=round(cy+off*normal[1]);samples.append({'offsetPublishedPx':off,'pixel':[px,py],'nativeRGBA':na[py,px].tolist(),'independentRGBA':ia[py,px].tolist(),'residualRGBA':(ia[py,px]-na[py,px]).tolist()})
  cross.append({'direction':d,'port':port,'localWorld':list(v),'publishedPixel':[cx,cy],'crossSection':samples,'crop':[cx-28,cy-28,cx+28,cy+28]})
for bg,c in bgs.items():
 sheet=Image.new('RGB',(448*4,650),c[:3]);dr=ImageDraw.Draw(sheet)
 for i,d in enumerate(DIR):
  im=Image.open(O/f'native-joined-{d}.png').convert('RGBA').resize((448,608),Image.Resampling.BOX);sheet.paste(flatten(im,c),(i*448,30));dr.text((i*448+12,8),f'{d} native - both joins / full frame',fill='white' if bg=='dark' else 'black')
 sheet.save(P/f'native-joins-all4-{bg}.png')
 # Independent published complete frames, same canvas, rendered independently per object.
 sheet=Image.new('RGB',(448*4,650),c[:3]);dr=ImageDraw.Draw(sheet)
 for i,d in enumerate(DIR):
  im=assemblies[d].resize((448,608),Image.Resampling.BOX);sheet.paste(flatten(im,c),(i*448,30));dr.text((i*448+12,8),f'{d} independent published - exact roots',fill='white' if bg=='dark' else 'black')
 sheet.save(P/f'independent-joins-all4-{bg}.png')
# Local truthful native-versus-independent crown RGB/alpha cross-section visual evidence.
sheet=Image.new('RGB',(4*352,2*214),(144,149,156));dr=ImageDraw.Draw(sheet)
for n,crossrow in enumerate(cross):
 col=list(DIR).index(crossrow['direction']);row=0 if crossrow['port']=='W' else 1;box=crossrow['crop'];nimg=Image.open(O/f"published-native-joined-{crossrow['direction']}.png").convert('RGBA');iimg=assemblies[crossrow['direction']]
 for j,(name,im) in enumerate([('native',nimg),('independent',iimg)]):
  cr=im.crop(box).resize((168,168),Image.Resampling.NEAREST);sheet.paste(flatten(cr,bgs['gray']),(col*352+j*176,row*214+28));dr.text((col*352+j*176+4,row*214+8),f"{crossrow['direction']} {crossrow['port']} {name}",fill='black')
sheet.save(P/'join-crown-cross-sections.png');write(O/'continuity-metrics.json',{'method':'Whole native joined 4x frame BOX2x compared to three separately published exact native object frames composed at actual projected roots. Pixel cross-sections sample ±8 published pixels across each crown port; no render correction. Geometry/albedo/normal evidence is separate and actual.','wholeFrame':metric,'crossSections':cross})
# Compact consumer sheets: actual screenshot bytes at logical128, phone32 and landscape32 plus noninteger phase/scale.
cases=json.loads((O/'consumer/cases.json').read_text());write(O/'consumer-checks.json',{'caseCount':len(cases['cases']),'allNearestAfterResize':all(c['smoothing'] is False for c in cases['cases']),'allOrdinaryFinalFilter':all(c['cssImageRendering']=='auto' for c in cases['cases']),'backgrounds':sorted(set(c['background'] for c in cases['cases'])),'pitches':sorted(set(c['pitch'] for c in cases['cases'])),'phases':sorted(set(c['phase'] for c in cases['cases'])),'viewports':sorted(set(tuple(c['viewport']) for c in cases['cases'])),'fixture':'source/consumer-round-04.mjs','runtimeVersion':cases['browser']})
for bg,c in bgs.items():
 rows=[]
 for layout in ['logical','phone','landscape']:
  panels=[]
  for d in DIR:
   im=Image.open(O/f'consumer/{layout}-{d}-phase0.61-{bg}.png').convert('RGB');im.thumbnail((320,440),Image.Resampling.LANCZOS);panels.append((d,im))
  rh=max(im.height for _,im in panels)+28;rows.append((layout,panels,rh))
 sheet=Image.new('RGB',(1280,sum(rh for _,_,rh in rows)),c[:3]);dr=ImageDraw.Draw(sheet);y=0
 for layout,panels,rh in rows:
  for i,(d,im) in enumerate(panels):sheet.paste(im,(i*320,y+24));dr.text((i*320+6,y+6),f'{layout} {d} phase .61 / scale .9875',fill='white' if bg=='dark' else 'black')
  y+=rh
 sheet.save(P/f'consumer-all4-{bg}.png')
write(O/'reproduction-checks.json',reproduction);write(O/'alpha-checks.json',alpha)
au=json.loads((O/'native-audit.json').read_text());sa=json.loads((O/'saved-source-audit.json').read_text());cal=au['camera']['calibration']
camera={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,256],'captureScale':2,'publishedCaptureScale':2,'nativeCaptureScale':4,'nativeFrame':[768,1408],'publishedFrame':[384,704],'fps':12,'camera':{'type':'orthographic','worldMatrix':au['camera']['worldMatrix'],'projectionMatrixAtNative4x':au['camera']['projectionMatrix'],'orthoScale':au['camera']['orthoScale'],'shift':au['camera']['shift'],'pixelAspect':au['camera']['pixelAspect']},'calibration':{k:[v/2 for v in a] for k,a in cal.items()},'nativeMeasurement':{'audit':'candidates/round-04/native-audit.json','savedSourceAudit':'candidates/round-04/saved-source-audit.json','nativeFrame':[768,1408],'nativeCaptureScale':4,'calibration':cal},'publication':'Exact whole native 768x1408 frame BOX-resized once to 384x704; current catalog captureScale2. Native measurement remains scale4 and is never fabricated as native2x.'}
write(D/'camera.json',camera)
asset=json.loads((R/'inputs/source-assetRecord.json').read_text());asset.update(scale=2,height=1.17,artStyle={'revision':'warm-soft-canonical-rock-family','nativeMaterial':'stone_albedo','lighting':'Canonical five translation-invariant SUN lights; no cast shadows','nativeCaptureScale':4,'publishedScale':2,'publication':'whole-frame BOX4x to2x'});write(D/'assetRecord.json',asset)
rig={'assetId':'rock-wall-corner','fps':12,'static':True,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'actions':[]}},'groundRootObject':au['root'],'armatures':[],'actions':[],'sockets':{},'footprint':[1,1],'projection':'top-down-oblique-square-grid','nativeAudit':'candidates/round-04/native-audit.json'};write(D/'rig.json',rig)
checks={'exactBrief':sha(R/'brief.json')=='08a40bb9e70485263776b8006dbec59e7b28f3166f3113f9c170946256b289b4','exactNativeContract':sha(R/'inputs/root-native-contract.json')=='ca67d1e07a787ba0bb2635cb660d0dea9bfb76288fea7ffef938e69f239cc723','originalSourceUnchanged':sha(R/'original-library.blend')=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','exactCanonicalSource':sha(R/'approved-middle/project.blend')=='d64f48e1548d5c56a721850701e5540a7a359e76604ade56ebb5aef8595033c9','savedSourceNoCompanions':sa['noCompanionMiddleSaved'],'sourceReopenedAll4PixelExact':all(x['nativeDecodedMaxDifference']==0 for x in reproduction.values()),'portProfilesFloatTolerance':all(p['maxExposedBoundaryProfileDistance']<=1e-5 for p in sa['ports'].values()),'nativeAlbedoFloatTolerance':sa['boundaryActualVsCanonical']['maxAlbedoLinearError']<1e-6,'nativeNormalQuantizationTolerance':sa['boundaryActualVsCanonical']['maxNormalDelta']<.001,'envelope':all(sa['boundMin'][i]>=(-.5,-.5,0)[i]-1e-7 and sa['boundMax'][i]<=(.5,.5,1.17)[i]+1e-7 for i in range(3)),'completeFramesUnclipped':all(v['outerFrameAlphaMax']==0 for v in alpha.values()),'noUsedExternalImagesOrLibraries':not sa['resources']['images'] and not sa['resources']['libraries'],'wholeBOXPublication':True,'finiteFullCellGroundSupport':json.loads((O/'ground-support-audit.json').read_text())['groundSupportAreaMax']>=.999999,'static1Frame12fps':sa['fps']==12 and sa['frameRange']==[1,1] and sa['staticActions']==0}
validation={'asset':'rock-wall-corner','round':'round-04','allTechnicalChecksPassed':all(checks.values()),'checks':checks,'visualApproval':'Pending original independent judge after coordinator seal; no self approval','nativeValidation':'candidates/round-04/native-audit.json','savedSourceAudit':'candidates/round-04/saved-source-audit.json','cameraRecord':'delivery/round-04/camera.json','nativeCaptures':au['views'],'sourceSHA256':sha(B/'source/round-04.blend'),'bounds':{'min':sa['boundMin'],'max':sa['boundMax']},'ports':sa['ports'],'boundaryActualVsCanonical':sa['boundaryActualVsCanonical'],'reproduction':'candidates/round-04/reproduction-checks.json','continuityMetrics':'candidates/round-04/continuity-metrics.json','consumerChecks':'candidates/round-04/consumer-checks.json','sideAlphaCrossSections':'candidates/round-04/side-alpha-cross-sections.json','groundSupport':'candidates/round-04/ground-support-audit.json','nativeIndependentJoins':'candidates/round-04/native-joins.json','pipeline':'Canonical Cycles48 seed0 BOX stored1.5 no denoise Standard, one symmetric SUN/material recipe; native4x full-frame BOX to published2x','technicalNote':'Profile checks measure exposed mesh-outline vertices, not interior connector cap points. Retained draft audit had measured cap interiors against silhouette and is marked draft. All split conical-apex limiting normals are measured from their real boundary-adjacent loop.'};write(O/'validation.json',validation)
# Bind every used mutable code/skill input and retained draft; no cache or mutable outside path required.
resources={}
for rootdir in [B/'source',B/'candidates',B/'delivery']:
 for p in sorted(rootdir.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p not in [D/'delivery.json',D/'handoff-manifest.json'] and not (p.parent==O and p.name.startswith('packet')):
   assert p.stat().st_size<100_000_000;resources[rel(p)]=rel(p)
previews={p.stem:rel(p) for p in sorted(P.glob('*.png'))}
delivery={'asset':'rock-wall-corner','project':'source/round-04.blend','recipeScript':'source/round-04.py','publicationRecipe':'source/package-round-04.py','validation':'candidates/round-04/validation.json','nativeRecords':{'camera':'delivery/round-04/camera.json','assetRecord':'delivery/round-04/assetRecord.json','rig':'delivery/round-04/rig.json','audit':'candidates/round-04/native-audit.json','savedSourceAudit':'candidates/round-04/saved-source-audit.json','resourceClosure':'delivery/round-04/resource-closure.json'},'heroes':{d:f'candidates/round-04/published-static-{d}.png' for d in DIR},'previews':previews,'revisionTargets':['Square cyan backing patches in N/E','Straight horizontal shell belt in S/W'],'rawFrames':raw,'nativeFrames':native,'atlases':atl,'resources':resources,'publishedSourceScale':2,'nativeCaptureScale':4,'reviewState':'Complete immutable editor handoff for coordinator seal and original independent judge; approval pending','reviewedPriorRound':{'project':'source/round-03.blend','packet':'candidates/round-03/packet.json','reviewSHA256':'6dab41ef8cbf2380f2369a207a4a108a91e3ed3647b0181631cbe9aa347312d3','preservationCheck':'source/round-04-resources/round-03-preservation-check.json'},'retainedDrafts':['source/round-01.blend','source/round-02.blend','source/round-04-draft-a.blend','source/round-04-draft-b.blend','source/round-04-draft-c.blend','source/round-04-draft-d.blend'],'replayDriver':'source/replay-round-04.sh','cleanReplay':['Run source/replay-round-04.sh in an isolated copy; set CORNER_BLENDER/CORNER_PYTHON when needed','blender --background --python source/round-04.py','blender --background --python source/audit-replay-round-04.py','python source/publish-frames-round-04.py','node source/consumer-round-04.mjs','python source/package-round-04.py (final measured evidence/handoff)'],'notes':'Portable asset recipe reads only own source/resources plus system Blender. Saved standalone before companion native append; paired captures remain memory only, no circular source dependency. Published assets preserve full original single-frame rectangles. No pixel repair, warp, mask, added overlap, per-view grade or approval claim.'};write(D/'delivery.json',delivery)
manifest={path:{'sha256':sha(B/path),'bytes':(B/path).stat().st_size} for path in resources}
manifest[rel(D/'delivery.json')]={'sha256':sha(D/'delivery.json'),'bytes':(D/'delivery.json').stat().st_size};write(D/'handoff-manifest.json',{'asset':'rock-wall-corner','round':'round-04','files':manifest,'fileCount':len(manifest),'allTechnicalChecksPassed':all(checks.values()),'deliverySHA256':sha(D/'delivery.json'),'approval':'pending independent original judge'})
print(json.dumps({'delivery':str(D/'delivery.json'),'deliverySHA256':sha(D/'delivery.json'),'manifestSHA256':sha(D/'handoff-manifest.json'),'checks':checks,'fileCount':len(manifest)},indent=2))
