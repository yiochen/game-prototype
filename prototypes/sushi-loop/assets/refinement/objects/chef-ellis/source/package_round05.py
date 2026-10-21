"""Copy untouched RGBA native pixels into original atlases; separate labeled review composites."""
from pathlib import Path
import json,hashlib,subprocess,shutil,math
from PIL import Image,ImageDraw,ImageFont,ImageChops
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-05';DS=['N','E','S','W'];CS=['idle','work','hold','load']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def rel(p):return p.relative_to(BASE).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def comp(im,bg):b=Image.new('RGBA',im.size,bg);b.alpha_composite(im);return b.convert('RGB')
def font(s):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',s)
 except OSError:return ImageFont.load_default()
def fp(c,d,i):return OUT/'frames'/(c+'-'+d)/(f'{i:03d}.png')
for n in ['atlases','playbacks','contact-sheets','native-records','resources']: (OUT/n).mkdir(exist_ok=True)
raw=[];atlases=[];pre={};vid=[];alphas=[];pixelhashes={}
backgrounds={'light':'#f5f4ed','gray':'#9a9e9b','dark':'#263238'}
for c in CS:
 for d in DS:
  ims=[];atlas=Image.new('RGBA',(2304,1280));sheets={k:Image.new('RGB',(1152,704),v) for k,v in backgrounds.items()}
  for i in range(12):
   path=fp(c,d,i);im=rgba(path);assert im.size==(384,640);ims.append(im);x=i%6*384;y=i//6*640;atlas.paste(im,(x,y));bbox=im.getchannel('A').getbbox();assert bbox and bbox[0]>0 and bbox[1]>0 and bbox[2]<384 and bbox[3]<640
   row={'clip':c,'direction':d,'index':i,'path':rel(path),'sha256':sha(path)};raw.append(row);alphas.append({**row,'alphaBounds':bbox,'clipped':False});pixelhashes[(c,d,i)]=hashlib.sha256(im.tobytes()).hexdigest()
   for name,bg in backgrounds.items():
    ss=sheets[name];ss.paste(comp(im.resize((192,320),Image.Resampling.LANCZOS),bg),(i%6*192,i//6*352+30));ImageDraw.Draw(ss).text((i%6*192+7,i//6*352+7),f'{c} {d} · {i:02}',font=font(16),fill='#edf0e8' if name=='dark' else '#26343a')
  path=OUT/'atlases'/(c+'-'+d+'.png');atlas.save(path,compress_level=9);check=rgba(path);rects=[]
  for i,im in enumerate(ims):
   x=i%6*384;y=i//6*640;assert check.crop((x,y,x+384,y+640)).tobytes()==im.tobytes();rects.append([x,y,384,640])
  atlases.append({'clip':c,'direction':d,'path':rel(path),'sha256':sha(path),'columns':6,'rows':2,'size':[2304,1280],'rects':rects,'fps':12,'loop':c!='load','frameOrder':list(range(12))})
  for name,ss in sheets.items():path=OUT/'contact-sheets'/(c+'-'+d+'-'+name+'.png');ss.save(path);pre['all-frames-'+c+'-'+d+'-'+name]=rel(path)
  path=OUT/'playbacks'/(c+'-'+d+'.mp4')
  subprocess.run(['ffmpeg','-y','-hide_banner','-loglevel','error','-framerate','12','-i',str(OUT/'frames'/(c+'-'+d)/'%03d.png'),'-f','lavfi','-i','color=c=0x9a9e9b:s=384x640:r=12:d=1','-filter_complex','[1:v][0:v]overlay=shortest=1:format=auto,format=yuv420p[v]','-map','[v]','-frames:v','12','-r','12','-c:v','libx264','-preset','fast','-crf','16','-movflags','+faststart',str(path)],check=True)
  data=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration','-of','json',str(path)]))['streams'][0];assert data['r_frame_rate']=='12/1' and int(data['nb_frames'])==12 and float(data['duration'])==1
  vid.append({'clip':c,'direction':d,'path':rel(path),'sha256':sha(path),'frames':12,'fps':12,'durationSeconds':1,'loop':c!='load','ffprobe':data});pre[c+'-'+d]=rel(path)
 # All48 overview shows source frame ordering/facing labels.
 ss=Image.new('RGB',(1152,704),backgrounds['gray']);dr=ImageDraw.Draw(ss)
 for di,d in enumerate(DS):
  for i in range(12):ss.paste(comp(rgba(fp(c,d,i)).resize((96,160),Image.Resampling.LANCZOS),backgrounds['gray']),(i*96,di*176+16));dr.text((i*96+3,di*176),f'{d} {i:02}',font=font(12),fill='#26343a')
 path=OUT/'contact-sheets'/(c+'-all48.png');ss.save(path);pre['overview-'+c]=rel(path)
for name,width,height,scale,coords in [('four-view-sheet',1536,680,1,[(i*384,34) for i in range(4)]),('repeated',768,640,.5,[(i%4*192,i//4*320) for i in range(8)])]:
 ss=Image.new('RGB',(width,height),'#e5e2d8');dr=ImageDraw.Draw(ss)
 for i,xy in enumerate(coords):
  d=DS[i%4];im=rgba(fp('hold',d,0 if i<4 else 6));im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS);ss.paste(comp(im,'#e5e2d8'),xy)
  if name=='four-view-sheet':dr.text((xy[0]+12,8),d+' · native384×640',font=font(20),fill='#26343a')
 path=OUT/(name+'.png');ss.save(path);pre[name]=rel(path)
ss=Image.new('RGB',(768,1014));dr=ImageDraw.Draw(ss)
for bi,(name,bg) in enumerate(backgrounds.items()):
 dr.rectangle((0,bi*338,768,(bi+1)*338),fill=bg)
 for di,d in enumerate(DS):ss.paste(comp(rgba(fp('hold',d,5)).resize((192,320),Image.Resampling.LANCZOS),bg),(di*192,bi*338+18));dr.text((di*192+8,bi*338+1),d,font=font(14),fill='#edf0e8' if name=='dark' else '#26343a')
ss.save(OUT/'background-sheet.png');pre['background-sheet']=rel(OUT/'background-sheet.png')
ss=Image.new('RGB',(768,678),'#e5e2d8');dr=ImageDraw.Draw(ss)
for i,(path,label) in enumerate([(BASE/'candidates/round-04/frames/hold-S/005.png','Approved04 · old packed2D'),(fp('hold','S',5),'Round05 · canonical packed2D')]):ss.paste(comp(rgba(path),'#e5e2d8'),(i*384,34));dr.text((i*384+12,8),label,font=font(20),fill='#26343a')
ss.save(OUT/'comparison.png');pre['comparison']=rel(OUT/'comparison.png')
closure=[]
for row in json.loads((OUT/'closure-renders.json').read_text()):
 c=row['clip'];d=row['direction'];a=rgba(BASE/row['path']);b=rgba(fp(c,d,0));diff=ImageChops.difference(a,b);ext=diff.getextrema();mx=max(x[1] for x in ext);assert mx<=2,(c,d,mx);nonzero=sum(any(px) for px in diff.getdata())
 ss=Image.new('RGB',(576,352),backgrounds['gray']);dr=ImageDraw.Draw(ss)
 for i,(im,label) in enumerate([(rgba(fp(c,d,11)),'last unique11'),(a,'closure key13'),(b,'first00')]):ss.paste(comp(im.resize((192,320),Image.Resampling.LANCZOS),backgrounds['gray']),(i*192,30));dr.text((i*192+5,7),label,font=font(15),fill='#26343a')
 path=OUT/'closures'/(c+'-'+d+'-boundary.png');ss.save(path);pre['closure-'+c+'-'+d]=rel(path);closure.append({**row,'maxRGBAChannelDifferenceToFirst':mx,'nonzeroPixelCount':nonzero,'pixelCount':384*640,'interpretation':'Exact source bone closure; at most2/255 render rounding tolerance, actual difference recorded','sourceClosingKey':13,'renderedAsCatalogFrame':False})
semantic=json.loads((OUT/'semantic-parity.json').read_text());assert semantic['ok'];rows=json.loads((OUT/'native-frames.json').read_text());assert len(rows)==192 and all(r['approved04BodyParity'] for r in rows)
bodyPixel=[]
for c in ['idle','work']:
 for d in DS:
  for i in range(12):
   a=rgba(fp(c,d,i));b=rgba(BASE/'candidates/round-04/frames'/(c+'-'+d)/(f'{i:03d}.png'));diff=ImageChops.difference(a,b);mx=max(e[1] for e in diff.getextrema());count=sum(any(px) for px in diff.getdata());assert mx<=2,(c,d,i,mx);bodyPixel.append({'clip':c,'direction':d,'index':i,'maxRGBAChannelDifference':mx,'nonzeroPixels':count,'pixelCount':384*640,'interpretation':'Hidden-food idle/work compares unchanged native body and knife; at most2/255 renderer rounding tolerance'})
diagnostics=[]
for d in DS:
 a=rgba(OUT/'body-diagnostics-v2/candidate05'/(d+'.png'));b=rgba(OUT/'body-diagnostics-v2/approved04'/(d+'.png'));diff=ImageChops.difference(a,b);mx=max(e[1] for e in diff.getextrema());count=sum(any(px) for px in diff.getdata());assert mx<=2,(d,mx)
 diagnostics.append({'direction':d,'approved04':rel(OUT/'body-diagnostics-v2/approved04'/(d+'.png')),'candidate05':rel(OUT/'body-diagnostics-v2/candidate05'/(d+'.png')),'nativeClip':'hold','sourceFrame':6,'maxRGBAChannelDifference':mx,'nonzeroPixels':count,'policy':'Diagnostic only: temporarily hide2D food in both exact native scenes, restore visibility; never saved or used in atlases'})
 ss=Image.new('RGB',(768,678),'#9a9e9b');dr=ImageDraw.Draw(ss)
 for i,(im,label) in enumerate([(b,'Approved04 · body only'),(a,'Candidate05 · body only')]):ss.paste(comp(im,'#9a9e9b'),(i*384,34));dr.text((i*384+9,8),label,font=font(18),fill='#26343a')
 path=OUT/'body-diagnostics-v2'/('comparison-'+d+'.png');ss.save(path);pre['body-only-diagnostic-'+d]=rel(path)
write(OUT/'body-pixel-parity.json',{'ok':True,'unchangedIdleWorkNativeFrames':bodyPixel,'foodHiddenBodyDiagnostics':diagnostics,'semanticNativeParity':'semantic-parity.json','all192BodyAndContactComparisons':'native-frames.json'})
# Food-bearing all-facing comparisons keep exact registration; no subject fitting or image edits.
for c in ['hold','load']:
 ss=Image.new('RGB',(1536,1328),'#9a9e9b');dr=ImageDraw.Draw(ss)
 for di,d in enumerate(DS):
  for row,(folder,label) in enumerate([('round-04','Approved04 old food'),('round-05','Canonical05 new food')]):
   im=rgba(BASE/'candidates'/folder/'frames'/(c+'-'+d)/'005.png');ss.paste(comp(im,'#9a9e9b'),(di*384,row*664+24));dr.text((di*384+10,row*664+5),label+' · '+d,font=font(17),fill='#26343a')
 path=OUT/(c+'-canonical-comparison.png');ss.save(path);pre[c+'-canonical-comparison']=rel(path)
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'frames':alphas,'allNativeRectanglesPreserved':True});write(OUT/'playback-validation.json',{'ok':True,'playbacks':vid,'visibleLoopClosure':closure,'pixelDistinctSamples':{c+'-'+d:len({pixelhashes[(c,d,i)] for i in range(12)}) for c in CS for d in DS}})
recipe=json.loads((P/'recipe-round05.json').read_text());nr=OUT/'native-records';camera={'projection':'character-orthographic','frame':[192,320],'anchor':[96,248],'captureScale':2,'fps':12,'cellSize':128,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':recipe['camera']['worldMatrix'],'projectionMatrix':recipe['camera']['projectionMatrix'],'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{k:recipe['camera'][k] for k in ['root','unitX','unitDepth','unitHeight']},'artStyle':{'lighting':'Exact approved04 native symmetric response','bodyBaseline':'round-04','foodRevision':'canonical731x505-fullUV-round05'}};write(nr/'camera.json',camera)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'approved04-native-body-with-canonical05-food','bodyCameraRigActionsMaterialsLightingUnchanged':True};asset['foodDependency']=recipe['foodDependency'];asset['foodDisplay']={'representation':'packed2D','worldWidth':.35,'worldHeight':.35*505/731,'fullUV':[0,0,1,1],'lowerEdge':'Original approved04 attachment','depthBiasWorld':.6};write(nr/'asset.json',asset);shutil.copyfile(P/'rig-round05.json',nr/'rig.json')
for path in (P/'dependencies/round05').glob('*'):
 if path.is_file():shutil.copyfile(path,OUT/'resources'/path.name)
for filename,key in [('native-context-validation.json','native-context'),('native-belt-dish-context-validation.json','native-belt-dish-context'),('native-side-context-validation.json','native-side-context')]:
 for i,r in enumerate(json.loads((OUT/filename).read_text())['renders']):pre[key+'-'+str(i)]=r['path']
for r in json.loads((OUT/'food-representatives.json').read_text()):pre['representative-'+r['clip']+'-'+r['direction']+'-'+str(r['sourceFrame'])]=r['path']
cards=[]
for v in vid:
 url=Path(v['path']).relative_to('candidates/round-05').as_posix();loop=' loop' if v['loop'] else '';cards.append(f'<figure><figcaption>{v["clip"]} · {v["direction"]} ·12fps · {"loop" if v["loop"] else "stops after12frames"}</figcaption><video src="{url}" width="192" height="320" muted playsinline controls{loop}></video></figure>')
(OUT/'playback.html').write_text('<!doctype html><meta charset="utf-8"><title>Ellis canonical salmon round05 playback</title><style>body{font:15px system-ui;background:#e5e2d8;color:#20323a;margin:24px}main{display:grid;grid-template-columns:repeat(4,212px);gap:12px}figure{margin:0;padding:10px;background:#f5f3eb}video{display:block;width:192px;height:320px}button{font:inherit;margin:8px;padding:8px}</style><h1>Ellis round05 · canonical packed2D salmon</h1><p>Approved04 native body/knife/camera/material/light/rig/actions unchanged. Only canonical731×505 packed2D food image/fullUV/aspect/provenance changed. All16 original clip/facing combinations, twelve384×640 native frames at12fps displayed at192×320. Idle/work/hold loop; load ends with dish retained. Video backgrounds are review composites; native PNG/atlases are untouched RGBA.</p><button id="play">Play all from frame00</button><button id="pause">Pause all</button><main>'+''.join(cards)+'</main><script>const videos=[...document.querySelectorAll("video")];document.querySelector("#play").onclick=()=>videos.forEach(v=>{v.currentTime=0;v.play()});document.querySelector("#pause").onclick=()=>videos.forEach(v=>v.pause());</script>');pre['playback-index']=rel(OUT/'playback.html')
validation=json.loads((OUT/'validation.json').read_text());validation.update({'status':'Complete food-only candidate evidence; independent judge verdict pending','activeBrief':'brief-v2-food.json','activeBriefSHA256':sha(BASE/'brief-v2-food.json'),'criteriaSHA256':sha(BASE/'reviews/criteria-v2-food.json'),'rawNativeFrameRecords':raw,'catalogRenderCount':192,'originalLayoutAtlasCount':16,'playbackCount':16,'playbacks':vid,'alphaAndAtlasValidation':rel(OUT/'alpha-and-atlas-validation.json'),'closureValidation':closure,'nativeSemanticParity':rel(OUT/'semantic-parity.json'),'explicitFoodPlaneDelta':rel(OUT/'food-plane-allowed-delta.json'),'bodyPixelParity':rel(OUT/'body-pixel-parity.json'),'exactCanonicalPackedImage':semantic['packedImage'],'foodDependency':recipe['foodDependency'],'approvedBodyBaseline':recipe['approvedBodyBaseline'],'nativeContexts':[rel(OUT/x) for x in ['native-context-validation.json','native-belt-dish-context-validation.json','native-side-context-validation.json']],'nativeUVandAspectAndLowerAnchor':{k:semantic[k] for k in ['fullUV','quadVertices','localWidth','localHeight','nativeWorldWidth','nativeWorldHeight','lowerEdgeUnchanged']},'baselineAndCanonicalReceiptVerification':'candidates/round-05/baseline04-packet-reverification.json','sourceVersionTruth':'Old1254x1254 payload is absent from reopened candidate; new canonical731x505 source is the sole packed image. Old version appears only in explicit provenance.'});write(OUT/'complete-validation.json',validation)
# Explicit reproduction closure for05; old packet-bound files remain byte-identical.
resourcePaths=[x for x in P.glob('*round05*') if x.is_file() and x.name!='body_diagnostic_round05.py']+[P/'round-04.blend',P/'recipe-round04.json',P/'original-library.blend']+list((P/'dependencies/round05').glob('*'));resourcePaths+=[P/'round-05.blend',BASE/'inputs/source-assetRecord.json']+[OUT/x for x in ['approved04-evaluated.json','approved04-semantic-v2.json','reopened-semantic.json','semantic-parity.json','food-plane-allowed-delta.json','native-frames.json','evaluated-contacts.json','body-pixel-parity.json','alpha-and-atlas-validation.json','playback-validation.json','native-context-validation.json','native-belt-dish-context-validation.json','native-side-context-validation.json','closure-renders.json']];resources={x.name:rel(x) for x in resourcePaths if x.is_file()};resources['baseline04PacketAndCanonicalReceiptVerification']='candidates/round-05/baseline04-packet-reverification.json';resources['approvedBodyBackup']=rel(BASE/'inputs/approved-round04.blend');resources['canonicalSalmonReceiptPacket']=str(recipe['foodDependency']['packet']);resources['canonicalSalmonReceiptReview']=str(recipe['foodDependency']['review'])
delivery={'schemaVersion':1,'asset':'chef-ellis','round':'round-05','pipeline':'native-3d','activeBrief':'brief-v2-food.json','status':'candidate-ready-for-independent-review','project':'source/round-05.blend','recipe':'source/recipe-round05.json','recipeScript':'source/build_round05.py','validation':rel(OUT/'complete-validation.json'),'heroes':{d:rel(fp('idle',d,0)) for d in DS},'rawFrames':raw,'atlases':atlases,'previews':pre,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':resources,'approvedBodyBaseline':recipe['approvedBodyBaseline'],'foodDependency':recipe['foodDependency'],'representation':{'actor':'exact approved04 native3D mesh/material/rig/response','knife':'exact approved04 native3D','heldDish':'canonical approved731x505 packed2D with fullUV/true aspect at original bottom anchor, .35worldwidth, .6camera-ray bias, yaw cancellation/visibility/actions'},'notes':['This is a food-only dependency revision; no approved body/knife/capture/lighting/material/action changes.','192 zero-based clip-local indexed captures and original16 atlases; old04 packet/source/review/brief/renders remain unchanged.','All shader response preserved; no food recolor, UV crop or raster repair. Review backgrounds/comparisons/body-only diagnostics are labeled separately.','Independent judge owns approval; coordinator seals exact bytes using brief-v2-food.json.']};write(OUT/'delivery.snapshot.json',delivery);write(BASE/'delivery.json',delivery);write(BASE/'delivery-round05.json',delivery)
print('PACKED',len(raw),len(atlases),len(vid),'activeBrief',delivery['activeBrief'],flush=True)
