"""Publish exact whole frames and assemble diagnostic previews after native capture."""
from pathlib import Path
import json,hashlib,math
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat
SRC=Path(__file__).resolve().parent;OBJ=SRC.parent;OUT=OBJ/'candidates/round-02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=list('NESW');bg=(35,55,69,255)

def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def framed(im,background=bg):
 c=Image.new('RGBA',im.size,background);c.alpha_composite(im);return c.convert('RGB')
def label(im,xy,text):ImageDraw.Draw(im).text(xy,text,fill=(235,237,241),font=ImageFont.load_default(size=16))
rows=[];nat=[];atl=[];alpha=[];closure={}
for d in D:
 pub=[]
 for i in range(12):
  native=OUT/'native'/d/f'{i:03}.png';dest=OUT/'frames/idle'/d/f'{i:03}.png'
  with Image.open(native)as im:
   assert im.size==(768,1536);im=im.convert('RGBA');im=im.resize((384,768),Image.Resampling.LANCZOS);save(im,dest);pub.append(im.copy())
  rows.append({'clip':'idle','direction':d,'index':i,'path':str(dest.relative_to(OBJ))});nat.append({'clip':'idle','direction':d,'index':i,'path':str(native.relative_to(OBJ))})
  box=im.getchannel('A').getbbox();edge=max(im.getchannel('A').crop((0,0,384,1)).getextrema()[1],im.getchannel('A').crop((0,767,384,768)).getextrema()[1],im.getchannel('A').crop((0,0,1,768)).getextrema()[1],im.getchannel('A').crop((383,0,384,768)).getextrema()[1]);alpha.append({'direction':d,'index':i,'alphaBounds':box,'maxCanvasEdgeAlpha':edge})
 atlas=Image.new('RGBA',(2304,1536))
 for i,im in enumerate(pub):atlas.paste(im,((i%6)*384,(i//6)*768))
 p=OUT/'atlases'/f'idle-{d}.png';save(atlas,p);atl.append({'clip':'idle','direction':d,'path':str(p.relative_to(OBJ)),'columns':6,'rows':2,'size':[2304,1536],'rects':[[i%6*384,i//6*768,384,768]for i in range(12)]})
 sheet=Image.new('RGB',(1536,2400),bg[:3])
 for i,im in enumerate(pub):
  x=(i%4)*384;y=(i//4)*800;sheet.paste(framed(im),(x,y+28));label(sheet,(x+12,y+6),f'{d} · published {i} / native {i+1}')
 save(sheet,OUT/f'phases-{d}.png')
 gif=[framed(im)for im in pub];gif[0].save(OUT/f'idle-{d}.gif',save_all=True,append_images=gif[1:],duration=[80,80,90]*4,loop=0,disposal=2,optimize=False)
 a=Image.open(OUT/'native'/d/'000.png').convert('RGBA');b=Image.open(OUT/'closure'/d/'012.png').convert('RGBA');diff=ImageChops.difference(a,b)
 closure[d]={'decodedNative1Equals13':not any(v for chan in diff.getextrema()for v in chan),'maxChannelDifference':[v[1]for v in diff.getextrema()],'firstNativeSHA256':sha(OUT/'native'/d/'000.png'),'closureNativeSHA256':sha(OUT/'closure'/d/'012.png'),'publishedUniqueDecoded':len({Image.open(OUT/'frames/idle'/d/f'{i:03}.png').convert('RGBA').tobytes()for i in range(12)})}
# Each panel keeps the complete frame and registered scale; only the same uniform resize yields logical-size diagnostics.
sheet=Image.new('RGB',(4*192,3*410),bg[:3])
for row,back in enumerate([(16,28,38,255),(115,122,129,255),(236,235,226,255)]):
 for j,d in enumerate(D):
  im=Image.open(OUT/'frames/idle'/d/'003.png').convert('RGBA').resize((192,384),Image.Resampling.LANCZOS);panel=framed(im,back);sheet.paste(panel,(j*192,row*410+26));label(sheet,(j*192+8,row*410+5),f'{d} · 192x384 · frame4')
save(sheet,OUT/'four-view-sheet.png')
compare=Image.new('RGB',(384*3,804),bg[:3]);original=Image.open(OBJ/'inputs/original.png').convert('RGBA');candidate=Image.open(OUT/'frames/idle/S/003.png').convert('RGBA');target=Image.open(OBJ/'inputs/target.png').convert('RGBA');target.thumbnail((384,768),Image.Resampling.LANCZOS)
for x,im,title in [(0,original,'Original S, registered frame'),(384,candidate,'Candidate S, native frame4'),(768,target,'Fixed target · display thumbnail')]:
 panel=Image.new('RGBA',(384,768),bg);panel.alpha_composite(im,((384-im.width)//2,(768-im.height)//2));compare.paste(panel.convert('RGB'),(x,36));label(compare,(x+8,8),title)
save(compare,OUT/'source-target-comparison.png')
v=json.loads((OUT/'native-validation.json').read_text());checks={}
checks['cameraWorldMatrixExact']=v['cameraMatrixMaxDifference']==0
checks['projectionMatrixMatches']=v['projectionMatrixMaxDifference']<1e-6
checks['allFramesInsideFrozenEnvelope']=all(r['boundsRoot'][0][0]>=-.513285 and r['boundsRoot'][0][1]<=.513285 and r['boundsRoot'][1][0]>=-.513285 and r['boundsRoot'][1][1]<=.513285 and r['boundsRoot'][2][0]>=-1e-5 and r['boundsRoot'][2][1]<=1.45001 for r in v['captureRecords'])
checks['allBaseRingSamplesSupported']=all(t['supported']==t['total']for f in v['finiteSupport']for t in f['tubeContacts'])
checks['fixedRootAndProperFacings']=all(r['rootLocation']==[0,0,0]and r['rootScale']==[1,1,1]and abs(math.atan2(math.sin(r['rootRotationZ']-{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[r['direction']]),math.cos(r['rootRotationZ']-{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[r['direction']])))<1e-5 for r in v['captureRecords'])
checks['closedEvaluatedPose']=all(v['closureEvaluatedPose'].values());checks['closedNativePixels']=all(c['decodedNative1Equals13']for c in closure.values());checks['twelveUniquePublishedFrames']=all(c['publishedUniqueDecoded']==12 for c in closure.values());checks['noNativeNonmanifoldEdges']=all(t['nonmanifoldEdges']==0 for t in v['topology']);checks['canvasEdgeAlphaZero']=all(r['maxCanvasEdgeAlpha']==0 for r in alpha)
geometry={'sweptBoundsRoot':[[min(r['boundsRoot'][i][0]for r in v['captureRecords']),max(r['boundsRoot'][i][1]for r in v['captureRecords'])]for i in range(3)],'contactSamples':sum(t['total']for f in v['finiteSupport']for t in f['tubeContacts']),'minBaseRingPenetration':min(p['penetration']for f in v['finiteSupport']for t in f['tubeContacts']for p in t['points']if p['penetration']is not None),'nativeCameraDifference':v['cameraMatrixMaxDifference'],'nativeProjectionDifference':v['projectionMatrixMaxDifference']}
(OUT/'publication-proof.json').write_text(json.dumps({'method':'Uniform complete native768x1536 RGBA to384x768 RGBA LANCZOS, no crop/fit/warp/RGBalpha repair','nativeCaptureScale':4,'publishedScale':2,'closure':closure,'alpha':alpha,'derivedPlayback':'GIF diagnostic on slate background: 80/80/90 ms repeated4, duration1000ms, original12 frames ordered, no thirteenth atlasframe','checks':checks,'geometry':geometry},indent=2)+'\n')
asset={'id':'decor-midground-coral','projection':'top-down-oblique-square-grid','frame':[192,384],'anchor':[96,288],'scale':2,'clips':{'idle':{'frames':12,'fps':12,'loop':True}},'footprint':[1,1],'height':1.45,'sockets':{},'directions':D,'blocking':False,'layer':2,'groundRootObject':'decor-midground-coral root','artStyle':{'revision':'warm-soft-native-round-02','lighting':'broad warm overhead plus four equal cardinal fills and uniform ambient','horizontalSymmetry':4,'materials':'native pink/violet/cobalt with rounded lips and stable generated detail'}}
(OUT/'assetRecord.json').write_text(json.dumps(asset,indent=2)+'\n')
actions=[{'ownerType':'Object','ownerName':r['ownerName'],'action':r['action'],'slotIdentifier':r['slot'],'keyframeCount':sum(len(c['keys'])for c in r['channels'])}for r in v['temporalOwnership']]
rig={'assetId':'decor-midground-coral','fps':12,'source':'source/reproduce-round-02.py','static':False,'clips':{'idle':{'frames':12,'fps':12,'loop':True,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':13,'actions':actions}},'armatures':[],'footprint':[1,1],'projection':'top-down-oblique-square-grid','groundRootObject':'decor-midground-coral root','sockets':{},'actionCount':len(actions),'notes':['Actual native object rotation_euler X/Y/Z actions at planted bases; static root/reef. No shader, material, shape, visibility, driver or NLA motion.','Native13 equals1; atlas only frames1..12.']}
(OUT/'rig.json').write_text(json.dumps(rig,indent=2)+'\n')
(SRC/'round-02-frame-records.json').write_text(json.dumps({'rawFrames':rows,'nativeRawFrames':nat,'atlases':atl},indent=2)+'\n')
print(json.dumps({'checks':checks,'geometry':geometry},indent=2))
