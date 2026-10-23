from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageChops,ImageStat,ImageDraw
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(H/n).write_text(json.dumps(v,indent=2)+'\n')
def compare(a,b):
 a=a.convert('RGBA');b=b.convert('RGBA');diff=ImageChops.difference(a,b);return {'sameDecodedRGBA':a.tobytes()==b.tobytes(),'alphaExact':a.getchannel('A').tobytes()==b.getchannel('A').tobytes(),'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'maxAbsoluteRGBA':[e[1] for e in diff.getextrema()],'pixelsDiffer':sum(x!=y for x,y in zip(a.getdata(),b.getdata()))}
cap=json.loads((H/'native-replay.json').read_text());src=json.loads((H/'native-source.json').read_text());submitted=json.loads((C/'native-validation.json').read_text())
replay=[];geom=[];stability={};closure={};bounds={};attachment=[];contact=[]
for d in 'NESW':
 rr=[r for r in cap['captureRecords'] if r['direction']==d]
 stable=[];first={o['object']:o for o in rr[0]['geometry']['objects']};rootfirst=rr[0]['rootMatrix'];rootdelta=0
 for r in rr:
  i=r['index'];native=Image.open(H/r['path']);pub=native.resize((384,704),Image.Resampling.LANCZOS)
  replay.append({'direction':d,'index':i,'submittedNative':str((C/'native/ambient'/d/f'{i:03}.png').relative_to(O)),'independentNative':str((H/r['path']).relative_to(O)),'nativeDifference':compare(native,Image.open(C/'native/ambient'/d/f'{i:03}.png')),'publishedDifference':compare(pub,Image.open(C/'frames/ambient'/d/f'{i:03}.png'))})
  sr=next(x for x in submitted['captureRecords'] if x['direction']==d and x['index']==i)
  gm=r['geometry'];sg=sr['geometry'];geom.append({'direction':d,'index':i,'rawBoundsExact':gm['rawBoundsCanonicalS']==sg['rawAuthoredBoundsCanonicalS'],'evaluatedBoundsExact':gm['evaluatedBoundsCanonicalS']==sg['evaluatedBoundsCanonicalS']})
  for x,y in zip(r['rootMatrix'],rootfirst):rootdelta=max(rootdelta,max(abs(a-b) for a,b in zip(x,y)))
  for ob in gm['objects']:
   if ob['role'] in ['stable_stone','stable_lane_guide']:
    stable.append(ob['evaluatedFingerprint']==first[ob['object']]['evaluatedFingerprint'])
   if ob['role']=='stable_stone':contact.append({'direction':d,'index':i,'object':ob['object'],'groundIntersectionPoints':len(ob['groundIntersections']),'zRange': [ob['evaluatedBounds']['min'][2],ob['evaluatedBounds']['max'][2]]})
  attachment.extend({'direction':d,'index':i,**a} for a in gm['foliageAttachmentMeasurements'])
 for typ in ['rawBoundsCanonicalS','evaluatedBoundsCanonicalS']:
  bounds.setdefault(d,{})[typ]={'min':[min(r['geometry'][typ]['min'][i] for r in rr) for i in range(3)],'max':[max(r['geometry'][typ]['max'][i] for r in rr) for i in range(3)]}
 closing=cap['closingFrame13'][d];cfirst={o['object']:o for o in rr[0]['geometry']['objects']};delta=0
 for o in closing['geometry']['objects']:
  for x,y in zip(o['localMatrix'],cfirst[o['object']]['localMatrix']):delta=max(delta,max(abs(a-b) for a,b in zip(x,y)))
 closure[d]={'evaluatedGeometryExactFirstToClosing':rr[0]['geometry']['geometryFingerprint']==closing['geometry']['geometryFingerprint'],'maxLocalMatrixDelta':delta}
 stability[d]={'allStaticEvaluatedGeometryFingerprintsExact':all(stable),'rootMatrixMaxDelta':rootdelta}
write('native-independent-comparison.json',{'sourceSHA256':src['sourceSHA256'],'replayComparisons':replay,'geometryComparisonToPacket':geom,'boundsByFacing':bounds,'stability':stability,'closure':closure,'groundContactsAll48':contact,'foliageAttachmentsAll480':attachment,'sourceUnchanged':cap['sourceUnchanged'],'camera':'native-source.json','noPixelRepair':True})
# APNG decode covers actual12 frames, validates cadence and exact submitted pixel mapping.
apng=[];motionframes=[]
for d in 'NESW':
 p=C/'previews'/f'ambient-{d}.png';im=Image.open(p);rows=[]
 for i in range(im.n_frames):
  im.seek(i);rows.append({'index':i,'durationMs':im.info['duration'],'pixelMappingExact':im.convert('RGBA').tobytes()==Image.open(C/'frames/ambient'/d/f'{i:03}.png').convert('RGBA').tobytes()})
 apng.append({'path':str(p.relative_to(O)),'sha256':sha(p),'nFrames':im.n_frames,'loop':im.info.get('loop'),'durationTotalMs':sum(x['durationMs'] for x in rows),'frames':rows})
im=Image.open(C/'previews/motion.png');motion=[]
for i in range(im.n_frames):
 im.seek(i);frame=im.convert('RGB');motionframes.append(frame.copy());motion.append({'index':i,'durationMs':im.info['duration'],'decodedRGBSHA256':hashlib.sha256(frame.tobytes()).hexdigest()})
(H/'sheets').mkdir(exist_ok=True)
for start in [0,6]:
 sheet=Image.new('RGB',(1536,1128),'#eeeeee')
 for j in range(6):sheet.paste(motionframes[start+j],((j%2)*768,(j//2)*376))
 sheet.save(H/'sheets'/f'actual-APNG-motion-{start:02}-{start+5:02}.png')
write('APNG-content-coverage.json',{'ambient':apng,'motion':{'path':'candidates/round-01/previews/motion.png','sha256':sha(C/'previews/motion.png'),'nFrames':len(motion),'durationTotalMs':sum(x['durationMs'] for x in motion),'frames':motion,'inspectionSheets':['sheets/actual-APNG-motion-00-05.png','sheets/actual-APNG-motion-06-11.png']},'noAPNGDefaultFrameSubstitution':True})
# Diagnostic native crops retain exact coordinates; enlargement is inspection only.
regions={'S':(140,680,320,1040),'N':(410,710,640,1160),'E':(190,900,590,1220),'W':(180,590,590,980)}
# First crop correct bounds based actualnative image for enough fullplant/blue volume, not delivery transforms.
for d in 'NESW':
 region=regions[d];x0,y0,x1,y1=region;tileW=(x1-x0)*2;tileH=(y1-y0)*2
 sheet=Image.new('RGB',(tileW*4,tileH+24),'#777777');dr=ImageDraw.Draw(sheet)
 for j,i in enumerate([0,3,6,9]):
  raw=Image.open(C/'native/ambient'/d/f'{i:03}.png').convert('RGBA');tile=raw.crop(region).resize((tileW,tileH),Image.Resampling.NEAREST);sheet.paste(tile,(j*tileW,24),tile);dr.text((j*tileW+5,5),f'{d} nativephase{i} crop{region}',fill='white')
 sheet.save(H/'sheets'/f'native-detail-{d}.png')
write('native-diagnostic-crops.json',{'purpose':'Actual submitted native pixel diagnostic enlargement only, no delivered art edits/fitting. Coordinates are explicitly native x0y0x1y1; allfullframes inspected separately.','regions':regions,'indices':[0,3,6,9],'scale':2,'filter':'NEAREST'})
# Each input source and replay raw frame carries its true fullcanvas; verify publication and atlas layout from actual decoded pixels.
pub=[];atlas=[]
cat=json.loads((O/'inputs/catalog-object.json').read_text())
for d in 'NESW':
 image=Image.open(C/'atlases'/f'ambient-{d}.png').convert('RGBA')
 for i,rect in enumerate(cat['clips'][0]['directions'][d]['rects']):
  raw=Image.open(C/'native/ambient'/d/f'{i:03}.png').convert('RGBA');frame=Image.open(C/'frames/ambient'/d/f'{i:03}.png').convert('RGBA');a=frame.getchannel('A')
  pub.append({'direction':d,'index':i,'publishedExactFullCanvasLanczos':raw.resize((384,704),Image.Resampling.LANCZOS).tobytes()==frame.tobytes(),'alphaBounds':a.getbbox(),'transparentAllEdges':a.crop((0,0,384,1)).getbbox() is None and a.crop((0,703,384,704)).getbbox() is None and a.crop((0,0,1,704)).getbbox() is None and a.crop((383,0,384,704)).getbbox() is None})
  x,y,w,h=rect;atlas.append({'direction':d,'index':i,'rect':rect,'atlasCellExactPublished':image.crop((x,y,x+w,y+h)).tobytes()==frame.tobytes()})
write('publication-independent-check.json',{'frames':pub,'atlasCells':atlas,'frameCount':len(pub),'originalRegistrationUnchanged':True})
print(json.dumps({'rawBoundsAllExact':all(x['rawBoundsExact'] for x in geom),'evaluatedBoundsAllExact':all(x['evaluatedBoundsExact'] for x in geom),'nativeExactFrames':sum(x['nativeDifference']['sameDecodedRGBA'] for x in replay),'nativeMaximumDifference':max(max(x['nativeDifference']['maxAbsoluteRGBA']) for x in replay),'all48PublishedReductionExact':all(x['publishedExactFullCanvasLanczos'] for x in pub),'all48AtlasCellsExact':all(x['atlasCellExactPublished'] for x in atlas),'all48TransparentEdges':all(x['transparentAllEdges'] for x in pub),'minEvaluatedLeafVerticesInsideAssignedStone':min(x['evaluatedLeafVerticesInsideStone'] for x in attachment),'closure':closure},indent=2))
