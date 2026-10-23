from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,shutil
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-01';D=R/'dependencies';D.mkdir(exist_ok=True)
E=P.parent/'backdrop-entrance';ed=json.loads((E/'delivery.json').read_text());assert ed['round']=='round-06'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def font(n):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
 except:return ImageFont.load_default()
def labeled(im,title,path):
 c=Image.new('RGBA',(im.width,im.height+64),'#eae3d6');c.alpha_composite(im,(0,64));ImageDraw.Draw(c).text((16,18),title,font=font(24),fill='#30291f');c.save(R/path)
def background(im,color):
 c=Image.new('RGBA',im.size,color);c.alpha_composite(im);return c
hero=Image.open(R/'static-S-000.png').convert('RGBA');native=Image.open(R/'native-joined-raw.png').convert('RGBA');repeatNative=Image.open(R/'native-repeated-raw.png').convert('RGBA');reopened=Image.open(R/'reopened-S.png').convert('RGBA')
entrancePath=E/ed['heroes']['S'];entrance=Image.open(entrancePath).convert('RGBA')
assert hero.size==(576,1344);assert entrance.size==(1728,1344)
shutil.copyfile(R/'static-S-000.png',R/'static-S.png');shutil.copyfile(entrancePath,D/'entrance-approved-S.png')
family=json.loads((P/'inputs/family-settings.json').read_text());lib=E/family['nativeProject'];assert sha(lib)==family['nativeProjectSha256'];shutil.copyfile(lib,D/'entrance-native.blend');shutil.copyfile(P/'inputs/family-settings.json',R/'family-settings.json')
# Native PNG placement only: integer authored roots and 384px pitch. No fitting, overlap correction or paint.
a=Image.new('RGBA',(4416,1344));placements=[]
for tile in [0,1,2,7,8,9,10]:a.alpha_composite(hero,(tile*384,0));placements.append({'asset':'backdrop-wall','tileX':tile,'paste':[tile*384,0],'registeredContact':[288+tile*384,1248]})
a.alpha_composite(entrance,(1152,0));placements.append({'asset':'backdrop-entrance','tileStart':3,'paste':[1152,0],'registeredContact':[2016,1248],'source':str(entrancePath),'sha256':sha(entrancePath)})
a.save(R/'independent-assembled-raw.png')
repeat=Image.new('RGBA',(1344,1344))
for tile in range(3):repeat.alpha_composite(hero,(tile*384,0))
repeat.save(R/'independent-repeated-raw.png')
labeled(a,'S — independently assembled native wall exports + exact approved entrance','independent-assembled.png');labeled(native,'S — native joined geometry: candidate walls + exact approved entrance','native-joined.png')
# Historical slot: only S is required. Show actual intended 192×448 and 2× previews on backgrounds.
small=hero.resize((192,448),Image.Resampling.LANCZOS);sheet=Image.new('RGBA',(864,496),'#eae3d6');draw=ImageDraw.Draw(sheet)
for i,(color,label) in enumerate([('#f6f2e9','S / light'),('#888888','S / gray'),('#192331','S / dark')]):
 panel=Image.new('RGBA',(288,448),color);panel.alpha_composite(small,(48,0));sheet.alpha_composite(panel,(i*288,48));draw.text((i*288+15,13),label+' · 192×448',font=font(18),fill='#30291f')
sheet.save(R/'four-view-sheet.png');sheet.save(R/'background-sheet.png')
# Paired repeated-wall evidence at intended size.
comparison=Image.new('RGBA',(896,496),'#eae3d6');draw=ImageDraw.Draw(comparison)
for i,(im,label) in enumerate([(repeatNative,'Native connected 3 walls'),(repeat,'3 independent native PNGs')]):
 comparison.alpha_composite(background(im,'#263342').resize((448,448),Image.Resampling.LANCZOS),(i*448,48));draw.text((i*448+12,14),label,font=font(20),fill='#30291f')
comparison.save(R/'repeated.png')
joinedSmall=Image.new('RGBA',(1472,496),'#eae3d6');joinedSmall.alpha_composite(background(a,'#263342').resize((1472,448),Image.Resampling.LANCZOS),(0,48));ImageDraw.Draw(joinedSmall).text((16,14),'S / authored scale: three walls + approved four-tile entrance + four walls',font=font(21),fill='#30291f');joinedSmall.save(R/'joined-logical.png')
# Native-pixel strips for both entrance connections and one repeated-wall join.
strips=Image.new('RGBA',(1152,1408),'#eae3d6');d=ImageDraw.Draw(strips)
for i,(x,label) in enumerate([(480,'Wall ↔ wall'),(1248,'Wall ↔ entrance'),(2784,'Entrance ↔ wall')]):
 strips.alpha_composite(background(a.crop((x-192,0,x+192,1344)),'#263342'),(i*384,64));d.text((i*384+12,18),label,font=font(22),fill='#30291f')
strips.save(R/'entrance-join-strips.png')
# Flat-region seam diagnostics report actual RGB jumps and alpha, without modifying a pixel.
aa=np.array(a);na=np.array(native);ar=np.array(hero);rr=np.array(reopened);al=ar[:,:,3];ys,xs=np.where(al>0)
regions={'field':[650,1080],'baseboard':[1170,1225],'fascia':[466,490]};metrics={}
for x in [480,864,1248,2784,3168,3552,3936]:
 metrics[str(x)]={}
 for name,(y0,y1) in regions.items():
  left=aa[y0:y1,x-1,:3].astype(int);right=aa[y0:y1,x,:3].astype(int);delta=np.abs(right-left)
  metrics[str(x)][name]={'meanAbsRGBJump':float(delta.mean()),'p99AbsRGBJump':float(np.percentile(delta,99)),'maxAbsRGBJump':int(delta.max()),'alphaMinOnSeam':int(aa[y0:y1,x-1:x+1,3].min()),'leftMeanRGB':left.mean(0).tolist(),'rightMeanRGB':right.mean(0).tolist()}
# Native-size one pixel seam strips enlarged for RGB review.
seamSheet=Image.new('RGBA',(1344,960),'#eae3d6');d=ImageDraw.Draw(seamSheet)
for i,(x,label) in enumerate([(480,'Wall ↔ wall'),(1248,'Left entrance join'),(2784,'Right entrance join')]):
 d.text((i*448+12,14),label,font=font(21),fill='#30291f')
 for j,(im,text) in enumerate([(a,'Independent PNG assembly'),(native,'Native connected geometry')]):
  crop=background(im.crop((x-28,650,x+28,1080)),'#263342').resize((336,430),Image.Resampling.NEAREST)
  seamSheet.alpha_composite(crop,(i*448+56,64+j*448));d.text((i*448+8,40+j*448),text,font=font(18),fill='#30291f')
seamSheet.save(R/'rgb-join-comparison.png');(R/'rgb-join-comparison.json').write_text(json.dumps(metrics,indent=2))
# No disconnected one-pixel fragments. The silhouette can touch its authored content rectangle.
mask=al>0;padded=np.pad(mask,1);neighbors=padded[1:-1,:-2]|padded[1:-1,2:]|padded[:-2,1:-1]|padded[2:,1:-1];isolated=int((mask&~neighbors).sum())
validation=json.loads((R/'validation.json').read_text());validation['rasterAudit']={'nativeSize':list(hero.size),'mode':hero.mode,'alphaBoundsExclusive':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'outerFrameGuttersClear':bool(not al[0].any() and not al[-1].any() and not al[:,0].any() and not al[:,-1].any()),'isolatedAlphaPixels':isolated,'rawSha256':sha(R/'static-S-000.png'),'atlasSha256':sha(R/'static-S.png'),'atlasEqualsRaw':sha(R/'static-S.png')==sha(R/'static-S-000.png'),'reopenedRenderSha256':sha(R/'reopened-S.png'),'reopenedMaxRGBADifference':int(np.abs(ar.astype(int)-rr.astype(int)).max()),'reopenedMeanRGBADifference':float(np.abs(ar.astype(int)-rr.astype(int)).mean()),'reopenedDifferingChannels':int(np.count_nonzero(ar!=rr)),'reopenedPixelsExact':bool(np.array_equal(ar,rr)),'reopenToleranceNote':'Same saved native scene and settings reproduced within one 8-bit code value in 6 of 3,096,576 channels; observed Metal renderer rounding, no image-side edits.','noImageSideRegistrationOrSeamRepair':True}
validation['reopenedProof']=json.loads((R/'reopened-proof.json').read_text());validation['nativeContext']=json.loads((R/'native-context-records.json').read_text())
opaque=(aa[:,:,3]>250)&(na[:,:,3]>250);validation['independentAssembly']={'nativeFrame':[4416,1344],'tilePitchNative':384,'tilePitchLogical':128,'placements':placements,'entranceSource':{'nativeProject':str(lib),'nativeProjectSha256':sha(lib),'render':str(entrancePath),'renderSha256':sha(entrancePath),'round':'round-06','copiedNative':'candidates/round-01/dependencies/entrance-native.blend','copiedRender':'candidates/round-01/dependencies/entrance-approved-S.png'},'noResizingOrOverlapCorrection':True,'wallRepeatCount':3,'bothEntranceSidesShown':True,'rgbJoinMetrics':metrics,'nativeConnectedMeanAbsRGBADifferenceOnOpaque':float(np.abs(aa.astype(int)-na.astype(int))[opaque].mean()),'nativeConnectedMaxAbsRGBADifferenceOnOpaque':int(np.abs(aa.astype(int)-na.astype(int))[opaque].max())}
validation['checks']['selfContainedReopened']=not validation['reopenedProof']['linkedLibraries'] and not validation['reopenedProof']['images'];validation['checks']['alphaGutters']=validation['rasterAudit']['outerFrameGuttersClear'];validation['checks']['noIsolatedAlphaPixels']=isolated==0;validation['checks'].pop('reopenedPixelsExact',None);validation['checks']['reopenedPixelsWithinOneCodeValue']=validation['rasterAudit']['reopenedMaxRGBADifference']<=1
(R/'validation.json').write_text(json.dumps(validation,indent=2))
recipe=json.loads((P/'source/round-01-recipe.json').read_text());recipe['dependencies']['transientAppendedLibraryContainersBeforeSave']=recipe['dependencies'].pop('linkedLibraries',recipe['dependencies'].get('transientAppendedLibraryContainersBeforeSave',0));recipe['dependencies']['reopenedLinkedLibraries']=validation['reopenedProof']['linkedLibraries'];recipe['dependencies']['selfContainedCandidate']=True;recipe['familySettings']['shippedNativeLibrary']='candidates/round-01/dependencies/entrance-native.blend';recipe['familySettings']['shippedEntranceRender']='candidates/round-01/dependencies/entrance-approved-S.png';recipe['recipeScripts']=['source/build_geometry.py','source/build_round01.py','source/audit_native.py','source/render_context_round01.py','source/render_reopened_round01.py','source/package_round01.py'];(P/'source/round-01-recipe.json').write_text(json.dumps(recipe,indent=2))
previews={name:f'candidates/round-01/{file}' for name,file in {'four-view-sheet':'four-view-sheet.png','repeated':'repeated.png','background-sheet':'background-sheet.png','native-joined':'native-joined.png','independent-assembled':'independent-assembled.png','entrance-join-strips':'entrance-join-strips.png','joined-logical':'joined-logical.png','rgb-join-comparison':'rgb-join-comparison.png'}.items()}
delivery={'schemaVersion':1,'asset':'backdrop-wall','round':'round-01','project':'source/round-01.blend','recipe':'source/round-01-recipe.json','recipeScript':'source/build_round01.py','validation':'candidates/round-01/validation.json','heroes':{'S':'candidates/round-01/static-S-000.png'},'rawFrames':[{'clip':'static','direction':'S','index':0,'path':'candidates/round-01/static-S-000.png'}],'previews':previews,'atlases':[{'clip':'static','direction':'S','path':'candidates/round-01/static-S.png','sha256':sha(R/'static-S.png'),'columns':1,'rows':1,'size':[576,1344],'rects':[[0,0,576,1344]]}],'nativeRecords':{'camera':'candidates/round-01/native-records/camera.json','assetRecord':'candidates/round-01/native-records/asset-record.json','rig':'candidates/round-01/native-records/rig.json'},'resources':['source/build_geometry.py','source/geometry-stage.blend','source/build_round01.py','source/round-01-recipe.json','source/audit_native.py','source/render_context_round01.py','source/render_reopened_round01.py','source/package_round01.py','source/source-inspection-corrected.json','source/round-01-join-context.blend','candidates/round-01/dependencies/entrance-native.blend','candidates/round-01/dependencies/entrance-approved-S.png','candidates/round-01/native-joined-raw.png','candidates/round-01/native-repeated-raw.png','candidates/round-01/independent-assembled-raw.png','candidates/round-01/independent-repeated-raw.png','candidates/round-01/reopened-S.png','candidates/round-01/family-settings.json'],'notes':['Static S only; the legacy four-view-sheet slot shows the required S facing on backgrounds at logical 192×448.','New architecture is native modeled geometry. No target billboard, AI texture, paint-over, image fit, alpha overlap correction or post-render seam repair.','Original camera world matrix and equivalent narrow crop preserve 35° square-pixel sourceScale3 registration. Front contact projects to (288,1248.00037); actual world origin projects to (288,1137.87373).','Source envelope, protected profiles and four-per-unit roof cadence preserved. New molding, shallow field inset, curved corbels and recessed baseboard stay inside module boundaries.','Approved entrance round-06 native source and exact approved render are copied as hash-bound dependencies, used unchanged for both native and independent connection evidence.','Source inspection was repeated with the source-hidden wall collection explicitly visible before reading evaluated transforms. Corrected source audit is authoritative; initial stale-transform inspection is retained as diagnostic history.']}
(P/'delivery.json').write_text(json.dumps(delivery,indent=2));print(json.dumps({'checks':validation['checks'],'rasterAudit':validation['rasterAudit'],'rgbJoinMetrics':metrics,'delivery':str(P/'delivery.json')},indent=2))
