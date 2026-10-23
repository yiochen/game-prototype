from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import hashlib,json,shutil
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-02'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dirs=['N','E','S','W'];frames={d:Image.open(OUT/f'static-{d}.png').convert('RGBA') for d in dirs}
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20)
small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
# Unmodified full-frame atlases: one native frame per static facing.
(OUT/'atlases').mkdir(exist_ok=True);atlases=[]
for d in dirs:
 p=OUT/'atlases'/f'static-{d}.png';shutil.copyfile(OUT/f'static-{d}.png',p)
 atlases.append({'clip':'static','sourceClipId':'idle','direction':d,'path':str(p.relative_to(BASE)),'sha256':sha(p),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]})
# Presentation-only composites preserve the whole registered frame.
sheet=Image.new('RGBA',(384*4,736),'#e4e2de');draw=ImageDraw.Draw(sheet)
for i,d in enumerate(dirs):draw.text((i*384+16,6),d,font=font,fill='#333333');sheet.alpha_composite(frames[d],(384*i,32))
sheet.convert('RGB').save(OUT/'four-view-sheet.png')
logical=Image.new('RGBA',(192*4,384),'#e4e2de');draw=ImageDraw.Draw(logical)
for i,d in enumerate(dirs):draw.text((i*192+10,5),d,font=font,fill='#333333');logical.alpha_composite(frames[d].resize((192,352),Image.Resampling.LANCZOS),(i*192,32))
logical.convert('RGB').save(OUT/'logical-four-view-sheet.png')
bg=Image.new('RGBA',(768,384*3),'white');draw=ImageDraw.Draw(bg)
for row,(name,c) in enumerate([('LIGHT','#f7f6f2'),('NEUTRAL','#8b9298'),('DARK','#20262c')]):
 draw.rectangle((0,row*384,768,(row+1)*384),fill=c);draw.text((8,row*384+5),name,font=small,fill='white' if row else '#333333')
 for col,d in enumerate(dirs):draw.text((col*192+156,row*384+5),d,font=font,fill='white' if row else '#333333');bg.alpha_composite(frames[d].resize((192,352),Image.Resampling.LANCZOS),(col*192,row*384+32))
bg.convert('RGB').save(OUT/'backgrounds.png')
repeat=Image.new('RGBA',(1024,920),'#e9e5dd');draw=ImageDraw.Draw(repeat);draw.text((16,12),'Independent native frames at one-cell pitch (256 native pixels)',font=font,fill='#414141')
for row in range(3):
 for col in range(3):
  d=dirs[(row*3+col)%4];repeat.alpha_composite(frames[d],(256+256*col-192,260+256*row-496))
repeat.convert('RGB').save(OUT/'repeated.png')
validation=json.loads((OUT/'validation.json').read_text());validation['alpha']={}
for d,im in frames.items():
 a=im.getchannel('A');bbox=a.getbbox();px=list(im.getdata());border=list(a.crop((0,0,384,1)).getdata())+list(a.crop((0,703,384,704)).getdata())+list(a.crop((0,0,1,704)).getdata())+list(a.crop((383,0,384,704)).getdata())
 validation['alpha'][d]={'size':list(im.size),'mode':im.mode,'bbox':list(bbox),'borderNonzeroPixels':sum(v>0 for v in border),'opaquePixels':sum(v[3]==255 for v in px),'partialAlphaPixels':sum(0<v[3]<255 for v in px),'opaqueNearBlackPixels':sum(v[3]==255 and max(v[:3])<8 for v in px),'atlasBytesIdentical':sha(OUT/f'static-{d}.png')==sha(OUT/'atlases'/f'static-{d}.png')}
validation['reopenedSource']=json.loads((OUT/'reopened-source.json').read_text());validation['checks']['reopenedSource']=True;validation['checks']['reopenedRenderMatchesSubmittedNPixels']=validation['reopenedSource']['reopenedNativeRender']['matchesSubmittedNPixels'];validation['checks']['noAlphaClipping']=all(r['borderNonzeroPixels']==0 for r in validation['alpha'].values());validation['previews']={'four-view-sheet':'candidates/round-02/four-view-sheet.png','logical-four-view-sheet':'candidates/round-02/logical-four-view-sheet.png','repeated':'candidates/round-02/repeated.png','backgrounds':'candidates/round-02/backgrounds.png'}
original_by_name={p['name']:p for p in validation['sourceOriginal']['parts']}
current_by_name={p['name']:p for p in validation['reopenedSource']['partTransforms']}
support_deltas={name:max(abs(p[field][i]-current_by_name[name][field][i]) for field in ('location','rotation','scale') for i in range(3)) for name,p in original_by_name.items() if '__leg_' in name or '__rung_' in name}
source_camera=json.loads((BASE/'inputs/source-camera.json').read_text());current_camera=json.loads((BASE/'source/round-02-camera.json').read_text())
camera_delta=max(abs(source_camera['camera']['worldMatrix'][r][c]-current_camera['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4))
projection_delta=max(abs(source_camera['camera']['projectionMatrix'][r][c]-current_camera['camera']['projectionMatrix'][r][c]) for r in range(4) for c in range(4))
validation['sourceComparison']={'supportTransformMaximumDeltas':support_deltas,'cameraWorldMatrixMaximumDelta':camera_delta,'cameraProjectionMatrixMaximumDelta':projection_delta,'metadataScaleCorrection':{'legacySourceRecord':4,'actualDeliveredScale':2,'cameraCalibrationPreservedAtLogicalScale':True},'nativeSourceBoundsUnchanged':validation['capture']['maximumBoundDelta']==0}
validation['checks']['supportTransformsPreserved']=all(v==0 for v in support_deltas.values())
validation['checks']['sourceCameraMatrixPreserved']=camera_delta<.000001 and projection_delta<.000001
validation['checks']['dependencyClosure']=not validation['reopenedSource']['externalImages'] and not validation['reopenedSource']['linkedLibraries'] and validation['dependencies']['selfContained']
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
delivery={'asset':'stool-blue','round':2,'status':'candidate-ready-for-independent-review','pipeline':'native-3d','project':'source/round-02.blend','recipe':'source/round-02.py','validation':'candidates/round-02/validation.json','heroes':{d:f'candidates/round-02/static-{d}.png' for d in dirs},'rawFrames':[{'clip':'static','sourceClipId':'idle','direction':d,'frame':0,'nativeFrame':1,'path':f'candidates/round-02/static-{d}.png','sha256':sha(OUT/f'static-{d}.png')} for d in dirs],'previews':validation['previews'],'atlases':atlases,'nativeRecords':{'camera':'source/round-02-camera.json','assetRecord':'source/round-02-assetRecord.json','rig':'source/round-02-rig.json'},'nativeProject':{'scene':'stool-blue warm soft native','collection':'S33_PROP_stool_blue.001','root':'stool_blue__root.001','selfContained':True,'externalResources':[],'staticFacingsDegrees':{'N':0,'E':-90,'S':180,'W':90},'frame':1},'replay':{'script':'source/replay-round-02.py','command':'/opt/homebrew/bin/blender -b source/round-02.blend --python source/replay-round-02.py -- /absolute/output-directory','instructions':'Run from this object folder. The project contains the complete scene, native meshes, procedural materials, neutral lighting and registered camera. Replay rotates only the common root; no camera fitting or image processing is used. Full rebuild recipe uses the immutable original source identified and hashed in validation.'},'evidence':{'reopenedSource':'candidates/round-02/reopened-source.json','reopenedNativeN':'candidates/round-02/reopened-N.png','packagingRecipe':'source/package-round-02.py'}}
(OUT/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');(BASE/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
(BASE/'source/README-round-02.txt').write_text('Native stool-blue warm soft candidate round 02\n\nProject: source/round-02.blend\nScene: stool-blue warm soft native\nRoot: stool_blue__root.001\nCollection: S33_PROP_stool_blue.001\n\nRender saved source without rebuilding:\n/opt/homebrew/bin/blender -b source/round-02.blend --python source/replay-round-02.py -- /absolute/output-directory\n\nCapture: native 384x704, logical 192x352, sourceScale 2, root 96,248, 12 fps, static frame 1. The saved project has neutral symmetric lighting, no ground plane and transparent film. Rotate only the common root for N=0, E=-90, S=180, W=90 degrees. All geometry and procedural material resources are packed in the scene. Full rebuild recipe: source/round-02.py. It reads the immutable production-source Blender file named and hashed in candidates/round-02/validation.json. Original source is never resaved. Source input metadata uses legacy scale 4; delivered camera and asset records use actual capture scale 2.\n')
print(json.dumps({'checks':validation['checks'],'delivery':'delivery.json'},indent=2))
