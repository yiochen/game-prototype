"""Assemble evidence previews/provenance only; never changes source or native art."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-06';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
peer=B.parent/'dock-floor';R=B/'source/resources/approved-human-v3/independent-floor-audit';R.mkdir(exist_ok=True)
paths=['candidates/round-04/approved-human-physical-audit.json','candidates/round-04/approved-human-contact-clearance.json','candidates/round-04/human-context-provenance.json','source/audit-approved-human-round04.py','source/audit-approved-human-clearance-round04.py','source/resources/approved-human-v3/native_actions.py'];copies=[]
for rel in paths:
 p=peer/rel;q=R/p.name
 if q.exists():assert q.read_bytes()==p.read_bytes()
 else:shutil.copyfile(p,q)
 copies.append({'originalObject':'dock-floor','originalPath':rel,'path':str(q.relative_to(B)),'sha256':sha(q)})
(O/'approved-human-crosscheck-binding.json').write_text(json.dumps({'method':'Exact independent companion audit outputs/helpers retained; paths inside copied originals remain historical and resolve via this explicit adapter. Own native approved-human capture is independently generated and primary native body evidence. No sibling packet dependency.','copies':copies,'sourceMapping':{'source/resources/approved-human-v3/customer-rosa-approved.blend':'source/resources/approved-human-v3/customer-rosa-approved.blend','source/resources/approved-human-v3/rig.json':'source/resources/approved-human-v3/customer-rosa-approved-rig.json','source/resources/approved-human-v3/camera.json':'source/resources/approved-human-v3/customer-rosa-approved-camera.json','inputs/paired-native/dock-entry-round-06.blend':'source/round-06.blend'}},indent=2))
peerprov=read(R/'human-context-provenance.json');d=read(O/'approved-human-native-validation.json');measure=d['humanPoseMeasurements'];browserbase='source/resources/paired-consumer-v3/floor-packet/source/resources/browser-v3-native-sampling/'
atlases=[]
for a in peerprov['actualConsumerAtlases']:
 a=dict(a);a['path']=browserbase+Path(a['path']).name;assert sha(B/a['path'])==a['sha256'];atlases.append(a)
feet=[f for x in measure for f in x['visibleFeet']];sole=[x['lowestVisibleSoleRelativeRootZ'] for x in measure];cross=read(R/'approved-human-contact-clearance.json');clearances=[c['conservativeLateralClearance'] for x in cross['records'] for c in x['postCapCrossSections'] if c['conservativeLateralClearance'] is not None]
report={'primaryConsumerActor':'Exact current published approved Rosa whole-frame atlases, unchanged authored35degreecamera, frame/root/scale; walk catalog indices0..8 are actual traversal. No new actor source publication or fitted proxy.','approvedNativeSource':d['humanApprovedSource'],'nativeContextEvidence':'candidates/round-06/approved-human-native-validation.json','crosscheckBinding':'candidates/round-06/approved-human-crosscheck-binding.json','authoredCamera':{'path':'source/resources/approved-human-v3/customer-rosa-approved-camera.json','sha256':sha(B/'source/resources/approved-human-v3/customer-rosa-approved-camera.json'),'elevationDegrees':35,'logicalFrame':[192,320],'root':[96,248],'sourceScale':2,'cameraWorldMatrix':read(B/'source/resources/approved-human-v3/customer-rosa-approved-camera.json')['camera']['worldMatrix']},'derivedNativeCamera':{'elevationDegrees':55.00797980144134,'meaning':'Technical common-environment body/physical evidence, not a replacement for primary published35degree sprite and no pixelparity claim.','logicalFrame':[768,768],'root':[384,440],'basis':{'x':[128,0],'depth':[0,128],'height':[0,-89.60003662109375]}},'actualConsumerAtlases':atlases,'path':d['humanPath'],'nativePathPoseCount':len(measure),'allNativeRootScalesPreserved':all(x['actualRootScale']==[1.25]*3 for x in measure),'visibleFootMeshNames':sorted(set(f['name'] for f in feet)),'soleRelativeToRootRange':[min(sole),max(sole)],'maxAbsoluteSoleRootError':max(abs(x) for x in sole),'visibleWalkPoseHeightsRange':[min(x['visibleBodyBoundsWorld'][1][2]-x['pathPositionFloorWorld'][2] for x in measure),max(x['visibleBodyBoundsWorld'][1][2]-x['pathPositionFloorWorld'][2] for x in measure)],'measuredStandPoseHeights':peerprov['measuredPoseHeights'],'metadataAnatomicalHeight':1.2746186554431915,'conservativeNativePostCapMinimumLateralClearance':min(clearances),'clearanceMethod':'Independent retained actual-triangle Y/Z-slab clipping audit at identical native walk poses/path, same approvedbody and entry6. Nonnegative clearance includes near tangency; not a broad gameplay collision guarantee. Rotation is shared rigid group in allfacings.','historicalScope':'Old native-context/walk-* and human-registration-visibility-audit.json use b176 bodyheight1.5125, retained diagnostic only; do not establish samebody parity with approved source.','sourceUnchanged':d['sourceBytesUnchanged'] and d['approvedHumanSourceUnchanged'],'reviewPolicy':'Technical evidence only; independent judge approval pending.'}
(O/'human-context-provenance.json').write_text(json.dumps(report,indent=2))
P=O/'previews';P.mkdir(exist_ok=True)
# Consistent whole-frame scaling; never cropped/fitted. Native frames remain untouched.
for direction in 'NESW':
 sheet=Image.new('RGB',(1152,1248),'#e6e1d4');draw=ImageDraw.Draw(sheet)
 for i in range(9):
  im=Image.open(O/f'native-approved-human/approved-walk-{direction}-{i}.png').convert('RGBA');assert im.size==(1536,1536);im=im.resize((384,384),Image.Resampling.LANCZOS);x=(i%3)*384;y=(i//3)*416+28;sheet.paste(im,(x,y),im);draw.text((x+9,y-20),f'{direction} path {i} / walk native frame {i+1}',fill='#2e241c')
 sheet.save(P/f'approved-human-traversal-{direction}.png')
sheet=Image.new('RGB',(1536,420),'#e6e1d4');draw=ImageDraw.Draw(sheet)
for i,direction in enumerate('NESW'):
 im=Image.open(O/f'native-approved-human/approved-walk-{direction}-4.png').convert('RGBA').resize((384,384),Image.Resampling.LANCZOS);sheet.paste(im,(i*384,30),im);draw.text((i*384+8,8),direction+' approved Rosa at shared landing / 55deg technical',fill='#2e241c')
sheet.save(P/'approved-human-landing-all-facings.png')
print('APPROVED_HUMAN_CLOSURE',report['nativePathPoseCount'],report['maxAbsoluteSoleRootError'],report['conservativeNativePostCapMinimumLateralClearance'],len(atlases))
