"""Closed deterministic existing native2D heart+smile publisher. No artistic edits.
Only the prepared PNGs are resized uniformly. Animation is the original math.
Run anywhere within the same object-relative source/round01 resource structure.
"""
from pathlib import Path
import json,hashlib,math,sys,copy,struct,zlib,io
import PIL
from PIL import Image,ImageDraw
S=Path(__file__).resolve().parent;O=S.parents[1];R=S/'resources';C=O/'candidates/round01'
FRAME=(384,640);LOGICAL=(192,320);ROOT=(96,248);SCALE=2
DIRS=['S','N','E','W'];MAIN=['appear','idle','fade','happy-transition'];SMILE=['happy-smile-appear','happy-smile-idle','happy-smile-fade','happy-smile-transition'];RS=Image.Resampling.LANCZOS
RECTS=[[i%6*384,i//6*640,384,640] for i in range(12)]
COLORS=[('light',(246,241,229)),('gray',(124,125,129)),('dark',(29,32,38))]
WINDOW=(88,284,296,500)
for sub in ['raw','atlases','runtime-variants/smile/raw','runtime-variants/smile/atlases','previews']:(C/sub).mkdir(parents=True,exist_ok=True)
def rel(p):return p.relative_to(O).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psha(im):return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def width(im,w):return im.resize((round(w),round(im.height/im.width*w)),RS)
def center(c,im,xy):c.alpha_composite(im,(round(xy[0]-im.width/2),round(xy[1]-im.height/2)))
def background(im,color):out=Image.new('RGBA',im.size,color+(255,));out.alpha_composite(im);return out.convert('RGB')
def components(image,threshold=8):
 alpha=image.getchannel('A');w,h=alpha.size;data=alpha.tobytes();visited=set();out=[]
 for start,value in enumerate(data):
  if value<=threshold or start in visited:continue
  queue=[start];visited.add(start);count=0;box=[w,h,0,0];maxalpha=0
  while queue:
   index=queue.pop();x=index%w;y=index//w;count+=1;box=[min(box[0],x),min(box[1],y),max(box[2],x+1),max(box[3],y+1)];maxalpha=max(maxalpha,data[index])
   for dy in [-1,0,1]:
    for dx in [-1,0,1]:
     xx=x+dx;yy=y+dy;j=yy*w+xx
     if 0<=xx<w and 0<=yy<h and j not in visited and data[j]>threshold:visited.add(j);queue.append(j)
  out.append({'pixels':count,'bounds':box,'maxAlpha':maxalpha})
 return sorted(out,key=lambda v:-v['pixels'])
def make_frame(cutout,clip,index):
 image=cutout.copy();phase=index/12*math.tau;opacity=1.;scale=1.
 if 'appear' in clip:scale=.5+.5*math.sin((index+1)/12*math.pi/2);opacity=(index+1)/12
 elif 'fade' in clip:opacity=1-index/12
 elif clip.endswith('transition'):scale=1+.12*math.sin(phase)
 if scale!=1:image=image.resize((round(image.width*scale),round(image.height*scale)),RS)
 if opacity<1:image.putalpha(image.getchannel('A').point(lambda a:round(a*opacity)))
 c=Image.new('RGBA',FRAME);center(c,image,(ROOT[0]*2,(ROOT[1]-52-3*math.sin(phase))*2));return c
prov=json.loads((S/'provenance.json').read_text());catalog=json.loads((R/'original-catalog-object.json').read_text());original_smile=json.loads((R/'smile/original-manifest.json').read_text())
arts={};normalized={};frames={};raws={};atlases={};entries={};alpha={};previews={};original_matches={}
for kind,clips in [('heart',MAIN),('smile',SMILE)]:
 record=prov['crop'][kind];art=load(O/record['canonical']);raw=load(O/record['raw']);box=raw.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
 assert list(box)==record['box'] and art.tobytes()==raw.crop(box).tobytes();assert sha(O/record['canonical'])==record['canonicalSHA256']
 arts[kind]=art;normalized[kind]=width(art,164);frames[kind]={};raws[kind]=[];atlases[kind]=[];entries[kind]={};alpha[kind]={}
 original=load(R/('original-heart-artwork.png' if kind=='heart' else 'smile/original-source/bubble-happy-smile.png'));ob=original.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox();oldcut=width(original.crop(ob),164)
 matches=0
 for clip in clips:
  prefix=Path('') if kind=='heart' else Path('runtime-variants/smile');fseq=[make_frame(normalized[kind],clip,i) for i in range(12)];frames[kind][clip]=fseq
  atlas=Image.new('RGBA',(2304,1280));hashes=[]
  for i,im in enumerate(fseq):
   rect=RECTS[i];atlas.alpha_composite(im,(rect[0],rect[1]));hashes.append(psha(im));p=C/prefix/'raw'/f'{clip}-S-{i:04d}.png';im.save(p,compress_level=9)
   for direction in (DIRS if kind=='heart' else ['S']):raws[kind].append({'clip':clip,'facing':direction,'direction':direction,'index':i,'frame':i,'path':rel(p),'size':list(FRAME),'sha256':sha(p),'pixelSHA256':psha(im),'aliasOf':f'{clip}:S:{i}' if direction!='S' else None})
  name=f'2d-{clip}-S.png' if kind=='heart' else f'{clip}-S.png';ap=C/prefix/'atlases'/name;atlas.save(ap,compress_level=9)
  entry={'image':f'sprites/bubble-happy/{name}','columns':6,'rows':2,'atlasSize':[2304,1280],'rects':RECTS,'uniqueFrames':len(set(hashes)),'sha256':sha(ap)}
  entries[kind][clip]=entry
  for direction in (DIRS if kind=='heart' else ['S']):atlases[kind].append({'clip':clip,'facing':direction,'direction':direction,'path':rel(ap),'size':[2304,1280],'atlasSize':[2304,1280],'columns':6,'rows':2,'rects':RECTS,'frames':12,'uniqueFrames':len(set(hashes)),'sha256':sha(ap),'aliasOf':clip+':S' if direction!='S' else None})
  for i,im in enumerate(fseq):
   rect=RECTS[i];assert atlas.crop((rect[0],rect[1],rect[0]+384,rect[1]+640)).tobytes()==im.tobytes()
  a=[im.getchannel('A') for im in fseq];bounds=[im.point(lambda v:255 if v>8 else 0).getbbox() for im in a]
  border=max(max(im.crop(b).getextrema()[1] for b in [(0,0,384,1),(0,639,384,640),(0,0,1,640),(383,0,384,640)])for im in a)
  alpha[kind][clip]={'frameAlpha8Bounds':[list(v) for v in bounds],'maxBorderAlpha':border,'distinctPixelPoses':len(set(hashes)),'allFramesNonempty':all(v for v in bounds),'alpha1to8PixelCountRange':[min(sum(v.histogram()[1:9])for v in a),max(sum(v.histogram()[1:9])for v in a)],'normalizedSourceComponentsAlpha0':components(normalized[kind],0),'normalizedSourceComponentsAlpha8':components(normalized[kind],8)};assert border==0
  oldname=f'2d-{clip}-S.png' if kind=='heart' else f'{clip}-S.png';oldatlas=load(R/('original-heart-atlases' if kind=='heart' else 'smile/original-atlases')/oldname)
  for i in range(12):
   r=RECTS[i];oldframe=oldatlas.crop((r[0],r[1],r[0]+384,r[1]+640));assert oldframe.tobytes()==make_frame(oldcut,clip,i).tobytes();matches+=1
 original_matches[kind]={'allOriginalAtlasFramesReproducedRGBA':True,'actualFrames':matches,'registeredSnapshotReproducedRGBA':make_frame(oldcut,clips[1],0).tobytes()==load(R/('original-heart-registered.png' if kind=='heart' else 'smile/original.png')).tobytes()}
# Preserve exact original main metadata/aliases; only artwork/source paths/hash annotations change.
main_manifest=copy.deepcopy(catalog)
main_manifest['source']={'pipeline':'imagegen-2d','artwork':'source/round01/bubble-happy-heart.png','sha256':sha(S/'bubble-happy-heart.png'),'modelScript':'source/round01/publish.py'}
for clip in main_manifest['clips']:
 clip['directions']={d:copy.deepcopy(entries['heart'][clip['id']])for d in clip['directions']}
main_manifest_path=C/'manifest.json';write(main_manifest_path,main_manifest)
variant=copy.deepcopy(original_smile);vo=variant['objects']['bubble-happy']
for cid,clip in vo['clips'].items():clip['directions']={'S':copy.deepcopy(entries['smile'][cid])}
variant['baseLibrarySha256']=original_smile['baseLibrarySha256'];variant['sourceFiles']={rel(p):sha(p)for p in [S/'bubble-happy-smile.png',S/'publish.py',S/'provenance.json']};variant['note']='Existing separate camera-facing runtime variant, same fixed registration and animation; S fallback unchanged.'
variant_path=C/'runtime-variants/smile/manifest.json';write(variant_path,variant)
def preview(key,im):
 p=C/'previews'/f'{key}.png';im.save(p,compress_level=9);previews[key]=rel(p)
def apng(path,frames,delays=None):
 # Explicit fullRGBA frames with exact rational1/12s delay. Preserve repeated
 # pixel poses as separate frames; Pillow's normal APNG writer coalesces them.
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 blobs=[];header=None
 for frame in frames:
  stream=io.BytesIO();frame.convert('RGBA').save(stream,format='PNG',compress_level=9);data=stream.getvalue();pos=8;ids=[]
  while pos<len(data):
   length=struct.unpack('>I',data[pos:pos+4])[0];kind=data[pos+4:pos+8];payload=data[pos+8:pos+8+length];pos+=length+12
   if kind==b'IHDR':header=payload
   elif kind==b'IDAT':ids.append(payload)
  blobs.append(b''.join(ids))
 result=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'acTL',struct.pack('>II',len(frames),0));sequence=0
 for index,blob in enumerate(blobs):
  numerator,denominator=delays[index] if delays else (1,12)
  result+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',sequence,frames[index].width,frames[index].height,0,0,numerator,denominator,0,0));sequence+=1
  if index==0:result+=chunk(b'IDAT',blob)
  else:result+=chunk(b'fdAT',struct.pack('>I',sequence)+blob);sequence+=1
 result+=chunk(b'IEND',b'');path.write_bytes(result)
def playback(key,seq):
 p=C/'previews'/f'{key}.png';apng(p,seq);previews[key]=rel(p)
for kind,clips in [('heart',MAIN),('smile',SMILE)]:
 for clip in clips:
  playback(clip+'-S',frames[kind][clip])
  if kind=='heart':
   for d in DIRS[1:]:previews[clip+'-'+d]=previews[clip+'-S']
 # Complete compact12framesx4clips contact sheet from fixed common preview window.
 sheet=Image.new('RGB',(1440,568),(222,218,208));draw=ImageDraw.Draw(sheet)
 for row,clip in enumerate(clips):
  draw.text((8,row*142+3),clip,fill='black')
  for i,im in enumerate(frames[kind][clip]):
   sample=im.crop(WINDOW).resize((104,108),RS);sheet.paste(background(sample,COLORS[row%3][1]),(i*120+8,row*142+22));draw.text((i*120+8,row*142+130),str(i),fill='black')
 preview(kind+'-all48-frames',sheet)
# Exact camera-facing heroes all refer to the same registered native idle frame.
hero=frames['heart']['idle'][0];smilehero=frames['smile']['happy-smile-idle'][0]
four=Image.new('RGB',(768,350),(222,218,208));draw=ImageDraw.Draw(four)
for col,d in enumerate(DIRS):four.paste(background(hero.resize(LOGICAL,RS),COLORS[0][1]),(col*192,30));draw.text((col*192+8,8),d+' camera-facing alias',fill='black')
preview('four-view-sheet',four)
# Same art at enlarged native, full logical82and game-use32occupied widths.
size_sheet=Image.new('RGB',(1220,1470),(222,218,208));draw=ImageDraw.Draw(size_sheet)
for row,(label,color) in enumerate(COLORS):
 for col,(kind,im) in enumerate([('heart',hero),('smile',smilehero)]):
  x=col*610;y=row*490;draw.text((x+8,y+6),kind+' / '+label,fill='black')
  for offset,w in [(8,328),(440,82),(552,32)]:
   # Uniformly scale entire registered frame before fixed display-window crop.
   cut=im.crop(WINDOW);ratio=w/164;sample=cut.resize((round(cut.width*ratio),round(cut.height*ratio)),RS);tile=background(sample,color);size_sheet.paste(tile,(x+offset,y+32));draw.text((x+offset,y+470),str(w)+'px',fill='black')
preview('light-gray-dark-game-and-enlarged',size_sheet)
# Lossless canonical source inspection at a common400px uniform preview width.
raw_sheet=Image.new('RGB',(1260,840),(222,218,208));draw=ImageDraw.Draw(raw_sheet)
for col,(label,color) in enumerate(COLORS):
 for row,(kind,art) in enumerate(arts.items()):
  tile=Image.new('RGBA',(420,400),color+(255,));center(tile,width(art,400),(210,200));raw_sheet.paste(tile.convert('RGB'),(col*420,row*420+20));draw.text((col*420+8,row*420+4),kind+' raw crop on '+label,fill='black')
preview('canonical-source-backgrounds',raw_sheet)
# Original versus candidate at the same common crop and registration/scale.
compare=Image.new('RGB',(800,500),(222,218,208));draw=ImageDraw.Draw(compare)
for col,kind in enumerate(['heart','smile']):
 old=load(R/('original-heart-registered.png'if kind=='heart'else'smile/original.png'));new=hero if kind=='heart'else smilehero
 for row,(label,frame)in enumerate([('Original',old),('Candidate',new)]):
  tile=background(frame.crop(WINDOW),COLORS[1][1]);compare.paste(tile,(col*400+8,row*250+24));sample=frame.crop(WINDOW).resize((104,108),RS);compare.paste(background(sample,COLORS[2][1]),(col*400+240,row*250+58));draw.text((col*400+8,row*250+8),kind+' '+label+' / same native and logical scale',fill='black')
preview('original-candidate-registered-comparison',compare)
# Current Godot context. Sprite-only assembly, exact root/canvas draw math.
context=json.loads((R/'context/manifest.json').read_text())
def contextframe(ident,cid,index=0):
 obj=context['objects'][ident];c=obj['clips'][cid];entry=c['directions']['S'];rect=entry['rects'][index%len(entry['rects'])];a=load(R/entry['resource']);return a.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
def place(scene,im,obj,base,pitch):
 k=pitch/128;scale=k/obj['sourceScale'];target=im.resize((round(im.width*scale),round(im.height*scale)),RS);scene.alpha_composite(target,(round(base[0]-obj['root'][0]*k),round(base[1]-obj['root'][1]*k)))
def assembly(kind,index=0,pitch=128,happy_seconds=1.1,catalog_mode=False):
 k=pitch/128;scene=Image.new('RGBA',(round(384*k),round(560*k)),COLORS[0][1]+(255,));base=(192*k,480*k);pose=0 if catalog_mode else (-math.sin(math.pi*happy_seconds/.55)*pitch*.14 if 0<=happy_seconds<.55 else 0)
 place(scene,contextframe('stool-wood','static'),context['objects']['stool-wood'],base,pitch)
 customerclip='seated-wait' if catalog_mode else 'eat-salmon';place(scene,contextframe('customer-rosa',customerclip,index),context['objects']['customer-rosa'],(base[0],base[1]+pose),pitch)
 cid='idle' if kind=='heart' else 'happy-smile-idle';attachment=-90 if catalog_mode else -172;place(scene,frames[kind][cid][index],{'root':ROOT,'sourceScale':2},(base[0],base[1]+pose+attachment*k),pitch)
 return scene
contexts=Image.new('RGB',(1200,1120),(222,218,208));draw=ImageDraw.Draw(contexts)
for col,kind in enumerate(['heart','smile']):
 logical=assembly(kind);contexts.paste(logical.convert('RGB'),(col*600+8,28));draw.text((col*600+8,8),kind+' / current Godot172logical attachment',fill='black');small=assembly(kind,pitch=50);contexts.paste(small.convert('RGB'),(col*600+414,200));draw.text((col*600+414,180),'50px cell / ~32px balloon',fill='black');enlarged=assembly(kind,pitch=192).crop((132,222,444,680));contexts.paste(enlarged.convert('RGB'),(col*600+144,630));draw.text((col*600+144,608),'1.5x existing2D sprite assembly focus',fill='black')
preview('heart-smile-actual-customer-context',contexts)
preview('current-smile-context-full-logical',assembly('smile'))
preview('historical-catalog-heart-context',assembly('heart',catalog_mode=True))
repeat=Image.new('RGBA',(768,560),COLORS[0][1]+(255,))
for i,kind in enumerate(['heart','smile']):repeat.alpha_composite(assembly(kind),(i*384,0))
preview('repeated',repeat)
# Actual selected happy runtime2.2s: transition,short idle,fade; same customer jump.
runtime=[]
for tick in range(27):
 t=tick/12;cid='happy-smile-transition' if t<1 else 'happy-smile-fade' if t>=1.2 else 'happy-smile-idle';age=t if t<1 else t-1.2 if cid.endswith('fade') else t-1;i=min(11,max(0,math.floor(age*12+1e-7)))
 im=assembly('smile',index=i,pitch=80,happy_seconds=t);# Replace idle balloon with selected clip by reassembling cleanly.
 k=80/128;im=Image.new('RGBA',(240,350),COLORS[0][1]+(255,));base=(120,300);pose=-math.sin(math.pi*t/.55)*80*.14 if t<.55 else 0
 place(im,contextframe('stool-wood','static'),context['objects']['stool-wood'],base,80);place(im,contextframe('customer-rosa','eat-salmon',tick),context['objects']['customer-rosa'],(120,300+pose),80);place(im,frames['smile'][cid][i],{'root':ROOT,'sourceScale':2},(120,300+pose-172*k),80);runtime.append(im)
p=C/'previews/happy-smile-runtime-playback.png';apng(p,runtime,[(1,12)]*26+[(1,30)]);previews['happy-smile-runtime-playback']=rel(p)
recipe={'asset':'bubble-happy','pipeline':'existing-imagegen-2d','project':rel(S/'bubble-happy-heart.png'),'runtimeVariantProject':rel(S/'bubble-happy-smile.png'),'publisher':rel(S/'publish.py'),'preparationRecipe':rel(S/'prepare_sources.py'),'capture':{'frame':list(FRAME),'logicalFrame':list(LOGICAL),'root':list(ROOT),'sourceScale':2,'cellSize':128,'fps':12,'atlasSize':[2304,1280],'columns':6,'rows':2},'crop':prov['crop'],'animation':{'phase':'index/12*math.tau','center':'[96*2,(248-52-3*sin(phase))*2]','appear':'scale=.5+.5*sin((index+1)/12*pi/2);opacity=(index+1)/12','fade':'opacity=1-index/12','transition':'scale=1+.12*sin(phase)','idle':'scale=1;opacity=1','placement':'Original Pythonround and PillowLANCZOS; one common82logicalwidth per artwork before animation.','loops':['idle','happy-smile-idle']},'aliases':'Main S/N/E/W reuse same S frames and atlas metadata; runtime smile only S with existing ArtBook fallback.','previews':'Honest2D sprite assemblies from existing Godot customer/stool art, current172logical head attachment and actual happy jump. Historical90logical catalog attachment is separately named. APNG retains all fullRGBAframes including repeated poses; delay is exact1/12second per frame. Preview replay loops for inspection; manifest loop policy remains original.','prohibitedOperationsApplied':[]}
write(S/'recipe.json',recipe)
validation={'asset':'bubble-happy','round':'round01','representation':'existing-imagegen-2d; noBlender geometry or native-scene-render claim','registration':recipe['capture'],'coverage':{'mainSlots':len(raws['heart']),'mainActualSFiles':48,'mainAtlasEntries':len(atlases['heart']),'mainActualAtlasFiles':4,'runtimeActualFrames':len(raws['smile']),'runtimeAtlasFiles':4,'totalSlots':240,'actualCaptureFiles':96,'independentFacingArt':False,'repeatPixelPosesAllowed':True},'sourceOperations':{'oneLosslessRectangleCropPerRawSource':True,'crop':prov['crop'],'uniformNormalizedSizes':{k:list(v.size)for k,v in normalized.items()},'originalAlphaRetainedInsideRectangle':True,'noArtisticPythonPaintingWarpErasureRegradeOrPerFrameFit':True},'originalPublisherReplay':original_matches,'alphaAndAnimation':alpha,'contract':{'mainClips':[{k:c[k] for k in ['id','frames','fps','loop','static','frameOrder']if k in c}for c in main_manifest['clips']],'runtimeClips':[{k:c[k]for k in ['id','frames','fps','loop','frameOrder']}for c in vo['clips'].values()],'originalMainAliasMetadataPreserved':True,'runtimeSeparateManifestAndSOnlyFallback':True,'all96NativeFramesRepackedIdenticalToAtlasRects':True,'allBorderAlphaZero':True},'context':{'evidence':'Honest deterministic existing2D sprite assembly, no Godot screenshot claim.','currentAttachmentLogical':[0,-172],'historicalCatalogAttachmentLogical':[0,-90],'customer':'existing Godot customer-rosa eat-salmon and seated-wait native atlas','stool':'existing Godot stool-wood static atlas','currentRuntimeHappyDuration':2.2,'currentRuntimePhaseSelection':'transition<1s;fade>=1.2s;idle otherwise;clamp12fps nonloop frame index','jump':'y-=sin(PI*happy/.55)*pitch*.14 for happy<.55; both customer and feedback share pose offset','runtimePlaybackDuration':2.2,'runtimePlaybackSampling':'26frames at1/12s plus final1/30s, exact2.2second happy event','gameUsePitch':50,'gameUseOccupiedWidth':82*50/128},'environment':{'python':sys.version.split()[0],'pillow':PIL.__version__},'independentJudgeApproval':False}
write(C/'validation.json',validation)
resources=[r['path']for r in prov['resources']]+[rel(p)for p in [S/'bubble-happy-heart.png',S/'bubble-happy-smile.png',S/'provenance.json',S/'prepare_sources.py',S/'publish.py',S/'verify.py',S/'recipe.json',main_manifest_path,variant_path]]
variant_resources=[rel(variant_path)]+[x['path']for x in raws['smile']+atlases['smile']]+[rel(S/'bubble-happy-smile.png')]
# Explicitly bind variantoutputs at top level as well; coordinator seal helper reads resources.
resources+=variant_resources
heroes={d:next(x['path']for x in raws['heart']if x['clip']=='idle'and x['facing']==d and x['index']==0)for d in DIRS}
delivery={'asset':'bubble-happy','round':'round01','pipeline':'existing-imagegen-2d','representation':'Editable raster artwork plus deterministic native2D animation/publisher','project':rel(S/'bubble-happy-heart.png'),'recipeScript':rel(S/'publish.py'),'recipe':rel(S/'recipe.json'),'recipeManifest':rel(S/'recipe.json'),'captureRecipe':rel(S/'publish.py'),'packagingRecipe':rel(S/'publish.py'),'preparationRecipe':rel(S/'prepare_sources.py'),'verificationRecipe':rel(S/'verify.py'),'provenance':rel(S/'provenance.json'),'reproductionEvidence':rel(C/'reproduction.json'),'validation':rel(C/'validation.json'),'manifest':rel(main_manifest_path),'heroes':heroes,'rawFrames':raws['heart'],'atlases':atlases['heart'],'previews':previews,'resources':sorted(set(resources)),'runtimeVariants':{'project':rel(S/'bubble-happy-smile.png'),'manifest':rel(variant_path),'rawFrames':raws['smile'],'atlases':atlases['smile'],'resources':sorted(set(variant_resources)),'clips':SMILE,'facingPolicy':'S only; existing ArtBook fallback','previews':{k:v for k,v in previews.items()if 'smile' in k}},'source':{'pipeline':'imagegen-2d','artwork':rel(S/'bubble-happy-heart.png'),'sha256':sha(S/'bubble-happy-heart.png'),'rawArtwork':rel(R/'fixed-heart-target-raw.png'),'rawSHA256':sha(R/'fixed-heart-target-raw.png'),'originalSource':rel(R/'original-heart-artwork.png'),'modelScript':rel(S/'publish.py'),'canonicalCrop':prov['crop']['heart']},'notes':'No selfapproval. Fixed targets adopted with sole authorized lossless rectangles and original registered2D animation/packing. Complete240slots and96actual captures. Raw targets, originalsources, exact generation prompts/provenance and closed contextresources retained.'}
write(C/'delivery.json',delivery);write(O/'delivery.json',delivery)
print(json.dumps({'slots':240,'actualFrames':96,'mainAtlasFiles':4,'variantAtlasFiles':4,'previews':len(previews),'originalReplay':original_matches,'delivery':rel(C/'delivery.json')},indent=2))
