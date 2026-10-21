"""Closed, deterministic existing2D preference publisher. No artistic image edits.
One prepared blank PNG and three full approved food PNGs, original animation math.
"""
from pathlib import Path
import copy,hashlib,importlib.util,io,json,math,struct,sys,zlib
import PIL
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;O=S.parents[1];R=S/'resources';C=O/'candidates/round01'
FRAME=(384,640);LOGICAL=(192,320);ROOT=(96,248);DIRS=['S','N','E','W'];RS=Image.Resampling.LANCZOS
RECTS=[[i%6*384,i//6*640,384,640]for i in range(12)];WINDOW=(88,290,296,490)
COLORS=[('light',(246,241,229)),('gray',(124,125,129)),('dark',(29,32,38))]
for sub in ['raw','atlases','previews','native-context']:(C/sub).mkdir(parents=True,exist_ok=True)
def rel(p):return p.relative_to(O).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psha(im):return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def width(im,w):return im.resize((round(w),round(im.height/im.width*w)),RS)
def center(c,im,xy):c.alpha_composite(im,(round(xy[0]-im.width/2),round(xy[1]-im.height/2)))
def bg(im,color):out=Image.new('RGBA',im.size,color+(255,));out.alpha_composite(im);return out.convert('RGB')
def components(im,threshold):
 a=im.getchannel('A');w,h=a.size;data=a.tobytes();seen=set();out=[]
 for start,v in enumerate(data):
  if v<=threshold or start in seen:continue
  q=[start];seen.add(start);n=0;b=[w,h,0,0];ma=0
  while q:
   j=q.pop();x=j%w;y=j//w;n+=1;b=[min(b[0],x),min(b[1],y),max(b[2],x+1),max(b[3],y+1)];ma=max(ma,data[j])
   for dy in [-1,0,1]:
    for dx in [-1,0,1]:
     xx=x+dx;yy=y+dy;k=yy*w+xx
     if 0<=xx<w and 0<=yy<h and k not in seen and data[k]>threshold:seen.add(k);q.append(k)
  out.append({'pixels':n,'bounds':b,'maxAlpha':ma})
 return sorted(out,key=lambda v:-v['pixels'])
def state(clip,index):
 phase=index/12*math.tau;scale=1.;alpha=1.
 if 'appear'in clip:scale=.5+.5*math.sin((index+1)/12*math.pi/2);alpha=(index+1)/12
 elif 'fade'in clip:alpha=1-index/12
 return scale,alpha,[ROOT[0],ROOT[1]-52-3*math.sin(phase)]
def paste(c,im,xy,alpha):
 if alpha<1:im=im.copy();im.putalpha(im.getchannel('A').point(lambda v:round(v*max(0,alpha))))
 center(c,im,[xy[0]*2,xy[1]*2])
def make_frame(balloon,food,clip,index):
 scale,alpha,xy=state(clip,index);b=balloon.copy();f=food.copy()
 if 'appear'in clip:
  b=b.resize((round(b.width*scale),round(b.height*scale)),RS);f=f.resize((round(f.width*scale),round(f.height*scale)),RS)
 c=Image.new('RGBA',FRAME);paste(c,b,xy,alpha);paste(c,f,[xy[0],xy[1]-5],alpha);return c
prov=json.loads((S/'provenance.json').read_text());catalog=json.loads((R/'original-catalog-object.json').read_text());clips=[c['id']for c in catalog['clips']]
raw=load(R/'fixed-target-raw.png');box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();art=load(S/'bubble-preference.png')
assert list(box)==prov['crop']['box']and art.tobytes()==raw.crop(box).tobytes();assert sha(S/'bubble-preference.png')==prov['crop']['canonicalSHA256']
balloon=width(art,164);foodarts={};foods={}
for ident,r in prov['foods'].items():
 p=O/r['path'];assert sha(p)==r['sha256'];im=load(p);assert list(im.size)==r['size']and psha(im)==r['pixelSHA256'];foodarts[ident]=im;foods[ident]=width(im,80)
def recipe_for(clip):return'dish-cucumber'if clip.startswith('cucumber')else'dish-eel'if clip.startswith('eel')else'dish-salmon'
spec=importlib.util.spec_from_file_location('original_publisher',R/'original-2d-pipeline/publish_2d.py');orig=importlib.util.module_from_spec(spec);spec.loader.exec_module(orig)
frames={};raw_records=[];atlas_records=[];entries={};alpha_audit={};old_replay=[];candidate_formula=[];animation=[]
for clip in clips:
 food=foods[recipe_for(clip)];seq=[make_frame(balloon,food,clip,i)for i in range(12)];frames[clip]=seq;atlas=Image.new('RGBA',(2304,1280));hashes=[]
 for i,im in enumerate(seq):
  path=C/'raw'/f'{clip}-S-{i:04d}.png';im.save(path,compress_level=9);hashes.append(psha(im));atlas.alpha_composite(im,(RECTS[i][0],RECTS[i][1]))
  for d in DIRS:raw_records.append({'clip':clip,'direction':d,'facing':d,'index':i,'frame':i,'path':rel(path),'size':list(FRAME),'sha256':sha(path),'pixelSHA256':psha(im),'aliasOf':clip+':S:'+str(i)if d!='S'else None})
  sc,al,xy=state(clip,i);animation.append({'clip':clip,'index':i,'scale':sc,'opacity':al,'balloonCenterLogical':xy,'foodCenterLogical':[xy[0],xy[1]-5],'balloonPhysicalSize':[round(balloon.width*sc),round(balloon.height*sc)]if'appear'in clip else list(balloon.size),'foodPhysicalSize':[round(food.width*sc),round(food.height*sc)]if'appear'in clip else list(food.size)})
 ap=C/'atlases'/f'2d-{clip}-S.png';atlas.save(ap,compress_level=9)
 entry={'image':f'sprites/bubble-preference/2d-{clip}-S.png','columns':6,'rows':2,'atlasSize':[2304,1280],'rects':RECTS,'uniqueFrames':len(set(hashes)),'sha256':sha(ap)};entries[clip]=entry
 for d in DIRS:atlas_records.append({'clip':clip,'direction':d,'facing':d,'path':rel(ap),'size':[2304,1280],'atlasSize':[2304,1280],'columns':6,'rows':2,'rects':RECTS,'frames':12,'uniqueFrames':len(set(hashes)),'sha256':sha(ap),'aliasOf':clip+':S'if d!='S'else None})
 oldatlas=load(R/'original-atlases'/f'2d-{clip}-S.png')
 for i in range(12):
  x,y,w,h=RECTS[i];assert atlas.crop((x,y,x+w,y+h)).tobytes()==seq[i].tobytes()
  old=orig.generated_frame(catalog,{'id':clip},i);actual=oldatlas.crop((x,y,x+w,y+h));assert actual.tobytes()==old.tobytes(),('original replay',clip,i)
  old_replay.append({'clip':clip,'index':i,'pixelSHA256':psha(old),'originalAtlasRectRGBAEqual':True})
 old_cutout=orig.cutout
 orig.cutout=lambda ident,w:width(art if ident=='bubble-preference'else foodarts[ident],w*2)
 for i in range(12):assert orig.generated_frame(catalog,{'id':clip},i).tobytes()==seq[i].tobytes();candidate_formula.append({'clip':clip,'index':i,'originalGeneratedFrameWithCanonicalSourcesRGBAEqual':True})
 orig.cutout=old_cutout
 a=[im.getchannel('A')for im in seq];border=max(max(v.crop(b).getextrema()[1]for b in [(0,0,384,1),(0,639,384,640),(0,0,1,640),(383,0,384,640)])for v in a);assert border==0
 alpha_audit[clip]={'boundsAlpha0':[v.getbbox()for v in a],'boundsAlpha8':[v.point(lambda a:255 if a>8 else 0).getbbox()for v in a],'borderAlphaMax':border,'distinctPixelBuffers':len(set(hashes)),'nonzeroPixelsRange':[min(sum(v.histogram()[1:])for v in a),max(sum(v.histogram()[1:])for v in a)],'alpha1to8PixelsRange':[min(sum(v.histogram()[1:9])for v in a),max(sum(v.histogram()[1:9])for v in a)]}
manifest=copy.deepcopy(catalog);manifest['source']={'pipeline':'imagegen-2d','artwork':rel(S/'bubble-preference.png'),'sha256':sha(S/'bubble-preference.png'),'modelScript':rel(S/'publish.py'),'recipe':rel(S/'recipe.json')}
for c in manifest['clips']:c['directions']={d:copy.deepcopy(entries[c['id']])for d in c['directions']}
write(C/'manifest.json',manifest);write(C/'animation-proof.json',animation);write(C/'original-replay-proof.json',old_replay)
previews={}
def preview(key,im):p=C/'previews'/f'{key}.png';im.save(p,compress_level=9);previews[key]=rel(p)
def apng(path,seq):
 # Preserve fullRGBA frames, including repeated bob poses, at exact rational12fps.
 def chunk(k,d):return struct.pack('>I',len(d))+k+d+struct.pack('>I',zlib.crc32(k+d)&0xffffffff)
 blobs=[];header=None
 for im in seq:
  stream=io.BytesIO();im.convert('RGBA').save(stream,format='PNG',compress_level=9);data=stream.getvalue();pos=8;ids=[]
  while pos<len(data):
   n=struct.unpack('>I',data[pos:pos+4])[0];k=data[pos+4:pos+8];p=data[pos+8:pos+8+n];pos+=n+12
   if k==b'IHDR':header=p
   elif k==b'IDAT':ids.append(p)
  blobs.append(b''.join(ids))
 out=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'acTL',struct.pack('>II',len(seq),0));counter=0
 for i,blob in enumerate(blobs):
  out+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',counter,seq[i].width,seq[i].height,0,0,1,12,0,0));counter+=1
  if i==0:out+=chunk(b'IDAT',blob)
  else:out+=chunk(b'fdAT',struct.pack('>I',counter)+blob);counter+=1
 out+=chunk(b'IEND',b'');path.write_bytes(out)
def playback(key,seq):p=C/'previews'/f'{key}.png';apng(p,seq);previews[key]=rel(p)
for clip in clips:
 playback(clip+'-S',frames[clip])
 for d in DIRS[1:]:previews[clip+'-'+d]=previews[clip+'-S']
 # Separate6x2 enlarged contact sheet for each state: every actual frame visible.
 sheet=Image.new('RGB',(1392,464),COLORS[0][1]);draw=ImageDraw.Draw(sheet)
 for i,im in enumerate(frames[clip]):
  x=i%6*232;y=i//6*232;sheet.paste(bg(im.crop(WINDOW),COLORS[(i//6)%3][1]),(x+8,y+24));draw.text((x+8,y+6),clip+' / '+str(i),fill='black')
 preview(clip+'-all12-enlarged',sheet)
for kind,prefix in [('salmon',''),('cucumber','cucumber-'),('eel','eel-')]:
 sheet=Image.new('RGB',(1440,426),COLORS[0][1]);draw=ImageDraw.Draw(sheet)
 for row,state_name in enumerate(['appear','idle','fade']):
  cid=prefix+state_name;draw.text((8,row*142+3),cid+' / all12 frames at logical scale',fill='black')
  for i,im in enumerate(frames[cid]):
   sample=im.crop(WINDOW).resize((104,100),RS);sheet.paste(bg(sample,COLORS[row][1]),(i*120+8,row*142+22));draw.text((i*120+8,row*142+126),str(i),fill='black')
 preview(kind+'-all36-logical',sheet);playback(kind+'-recipe-appear-idle-fade',frames[prefix+'appear']+frames[prefix+'idle']*2+frames[prefix+'fade'])
hero=frames['idle'][0];four=Image.new('RGB',(768,350),COLORS[0][1]);draw=ImageDraw.Draw(four)
for col,d in enumerate(DIRS):four.paste(bg(hero.resize(LOGICAL,RS),COLORS[0][1]),(col*192,30));draw.text((col*192+4,8),d+' camera-facing alias',fill='black')
preview('four-view-sheet',four)
# Fixed common inspection window; no view or pose fitting.
empty=Image.new('RGBA',FRAME);paste(empty,balloon,[96,196],1)
recipes=Image.new('RGB',(960,240),COLORS[0][1]);draw=ImageDraw.Draw(recipes)
for col,(label,im)in enumerate([('Empty / 82 logical',empty),('Salmon / 40 logical food',hero),('Cucumber / 40 logical food',frames['cucumber-idle'][0]),('Eel / 40 logical food / catalog',frames['eel-idle'][0])]):recipes.paste(bg(im.crop(WINDOW),COLORS[0][1]),(col*240+8,30));draw.text((col*240+8,8),label,fill='black')
preview('empty-and-three-recipes',recipes)
size_sheet=Image.new('RGB',(1200,1380),COLORS[0][1]);draw=ImageDraw.Draw(size_sheet)
for row,(label,color)in enumerate(COLORS):
 for col,(kind,cid)in enumerate([('salmon','idle'),('cucumber','cucumber-idle'),('eel','eel-idle')]):
  x=col*400;y=row*460;draw.text((x+8,y+6),kind+' / '+label,fill='black');cut=frames[cid][0].crop((100,320,284,460))
  for xx,yy,w,caption in [(8,28,328,'4x logical'),(8,340,82,'logical82'),(128,340,32,'balloon32'),(220,340,20.5,'cell32 / balloon20.5')]:
   sample=cut.resize((round(cut.width*w/164),round(cut.height*w/164)),RS);size_sheet.paste(bg(sample,color),(x+xx,y+yy));draw.text((x+xx,y+yy+sample.height+3),caption,fill='black')
preview('light-gray-dark-logical-game32-enlarged',size_sheet)
source_sheet=Image.new('RGB',(1260,360),COLORS[0][1]);draw=ImageDraw.Draw(source_sheet)
for col,(label,color)in enumerate(COLORS):
 tile=Image.new('RGBA',(420,320),color+(255,));center(tile,width(art,400),(210,160));source_sheet.paste(tile.convert('RGB'),(col*420,24));draw.text((col*420+8,6),'Unmodified canonical crop / '+label,fill='black')
preview('canonical-source-backgrounds',source_sheet)
compare=Image.new('RGB',(1120,530),COLORS[0][1]);draw=ImageDraw.Draw(compare)
for col,(label,im)in enumerate([('Original registered salmon',load(R/'original-registered.png')),('Candidate registered salmon',hero),('Fixed blank target / registered',empty),('Candidate cucumber',frames['cucumber-idle'][0]),('Candidate eel / catalog',frames['eel-idle'][0])]):
 x=col%3*370;y=col//3*265;compare.paste(bg(im.crop(WINDOW),COLORS[1][1]),(x+8,y+25));compare.paste(bg(im.crop(WINDOW).resize((104,100),RS),COLORS[2][1]),(x+240,y+80));draw.text((x+8,y+7),label,fill='black')
preview('original-fixed-target-candidate-comparison',compare)
# Native code-equivalent assemblies use full fixed frames and actual copied metadata.
context=json.loads((R/'context/manifest.json').read_text())
def context_frame(ident,cid,index=0):
 o=context['objects'][ident];c=o['clips'][cid];e=c['directions']['S'];r=e['rects'][index%len(e['rects'])];return load(R/e['resource']).crop((r[0],r[1],r[0]+r[2],r[1]+r[3]))
def place(scene,im,obj,base,pitch):
 k=pitch/128;ratio=k/obj['sourceScale'];target=im.resize((round(im.width*ratio),round(im.height*ratio)),RS);scene.alpha_composite(target,(round(base[0]-obj['root'][0]*k),round(base[1]-obj['root'][1]*k)))
def assembly(cid='idle',index=0,pitch=128,timer=.6,historical=False,pose=(0,0)):
 k=pitch/128;scene=Image.new('RGBA',(round(384*k),round(560*k)),COLORS[0][1]+(255,));base=[192*k,480*k];posed=[base[0]+pose[0]*pitch,base[1]+pose[1]*pitch];attachment=-90 if historical else -172
 place(scene,context_frame('stool-wood','static'),context['objects']['stool-wood'],base,pitch)
 place(scene,context_frame('customer-rosa','seated-wait-empty',index),context['objects']['customer-rosa'],posed,pitch)
 bb=[posed[0],posed[1]+attachment*k];place(scene,frames[cid][index],{'root':ROOT,'sourceScale':2},bb,pitch)
 if timer>=0:
  # Separate overlay; Godot capture below supplies actual native draw_circle/draw_arc.
  d=ImageDraw.Draw(scene);cx=bb[0]+37*k;cy=bb[1]-84*k;radius=pitch*.115;stroke=max(1.4,pitch*.032)
  d.ellipse((cx-radius-stroke,cy-radius-stroke,cx+radius+stroke,cy+radius+stroke),fill='#fff5dc');d.arc((cx-radius,cy-radius,cx+radius,cy+radius),0,360,fill='#c5ccbc',width=max(1,round(stroke)));d.arc((cx-radius,cy-radius,cx+radius,cy+radius),-90,-90+360*timer,fill='#3c8d7b'if timer>.25 else'#bf8147',width=max(1,round(stroke)))
 return scene
contexts=Image.new('RGB',(1200,1400),COLORS[0][1]);draw=ImageDraw.Draw(contexts)
for col,(kind,cid)in enumerate([('salmon','idle'),('cucumber','cucumber-idle'),('eel catalog only','eel-idle')]):
 x=col*400;contexts.paste(assembly(cid,pitch=100,timer=-1 if cid.startswith('eel')else .6).convert('RGB'),(x+8,38));draw.text((x+8,8),kind+' / code-equivalent -172',fill='black');small=assembly(cid,pitch=50,timer=-1 if cid.startswith('eel')else .6);contexts.paste(small.convert('RGB'),(x+8,520));draw.text((x+8,500),'50px cell / balloon~32px / timer separate',fill='black');contexts.paste(assembly(cid,pitch=128,pose=(.06,-.02),timer=-1 if cid.startswith('eel')else .6).convert('RGB'),(x+8,790));draw.text((x+8,770),'pose offset(.06,-.02) cell / current attachment',fill='black')
preview('current-customer-code-equivalent-context',contexts)
preview('current-salmon-full-logical-context',assembly('idle'));preview('current-cucumber-full-logical-context',assembly('cucumber-idle'))
preview('historical-catalog-minus90-context',assembly('idle',historical=True,timer=-1))
repeat=Image.new('RGBA',(1152,560),COLORS[0][1]+(255,))
for i,cid in enumerate(['idle','cucumber-idle','eel-idle']):repeat.alpha_composite(assembly(cid,timer=.6 if i<2 else -1),(i*384,0))
preview('repeated',repeat)
# Runtime samples: appearance, looping idle, and expiration fade. Timers remain separate.
for kind,prefix in [('salmon',''),('cucumber','cucumber-')]:
 seq=[]
 for tick in range(60):
  t=tick/12;cid=prefix+('appear'if t<1 else'fade'if t>=4 else'idle');age=t if t<1 else t-4 if t>=4 else t-1;index=min(11,max(0,math.floor(age*12+1e-7)))if not cid.endswith('idle')else math.floor(age*12+1e-7)%12
  seq.append(assembly(cid,index,pitch=80,timer=max(0,1-t/4)if t<4 else -1))
 playback(kind+'-current-context-playback',seq)
# Build an isolated native capture project; original runtime methods are inherited unchanged.
# This is a harness, not a production-game screenshot or a native3D scene.
N=C/'native-context';(N/'scripts').mkdir(exist_ok=True)
for name in ['restaurant_view.gd','art_book.gd','typography.gd']:(N/'scripts'/name).write_bytes((R/'context/original-runtime-scripts'/name).read_bytes())
native_objects=copy.deepcopy(context['objects'])
for obj in native_objects.values():
 for clip in obj['clips'].values():
  for e in clip['directions'].values():
   q=N/'assets'/e['resource'];q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((R/e['resource']).read_bytes());e['image']='assets/'+e['resource'];e['_directory']='res://'
nb={'frameSize':list(LOGICAL),'root':list(ROOT),'sourceScale':2,'clips':{}}
for c in manifest['clips']:
 c=copy.deepcopy(c)
 for e in c['directions'].values():e['image']='assets/2d-'+c['id']+'-S.png';e['_directory']='res://'
 nb['clips'][c['id']]=c;(N/'assets'/('2d-'+c['id']+'-S.png')).write_bytes((C/'atlases'/('2d-'+c['id']+'-S.png')).read_bytes())
native_objects['bubble-preference']=nb;write(N/'objects.json',native_objects)
(N/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Preference native context harness"\nrun/main_scene="res://capture.tscn"\n[display]\nwindow/size/viewport_width=1080\nwindow/size/viewport_height=760\nwindow/size/window_width_override=1080\nwindow/size/window_height_override=760\n[rendering]\nrenderer/rendering_method="gl_compatibility"\ntextures/default_filters/use_nearest_mipmap_filter=false\nenvironment/defaults/default_clear_color=Color(0.965,0.945,0.898,1)\n')
(N/'capture.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://capture.gd" id="1"]\n[node name="NativeContextCapture" type="Control"]\nlayout_mode=3\nanchors_preset=15\nanchor_right=1.0\nanchor_bottom=1.0\ngrow_horizontal=2\ngrow_vertical=2\nscript=ExtResource("1")\n')
# Native harness source is static retained alongside publisher, copied exactly.
(N/'capture.gd').write_bytes((S/'native_capture.gd').read_bytes())
recipe={'asset':'bubble-preference','project':rel(S/'bubble-preference.png'),'publisher':rel(S/'publish.py'),'preparationRecipe':rel(S/'prepare_sources.py'),'capture':{'frame':list(FRAME),'logicalFrame':list(LOGICAL),'logicalRoot':list(ROOT),'sourceScale':2,'cellSize':128,'fps':12,'columns':6,'rows':2,'atlasSize':[2304,1280]},'crop':prov['crop'],'food':prov['foods'],'normalization':{'blankPhysical':list(balloon.size),'blankLogicalWidth':82,'foodPhysical':{k:list(v.size)for k,v in foods.items()},'foodLogicalWidth':40,'foodCropCount':0,'resampling':'PillowLANCZOS; uniform aspect; original Pythonround'},'animation':{'phase':'index/12*tau','center':'[96,248-52-3*sin(phase)]','foodCenter':'[centerX,centerY-5]','appearScale':'.5+.5*sin((index+1)/12*pi/2)','appearAlpha':'(index+1)/12','fadeAlpha':'1-index/12','idleAlpha':1,'jointScaleAndAlpha':True},'aliases':'S,N,E,W all share original S atlas/rects; native ArtBook direction_data falls back to S. No separate artwork or runtime extra variant.','context':{'actualNativeHarness':rel(N/'project.godot'),'originalMethodsCalled':['sprite','_customer_at','_feedback_at','customer_pose_offset','customer_feedback','ArtBook.frame_data','ArtBook.registered_rect'],'currentAttachment':[0,-172],'historicalAttachment':[0,-90],'timer':'Separate current native draw_circle/draw_arc; code-equivalent Pillow assembly separately labeled.','eel':'Preserved catalog clips; not selected by current customer_feedback.','postgenerationFamilyContext':'Approved heart/smile finish images were added after ImageGen call, never claimed as generation inputs.'},'playback':'Nine clip APNGs have12 fullRGBA frames at exact1/12s. Recipe APNGs show appear+two idle cycles+fade. Inspection replays loop; original clip loop flags unchanged.','prohibitedOperationsApplied':[]}
write(S/'recipe.json',recipe)
validation={'asset':'bubble-preference','round':'round01','representation':'Actual existing raster source + deterministic native2D publisher; no Blender/camera/3D claim','registration':recipe['capture'],'coverage':{'logicalSlots':len(raw_records),'physicalSFrames':len({r['path']for r in raw_records}),'atlasEntries':len(atlas_records),'physicalSAtlases':len({r['path']for r in atlas_records}),'clips':len(clips),'facings':DIRS,'independentFacingArtwork':False,'idleMayRepeatPixels':True},'sourceOperations':{'soleCrop':prov['crop'],'cropRGBAEqualRawRectangle':art.tobytes()==raw.crop(box).tobytes(),'retainedAlphaNotThresholded':True,'uniformBlankPhysical':list(balloon.size),'foodsFullBoundsNoSecondCrop':{k:{'size':list(v.size),'sha256':prov['foods'][k]['sha256'],'normalizedPhysical':list(foods[k].size)}for k,v in foodarts.items()},'noPaintEraseWarpRegradeOrPoseFit':True},'alpha':{'canonicalAlpha0Components':components(art,0),'canonicalAlpha8Components':components(art,8),'normalizedAlpha0Components':components(balloon,0),'normalizedAlpha8Components':components(balloon,8),'allFrames':alpha_audit},'originalPublisherReplay':{'original108AtlasRectRGBAEqual':len(old_replay)==108,'registeredOriginalIdle0RGBAEqual':orig.generated_frame(catalog,{'id':'idle'},0).tobytes()==load(R/'original-registered.png').tobytes(),'candidate108FramesRGBAEqualOriginalMathWithCanonicalSourceReplacement':len(candidate_formula)==108,'proof':rel(C/'original-replay-proof.json')},'contract':{'clips':[{k:c[k]for k in ['id','frames','fps','loop','static','frameOrder']if k in c}for c in manifest['clips']],'aliasesHaveIdenticalSMetadata':all(len({json.dumps(e,sort_keys=True)for e in c['directions'].values()})==1 for c in manifest['clips']),'all108AtlasRectsEqualFrames':True,'allFramesBorderAlphaZero':True,'fallback':'Copied current ArtBook.direction_data returns requested facing elseS; no new fallback policy.'},'context':recipe['context'],'environment':{'python':sys.version.split()[0],'pillow':PIL.__version__},'independentJudgeApproval':False}
write(C/'validation.json',validation)
# Retained actual native capture evidence, if already captured, is source-closed.
if (R/'native-capture/evidence.json').is_file():
 receipt=json.loads((R/'native-capture/evidence.json').read_text())
 for r in receipt['files']:
  src=R/'native-capture'/r['name'];assert sha(src)==r['sha256'];dest=C/'previews'/r['name'];dest.write_bytes(src.read_bytes());previews[r['key']]=rel(dest)
 write(C/'native-capture-evidence.json',receipt)
# Portable review page: all clips, compact36frame sheets, alpha/context evidence.
html='''<!doctype html><meta charset="utf-8"><title>Preference balloon round01</title><style>body{font:15px system-ui;background:#f6f1e5;color:#253b3b;max-width:1440px;margin:24px auto;padding:0 20px}img{max-width:100%;height:auto}section{margin:24px 0}button,select{font:inherit;padding:8px}#motion{width:192px;height:320px;background:#7c7d81}a{color:#155e58}</style><h1>Preference balloon — existing native2D round01</h1><p>Fixed blank target, exact separately approved full food RGBA, original animation and fixed canvas. Four facings alias S. Eel is preserved catalog coverage. Native harness evidence calls original runtime methods; Pillow code-equivalent assemblies are explicitly labeled.</p><section><label>12fps clip <select id="clip">'''
for cid in clips:html+='<option>'+cid+'</option>'
html+='''</select></label><button id="restart">Restart</button><div><img id="motion" alt="12fps full registered animation"></div></section>'''
for key in ['empty-and-three-recipes','light-gray-dark-logical-game32-enlarged','original-fixed-target-candidate-comparison','salmon-all36-logical','cucumber-all36-logical','eel-all36-logical','current-customer-code-equivalent-context','native-current-context','native-current-context-posed']:
 if key in previews:html+='<section><h2>'+key+'</h2><img loading="lazy" src="'+Path(previews[key]).name+'" alt="'+key+'"></section>'
html+='''<script>const s=document.querySelector('#clip'),im=document.querySelector('#motion');function play(){im.src=s.value+'-S.png?restart='+Date.now()}s.onchange=play;document.querySelector('#restart').onclick=play;play();</script>'''
p=C/'previews/index.html';p.write_text(html);previews['review-page']=rel(p)
resource_paths=[r['path']for r in prov['resources']]+[rel(p)for p in [S/'bubble-preference.png',S/'provenance.json',S/'prepare_sources.py',S/'publish.py',S/'verify.py',S/'native_capture.gd',S/'capture_native.py',S/'recipe.json',C/'manifest.json',C/'animation-proof.json',C/'original-replay-proof.json']]
resource_paths += [rel(p)for p in N.rglob('*')if p.is_file()and'.godot'not in p.relative_to(N).parts and not p.name.endswith(('.import','.uid'))]
resource_paths += [rel(p)for p in (R/'native-capture').rglob('*')if p.is_file()]if(R/'native-capture').exists()else[]
if(C/'native-capture-evidence.json').is_file():resource_paths.append(rel(C/'native-capture-evidence.json'))
heroes={d:next(r['path']for r in raw_records if r['clip']=='idle'and r['direction']==d and r['index']==0)for d in DIRS}
delivery={'asset':'bubble-preference','round':'round01','pipeline':'existing-imagegen-2d','representation':'Editable actual blank PNG + exact approved full foodPNG + deterministic native2D recipe','project':rel(S/'bubble-preference.png'),'recipeScript':rel(S/'publish.py'),'recipe':rel(S/'recipe.json'),'validation':rel(C/'validation.json'),'manifest':rel(C/'manifest.json'),'provenance':rel(S/'provenance.json'),'preparationRecipe':rel(S/'prepare_sources.py'),'verificationRecipe':rel(S/'verify.py'),'nativeCaptureRecipe':rel(S/'capture_native.py'),'reproductionEvidence':rel(C/'reproduction.json'),'heroes':heroes,'rawFrames':raw_records,'atlases':atlas_records,'previews':previews,'resources':sorted(set(resource_paths)),'source':{'pipeline':'imagegen-2d','artwork':rel(S/'bubble-preference.png'),'sha256':sha(S/'bubble-preference.png'),'rawArtwork':rel(R/'fixed-target-raw.png'),'rawSHA256':sha(R/'fixed-target-raw.png'),'modelScript':rel(S/'publish.py'),'canonicalCrop':prov['crop'],'approvedFoodSources':prov['foods']},'notes':'No selfapproval.432logical slots /108physicalSframes /36entries /9physicalatlases. All original bytes and approved food receipts retained. Camera-facing aliases, original animation/endpoints/order/loop/fallback, current−172native context and historical−90catalog context separately labeled. No runtime extra variant.'}
write(C/'delivery.json',delivery);write(O/'delivery.json',delivery)
print(json.dumps({'slots':len(raw_records),'physicalFrames':108,'atlasEntries':36,'physicalAtlases':9,'previews':len(previews),'originalReplay':108,'candidateOriginalFormulaReplay':108,'delivery':rel(C/'delivery.json')},indent=2))
