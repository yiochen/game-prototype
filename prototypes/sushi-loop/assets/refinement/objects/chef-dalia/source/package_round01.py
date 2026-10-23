"""Exact native frame packing and identified review-only composites/playbacks."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,subprocess,shutil
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-01';PROD=BASE.parents[2]/'production'
CLIPS=['idle','work','hold','load'];DIRS=['N','E','S','W'];BG={'light':'#f3f0e7','gray':'#8a8d8b','dark':'#242c30'}
for n in ['atlases','sheets','playbacks','backgrounds','contexts','native-records','resources']:(OUT/n).mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def rel(p):return p.relative_to(BASE).as_posix()
def rgba(p):return Image.open(p).convert('RGBA')
def logical(im):return im.resize((192,320),Image.Resampling.LANCZOS)
def flat(im,bg):
 a=Image.new('RGBA',im.size,bg);a.alpha_composite(im);return a.convert('RGB')
def font(n):
 try:return ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',n)
 except OSError:return ImageFont.load_default()
def rawpath(c,d,i):return OUT/'frames'/f'{c}-{d}'/f'{i:03d}.png'
def video_encode(pattern,path,w=384,h=640):
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','12','-i',str(pattern),'-frames:v','12','-r','12','-c:v','libx264','-crf','16','-pix_fmt','yuv420p','-movflags','+faststart',str(path)],check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=r_frame_rate,avg_frame_rate,nb_read_frames,width,height,duration','-of','json',str(path)]))['streams'][0]
 assert probe['r_frame_rate']=='12/1' and int(probe['nb_read_frames'])==12 and float(probe['duration'])==1
 return probe
rows=json.loads((OUT/'native-frames.json').read_text());assert len(rows)==192
lookup={(r['clip'],r['direction'],r['index']):r for r in rows};catalog=json.loads((BASE/'inputs/catalog-object.json').read_text());clips={c['id']:c for c in catalog['clips']}
raw=[];atlases=[];videos=[];sheets=[];alpha=[];previews={};sheetchecks=[]
for clip in CLIPS:
 for direction in DIRS:
  ims=[rgba(rawpath(clip,direction,i)) for i in range(12)];record=clips[clip]['directions'][direction];assert record['atlasSize']==[2304,1280]
  atlas=Image.new('RGBA',record['atlasSize'])
  for i,im in enumerate(ims):
   p=rawpath(clip,direction,i);assert im.size==(384,640) and sha(p)==lookup[(clip,direction,i)]['sha256'];r=record['rects'][i];assert r[2:]==[384,640];atlas.paste(im,tuple(r[:2]));box=im.getchannel('A').getbbox();assert box and 0<box[0]<box[2]<384 and 0<box[1]<box[3]<640
   raw.append({'clip':clip,'direction':direction,'index':i,'path':rel(p),'sha256':sha(p)});alpha.append({'clip':clip,'direction':direction,'index':i,'alphaBounds':box,'clipped':False})
  path=OUT/'atlases'/f'{clip}-{direction}.png';atlas.save(path,compress_level=9)
  reread=rgba(path)
  for i,im in enumerate(ims):
   x,y,w,h=record['rects'][i];assert reread.crop((x,y,x+w,y+h)).tobytes()==im.tobytes()
  atlases.append({'clip':clip,'direction':direction,'path':rel(path),'sha256':sha(path),'columns':record['columns'],'rows':record['rows'],'atlasSize':record['atlasSize'],'rects':record['rects'],'frameOrder':list(range(12)),'fps':12,'loop':clips[clip]['loop']})
  for bg,color in BG.items():
   for display,scale in [('logical',1),('enlarged',2)]:
    fw,fh=192*scale,320*scale;head=24*scale;sheet=Image.new('RGB',(6*fw,2*(fh+head)),color);dr=ImageDraw.Draw(sheet)
    for i,im in enumerate(ims):
     x=i%6*fw;y=i//6*(fh+head);shown=logical(im) if scale==1 else im;shown=flat(shown,color);sheet.paste(shown,(x,y+head));dr.text((x+6*scale,y+4*scale),f'{clip} {direction} · {i:02} · 12fps',font=font(14*scale),fill='#243339' if bg!='dark' else '#f1ede0')
     assert sheet.crop((x,y+head,x+fw,y+head+fh)).tobytes()==shown.tobytes()
    path=OUT/'sheets'/f'{clip}-{direction}-{bg}-{display}.png';sheet.save(path);sheets.append({'clip':clip,'direction':direction,'background':bg,'display':display,'path':rel(path),'sha256':sha(path),'nativeFrameSize':[384,640],'displayFrameSize':[fw,fh],'pixelVerified':True});previews[f'all-frames-{clip}-{direction}-{bg}-{display}']=rel(path)
  temp=OUT/'playbacks'/f'_{clip}-{direction}';temp.mkdir(exist_ok=True)
  for i,im in enumerate(ims):flat(im,BG['gray']).save(temp/f'{i:03d}.png')
  path=OUT/'playbacks'/f'{clip}-{direction}.mp4';probe=video_encode(temp/'%03d.png',path);shutil.rmtree(temp)
  videos.append({'clip':clip,'direction':direction,'path':rel(path),'sha256':sha(path),'fps':12,'frames':12,'durationSeconds':1,'loop':clips[clip]['loop'],'ffprobe':probe});previews[f'{clip}-{direction}']=rel(path)
# Four registered native facings and all-state/background evidence.
four=Image.new('RGB',(1536,674),BG['light']);dr=ImageDraw.Draw(four)
for di,d in enumerate(DIRS):four.paste(flat(rgba(rawpath('idle',d,0)),BG['light']),(di*384,34));dr.text((di*384+14,8),f'{d} · native384×640',font=font(19),fill='#243339')
four.save(OUT/'four-view-sheet.png');previews['four-view-sheet']=rel(OUT/'four-view-sheet.png')
for bg,color in BG.items():
 sheet=Image.new('RGB',(768,1376),color);dr=ImageDraw.Draw(sheet)
 for ci,c in enumerate(CLIPS):
  for di,d in enumerate(DIRS):sheet.paste(flat(logical(rgba(rawpath(c,d,5))),color),(di*192,ci*344+24));dr.text((di*192+7,ci*344+5),f'{c} {d} frame05',font=font(14),fill='#243339' if bg!='dark' else '#f1ede0')
 path=OUT/'backgrounds'/f'all-states-facings-{bg}.png';sheet.save(path);previews[f'background-{bg}']=rel(path)
# Registered128px cell-pitch repeated context at logical scale.
repeat=Image.new('RGBA',(768,520),BG['light']);dr=ImageDraw.Draw(repeat)
for row in range(2):
 for col,d in enumerate(DIRS):
  rootpx=(192+col*128,248+row*128);dr.line([(rootpx[0]-64,rootpx[1]),(rootpx[0]+64,rootpx[1])],fill='#c8c3b8');repeat.alpha_composite(logical(rgba(rawpath('idle',d,0))),(rootpx[0]-96,rootpx[1]-248))
repeat.convert('RGB').save(OUT/'repeated.png');previews['repeated']=rel(OUT/'repeated.png')
comparison=Image.new('RGB',(768,674),BG['light']);dr=ImageDraw.Draw(comparison)
for i,(title,path) in enumerate([('Original · same registration',BASE/'inputs/original.png'),('Dalia round01 · native',rawpath('idle','S',0))]):comparison.paste(flat(rgba(path),BG['light']),(i*384,34));dr.text((i*384+12,8),title,font=font(19),fill='#243339')
comparison.save(OUT/'comparison.png');previews['comparison']=rel(OUT/'comparison.png')
# Evaluated contact markers only on labeled review contexts.
cal=json.loads((P/'recipe-round01.json').read_text())['camera'];ct={(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'evaluated-contacts.json').read_text())}
def project(v):return tuple(cal['root'][i]+cal['unitX'][i]*v[0]-cal['unitDepth'][i]*v[1]+cal['unitHeight'][i]*v[2] for i in range(2))
for clip in ['work','hold','load']:
 sheet=Image.new('RGB',(1536,674),BG['light']);dr=ImageDraw.Draw(sheet)
 for di,d in enumerate(DIRS):
  im=flat(rgba(rawpath(clip,d,5)),BG['light']);draw=ImageDraw.Draw(im);r=ct[(clip,d,5)]
  def dot(v,color,radius=5):
   x,y=project(v);draw.ellipse((x-radius,y-radius,x+radius,y+radius),outline=color,width=2)
  for v in r['palms'].values():dot(v,'#0873d2')
  for foot in r['feet'].values():dot([(x[0]+x[1])*.5 for x in foot['bounds']],'#148c39')
  for n,p in r['props'].items():
   if ('__held_' in n and '__image_plane' not in n) or ('__utensil' in n and clip=='work'):dot([p['matrix'][i][3] for i in range(3)],'#d15b22',7)
  sheet.paste(im,(di*384,34));dr.text((di*384+10,8),f'{clip} {d} f05 · contact markers',font=font(16),fill='#243339')
 path=OUT/'contexts'/f'{clip}-contacts.png';sheet.save(path);previews[f'{clip}-contact-context']=rel(path)
# Original source/candidate serving contexts use the same registered roots and128px cell pitch.
contextdeps=[];contexts=[];dep=OUT/'resources/context';dep.mkdir(exist_ok=True)
def copy_context(src,name):
 dest=dep/name;shutil.copyfile(src,dest);contextdeps.append({'path':rel(dest),'sourcePath':str(src),'sha256':sha(dest)});return dest
beltpath=copy_context(PROD/'sprites/belt-straight-e/running-S.png','belt-straight-e-running-S.png')
# Resolve actual source belt record if naming differs, without inventing a crop.
lib=json.loads((PROD/'library.json').read_text());belt=next(a for a in lib['objects'] if a['id']=='belt-straight-e');beltrec=belt['clips'][0]['directions']['S'];assert (PROD/beltrec['image']).is_file()
if (PROD/beltrec['image']).resolve()!= (PROD/'sprites/belt-straight-e/running-S.png').resolve():beltpath=copy_context(PROD/beltrec['image'],'belt-context-source.png')
beltim=rgba(beltpath).crop((0,0,384,704)).resize((192,352),Image.Resampling.LANCZOS)
for d in DIRS:
 originalpath=copy_context(PROD/'sprites/chef-dalia'/f'load-{d}.png',f'original-load-{d}.png');original=rgba(originalpath)
 delta={'N':(0,-128),'E':(128,0),'S':(0,128),'W':(-128,0)}[d];cr=(256,360);br=(cr[0]+delta[0],cr[1]+delta[1])
 for kind in ['source','candidate']:
  temp=OUT/'contexts'/f'_{kind}-load-{d}';temp.mkdir(exist_ok=True)
  for i in range(12):
   x,y,w,h=clips['load']['directions'][d]['rects'][i];chef=logical(original.crop((x,y,x+w,y+h))) if kind=='source' else logical(rgba(rawpath('load',d,i)))
   im=Image.new('RGBA',(512,640),BG['light']);draw=ImageDraw.Draw(im)
   for x in range(0,513,128):draw.line([(x,0),(x,640)],fill='#ded8cc')
   for y in range(-24,641,128):draw.line([(0,y),(512,y)],fill='#ded8cc')
   def putbelt():im.alpha_composite(beltim,(br[0]-96,br[1]-248))
   def putchef():im.alpha_composite(chef,(cr[0]-96,cr[1]-248))
   if d=='S':putchef();putbelt()
   else:putbelt();putchef()
   draw=ImageDraw.Draw(im);draw.text((12,10),f'{kind} load {d} · frame{i:02d} ·128px cell pitch',font=font(17),fill='#243339');draw.text((12,611),'Original load returns holding. No release trajectory is authored.',font=font(14),fill='#243339')
   im=im.convert('RGB');im.save(temp/f'{i:03d}.png')
   if i in [0,5,11]:im.save(OUT/'contexts'/f'{kind}-load-{d}-{i:02d}.png')
  path=OUT/'contexts'/f'{kind}-load-{d}.mp4';probe=video_encode(temp/'%03d.png',path);shutil.rmtree(temp);contexts.append({'kind':kind,'clip':'load','direction':d,'path':rel(path),'sha256':sha(path),'fps':12,'frames':12,'loop':False,'chefRoot':cr,'beltRoot':br,'cellPitch':128,'probe':probe});previews[f'{kind}-load-{d}-context']=rel(path)
# Native registration records honestly describe captureScale2.
recipe=json.loads((P/'recipe-round01.json').read_text());nr=OUT/'native-records'
camera=json.loads((BASE/'inputs/source-camera.json').read_text());camera['captureScale']=2;camera['sourceScale']=2;camera['calibration']={k:recipe['camera'][k] for k in ['root','unitX','unitDepth','unitHeight']};camera['camera']['worldMatrix']=recipe['camera']['worldMatrix'];camera['camera']['projectionMatrix']=recipe['camera']['projectionMatrix'];camera['artStyle']={'revision':'warm-soft-native-round01','lighting':'Symmetric overhead plus four equal cardinal fills','renderer':recipe['renderer']};write(nr/'camera.json',camera)
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['sourceScale']=2;asset['artStyle']={'revision':'warm-soft-native-round01','lightingSymmetry':4,'noGroundShadow':True,'nativeRenderer':'Cycles Metal','sourceRigAndActionsPreserved':True};write(nr/'asset.json',asset)
rig=json.loads((P/'rig-round01.json').read_text());rig['sourceScale']=2;rig['originalBakeSource']=rig.get('source');rig['source']='source/native_actions_round01.py';rig['refinementNativeSource']={'project':'source/round-01.blend','runtime':'source/native_actions_round01.py','runtimeSHA256':sha(P/'native_actions_round01.py'),'sourceScale':2,'all192FramesAudited':True,'originalRestBonesAndActionCurvesPreserved':True};write(nr/'rig.json',rig)
for p in (P/'dependencies').glob('*.png'):shutil.copyfile(p,OUT/'resources'/p.name)
write(OUT/'alpha-and-atlas-validation.json',{'ok':True,'rawFrameCount':192,'atlasCount':16,'allRectanglesEqualNativePixels':True,'originalRectsPreserved':True,'allFrameSheetsPixelVerified':True,'sheetCount':len(sheets),'alpha':alpha})
write(OUT/'playback-validation.json',{'ok':True,'actual12fpsNativePlaybacks':videos,'contexts':contexts})
write(OUT/'preview-manifest.json',{'sheets':sheets,'videos':videos,'contexts':contexts,'contextDependencies':contextdeps,'policy':'Native frames/atlases unchanged. Backgrounds, labels, contact markers and registered source belt compositions are review-only.'})
# One human-readable evidence index preserves authored nonloop load behavior.
html='''<!doctype html><meta charset="utf-8"><title>Dalia round01 native motion evidence</title><style>body{font:14px system-ui;background:#ece8de;color:#243339;margin:24px}main{display:grid;grid-template-columns:repeat(4,192px);gap:16px}figure{margin:0}video{display:block;width:192px;height:320px;background:#8a8d8b}button{font:inherit;padding:8px;margin:8px}.contexts{display:grid;grid-template-columns:repeat(4,256px);gap:16px}.contexts video{width:256px;height:320px}img{max-width:100%}details{margin-top:20px}a{color:#075c65}</style><h1>Dalia · round01 · exact native motion</h1><p>All16 required clips have12 indexed runtime frames at12fps. Idle/work/hold loop. Load ends at the original returned holding pose. Original packed2D salmon remains an explicit exception; the chef and knife are native3D.</p><button onclick="document.querySelectorAll('video').forEach(v=>{v.currentTime=0;v.play()})">Play all from frame00</button><button onclick="document.querySelectorAll('video').forEach(v=>v.pause())">Pause all</button><main>'''
for v in videos:
 url=Path(v['path']).relative_to('candidates/round-01').as_posix();loop=' loop' if v['loop'] else ''
 html+=f'<figure><figcaption>{v["clip"]}-{v["direction"]} ·12fps ·{"loop" if v["loop"] else "nonloop"}</figcaption><video muted controls playsinline preload="auto"{loop} src="{url}"></video></figure>'
html+='</main><h2>Registered source and candidate serving contexts</h2><p>Both use the original128px cell pitch. The authored load extends and returns with the dish held; no new release or belt flight is added.</p><div class="contexts">'
for v in contexts:
 url=Path(v['path']).relative_to('candidates/round-01').as_posix();html+=f'<figure><figcaption>{v["kind"]} load {v["direction"]}</figcaption><video muted controls playsinline preload="auto" src="{url}"></video></figure>'
html+='</div><details><summary>Four native facings and comparison</summary><img src="four-view-sheet.png"><img src="comparison.png"></details><details><summary>All native frames · intended and enlarged size · light/gray/dark</summary>'
for s in sheets:html+=f'<a href="{Path(s["path"]).relative_to("candidates/round-01")}">{s["clip"]}-{s["direction"]}-{s["background"]}-{s["display"]}</a> · '
html+='</details>';(OUT/'playback.html').write_text(html);previews['playback-index']=rel(OUT/'playback.html')
v=json.loads((OUT/'validation.json').read_text());source_path=(BASE/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend').resolve();source_sha=sha(source_path);expected=json.loads((BASE/'brief.json').read_text())['source']['backupSHA256'];v['originalSourceIntegrity']={'path':str(source_path),'sha256':source_sha,'expectedSHA256':expected,'unchanged':source_sha==expected};v['ok']=v['ok'] and source_sha==expected;ev=json.loads((OUT/'envelope-validation.json').read_text());v.update(atlasCount=16,playbackCount=16,allFramesSheetCount=len(sheets),contextPlaybackCount=len(contexts),allAtlasFramesPixelExact=True,originalLayoutPreserved=True,allFramesInsideAlphaCanvas=True,envelopeValidation=rel(OUT/'envelope-validation.json'),previewManifest=rel(OUT/'preview-manifest.json'),playbackValidation=rel(OUT/'playback-validation.json'),alphaValidation=rel(OUT/'alpha-and-atlas-validation.json'));v['ok']=v['ok'] and ev['ok'];v['runtimeFrameInterpretation']='Twelve indexed runtime frames per clip; original authored endpoint pose repeats are retained and do not reduce frame count.';v['topologyScout']='candidates/round-01/topology-scout.json';write(OUT/'complete-validation.json',v)
resources={p.name:rel(p) for p in P.glob('*') if p.is_file() and p.suffix in ['.blend','.py','.json']}
for p in (OUT/'resources').rglob('*'):
 if p.is_file():resources['evidence-'+p.name]=rel(p)
delivery={'schemaVersion':1,'asset':'chef-dalia','round':'round-01','pipeline':'native-3d','status':'candidate-ready-for-independent-review','project':'source/round-01.blend','recipe':'source/recipe-round01.json','recipeScript':'source/build_round01.py','validation':rel(OUT/'complete-validation.json'),'heroes':{d:rel(rawpath('idle',d,0)) for d in DIRS},'rawFrames':raw,'atlases':atlases,'previews':previews,'nativeRecords':{'camera':rel(nr/'camera.json'),'assetRecord':rel(nr/'asset.json'),'rig':rel(nr/'rig.json')},'resources':resources,'representation':{'actor':'editable native Blender mesh/materials/rig','knife':'native3D','heldSalmon':'exact original packed2D image plane, original UV/geometry/actions and yaw/depth drivers'},'notes':['Frozen qualityCriteria v1 acknowledged; judge owns visual verdict.','One registered camera/scale and one common material/light setup. No per-view fitting or recoloring.','All12 indexed runtime frames preserved, including authored endpoint repeat; no load release invented.','All review backgrounds, text, markers and context assembly are identified composites; raw frames and atlases are exact native RGBA.']}
write(BASE/'delivery.json',delivery)
write(OUT/'editor-handoff-hashes.json',{'status':'Ready for coordinator sealing and independent judge review','files':{rel(p):sha(p) for p in [P/'round-01.blend',P/'recipe-round01.json',OUT/'complete-validation.json',BASE/'delivery.json']},'nativeFrames':192,'atlases':16,'playbacks':16})
print('PACKED',v['ok'],len(raw),len(atlases),len(videos),len(sheets),len(contexts))
