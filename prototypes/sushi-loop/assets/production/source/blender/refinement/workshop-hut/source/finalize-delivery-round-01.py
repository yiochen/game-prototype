"""Build evidence sheets, explicit delivery metadata; never seal or self-approve."""
import json,hashlib,math,shutil
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-01';P=O/'previews';P.mkdir(exist_ok=True);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def sheet(path,files,columns=2,cell=(384,384),labels=None):
 w,h=cell;rows=math.ceil(len(files)/columns);out=Image.new('RGB',(w*columns,(h+25)*rows),'#a7a7a7');draw=ImageDraw.Draw(out)
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGBA');im.thumbnail(cell,Image.Resampling.LANCZOS);x=(i%columns)*w;y=(i//columns)*(h+25);draw.text((x+6,y+5),(labels[i] if labels else Path(p).stem),fill='#111111');bg=Image.new('RGBA',cell,'#a7a7a7');bg.alpha_composite(im,((w-im.width)//2,(h-im.height)//2));out.paste(bg.convert('RGB'),(x,y+25))
 out.save(path)
dirs='NESW'
sheet(P/'four-view-sheet.png',[O/'frames'/f'static-{d}'/'000.png' for d in dirs],4,(192,448),list(dirs))
sheet(P/'native-family.png',[O/'contexts'/f'family-{d}.png' for d in dirs],2,(480,480),list(dirs))
sheet(P/'consumer-family.png',[O/'browser'/f'consumer-family-{d}.png' for d in dirs],2,(480,480),list(dirs))
sheet(P/'base-contact.png',[O/'browser'/f'base-{d}-logical.png' for d in dirs],2,(600,640),list(dirs))
sheet(P/'human-approach.png',[O/'browser'/f'approved-human-{d}-phone.png' for d in dirs],2,(668,720),list(dirs))
sheet(P/'repeated.png',[O/'browser'/f'repeated-{d}-phone.png' for d in dirs],2,(350,520),list(dirs))
sheet(P/'consumer-quarter-phases.png',[O/'browser'/f'family-{d}-gray-phone.png' for d in dirs],2,(668,1440),list(dirs))
sheet(P/'source-target-candidate.png',[B/'inputs/original.png',B/'inputs/target.png',O/'frames/static-S/000.png'],3,(256,598),['Original wholeframe','Frozen style target wholeframe','Candidate native S wholeframe'])
sheet(P/'old-canopy-diagnostic.png',[O/'browser'/f'old-cover-diagnostic-{d}.png' for d in dirs],2,(538,1440),list(dirs))
audit=read(O/'native-audit.json');human=read(O/'approved-human-audit.json');browser=read(O/'browser/browser-evidence.json');repro=read(O/'reproduction.json')
# Every decoded channel is compared, including RGB under alpha; do not alter PNG bytes.
for rec in repro['captures']:
 a=Image.open(B/rec['path']).convert('RGBA');b=Image.open(B/rec['reference']).convert('RGBA');delta=ImageChops.difference(a,b);rec['decodedRGBAIdentical']=a.tobytes()==b.tobytes();rec['maxChannelDifference']=max(x[1] for x in delta.getextrema());rec['pixelSHA256']=hashlib.sha256(a.tobytes()).hexdigest();rec['referencePixelSHA256']=hashlib.sha256(b.tobytes()).hexdigest()
repro['allDecodedRGBAIdentical']=all(r['decodedRGBAIdentical'] for r in repro['captures']);repro['metadataNote']='PNG file hashes differ because Blender writes Date and RenderTime text. Actual reviewed candidate bytes remain untouched; decodedRGBA is identical for all4 clean-process renders.';write(O/'reproduction.json',repro)
assert repro['allDecodedRGBAIdentical']
# Native geometry-derived technical measurements, separate from independent visual judgment.
low=[v for obj in audit['objects'] for v in obj['vertices'] if v[2]<.065-1e-8]
repairbox={'x':[-.4375,.4375],'y':[-.56,.45],'z':[-.012,.065]};outside=[v for v in low if any(v[i]<repairbox[k][0]-1e-5 or v[i]>repairbox[k][1]+1e-5 for i,k in enumerate(['x','y','z']))]
# Full polygon clipping below .12 is unnecessary for the clear low corridor because every mesh
# with any vertex below .12 has its entire evaluated XY box outside the exterior corridor.
corridor=[]
for obj in audit['objects']:
 if obj['bounds']['min'][2]>=.12:continue
 b=obj['bounds'];intersect=b['max'][0]>-.28 and b['min'][0]<.04 and b['min'][1]<-.56-1e-5 and b['max'][1]>-1.26
 if intersect:corridor.append(obj['name'])
rebuild=read(O/'clean-rebuild-audit.json')
for rec in rebuild['captures']:
 a=Image.open(B/rec['path']).convert('RGBA');b=Image.open(B/rec['reference']).convert('RGBA');rec['decodedRGBAIdentical']=a.tobytes()==b.tobytes();rec['maxChannelDifference']=max(x[1] for x in ImageChops.difference(a,b).getextrema())
rebuild['allDecodedRGBAIdentical']=all(r['decodedRGBAIdentical'] for r in rebuild['captures']);write(O/'clean-rebuild-audit.json',rebuild)
assert rebuild['geometryExact'] and rebuild['allDecodedRGBAIdentical']
additional=read(O/'additional-native-contract.json')
validation={'additionalNativeContract':'candidates/round-01/additional-native-contract.json','cleanRecipeRebuild':'candidates/round-01/clean-rebuild-audit.json','asset':'workshop-hut','stage':'complete editor handoff; independent verdict pending','frozenBriefSHA256':sha(B/'brief.json'),'nativeValidation':'candidates/round-01/native-audit.json','contextValidation':'candidates/round-01/context-audit.json','approvedHumanValidation':'candidates/round-01/approved-human-audit.json','browserValidation':'candidates/round-01/browser/browser-evidence.json','reproduction':'candidates/round-01/reproduction.json','actualMeasuredGeometrySHA256':audit['geometrySHA256'],'capture':{'nativeFrame':[384,896],'logicalFrame':[192,448],'root':[96,352],'sourceScale':2,'cellSize':128,'fps':12,'frames':1,'loop':False,'filterSize':audit['settings']['filterSize'],'cameraCalibration':audit['camera']['calibration']},'nativeCaptures':audit['nativeCaptures'],'lowRepairBox':{'box':repairbox,'evaluatedVerticesBelowTop':len(low),'outsideVertices':outside},'exteriorLowCorridor':{'localX':[-.28,.04],'localY':[-1.26,-.56],'heightChecked':[0,.12],'intersectingMeshBoxes':corridor,'note':'Above this band, ordinary source-facing eaves project toY-.588. Approved actor full visible triangle meshes have zero hut overlap at all demonstrated positions.'},'pairedContact':{'hutSHA256':audit['sourceSHA256'],'floorSHA256':audit['pairedSupport']['floorSHA256'],'finitePatches':3,'areaEach':.0048,'patchSeparationWorld':[.55,.50],'maxAbsoluteDifferenceWorld':max(c['maxAbsoluteDifferenceWorld'] for c in audit['pairedSupport']['contacts']),'exactSamples':243},'nativeHuman':{'sourceSHA256':human['sources']['approvedRosa']['sha256'],'authoredRootScalePreserved':[1.25,1.25,1.25],'extraWorldFittingScale':1,'metadataAnatomyHeight':1.2746186554431915,'actualStandFrame1VisibleHeight':human['humanEvidence'][0]['bounds']['max'][2]-human['humanEvidence'][0]['bounds']['min'][2],'pointsUnrotatedWorld':[[.66,-.90,.22],[.66,-.67,.22]],'actorFacesFacadeRelativeRadians':math.pi,'zeroHutTriangleOverlap':all(r['hutOverlapTrianglePairs']==0 for r in human['humanEvidence']),'zeroSubmarineTriangleOverlap':all(r['submarineOverlapTrianglePairs']==0 for r in human['humanEvidence']),'finiteSoleAreaEach':.0009,'soleFinitePatchMaxDifferenceWorld':max(p['maxAbsoluteDifferenceWorld'] for r in human['humanEvidence'] for p in r['soleSupportFiniteAreas']),'soleCornerGapOverDeckGroove':'Some extreme sole vertices bridge actual beveled plank grooves by up to .0038283world; finite useful sole areas contact deck exactly. This is not global root fitting or a whole foot float.'},'browser':{'screenshots':len(browser['records']),'errors':browser['errors'],'sizesPxPerCell':{'logical':128,'phone':55.7143,'landscape':31.3393},'phases':[0,.25,.5,.75],'backgrounds':['light','gray','dark'],'codeHashes':browser['inputs']['renderer'],'allNativeBufferSmoothingDisabled':all(not c['imageSmoothingEnabled'] for r in browser['records'] for c in r['cases']),'support':'ActualsupportedBy:dock-deck for hut/sub and physical on-deck approved human only; original analytical roots/offsets retained.'},'reproductionDecodedRGBAIdentical':repro['allDecodedRGBAIdentical'],'lighting':{'horizontalSymmetry':4,'centeredOverheadWatts':360,'cardinalFillWattsEach':180,'groundGeometry':False,'directionalGroundShadow':False,'recipe':'Persisted common neutral world+.45 strength, standard exposure-1.8. Same recipe all4 facings.'},'limits':['Closed static exterior facade only; no opening/pass-through gameplay claim. Doorleaf has .036world ground clearance with fixed frame/hinge attachment and low threshold; marker is unchanged.','Existing source cover collision remains diagnostic; sample covered/uncover frames0/5/11 in all4 directions are retained. Future cover repair owns clearance and must bind exact accepted hut.','Old source submarine support gap.055 remains diagnostic, assigned to later submarine repair.','Actual consumer retains current submarine authored character projection and sourceScale; native diagnostic submarine uses common environment camera and exact original meshes. Native physical Rosa uses exact approved geometry under environment camera. Actual consumer uses exact approved published35degree stand atlas; no actor body pixelidentity claimed.','Retained originalb176 actor diagnostics and genericunit-root failed draft are superseded by exact current approved actor evidence.']}
assert not outside and not corridor
assert validation['nativeHuman']['zeroHutTriangleOverlap'] and validation['nativeHuman']['zeroSubmarineTriangleOverlap']
assert validation['nativeHuman']['soleFinitePatchMaxDifferenceWorld']<1e-5
write(O/'validation.json',validation)
raw=[];atl=[]
for d in dirs:
 p=O/'frames'/f'static-{d}'/'000.png';a=O/'atlases'/f'static-{d}.png';assert Image.open(a).size==(384,896) and p.read_bytes()==a.read_bytes()
 raw.append({'clip':'static','direction':d,'index':0,'path':str(p.relative_to(B)),'sha256':sha(p)})
 atl.append({'clip':'static','direction':d,'path':str(a.relative_to(B)),'sha256':sha(a),'columns':1,'rows':1,'size':[384,896],'rects':[[0,0,384,896]],'fps':12,'loop':False,'frameOrder':[0],'frames':1,'sourceScale':2,'frameSize':[192,448],'root':[96,352]})
# Only own mutable output trees. Coordinator additionally binds frozen inputs/brief/target and reviews.
resources=[]
for folder in [B/'source',O]:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.name not in ['packet.json','delivery.snapshot.json','finalize-delivery-round-01.log']:
   assert p.stat().st_size<100_000_000
   resources.append({'path':str(p.relative_to(B)),'sha256':sha(p)})
delivery={'asset':'workshop-hut','round':1,'status':'complete editor handoff awaiting independent judge; unsealed','frozenBriefSHA256':sha(B/'brief.json'),'project':'source/round-01.blend','projectSHA256':sha(B/'source/round-01.blend'),'recipeScript':'source/build-round-01.py','replayScript':'source/replay-round-01.py','contextRecipeScripts':['source/capture-context-round-01.py','source/capture-cover-references-round-01.py','source/capture-approved-human-round-01.py'],'validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/native-records/camera.json','assetRecord':'candidates/round-01/native-records/asset.json','rig':'candidates/round-01/native-records/rig.json'},'heroes':{d:f'candidates/round-01/frames/static-{d}/000.png' for d in dirs},'rawFrames':raw,'atlases':atl,'previews':{n:f'candidates/round-01/previews/{n}.png' for n in ['four-view-sheet','repeated','native-family','consumer-family','base-contact','human-approach','consumer-quarter-phases']},'additionalPreviews':{'source-target-candidate':'candidates/round-01/previews/source-target-candidate.png','old-canopy-diagnostic':'candidates/round-01/previews/old-canopy-diagnostic.png'},'resources':resources,'approval':'None. Coordinator seals completed delivery for original independent judge. Editor makes no visual approval or wholefamily clearance claim.'}
write(B/'delivery.json',delivery)
print('DELIVERY_READY',sha(B/'delivery.json'),len(resources),validation['pairedContact'],validation['nativeHuman'],flush=True)
