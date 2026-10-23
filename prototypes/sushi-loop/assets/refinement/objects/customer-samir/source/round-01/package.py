from pathlib import Path
import json,hashlib,math,subprocess,shutil
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;P=D.parent.parent;R=P/'candidates/round-01';RES=D/'resources';B=json.loads((RES/'frozen-brief.json').read_text())
DIRS=['S','E','N','W'];BGS={'light':'#f3ede2','gray':'#89939b','dark':'#202832'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(P))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def load(p):return json.loads(p.read_text())
def composite(im,bg):return Image.alpha_composite(Image.new('RGBA',im.size,bg),im)
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def video(inputpattern,out,width=384,height=640):
 out.parent.mkdir(parents=True,exist_ok=True)
 cmd=['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(inputpattern),'-filter_complex',f'color=c=0x89939b:s={width}x{height}:r=12:d=1[bg];[bg][0:v]overlay=shortest=1:format=auto,format=yuv420p','-frames:v','12','-c:v','libx264','-preset','veryfast','-crf','16','-movflags','+faststart',str(out)]
 subprocess.run(cmd,check=True)
 probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,avg_frame_rate,nb_frames,width,height,duration','-of','json',str(out)]))['streams'][0]
 assert probe['r_frame_rate']=='12/1' and int(probe['nb_frames'])==12 and abs(float(probe['duration'])-1)<.001,probe
 return probe
allatlases={};allframes={};clips={};preview={};imagechecks=[];videochecks=[];temporal=[]
for mode in ['main','runtime']:
 a=load(R/mode/'validation-native.json');assert not a['errors'],a['errors'];allatlases[mode]=[];allframes[mode]=[];clips[mode]=[]
 for clip,info in a['clips'].items():
  clips[mode].append({'id':clip,'sourceClipId':info['sourceClipId'],'frames':12,'fps':12,'loop':info['loop'],'static':False,'frameOrder':list(range(12))})
  for direction in DIRS:
   frames=[R/mode/'frames'/clip/direction/f'{i:02}.png' for i in range(12)];ims=[Image.open(p).convert('RGBA') for p in frames];assert all(i.size==(384,640) for i in ims)
   atlas=Image.new('RGBA',(2304,1280));rects=[];records=[]
   for i,(fp,im) in enumerate(zip(frames,ims)):
    x,y=(i%6)*384,(i//6)*640;atlas.paste(im,(x,y));rect=[x,y,384,640];rects.append(rect)
    assert atlas.crop((x,y,x+384,y+640)).tobytes()==im.tobytes()
    alpha=im.getchannel('A');box=alpha.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<384 and box[3]<640,(fp,box)
    imagechecks.append({'path':rel(fp),'sha256':sha(fp),'alphaBounds':box,'edgeClear':True});records.append({'index':i,'nativeFrame':rel(fp),'sha256':sha(fp),'rect':rect});allframes[mode].append(rel(fp))
   ap=R/mode/'atlases'/f'{clip}-{direction}.png';save(atlas,ap)
   item={'clip':clip,'direction':direction,'path':rel(ap),'sha256':sha(ap),'columns':6,'rows':2,'frame':[384,640],'size':[2304,1280],'atlasSize':[2304,1280],'rects':rects,'frames':records,'fps':12,'loop':info['loop']};allatlases[mode].append(item)
   vp=R/mode/'playback'/f'{clip}-{direction}.mp4';probe=video(frames[0].parent/'%02d.png',vp);videochecks.append({'path':rel(vp),'sha256':sha(vp),**probe});preview[f'{clip}-{direction}']=rel(vp)
   temporal.append({'mode':mode,'clip':clip,'direction':direction,'loop':info['loop'],'fps':12,'frames':[str(p.relative_to(R)) for p in frames],'mp4':str(vp.relative_to(R))})
   for name,bg in BGS.items():
    sheet=Image.new('RGBA',(2304,346),bg);dr=ImageDraw.Draw(sheet);dr.text((8,5),f'{clip} {direction} | frames 00–11 | 12fps | logical 192×320 | {name}',fill='#0f1921' if name!='dark' else '#f4eee4')
    for i,im in enumerate(ims):sheet.alpha_composite(im.resize((192,320),Image.Resampling.LANCZOS),(i*192,26))
    sp=R/'sheets'/f'{clip}-{direction}-{name}.png';save(sheet,sp);preview[f'{clip}-{direction}-{name}']=rel(sp)
   print('PACKED',clip,direction,flush=True)
# 48 pose/facing representatives on every review background; complete native frames remain untouched.
for name,bg in BGS.items():
 rows=list(clips['main'])+list(clips['runtime']);sheet=Image.new('RGBA',(800,len(rows)*352),bg);dr=ImageDraw.Draw(sheet)
 for row,entry in enumerate(rows):
  mode='main' if entry in clips['main'] else 'runtime';dr.text((8,row*352+4),entry['id'],fill='#17212b' if name!='dark' else '#f4eee4')
  for j,direction in enumerate(DIRS):
   im=Image.open(R/mode/'frames'/entry['id']/direction/'04.png').convert('RGBA');sheet.alpha_composite(im.resize((192,320),Image.Resampling.LANCZOS),(j*200,row*352+24));dr.text((j*200+8,row*352+336),direction,fill='#17212b' if name!='dark' else '#f4eee4')
 path=R/'backgrounds'/f'all-states-facings-{name}.png';save(sheet,path);preview['background-'+name]=rel(path)
# Four native cardinal heroes, and a source/target/candidate comparison with complete uniform canvases.
four=Image.new('RGBA',(768,340),BGS['light']);dr=ImageDraw.Draw(four)
for j,d in enumerate(DIRS):
 im=Image.open(R/'main/frames/stand'/d/'04.png').convert('RGBA');four.alpha_composite(im.resize((192,320),Image.Resampling.LANCZOS),(j*192,20));dr.text((j*192+8,4),d,fill='#17212b')
save(four,R/'four-view-sheet.png');preview['four-view-sheet']=rel(R/'four-view-sheet.png');save(four,R/'repeated.png');preview['repeated']=rel(R/'repeated.png')
comp=Image.new('RGBA',(576,350),BGS['light']);dr=ImageDraw.Draw(comp)
for j,(label,p) in enumerate([('Source native snapshot',RES/'original.png'),('Frozen design target',RES/'target.png'),('Native candidate',R/'main/frames/stand/S/04.png')]):
 im=Image.open(p).convert('RGBA');im.thumbnail((192,320),Image.Resampling.LANCZOS);comp.alpha_composite(im,(j*192+(192-im.width)//2,24));dr.text((j*192+8,5),label,fill='#17212b')
save(comp,R/'comparison.png');preview['reference-comparison']=rel(R/'comparison.png')
# Registered separate-sprite stool assemblies: no fitted/cropped character frames.
contextclips=[]
for mode,ids in [('main',['seated-wait','eat']),('runtime',['eat-salmon','seated-wait-empty'])]:
 for clip in ids:
  for d in DIRS:
   stool=Image.open(RES/f'context-stool-{d}.png').convert('RGBA');assert stool.size==(384,704)
   for i in range(12):
    out=stool.copy();im=Image.open(R/mode/'frames'/clip/d/f'{i:02}.png').convert('RGBA');out.alpha_composite(im,(0,0));save(out,R/'contexts/frames'/clip/d/f'{i:02}.png')
   vp=R/'contexts'/f'{clip}-{d}.mp4';probe=video(R/'contexts/frames'/clip/d/'%02d.png',vp,384,704);videochecks.append({'path':rel(vp),'sha256':sha(vp),'context':True,**probe});preview[f'context-{clip}-{d}']=rel(vp);contextclips.append({'mode':mode,'clip':clip,'direction':d,'mp4':str(vp.relative_to(R))})
contextsheet=Image.new('RGBA',(768,2*372),BGS['light']);dr=ImageDraw.Draw(contextsheet)
for row,clip in enumerate(['eat','eat-salmon']):
 dr.text((8,row*372+4),clip+' + approved stool | shared native root(192,496)',fill='#17212b')
 for j,d in enumerate(DIRS):contextsheet.alpha_composite(Image.open(R/'contexts/frames'/clip/d/'04.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS),(j*192,row*372+20))
save(contextsheet,R/'contexts/stool-eating.png');preview['stool-eating-context']=rel(R/'contexts/stool-eating.png')
# Surface attachment comparison independently measures actual posed native meshes.
surface={};maxsurface=0
for mode in ['main','runtime']:
 src=load(R/f'support-{mode}-source.json')['samples'];cur=load(R/f'support-{mode}-candidate.json')['samples'];assert len(src)==(480 if mode=='main' else 96)
 values={}
 for a,b in zip(src,cur):
  assert (a['clip'],a['direction'],a['frame'])==(b['clip'],b['direction'],b['frame'])
  for k in a['supports']:
   value=math.dist(a['supports'][k]['nearestRemodeledSurfaceWorld'],b['supports'][k]['nearestRemodeledSurfaceWorld']);values[k]=max(values.get(k,0),value)
 surface[mode]={'samples':len(src),'maxDeviationBySurfaceWorld':values,'toleranceWorld':.005};maxsurface=max(maxsurface,*values.values())
assert maxsurface<=.005,surface
# Canonical pixel-edge semantic maps, full UV and aspect at primary alpha128;64/192 remain sensitivity evidence.
foodchecks={};mapping=load(RES/'food-mapping-proposal.json')
for food in ['cucumber','salmon']:
 im=Image.open(RES/f'dish-{food}-canonical.png').convert('RGBA');alpha=im.getchannel('A');W,H=im.size;mask=alpha.point(lambda a:255 if a>=128 else 0);L,T,RR,BB=mask.getbbox();xs=[x for x in range(W) if alpha.getpixel((x,BB-1))>=128];rim=((min(xs)+max(xs)+1)/2,BB)
 proposal=mapping['proposals'][food];m=proposal['thresholdSensitivity']['128'];v=m['newFullUVLocalVertices'];left,bottom=v[0][:2];right,top=v[2][:2];width=(right-left)*(RR-L)/W*1.25;support=[left+(right-left)*rim[0]/W,bottom+(top-bottom)*(1-rim[1]/H)]
 err=max(abs(width-proposal['thresholdSensitivity']['128']['sourceOccupiedWorldWidth']),*[(abs(support[i]-m['sourceBottomRimLocalXY'][i]) if 'sourceBottomRimLocalXY' in m else abs(support[i]-proposal['thresholdSensitivity']['128']['sourceBottomRimLocalXY'][i])) for i in [0,1]])
 assert err<1e-8,(food,width,support,err)
 assert abs((right-left)/(top-bottom)-W/H)<1e-8
 foodchecks[food]={'canonicalSHA256':sha(RES/f'dish-{food}-canonical.png'),'size':[W,H],'alpha128BoxPixelEdges':[L,T,RR,BB],'alpha128BottomRimPixelEdge':rim,'pointConvention':mapping['pointConvention'],'mappedOccupiedWidthWorld':width,'sourceOccupiedWidthWorld':m['sourceOccupiedWorldWidth'],'mappedBottomRimLocalXY':support,'sourceBottomRimLocalXY':m['sourceBottomRimLocalXY'],'mappingErrorWorld':err,'fullUV':True,'aspectPreserved':True,'depthWorldCells':.30,'sensitivity64And192':'Frozen proposal retained as descriptive sensitivity; not alternative mappings.'}
# Same-input repeated Blender processes empirically calibrate raster repeatability; never assert universal RGB identity.
repeat=[]
for clip,d,f in [('stand','S',0),('eat','S',4),('eat','N',4)]:
 aa=Image.open(R/'repeatability/A'/f'{clip}-{d}.png').convert('RGBA');bb=Image.open(R/'repeatability/B'/f'{clip}-{d}.png').convert('RGBA');cc=Image.open(R/'main/frames'/clip/d/f'{f:02}.png').convert('RGBA')
 for label,im in [('fresh-A-vs-fresh-B',bb),('fresh-A-vs-delivered-sequence',cc)]:
  diffs=[abs(x-y) for a,b in zip(aa.getdata(),im.getdata()) for x,y in zip(a,b)];repeat.append({'clip':clip,'direction':d,'frameIndex':f,'comparison':label,'maxRGBAChannelError8bit':max(diffs),'meanRGBAChannelError8bit':sum(diffs)/len(diffs),'differentChannels':sum(x!=0 for x in diffs)})
write(R/'repeatability/calibration.json',{'observations':repeat,'scope':'Three fixed same-input samples in two independent Blender processes, additionally compared with delivered full-sequence capture. These observations are not a universal RGB bit-identity claim.'})
# Actual saved scene dependency/mesh signatures, including groups and weights, agree between sources.
deps={mode:load(R/f'dependencies-{mode}.json') for mode in ['main','runtime']};assert deps['main']['bodySignatures']==deps['runtime']['bodySignatures'];assert all(all(v['bodyMaterials']) and v['allImagesPacked'] and not v['libraries'] and not v['foreignSceneObjects'] for v in deps.values())
# Registered native camera records with current scale2, independent of stale production scale4 metadata.
nativeRecords={}
for mode in ['main','runtime']:
 a=load(R/mode/'validation-native.json');rec=R/mode/'records';rec.mkdir(exist_ok=True)
 camera=load(RES/'source-camera.json');camera.update({'captureScale':2,'frame':[192,320],'anchor':[96,248],'fps':12,'actualNativeFrame':[384,640],'actualNativeRootPixels':a['rootProjection'],'actualRegisteredCamera':a['camera'],'camera':{'type':'orthographic','worldMatrix':a['camera']['matrix'],'projectionMatrix':a['camera']['projectionMatrix'],'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35,'orthoScale':a['camera']['orthoScale'],'shift':a['camera']['shift']},'artStyle':{'lighting':'Warm soft;300W overhead+4 symmetric125W broad area fills','horizontalSymmetry':4,'noDirectionalGroundShadows':True,'colorManagement':'Standard; no compositor grade'}})
 camera['calibration']={k:[x/2 for x in v] for k,v in camera['calibration'].items()};camera['calibration']['root']=a['rootProjection'];write(rec/'camera.json',camera)
 sourceasset=P/'inputs/source-assetRecord.json' if mode=='main' else P/'inputs/runtime-variants/export/source/customer-samir/asset.json';asset=load(sourceasset);asset.update({'scale':2,'frame':[192,320],'anchor':[96,248],'captureScale':2,'refinement':'warm-soft-round-01','functionalBodyBoundsByClip':{k:v['boundsUnion'] for k,v in a['clips'].items()},'artStyle':camera['artStyle']});write(rec/'asset.json',asset)
 write(rec/'rig.json',load(RES/f'source-{mode}-rig.json'));nativeRecords[mode]={'camera':rel(rec/'camera.json'),'assetRecord':rel(rec/'asset.json'),'rig':rel(rec/'rig.json')}
# Full native validation summary: individual frame evidence is retained in main/runtime validation-native.json.
errors=[]
for mode in ['main','runtime']:
 a=load(R/mode/'validation-native.json');errors+=a['errors'];assert len(a['clips'])==(10 if mode=='main' else 2)
 for clip,info in a['clips'].items():
  env=B['constraints']['functionalGeometryEnvelope']['perClipBodyZWorld'][clip]
  for s in info['samples']:
   lo,hi=s['bodyBounds'];assert lo[2]>=env[0]-1e-5 and hi[2]<=env[1]+1e-5,(mode,clip,s['direction'],s['frame'],lo,hi,env)
  assert len(info['samples'])==48
 for k,v in a['maxima'].items():assert v<(0.01 if 'Pixels' in k else 1e-5),(k,v)
 assert max(a['loopClosureMaxBoneMatrixError'].values(),default=0)<1e-5
validation={'status':'technical-checks-passed; independent aesthetic review pending','totalNativeFrames':len(imagechecks),'mainNativeFrames':len(allframes['main']),'runtimeNativeFrames':len(allframes['runtime']),'mainAtlases':len(allatlases['main']),'runtimeAtlases':len(allatlases['runtime']),'actual12fpsClips':48,'additionalRegisteredContextClips':16,'wholeCanvasAtlasPixelChecksPassed':True,'sourceRigRestActionsContactsVisibility':{mode:load(R/mode/'validation-native.json')['maxima'] for mode in ['main','runtime']},'nativeFrameAudits':{mode:rel(R/mode/'validation-native.json') for mode in ['main','runtime']},'functionalSurfaceAttachments':surface,'matchingMainRuntimeNativeGeometryMaterialsAndWeights':True,'dependencyClosure':{mode:rel(R/f'dependencies-{mode}.json') for mode in ['main','runtime']},'foodSemantics':foodchecks,'repeatabilityCalibration':rel(R/'repeatability/calibration.json'),'allNativeAlphaClippingChecks':imagechecks,'videoVerification':videochecks,'errors':errors};assert len(imagechecks)==576;write(R/'validation.json',validation)
# Playback data and self-contained review page; exact PNG frames animate at12fps with correct source loop semantics.
write(R/'playback-manifest.json',{'clips':temporal,'contexts':contextclips,'frameRate':12,'noFrameCroppingOrFitting':True,'backgrounds':BGS,'stoolRegistration':'Approved 384x704 stool and candidate384x640 share native root192,496. Compose at0,0 without rescaling; displayed at logical half scale.'})
page='''<!doctype html><meta charset="utf-8"><title>Samir native round01 review</title><style>body{margin:0;background:#e8e3d8;color:#182734;font:15px system-ui}header{position:sticky;top:0;background:#f5efe4;padding:12px;z-index:2;box-shadow:0 2px 8px #0002}button,select{font:inherit;margin:4px;padding:8px}section{max-width:820px;margin:24px auto}.row{display:grid;grid-template-columns:repeat(4,192px);gap:8px}.tile{background:var(--bg,#f3ede2);border-radius:12px;text-align:center}canvas.sprite{width:192px;height:320px;display:block}a{color:#1c566e}.phone{width:390px;height:844px;max-width:100%;border:2px solid #59616c;border-radius:20px;overflow:hidden;margin:auto}#phone{width:390px;height:844px;max-width:100%}@media(max-width:810px){.row{grid-template-columns:repeat(2,192px);justify-content:center}}@media(max-width:400px){.row{grid-template-columns:192px}section{padding:8px}}</style><header><b>Samir · native round01 · independent review pending</b><br>576 native frames ·48 real12fps MP4 clips ·exact canonical packed2D food<br><button onclick="replay()">Replay source clips</button><select id="bg" onchange="setbg(this.value)"><option value="#f3ede2">Light</option><option value="#89939b">Gray</option><option value="#202832">Dark</option></select><label><input id="force" type="checkbox">Repeat nonlooping clips for inspection</label><a href="validation.json">Technical evidence</a> ·<a href="comparison.png">Frozen comparison</a></header><section><h2>Registered phone / stool / eating context</h2><select id="context"><option>eat</option><option>seated-wait</option><option>eat-salmon</option><option>seated-wait-empty</option></select><select id="facing"><option>S</option><option>E</option><option>N</option><option>W</option></select><div class="phone"><canvas id="phone" width="390" height="844"></canvas></div><p>Shared logical root195,530; native192,496. Approved stool and new body are separately captured whole canvases. Food in character frames is explicitly2D.</p></section><main id="clips"></main><script>let data,players=[],start=performance.now(),bg='#f3ede2',images={};function replay(){start=performance.now()}function setbg(v){bg=v;document.documentElement.style.setProperty('--bg',v)}function load(src){if(!images[src]){let im=new Image;im.src=src;images[src]=im}return images[src]}fetch('playback-manifest.json').then(r=>r.json()).then(m=>{data=m;for(let c of m.clips){let sec=document.getElementById(c.clip);if(!sec){sec=document.createElement('section');sec.id=c.clip;sec.innerHTML='<h2>'+c.clip+' ·12fps ·'+(c.loop?'loop':'source one-shot')+'</h2><div class="row"></div>';document.querySelector('main').append(sec)}let tile=document.createElement('div');tile.className='tile';let cv=document.createElement('canvas');cv.width=384;cv.height=640;cv.className='sprite';cv.dataset.clip=c.clip;cv.dataset.direction=c.direction;tile.append(cv);let a=document.createElement('a');a.href=c.mp4;a.innerText=c.direction+' ·actual12fps MP4';tile.append(a);sec.querySelector('.row').append(tile);players.push({...c,cv,ims:c.frames.map(load)})}requestAnimationFrame(tick)});function tick(t){let n=Math.floor((t-start)*12/1000);for(let p of players){let f=p.loop||document.getElementById('force').checked?n%12:Math.min(11,n),ctx=p.cv.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,384,640);if(p.ims[f].complete)ctx.drawImage(p.ims[f],0,0);p.cv.dataset.frame=f}let cv=document.getElementById('phone'),ctx=cv.getContext('2d');ctx.fillStyle='#f2e7d1';ctx.fillRect(0,0,390,844);ctx.strokeStyle='#dbceaf';for(let y=300;y<844;y+=73.42){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(390,y);ctx.stroke()}for(let x=3;x<390;x+=128){ctx.beginPath();ctx.moveTo(x,300);ctx.lineTo(x,844);ctx.stroke()}ctx.fillStyle='#1d3342';ctx.font='24px system-ui';ctx.fillText('Samir · registered context',28,66);ctx.font='15px system-ui';ctx.fillText('12fps ·whole sprite frames ·shared ground root',28,96);let c=document.getElementById('context').value,d=document.getElementById('facing').value,f=n%12,im=load('contexts/frames/'+c+'/'+d+'/'+String(f).padStart(2,'0')+'.png');if(im.complete)ctx.drawImage(im,99,282,192,352);ctx.fillStyle='#a6432b';ctx.fillRect(191,528,8,4);ctx.fillRect(194,525,2,10);cv.dataset.frame=f;cv.dataset.clip=c;cv.dataset.direction=d;requestAnimationFrame(tick)}</script>'''
(R/'playback.html').write_text(page);preview['playback-index']=rel(R/'playback.html');preview['phone-context']=rel(R/'playback.html')
# Input provenance binds original raw packed source food and all approved context rasters in addition to frozen brief/criteria.
provenance=load(D/'input-provenance.json')
for p in RES.iterdir():
 if p.is_file() and p.name not in provenance:provenance[p.name]={'sourcePath':'Copied immutable original / approved context resource; see recipe','sha256':sha(p)}
write(D/'input-provenance.json',provenance)
resources={rel(p):rel(p) for p in list(RES.iterdir())+list(D.glob('*.py'))+[D/'input-provenance.json',R/'playback-manifest.json',R/'repeatability/calibration.json',R/'dependencies-main.json',R/'dependencies-runtime.json'] if p.is_file()}
for p in R.glob('support-*.json'):resources[rel(p)]=rel(p)
for mode in ['main','runtime']:
 for p in (R/mode/'records').glob('*.json'):resources[rel(p)]=rel(p)
runtime={'project':rel(D/'samir-runtime.blend'),'recipe':rel(D/'refine.py'),'settings':rel(D/'build-runtime.json'),'validation':rel(R/'runtime/validation-native.json'),'rawFrames':allframes['runtime'],'atlases':allatlases['runtime'],'clips':clips['runtime'],'nativeRecords':nativeRecords['runtime'],'previews':{k:v for k,v in preview.items() if k.startswith(('eat-salmon','seated-wait-empty','context-eat-salmon','context-seated-wait-empty'))},'food':'Exact canonical packed2D salmon only for eat-salmon; seated-wait-empty remains empty.'}
delivery={'asset':'customer-samir','assetId':'customer-samir','round':'round-01','status':'ready-for-independent-review','brief':'brief.json','briefSHA256':sha(P/'brief.json'),'criteriaFile':'reviews/proposedcriteria.json','criteriaFileSHA256':sha(P/'reviews/proposedcriteria.json'),'project':rel(D/'samir-main.blend'),'recipe':rel(D/'refine.py'),'settings':rel(D/'build-main.json'),'validation':rel(R/'validation.json'),'heroes':{d:rel(R/'main/frames/stand'/d/'04.png') for d in DIRS},'rawFrames':allframes['main'],'atlases':allatlases['main'],'clips':clips['main'],'previews':preview,'playbackIndex':rel(R/'playback.html'),'nativeRecords':nativeRecords['main'],'runtimeVariants':runtime,'capture':{'frame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'captureScale':2,'fps':12,'cardinalRootAnglesDegrees':{'S':0,'E':90,'N':180,'W':-90},'poseFitting':False},'resources':resources,'sourceConsistentLimits':['Actual35° registered camera used; ImageGen apparent frontal pose/framing does not replace it.','Cap sewing/grain are not copied literally; solid curved bill/crown/button and native collar carry construction.','Native source timing and functional contacts are retained; neutral height is not an all-pose cap.','Canonical food is an honest packed2D image plane, not modeled3D sushi. Alpha128 source-specific mapping retained; one constant .30world-cell camera-ray depth per composition.','RGB repeatability is empirically calibrated only for the declared same-input samples.'],'editorInspection':'source/editor-observations.json','reviewRule':'No editor self-approval. Root coordinator must seal complete delivery and request original independent Samir judge review before promotion.'}
write(R/'delivery.json',delivery)
write(R/'file-hashes.json',{rel(p):sha(p) for p in [D/'samir-main.blend',D/'samir-runtime.blend',D/'refine.py',R/'validation.json',R/'delivery.json']})
print('COMPLETE',R/'delivery.json',sha(R/'delivery.json'),flush=True)
