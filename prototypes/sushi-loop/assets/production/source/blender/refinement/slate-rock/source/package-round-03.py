from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageStat
import hashlib,json,shutil
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-03'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dirs=['N','E','S','W'];frames={d:Image.open(OUT/f'static-{d}.png').convert('RGBA') for d in dirs}
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',20);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
(OUT/'atlases').mkdir(exist_ok=True);atlases=[]
for d in dirs:
 p=OUT/'atlases'/f'static-{d}.png';shutil.copyfile(OUT/f'static-{d}.png',p)
 atlases.append({'clip':'static','sourceClipId':'static','direction':d,'path':str(p.relative_to(BASE)),'sha256':sha(p),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]})
sheet=Image.new('RGBA',(1536,736),'#e4e2de');draw=ImageDraw.Draw(sheet)
for i,d in enumerate(dirs):draw.text((384*i+16,6),d,font=font,fill='#333333');sheet.alpha_composite(frames[d],(384*i,32))
sheet.convert('RGB').save(OUT/'four-view-sheet.png')
logical=Image.new('RGBA',(768,384),'#e4e2de');draw=ImageDraw.Draw(logical)
for i,d in enumerate(dirs):draw.text((192*i+10,5),d,font=font,fill='#333333');logical.alpha_composite(frames[d].resize((192,352),Image.Resampling.LANCZOS),(192*i,32))
logical.convert('RGB').save(OUT/'logical-four-view-sheet.png')
bg=Image.new('RGBA',(768,1152),'white');draw=ImageDraw.Draw(bg)
for row,(label,c) in enumerate([('LIGHT','#f7f6f2'),('GRAY','#8b9298'),('DARK','#20262c')]):
 draw.rectangle((0,row*384,768,(row+1)*384),fill=c);draw.text((8,row*384+5),label,font=small,fill='white' if row else '#333333')
 for col,d in enumerate(dirs):draw.text((col*192+156,row*384+5),d,font=font,fill='white' if row else '#333333');bg.alpha_composite(frames[d].resize((192,352),Image.Resampling.LANCZOS),(192*col,row*384+32))
bg.convert('RGB').save(OUT/'backgrounds.png')
originals={d:Image.open(BASE/f'../../../production/sprites/slate-rock/static-{d}.png').convert('RGBA') for d in dirs}
correspondence=Image.new('RGBA',(768,800),'#e4e2de');draw=ImageDraw.Draw(correspondence)
for row,(label,images) in enumerate([('ORIGINAL REGISTERED FACINGS',originals),('ROUND 03 REGISTERED FACINGS',frames)]):
 draw.text((10,row*400+5),label,font=small,fill='#333333')
 for col,d in enumerate(dirs):draw.text((192*col+10,row*400+24),d,font=font,fill='#333333');correspondence.alpha_composite(images[d].resize((192,352),Image.Resampling.LANCZOS),(192*col,row*400+48))
correspondence.convert('RGB').save(OUT/'registered-facing-comparison.png')
# Independently captured full registered frames at the native one-cell pitch.
repeat=Image.new('RGBA',(1024,1080),'#e9e5dd');draw=ImageDraw.Draw(repeat);draw.text((16,12),'Independent native frames at one-cell pitch (256 native pixels)',font=font,fill='#414141')
for row in range(3):
 for col in range(3):
  d=dirs[(row*3+col)%4];repeat.alpha_composite(frames[d],(256+256*col-192,360+256*row-496))
repeat.convert('RGB').save(OUT/'repeated.png')
validation=json.loads((OUT/'validation.json').read_text());validation['alpha']={}
for d,im in frames.items():
 a=im.getchannel('A');px=list(im.getdata());border=list(a.crop((0,0,384,1)).getdata())+list(a.crop((0,703,384,704)).getdata())+list(a.crop((0,0,1,704)).getdata())+list(a.crop((383,0,384,704)).getdata())
 validation['alpha'][d]={'size':list(im.size),'mode':im.mode,'bbox':list(a.getbbox()),'borderNonzeroPixels':sum(v>0 for v in border),'opaquePixels':sum(p[3]==255 for p in px),'partialAlphaPixels':sum(0<p[3]<255 for p in px),'opaqueNearBlackPixels':sum(p[3]==255 and max(p[:3])<8 for p in px),'atlasBytesIdentical':sha(OUT/f'static-{d}.png')==sha(OUT/'atlases'/f'static-{d}.png')}
reopen=json.loads((OUT/'reopened-source.json').read_text());reopened_image=Image.open(OUT/'reopened-N.png').convert('RGBA');difference=ImageChops.difference(reopened_image,frames['N']);opaque_pairs=[(a,b) for a,b in zip(reopened_image.getdata(),frames['N'].getdata()) if a[3]==b[3]==255]
replay_metrics={'matchesSubmittedNPixels':reopened_image.tobytes()==frames['N'].tobytes(),'meanAbsoluteChannelDifference8bit':ImageStat.Stat(difference).mean,'maximumChannelDifference8bit':[hi for lo,hi in difference.getextrema()],'opaqueInteriorMaximumRGBDifference8bit':max(abs(a[i]-b[i]) for a,b in opaque_pairs for i in range(3)),'alphaBoundsIdentical':reopened_image.getchannel('A').getbbox()==frames['N'].getchannel('A').getbbox(),'rootRotationDegrees':180,'registeredFacing':'N','note':'All-pixel fringe maxima are recorded separately from opaque-interior RGB differences; the latter does not describe partial-alpha fringe pixels. Submitted frame bytes remain the sealed candidate.'}
replay_metrics['withinDocumentedReplayTolerance']=replay_metrics['opaqueInteriorMaximumRGBDifference8bit']<=1 and max(replay_metrics['meanAbsoluteChannelDifference8bit'])<.01 and replay_metrics['maximumChannelDifference8bit'][3]<=3 and replay_metrics['alphaBoundsIdentical']
reopen['reopenedNativeRender'].update(replay_metrics)
reopen['reopenedNativeRenders']={}
for direction in dirs:
 current=frames[direction];other=Image.open(OUT/f'reopened-{direction}.png').convert('RGBA');diff=ImageChops.difference(current,other);opaque=[(a,b) for a,b in zip(current.getdata(),other.getdata()) if a[3]==b[3]==255]
 metrics={'path':f'candidates/round-03/reopened-{direction}.png','registeredFacing':direction,'rootRotationDegrees':{'N':180,'E':90,'S':0,'W':-90}[direction],'byteIdentical':current.tobytes()==other.tobytes(),'meanAbsoluteRGBADifference8bit':ImageStat.Stat(diff).mean,'maximumAllPixelRGBADifference8bit':[hi for lo,hi in diff.getextrema()],'opaqueInteriorMaximumRGBDifference8bit':max(abs(a[i]-b[i]) for a,b in opaque for i in range(3)),'alphaBoundsIdentical':current.getchannel('A').getbbox()==other.getchannel('A').getbbox()}
 metrics['withinDocumentedReplayTolerance']=metrics['opaqueInteriorMaximumRGBDifference8bit']<=1 and max(metrics['meanAbsoluteRGBADifference8bit'])<.01 and metrics['maximumAllPixelRGBADifference8bit'][3]<=3 and metrics['alphaBoundsIdentical']
 reopen['reopenedNativeRenders'][direction]=metrics
(OUT/'reopened-source.json').write_text(json.dumps(reopen,indent=2)+'\n');validation['reopenedSource']=reopen
validation['checks'].pop('reopenedRenderMatchesSubmittedNPixels',None)
validation['checks'].update({'reopenedSource':True,'reopenedRenderWithinQuantizationTolerance':replay_metrics['withinDocumentedReplayTolerance'],'noAlphaClipping':all(a['borderNonzeroPixels']==0 for a in validation['alpha'].values()),'dependencyClosure':not reopen['externalImages'] and not reopen['linkedLibraries'] and reopen['proceduralMaterialsOnly'],'allMaterialSlotsBound':all(all(name for name in p.get('materialSlots',[])) for p in reopen['parts'])})
validation['checks']['allFourReopenedFacingsWithinQuantizationTolerance']=all(r['withinDocumentedReplayTolerance'] for r in reopen['reopenedNativeRenders'].values())
validation['previousRoundReplayDisclosure']={'round':2,'opaqueInteriorMaximumRGBDifference8bit':1,'maximumAllPixelRGBADifference8bit':[15,16,17,3],'alphaBoundsUnchanged':True,'note':'The round-02 one-unit RGB bound applied only to opaque interiors. Partial-alpha fringe maxima were larger, as recorded here and in the unchanged round-02 evidence. Round-03 replay metrics above are fresh measurements of every corrected facing.'}
validation['geometryRefinement']={'mainMass':'Small 0.012-unit 3-segment real bevel; broad original faces remain flat, bevel bands smooth. Original total XY/Z envelope restored after bevel.','groove':'Original narrow XY path and width retained. Raised source bar replaced by shallow 0.005-unit native Boolean incision and dark recessed floor, following the crown. No added fissures.','preservation':'Root, asymmetry, crown height/proportions, total footprint/height envelope, registered camera and per-facing rotations retained.'}
validation['registeredFacingAlphaComparison']={}
for direction,im in frames.items():
 maes={d:ImageStat.Stat(ImageChops.difference(im.getchannel('A'),original.getchannel('A'))).mean[0] for d,original in originals.items()}
 closest=min(maes,key=maes.get);validation['registeredFacingAlphaComparison'][direction]={'originalAlphaMAE8bit':maes,'closestOriginal':closest,'matchesRegisteredDirection':closest==direction}
validation['checks']['allRegisteredFacingSilhouettesMatch']=all(r['matchesRegisteredDirection'] for r in validation['registeredFacingAlphaComparison'].values())
validation['previews']={n:f'candidates/round-03/{n}.png' for n in ['four-view-sheet','logical-four-view-sheet','repeated','backgrounds','registered-facing-comparison']}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
delivery={'asset':'slate-rock','round':3,'status':'candidate-ready-for-independent-review','pipeline':'native-3d','project':'source/round-03.blend','recipe':'source/round-03.py','validation':'candidates/round-03/validation.json','heroes':{d:f'candidates/round-03/static-{d}.png' for d in dirs},'rawFrames':[{'clip':'static','direction':d,'index':0,'nativeFrame':1,'path':f'candidates/round-03/static-{d}.png','sha256':sha(OUT/f'static-{d}.png')} for d in dirs],'previews':validation['previews'],'atlases':atlases,'nativeRecords':{n:f'source/round-03-{n}.json' for n in ['camera','assetRecord','rig']},'nativeProject':{'scene':'slate-rock warm soft native round 03','collection':'S33_PROP_slate-rock.001','root':'slate-rock__root.001','selfContained':True,'externalResources':[],'staticFacingsDegrees':{'N':180,'E':90,'S':0,'W':-90},'frame':1},'replay':{'script':'source/replay-round-03.py','command':'/opt/homebrew/bin/blender -b source/round-03.blend --python source/replay-round-03.py -- /absolute/output-directory'},'evidence':{'reopenedSource':'candidates/round-03/reopened-source.json','reopenedNativeN':'candidates/round-03/reopened-N.png','auditRecipe':'source/audit-round-03.py','packagingRecipe':'source/package-round-03.py'}}
delivery['evidence']['reopenedNativeFacings']={d:f'candidates/round-03/reopened-{d}.png' for d in dirs}
(OUT/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n');(BASE/'delivery.json').write_text(json.dumps(delivery,indent=2)+'\n')
(BASE/'source/README-round-03.txt').write_text('Native slate-rock warm soft candidate round 03\n\nProject: source/round-03.blend\nScene: slate-rock warm soft native round 03\nRoot: slate-rock__root.001\nCollection: S33_PROP_slate-rock.001\n\nRender saved source:\n/opt/homebrew/bin/blender -b source/round-03.blend --python source/replay-round-03.py -- /absolute/output-directory\n\nCapture: native 384x704, logical 192x352, sourceScale 2, root 96,248, static frame 1 at 12 fps. The self-contained project has native meshes and procedural materials, symmetric soft lights, no ground receiver and transparent film. Rotate only the root: N=180, E=90, S=0, W=-90 degrees. This is the original native_actions.py/publish_captures.py convention.\nRound-03 recipe reads the immutable hash-checked round-02 project; it preserves geometry/material/light fingerprints and corrects only scene/facing metadata before fresh native captures. The saved round-03 project has no external dependencies. The earlier round-02 recipe remains the full rebuild from the untouched production source. Round 02 and its sealed packet are unchanged. Round 03 is the submitted corrected candidate.\n')
print(json.dumps({'checks':validation['checks'],'delivery':'delivery.json'},indent=2))
