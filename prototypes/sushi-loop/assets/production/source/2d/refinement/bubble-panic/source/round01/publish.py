"""Closed native2D panic publisher. Original raster animation and atlas math.
No paint/erase/warp: sole crop declared in prepare_sources.py; uniform width82.
Python3 + Pillow are the only publisher dependencies. Godot evidence retained.
"""
from pathlib import Path
import copy,json,hashlib,math,sys,struct,zlib,io,importlib.util
import PIL
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;O=S.parents[1];R=S/'resources';C=O/'candidates/round01'
FRAME=(384,640);LOGICAL=(192,320);ROOT=(96,248);DIRS=['S','N','E','W'];CLIPS=['appear','idle','fade'];RS=Image.Resampling.LANCZOS
RECTS=[[i%6*384,i//6*640,384,640]for i in range(12)];COLORS=[('light',(246,241,229)),('gray',(124,125,129)),('dark',(29,32,38))];WINDOW=(88,284,296,500)
def rel(p):return p.relative_to(O).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psha(im):return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def width(im,w):return im.resize((round(w),round(im.height/im.width*w)),RS)
def center(c,im,xy):c.alpha_composite(im,(round(xy[0]-im.width/2),round(xy[1]-im.height/2)))
def background(im,color):c=Image.new('RGBA',im.size,color+(255,));c.alpha_composite(im);return c.convert('RGB')
def apng(path,frames,plays=0):
 def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v)&0xffffffff)
 blobs=[];header=None
 for frame in frames:
  stream=io.BytesIO();frame.convert('RGBA').save(stream,format='PNG',compress_level=9);data=stream.getvalue();pos=8;ids=[]
  while pos<len(data):
   n=struct.unpack('>I',data[pos:pos+4])[0];k=data[pos+4:pos+8];v=data[pos+8:pos+8+n];pos+=n+12
   if k==b'IHDR':header=v
   elif k==b'IDAT':ids.append(v)
  blobs.append(b''.join(ids))
 result=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'acTL',struct.pack('>II',len(frames),plays));seq=0
 for i,blob in enumerate(blobs):
  result+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',seq,frames[i].width,frames[i].height,0,0,1,12,0,0));seq+=1
  if i==0:result+=chunk(b'IDAT',blob)
  else:result+=chunk(b'fdAT',struct.pack('>I',seq)+blob);seq+=1
 path.write_bytes(result)
def make_frame(cutout,clip,index):
 image=cutout.copy();phase=index/12*math.tau;opacity=1.;scale=1.
 if 'appear' in clip:scale=.5+.5*math.sin((index+1)/12*math.pi/2);opacity=(index+1)/12
 elif 'fade' in clip:opacity=1-index/12
 if scale!=1:image=image.resize((round(image.width*scale),round(image.height*scale)),RS)
 if opacity<1:image.putalpha(image.getchannel('A').point(lambda a:round(a*max(0,opacity))))
 c=Image.new('RGBA',FRAME);center(c,image,(ROOT[0]*2,(ROOT[1]-52-3*math.sin(phase))*2));return c

def main():
 for sub in ['raw','atlases','previews','native-context/scripts']:(C/sub).mkdir(parents=True,exist_ok=True)
 prov=json.loads((S/'provenance.json').read_text());crop=json.loads((S/'crop.json').read_text());catalog=json.loads((R/'catalog-object.json').read_text())
 for r in prov['resources']:assert sha(O/r['path'])==r['sha256'],r['path']
 assert sha(R/'frozen-brief.json')=='b4896deb6746eb974bc42f02fd9a256336fd64435cc0510cfbe013c5949ca776'
 assert sha(R/'frozen-criteria.json')=='972b91f779f72b132ee58e0e27e0d9767a406f04dc6ef8c7dac1a1c82480241d'
 art=load(S/'bubble-panic.png');raw=load(R/'target.png');assert art.tobytes()==raw.crop(crop['box']).tobytes();cutout=width(art,164)
 frames={};records=[];atlases=[];entries={};alpha=[];previews={}
 def preview(key,im):
  p=C/'previews'/(key+'.png');im.save(p,compress_level=9);previews[key]=rel(p)
 for clip in CLIPS:
  seq=[make_frame(cutout,clip,i)for i in range(12)];frames[clip]=seq;atlas=Image.new('RGBA',(2304,1280));hashes=[]
  for i,im in enumerate(seq):
   p=C/'raw'/f'{clip}-S-{i:04d}.png';im.save(p,compress_level=9);x,y,w,h=RECTS[i];atlas.alpha_composite(im,(x,y));hashes.append(psha(im))
   for d in DIRS:records.append({'clip':clip,'facing':d,'direction':d,'index':i,'frame':i,'path':rel(p),'size':list(FRAME),'sha256':sha(p),'pixelSHA256':psha(im),'aliasOf':f'{clip}:S:{i}'if d!='S'else None})
   a=im.getchannel('A');border=max(a.crop(b).getextrema()[1]for b in [(0,0,384,1),(0,639,384,640),(0,0,1,640),(383,0,384,640)]);assert border==0
   alpha.append({'clip':clip,'index':i,'alpha0Bounds':a.getbbox(),'alpha8Bounds':a.point(lambda v:255 if v>8 else 0).getbbox(),'maxBorderAlpha':border,'maxAlpha':a.getextrema()[1],'alpha1to8PixelCount':sum(a.histogram()[1:9])})
  ap=C/'atlases'/f'2d-{clip}-S.png';atlas.save(ap,compress_level=9);entry={'image':f'sprites/bubble-panic/2d-{clip}-S.png','columns':6,'rows':2,'atlasSize':[2304,1280],'rects':RECTS,'uniqueFrames':len(set(hashes)),'sha256':sha(ap)};entries[clip]=entry;assert len(set(hashes))>=6
  for d in DIRS:atlases.append({'clip':clip,'facing':d,'direction':d,'path':rel(ap),'size':[2304,1280],'atlasSize':[2304,1280],'columns':6,'rows':2,'rects':RECTS,'frames':12,'uniqueFrames':len(set(hashes)),'sha256':sha(ap),'aliasOf':clip+':S'if d!='S'else None})
  p=C/'previews'/f'{clip}-S.png';apng(p,seq,0 if clip=='idle' else 1)
  for d in DIRS:previews[clip+'-'+d]=rel(p)
 # Direct replay of untouched original publisher and each original atlas rectangle.
 spec=importlib.util.spec_from_file_location('untouched_original',R/'original-2d-pipeline/publish_2d.py');orig=importlib.util.module_from_spec(spec);spec.loader.exec_module(orig)
 original_replay=[];candidate_math=[];oldcut=orig.cutout('bubble-panic',82)
 for clip in CLIPS:
  oldatlas=load(R/'original-atlases'/f'2d-{clip}-S.png')
  for i in range(12):
   x,y,w,h=RECTS[i];of=orig.generated_frame(catalog,{'id':clip},i);assert oldatlas.crop((x,y,x+w,y+h)).tobytes()==of.tobytes();original_replay.append({'clip':clip,'index':i,'pixelSHA256':psha(of)})
   # Swap only original publisher's cutout-return; generated_frame remains unchanged.
   orig.cutout=lambda ident,w:cutout.copy();expected=orig.generated_frame(catalog,{'id':clip},i);assert expected.tobytes()==frames[clip][i].tobytes();candidate_math.append({'clip':clip,'index':i,'pixelSHA256':psha(expected)});orig.cutout=lambda ident,w:oldcut.copy()
 assert load(R/'original.png').tobytes()==make_frame(oldcut,'idle',0).tobytes()
 write(C/'original-replay-proof.json',{'original36AtlasRectMatches':original_replay,'candidate36FramesEqualUnchangedOriginalGeneratedFrameWithOnlySourceReplacement':candidate_math,'registeredOriginalIdle0Match':True})
 manifest=copy.deepcopy(catalog);manifest['productionStage']='Existing native2D candidate; independent visual review pending';manifest['source']={'pipeline':'imagegen-2d','artwork':rel(S/'bubble-panic.png'),'sha256':sha(S/'bubble-panic.png'),'modelScript':rel(S/'publish.py')}
 for clip in manifest['clips']:clip['directions']={d:copy.deepcopy(entries[clip['id']])for d in DIRS}
 write(C/'manifest.json',manifest)
 # Complete registered contact sheets: one full 192x320 logical frame per slot.
 for clip in CLIPS:
  for bg,color in COLORS:
   full=Image.new('RGB',(1152,688),color);dr=ImageDraw.Draw(full)
   for i,im in enumerate(frames[clip]):
    x=i%6*192;y=i//6*344;full.paste(background(im.resize(LOGICAL,RS),color),(x,y+18));dr.text((x+6,y+3),f'{clip} {i:02} / {bg}',fill='white'if bg=='dark'else'black')
   preview(clip+'-full-registered-'+bg,full)
   nativefull=Image.new('RGB',(2304,1336),color);dr=ImageDraw.Draw(nativefull)
   for i,im in enumerate(frames[clip]):
    x=i%6*384;y=i//6*668;nativefull.paste(background(im,color),(x,y+24));dr.text((x+8,y+4),f'{clip} {i:02} / {bg} / full2xlogical',fill='white'if bg=='dark'else'black')
   preview(clip+'-full-registered-enlarged-'+bg,nativefull)
  # Three-background complete motion inspection from a fixed common window.
  sheet=Image.new('RGB',(2496,744),(222,218,208));dr=ImageDraw.Draw(sheet)
  for row,(bg,color)in enumerate(COLORS):
   for i,im in enumerate(frames[clip]):
    x=i*208;y=row*248;sample=im.crop(WINDOW);sheet.paste(background(sample,color),(x,y+25));dr.text((x+8,y+5),f'{clip}{i:02} {bg} 2xlogical',fill='black')
  preview(clip+'-all12-three-backgrounds',sheet)
 hero=frames['idle'][0]
 four=Image.new('RGB',(768,350),COLORS[0][1]);dr=ImageDraw.Draw(four)
 for j,d in enumerate(DIRS):four.paste(background(hero.resize(LOGICAL,RS),COLORS[0][1]),(j*192,25));dr.text((j*192+4,6),d+' camera-facing alias',fill='black')
 preview('four-view-sheet',four)
 # Uniform same registration comparison; fixedtarget adopts same declared recipe.
 comparison=Image.new('RGB',(1536,950),(222,218,208));dr=ImageDraw.Draw(comparison)
 items=[('Original',load(R/'original.png')),('Fixed target / candidate',hero),('Family heart',load(R/'approved-feedback-family-heart.png')),('Family smile',load(R/'approved-feedback-family-smile.png'))]
 for j,(label,im)in enumerate(items):
  x=j*384;dr.text((x+8,8),label,fill='black');comparison.paste(background(im.resize(LOGICAL,RS),COLORS[1][1]),(x+8,30));comparison.paste(background(im.crop(WINDOW).resize((312,324),RS),COLORS[0][1]),(x+8,380));comparison.paste(background(im.crop(WINDOW).resize((83,86),RS),COLORS[2][1]),(x+8,760));dr.text((x+8,735),'32px occupied width stress',fill='black')
 preview('original-target-candidate-family-registered-comparison',comparison)
 sizes=Image.new('RGB',(840,1220),(222,218,208));dr=ImageDraw.Draw(sizes)
 for row,(bg,color)in enumerate(COLORS):
  y=row*405;dr.text((8,y+5),bg+' / common source window / enlarged328, logical82, stress32',fill='black')
  for x,w in [(8,328),(500,82),(700,32)]:
   v=hero.crop(WINDOW);v=v.resize((round(v.width*w/164),round(v.height*w/164)),RS);sizes.paste(background(v,color),(x,y+35));dr.text((x,y+380),str(w)+'px occupied',fill='black')
 preview('three-backgrounds-enlarged-logical82-stress32',sizes)
 # Native isolated project: byte-exact current scripts; original methods inherited.
 context=json.loads((R/'context/manifest.json').read_text());N=C/'native-context'
 for name in ['restaurant_view.gd','art_book.gd','typography.gd']:(N/'scripts'/name).write_bytes((R/'context/runtime-scripts'/name).read_bytes())
 native=copy.deepcopy(context['objects'])
 for obj in native.values():
  for clip in obj['clips'].values():
   for e in clip['directions'].values():
    dest=N/'assets'/e['resource'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((R/e['resource']).read_bytes());e['image']='assets/'+e['resource'];e['_directory']='res://'
 nb={'frameSize':list(LOGICAL),'root':list(ROOT),'sourceScale':2,'clips':{}}
 for clip in manifest['clips']:
  c=copy.deepcopy(clip)
  for e in c['directions'].values():e['image']='assets/2d-'+c['id']+'-S.png';e['_directory']='res://'
  nb['clips'][c['id']]=c;(N/'assets'/('2d-'+c['id']+'-S.png')).write_bytes((C/'atlases'/('2d-'+c['id']+'-S.png')).read_bytes())
 native['bubble-panic']=nb;write(N/'objects.json',native)
 (N/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Panic native2D isolated renderer harness"\nrun/main_scene="res://capture.tscn"\n[display]\nwindow/size/viewport_width=1080\nwindow/size/viewport_height=760\nwindow/size/window_width_override=1080\nwindow/size/window_height_override=760\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\nenvironment/defaults/default_clear_color=Color(0.965,0.945,0.898,1)\n')
 (N/'capture.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://capture.gd" id="1"]\n[node name="NativeContextCapture" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n')
 (N/'capture.gd').write_bytes((S/'native_capture.gd').read_bytes())
 if (R/'native-capture/evidence.json').is_file():
  receipt=json.loads((R/'native-capture/evidence.json').read_text())
  for r in receipt['files']:
   src=R/'native-capture'/r['name'];assert sha(src)==r['sha256'];dest=C/'previews'/r['name'];dest.write_bytes(src.read_bytes());previews[r['key']]=rel(dest)
  write(C/'native-capture-evidence.json',receipt)
  preview('repeated',load(C/'previews/native-current-context.png'))
 recipe={'asset':'bubble-panic','representation':'existing-imagegen-2d','project':rel(S/'bubble-panic.png'),'publisher':rel(S/'publish.py'),'preparationRecipe':rel(S/'prepare_sources.py'),'capture':{'frame':list(FRAME),'logicalFrame':list(LOGICAL),'logicalRoot':list(ROOT),'sourceScale':2,'cellSize':128,'fps':12,'columns':6,'rows':2,'atlasSize':[2304,1280]},'crop':crop,'normalizedPhysical':list(cutout.size),'animation':{'phase':'index/12*tau','center':'[96,248-52-3*sin(phase)]','appearScale':'.5+.5*sin((index+1)/12*pi/2)','appearOpacity':'(index+1)/12','fadeOpacity':'1-index/12','idle':'full size and opacity; 12frames repeating 6poses; loop true','rounding':'Original Python round; Pillow LANCZOS'},'aliases':'S,N,E,W equal original S atlas/rects; current native ArtBook requested-facing else S fallback unchanged.','context':{'harness':rel(N/'project.godot'),'methods':['sprite','_customer_at','_feedback_at','customer_pose_offset','customer_feedback','ArtBook.frame_data','ArtBook.registered_rect'],'currentAttachment':[0,-172],'poseOffsetCell':[.06,-.02],'phase':'walking and leaving, navigation_mode=wander, walk customer','runtime':'4seconds: appear<1s then idle(seconds=wander_elapsed-1); reduced_motion idle frame0; timer=-1, no timer ring or runtime fade','legacy':'Separate -90logical catalog seated-wait/stool example, never used to adjust candidate registration'},'prohibitedOperationsApplied':[]}
 write(S/'recipe.json',recipe)
 validation={'asset':'bubble-panic','round':'round01','representation':'Existing raster + deterministic native2D; no Blender claim','registration':recipe['capture'],'coverage':{'logicalSlots':len(records),'actualSFrames':36,'atlasEntries':len(atlases),'actualSAtlases':3,'directionAliases':DIRS,'clips':3},'sourceOperations':{'crop':crop,'cropRGBAEqualsRawRectangle':True,'uniformPhysicalSize':list(cutout.size),'noPaintEraseWarpRegradeOrPerFrameFit':True},'allFramesAlpha':alpha,'alphaSupportAudit':{'path':rel(S/'crop.json'),'summary':'Raw target retained; original alpha>8 bounds-only rectangle; all inside RGBA unchanged.'},'playbackInspection':rel(S/'playback-inspection.json'),'originalPublisherReplay':{'original36AtlasRectRGBAEqual':True,'candidate36FramesRGBAEqualUnchangedOriginalGeneratedFrameWithOnlySourceReplacement':True,'originalRegisteredIdle0RGBAEqual':True,'proof':rel(C/'original-replay-proof.json')},'contract':{'clips':[{k:c[k]for k in ['id','frames','fps','loop','static','frameOrder']}for c in manifest['clips']],'allAliasMetadataIdentical':True,'allAtlasRectRGBAEqual':True,'allBorderAlphaZero':True,'minimumUniqueFrames':6},'context':recipe['context'],'environment':{'python':sys.version.split()[0],'pillow':PIL.__version__},'technicalAmbiguity':'All raw target bytes retained. Crop omits measured faint-alpha pixels outside declared original threshold rectangle; do not read raw-alpha preservation as an unqualified packed-cutout claim.'}
 write(C/'validation.json',validation)
 # Browser uses exact raw frames at12fps, once/loop flags; manual restart explicit.
 html="""<!doctype html><meta charset="utf-8"><title>Panic native2D round01</title><style>body{font:15px system-ui;background:#f6f1e5;color:#253b3b;max-width:1440px;margin:24px auto;padding:0 20px}img{max-width:100%;height:auto}section{margin:24px 0}button,select{font:inherit;padding:8px}.motion{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}canvas{background:#7c7d81}#motion{width:192px;height:320px}#large{width:384px;height:640px}#phone{width:75px;height:125px}#runtime{width:810px}a{color:#155e58}</style><h1>Panic balloon / existing native2D round01</h1><p>Frozen target, original alpha-bounds crop, uniform82logical width, original12fps motion. Four facings alias S. Current-method Godot harness below is an isolated fixture renderer, not a game simulation. Legacy -90 context is separate.</p><section><label>12fps clip <select id="clip"><option>appear</option><option>idle</option><option>fade</option></select></label> <button id="restart">Restart once</button> <button id="repeat">Repeat with1s endpoint hold</button> <label>Background <select id="bg"><option value="#7c7d81">gray</option><option value="#f6f1e5">light</option><option value="#1d2026">dark</option></select></label><p id="status"></p><div class="motion"><div>Logical full frame /82px art<br><canvas id="motion" width="384" height="640"></canvas></div><div>Enlarged full frame /164px art<br><canvas id="large" width="384" height="640"></canvas></div><div>Phone stress /32px art<br><canvas id="phone" width="384" height="640"></canvas></div></div><p>Appear/fade play once then hold frame11. Idle loops. Repeat inserts1s endpoint hold; that hold is review UI only. Appear starts1/12alpha, fade ends1/12alpha. Idle repeats6rounded bob poses across12samples.</p></section>"""
 if 'native-runtime-wander-playback'in previews:html+='<section><h2>Actual Godot walking+leaving wander /4seconds /12fps /nonzero pose</h2><img id="runtime" src="native-runtime-wander-playback.png"></section>'
 for key in ['original-target-candidate-family-registered-comparison','three-backgrounds-enlarged-logical82-stress32','native-current-context','native-current-context-posed','native-reduced-motion','legacy-catalog-90']+[clip+'-all12-three-backgrounds'for clip in CLIPS]+[clip+'-full-registered-'+bg for clip in CLIPS for bg,color in COLORS]+[clip+'-full-registered-enlarged-'+bg for clip in CLIPS for bg,color in COLORS]:
  if key in previews:html+='<section><h2>'+key+'</h2><img loading="lazy" src="'+Path(previews[key]).name+'" alt="'+key+'"></section>'
 html+="""<script>const sel=document.querySelector('#clip'),canvases=[...document.querySelectorAll('canvas')],status=document.querySelector('#status');let frames={},start=0,last=-1,clip='appear',repeat=false;Promise.all(['appear','idle','fade'].map(async c=>{frames[c]=await Promise.all(Array.from({length:12},(_,i)=>new Promise(r=>{let im=new Image;im.onload=()=>r(im);im.src='../raw/'+c+'-S-'+String(i).padStart(4,'0')+'.png'})))})).then(()=>{start=performance.now();requestAnimationFrame(tick)});function tick(now){let age=(now-start)/1000,i=Math.floor(age*12+1e-7);if(clip==='idle')i%=12;else i=repeat?Math.min(i%24,11):Math.min(i,11);if(i!==last){for(let canvas of canvases){let ctx=canvas.getContext('2d');ctx.clearRect(0,0,384,640);ctx.drawImage(frames[clip][i],0,0)}last=i;}status.textContent=clip+' / frame '+String(i).padStart(2,'0')+' / elapsed '+age.toFixed(3)+'s /12fps /'+(clip==='idle'?'loop':repeat?'repeat with endpoint hold':'once; holds11');requestAnimationFrame(tick)}function restart(){clip=sel.value;start=performance.now();last=-1}sel.onchange=restart;document.querySelector('#restart').onclick=()=>{repeat=false;restart()};document.querySelector('#repeat').onclick=()=>{repeat=true;restart()};document.querySelector('#bg').onchange=e=>canvases.forEach(c=>c.style.background=e.target.value);</script>"""
 p=C/'previews/index.html';p.write_text(html);previews['review-page']=rel(p)
 resources=[rel(p)for p in sorted(S.rglob('*'))if p.is_file()and'__pycache__'not in p.parts and not p.name.endswith('.pyc')]
 resources+=[rel(p)for p in sorted(N.rglob('*'))if p.is_file()and'.godot'not in p.relative_to(N).parts and not p.name.endswith(('.import','.uid'))]
 resources+=[rel(C/'original-replay-proof.json'),rel(O/'source/initial-observations.json')]
 if(C/'native-capture-evidence.json').is_file():resources.append(rel(C/'native-capture-evidence.json'))
 delivery={'asset':'bubble-panic','round':'round01','pipeline':'existing-imagegen-2d','representation':'Actual editable raster + deterministic native2D publisher','project':rel(S/'bubble-panic.png'),'recipeScript':rel(S/'publish.py'),'recipe':rel(S/'recipe.json'),'recipeManifest':rel(S/'recipe.json'),'captureRecipe':rel(S/'publish.py'),'packagingRecipe':rel(S/'publish.py'),'preparationRecipe':rel(S/'prepare_sources.py'),'verificationRecipe':rel(S/'verify.py'),'nativeCaptureRecipe':rel(S/'capture_native.py'),'provenance':rel(S/'provenance.json'),'reproductionEvidence':rel(C/'reproduction.json'),'validation':rel(C/'validation.json'),'manifest':rel(C/'manifest.json'),'heroes':{d:rel(C/'raw/idle-S-0000.png')for d in DIRS},'rawFrames':records,'atlases':atlases,'previews':previews,'resources':sorted(set(resources)),'source':{'pipeline':'imagegen-2d','artwork':rel(S/'bubble-panic.png'),'sha256':sha(S/'bubble-panic.png'),'rawArtwork':rel(R/'target.png'),'rawSHA256':sha(R/'target.png'),'originalSource':rel(R/'original-source/bubble-panic.png'),'modelScript':rel(S/'publish.py'),'canonicalCrop':crop},'notes':'No editor rating or approval.36actual capture files/3atlases/144alias slots. Raw target/source/provenance retained; declared faint-alpha crop omission measured, no Python artwork edits. Current native Godot use and legacy catalog context separate.'}
 write(C/'delivery.json',delivery);write(O/'delivery.json',delivery)
 print(json.dumps({'asset':'bubble-panic','frames':36,'slots':len(records),'atlasFiles':3,'previews':len(previews),'normalizedSize':list(cutout.size),'nativeEvidence':(R/'native-capture/evidence.json').is_file()},indent=2))
if __name__=='__main__':main()
