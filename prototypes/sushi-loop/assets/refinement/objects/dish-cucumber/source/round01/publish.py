"""Deterministic existing-raster2D packing, previews and audit. No painting.
Run with Pillow Python. Canonical source has already received its sole authorized
lossless alpha>8 bounding-rectangle crop. This publisher NEVER crops it again.
"""
from pathlib import Path
import hashlib,json,math,sys,PIL
from collections import deque
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;C=O/'candidates/round01';R=S/'resources'
DIRS=['N','E','S','W'];FRAME=(384,640);ROOT=(192,496);RESAMPLE=Image.Resampling.LANCZOS
for folder in ['raw','atlases','previews']:(C/folder).mkdir(parents=True,exist_ok=True)
def rel(p):return str(p.relative_to(O))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def psha(im):return hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def save_json(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def resize_width(im,w):return im.resize((round(w),round(im.height/im.width*w)),RESAMPLE)
def center(canvas,im,xy):canvas.alpha_composite(im,(round(xy[0]-im.width/2),round(xy[1]-im.height/2)))
def bg(im,color):out=Image.new('RGBA',im.size,color+(255,));out.alpha_composite(im);return out.convert('RGB')
def components(a,threshold):
 w,h=a.size;b=a.tobytes();seen=set();out=[]
 for start,v in enumerate(b):
  if v<=threshold or start in seen:continue
  seen.add(start);q=deque([start]);count=0;minx=w;miny=h;maxx=maxy=0;maxa=0;total=0
  while q:
   i=q.popleft();x=i%w;y=i//w;count+=1;minx=min(minx,x);miny=min(miny,y);maxx=max(maxx,x+1);maxy=max(maxy,y+1);maxa=max(maxa,b[i]);total+=b[i]
   for dy in [-1,0,1]:
    for dx in [-1,0,1]:
     nx=x+dx;ny=y+dy;j=ny*w+nx
     if 0<=nx<w and 0<=ny<h and j not in seen and b[j]>threshold:seen.add(j);q.append(j)
  out.append({'pixels':count,'bounds':[minx,miny,maxx,maxy],'maxAlpha':maxa,'sumAlpha':total})
 return sorted(out,key=lambda v:-v['pixels'])
art=load(S/'dish-cucumber.png');raw=load(R/'fixed-target-raw.png');prov=json.loads((S/'provenance.json').read_text());box=tuple(prov['canonicalCrop']['box'])
assert art.tobytes()==raw.crop(box).tobytes()
assert art.size==(635,511)
food=resize_width(art,132);frame=Image.new('RGBA',FRAME);center(frame,food,ROOT)
reproduced=Image.new('RGBA',FRAME);rawbox=raw.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox();center(reproduced,resize_width(raw.crop(rawbox),132),ROOT)
assert frame.tobytes()==reproduced.tobytes()
original=load(R/'original-artwork.png');ob=original.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox();original_frame=Image.new('RGBA',FRAME);center(original_frame,resize_width(original.crop(ob),132),ROOT)
assert original_frame.tobytes()==load(R/'original-registered.png').tobytes()
raw_records=[];atlases=[];heroes={}
for facing in DIRS:
 f=C/'raw'/f'static-{facing}-0000.png';a=C/'atlases'/f'2d-static-{facing}.png';frame.save(f);frame.save(a);heroes[facing]=rel(f)
 raw_records.append({'clip':'static','facing':facing,'direction':facing,'frame':0,'index':0,'path':rel(f),'size':list(FRAME),'sha256':sha(f),'pixelSHA256':psha(frame)})
 atlases.append({'clip':'static','facing':facing,'direction':facing,'path':rel(a),'size':list(FRAME),'atlasSize':list(FRAME),'columns':1,'rows':1,'rects':[[0,0,384,640]],'frames':1,'uniqueFrames':1,'sha256':sha(a)})
previews={}
def preview(key,im,name=None):
 p=C/'previews'/(name or key+'.png');im.save(p);previews[key]=rel(p);return p
# Full fixed registered canvases. Labels are outside the canvas area.
sheet=Image.new('RGB',(384*4,680),(224,220,211));d=ImageDraw.Draw(sheet)
for n,facing in enumerate(DIRS):d.text((n*384+12,10),f'{facing} - same camera-facing static pixels',fill='black');sheet.paste(bg(frame,(241,236,223)),(n*384,40))
preview('four-view-sheet',sheet)
repeat=Image.new('RGBA',(768,768),(241,236,223,255))
for y in range(3):
 for x in range(3):repeat.alpha_composite(frame,(x*256+128-192,y*256+128-496))
preview('repeated',repeat)
# Native and logical widths on backgrounds, no color/alpha alterations.
backgrounds=[('light',(246,241,229)),('gray',(124,125,129)),('dark',(29,32,38))]
canvas=Image.new('RGB',(1100,1350),(224,220,211));d=ImageDraw.Draw(canvas)
for row,(label,color) in enumerate(backgrounds):
 y=row*450;d.text((10,y+8),label,fill='black')
 for x,w,name in [(10,396,'3x native / 396px'),(430,132,'native132px'),(600,66,'logical66px'),(710,40,'bubble logical40px'),(860,16,'32px cell (~16.5px food)')]:
  if w==16:
   scaled=frame.resize((48,80),RESAMPLE);tile=bg(scaled,color);canvas.paste(tile,(x,y+50))
  else:
   scaled=resize_width(art,w);tile=Image.new('RGBA',(max(w+16,100),max(scaled.height+16,100)),color+(255,));center(tile,scaled,(tile.width/2,tile.height/2));canvas.paste(tile.convert('RGB'),(x,y+50))
  d.text((x,y+30),name,fill='black')
preview('backgrounds-actual-widths',canvas)
# Full fixed canvas previews retain exact registration at each declared scale.
for label,color in backgrounds:
 preview('full-native-'+label,bg(frame,color))
 preview('full-logical-'+label,bg(frame.resize((192,320),RESAMPLE),color))
 preview('full-cell32-'+label,bg(frame.resize((48,80),RESAMPLE),color))
# Source crop expanded on each background reveals residual halo/debris honestly.
source_sheet=Image.new('RGB',(760*3,550),(224,220,211));d=ImageDraw.Draw(source_sheet)
for x,(label,color) in enumerate(backgrounds):
 pane=Image.new('RGBA',(760,520),color+(255,));center(pane,art,(380,260));source_sheet.paste(pane.convert('RGB'),(x*760,30));d.text((x*760+10,10),f'Canonical unresized source / {label}',fill='black')
preview('canonical-source-backgrounds',source_sheet)
# Frame-level tightly bounded inspection is a preview only, never an export fit.
window=(112,438,272,554)
frame_sheet=Image.new('RGB',(160*4,116*3+28),(224,220,211));d=ImageDraw.Draw(frame_sheet)
for row,(label,color) in enumerate(backgrounds):
 for col,facing in enumerate(DIRS):frame_sheet.paste(bg(frame.crop(window),color),(col*160,28+row*116))
for col,facing in enumerate(DIRS):d.text((col*160+6,8),facing+' actual native pixels',fill='black')
preview('registered-frames-backgrounds',frame_sheet)
# Exact existing preference composition at idle index0; only dish source changes.
bubble_raw=load(R/'context/bubble-preference-raw.png');bb=bubble_raw.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox();bubble_art=resize_width(bubble_raw.crop(bb),164)
bubble_frame=Image.new('RGBA',FRAME);center(bubble_frame,bubble_art,(192,392));center(bubble_frame,resize_width(art,80),(192,382));preview('preference-full-frame',bubble_frame)
bubble_sheet=Image.new('RGB',(920,430),(224,220,211));d=ImageDraw.Draw(bubble_sheet)
for x,(label,color) in enumerate(backgrounds):
 # Actual logical192x320 frame and reduced32pxcell factor. Context is not alpha-fit.
 logical=bubble_frame.resize((192,320),RESAMPLE);bubble_sheet.paste(bg(logical,color),(10+x*300,40));reduced=bubble_frame.resize((48,80),RESAMPLE);bubble_sheet.paste(bg(reduced,color),(210+x*300,170));d.text((10+x*300,8),label+' / actual40logical food',fill='black');d.text((210+x*300,260),'32px cell',fill='black')
preview('preference-actual40-context',bubble_sheet)
# Original source manifest records and original atlas pixels retained in resources.
lib=json.loads((R/'context-library.json').read_text());byid={v['id']:v for v in lib['objects']}
def context_frame(ident,clip,facing,index=0):
 obj=byid[ident];c=next(v for v in obj['clips']if v['id']==clip);a=c['directions'][facing];im=load(R/'context'/a['image']);rect=a['rects'][index];return im.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]))
def place(scene,im,obj,xy):
 scale=obj.get('sourceScale',2);root=obj['root'];scene.alpha_composite(im,(round((xy[0]-root[0])*2),round((xy[1]-root[1])*2)))
placements=json.loads((R/'original-catalog-object.json').read_text())['interactions'][0]['placements']
serving=Image.new('RGBA',(1024,1024),(235,226,205,255));belt_only=serving.copy()
for placement in placements:
 ident=placement['object'];obj=byid[ident];offset=placement.get('offset',[0,0]);rootcell=obj.get('directionRootCells',{}).get(placement.get('direction','S'),obj.get('rootCell',[.5,.5]));xy=((placement['x']+rootcell[0])*128+offset[0],(placement['y']+rootcell[1])*128+offset[1])
 im=frame if ident=='dish-cucumber' else context_frame(ident,placement.get('clip','static'),placement.get('direction','S'))
 place(serving,im,obj,xy)
 if ident in ['belt-straight-e','dish-cucumber']:place(belt_only,im,obj,xy)
preview('serving-full-original-offsets',serving);preview('serving-belt-without-foreground',belt_only)
preview('serving-cell32-original-offsets',serving.resize((128,128),RESAMPLE))
preview('serving-cell32-inspection-only',belt_only.resize((128,128),RESAMPLE))
context_sheet=Image.new('RGB',(1024,980),(224,220,211));d=ImageDraw.Draw(context_sheet)
context_sheet.paste(serving.resize((512,512),RESAMPLE).convert('RGB'),(0,30));context_sheet.paste(belt_only.resize((512,512),RESAMPLE).convert('RGB'),(512,30));d.text((10,10),'Actual logical context / original foreground occlusion',fill='black');d.text((522,10),'Same placement / foreground omitted for plate inspection',fill='black')
focus=(215,190,555,590);context_sheet.paste(serving.crop(focus).convert('RGB'),(20,560));context_sheet.paste(belt_only.crop(focus).convert('RGB'),(530,560));preview('serving-context',context_sheet)
# Honest representative existing native held captures. No replacement simulation.
held=Image.new('RGB',(896,420),(235,226,205));d=ImageDraw.Draw(held)
for i,facing in enumerate(DIRS):
 im=context_frame('customer-rosa','eat',facing);logical=im.resize((192,320),RESAMPLE);held.paste(bg(logical,(241,236,223)),(i*224,30));d.text((i*224+8,8),'Rosa '+facing+' existing baked art',fill='black');candidate=resize_width(art,45);pane=Image.new('RGBA',(64,50),(241,236,223,255));center(pane,candidate,(32,25));held.paste(pane.convert('RGB'),(i*224+64,355))
d.text((8,404),'Candidate45px size swatches only; native held replacements require separate source/UV/pair recaptures.',fill='black');preview('held-existing-dependency',held)
# Identity comparison at actual logical width.
compare=Image.new('RGB',(860,360),(224,220,211));d=ImageDraw.Draw(compare)
for x,(label,color) in enumerate(backgrounds):
 for y,(name,im) in enumerate([('Original',original_frame),('Candidate',frame)]):
  crop=im.crop(window);pane=bg(crop,color);compare.paste(pane,(x*285+10,y*160+34));logical=bg(crop.resize((80,58),RESAMPLE),color);compare.paste(logical,(x*285+185,y*160+63));d.text((x*285+10,y*160+10),label+' / '+name+' native132 & logical66',fill='black')
preview('original-candidate-actual-widths',compare)
alpha=frame.getchannel('A');hist=alpha.histogram();comps0=components(alpha,0);comps8=components(alpha,8)
source_comps=components(art.getchannel('A'),8);source_comps0=components(art.getchannel('A'),0)
validation={'asset':'dish-cucumber','round':'round01','representation':'existing-imagegen-2d','technicalChecks':{'nativeFrame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'sourceScale':2,'cellSize':128,'sourceCropCount':1,'cropThreshold':'>8','noAlphaThresholdAppliedToPixels':True,'noArtisticEditOrBackgroundRemoval':True,'canonicalCropPixelIdentity':art.tobytes()==raw.crop(box).tobytes(),'canonicalCropBox':list(box),'canonicalSize':list(art.size),'canonicalAlpha0Bounds':list(art.getchannel('A').getbbox()),'canonicalAlpha8Bounds':list(art.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()),'canonicalSourceSHA256':sha(S/'dish-cucumber.png'),'originalPublisherSnapshotReproducedPixels':True,'originalSourceBackupHashMatch':sha(R/'original-artwork.png')==sha(R/'original-backup.png'),'publisherDoesNotRecrop':True,'uniformNativeWidth':132,'normalizedFoodSize':list(food.size),'pasteXY':[round(192-food.width/2),round(496-food.height/2)],'intendedNativeCenter':[192,496],'rawTargetDirectOriginalAlgorithmReproduction':frame.tobytes()==reproduced.tobytes(),'facingsIdenticalPixels':len({v['pixelSHA256']for v in raw_records})==1,'allFourFramesAndAtlasesFileHashesIdentical':len({v['sha256']for v in raw_records+atlases})==1,'clips':[{'id':'static','frames':1,'fps':12,'static':True,'loop':False,'frameOrder':[0]}]},'alphaAudit':{'frameBounds':list(alpha.getbbox()),'frameBoundsAlpha8':list(alpha.point(lambda a:255 if a>8 else 0).getbbox()),'borderAlphaMax':max(list(alpha.crop((0,0,384,1)).tobytes())+list(alpha.crop((0,639,384,640)).tobytes())+list(alpha.crop((0,0,1,640)).tobytes())+list(alpha.crop((383,0,384,640)).tobytes())),'fullyTransparentPixels':hist[0],'nonzeroAlphaPixels':sum(hist[1:]),'lowAlpha1to8Pixels':sum(hist[1:9]),'connectedComponentsAlpha0':comps0,'connectedComponentsAlpha8':comps8,'canonicalSourceComponentsAlpha8':source_comps,'canonicalSourceComponentsAlpha0':source_comps0,'inspectionPreviews':[previews['backgrounds-actual-widths'],previews['canonical-source-backgrounds'],previews['registered-frames-backgrounds']]},'contexts':{'servingOffsets':placements,'preference':{'bubbleSource':'source/round01/resources/context/bubble-preference-raw.png','bubbleOriginalAlpha8Crop':list(bb),'bubbleNativeWidth':164,'bubbleCenter':[192,392],'dishNativeWidth':80,'dishCenter':[192,382],'timing':'idle index0, original formula, no additional grade'},'held':{'existingCaptureOnly':True,'source':'source/round01/resources/context/character_composition.py','alphaPolicyHistorical':'>0 full source UV rectangle','canonicalAlpha0Bounds':list(art.getchannel('A').getbbox()),'futureCanonicalSource':'source/round01/dish-cucumber.png','futureCanonicalSourceSHA256':sha(S/'dish-cucumber.png'),'worldWidthCells':.35,'attachmentPolicy':'Keep palm attachment, lowest plate registration, yaw cancellation, native scale,55degree plane and35degree camera,ray-depth bias and actions; explicitly version sourcecrop/UV before independent same-pair dependent reviews.','recaptureApproved':False}},'environment':{'python':sys.version.split()[0],'pillow':PIL.__version__,'interpreter':sys.executable},'reproduction':{'recipe':'source/round01/publish.py','recipeSHA256':sha(Path(__file__)),'provenance':'source/round01/provenance.json','pixelSHA256':psha(frame)},'independentJudgeApproval':False}
# Explicit alpha/UV handoff: no rawtarget swap into historical native textures.
def bounds(im,threshold=0):return list(im.getchannel('A').point(lambda a:255 if a>threshold else 0).getbbox())
def measured(im):
 b0=bounds(im);b8=bounds(im,8)
 return {'size':list(im.size),'alphaGT0Bounds':b0,'alphaGT8Bounds':b8,'heldAlpha0Aspect':(b0[3]-b0[1])/(b0[2]-b0[0]),'visibleWidthFractionOfHeldUV':(b8[2]-b8[0])/(b0[2]-b0[0])}
validation['contexts']['held']['versionedHandoff']={'version':1,'historicalRawOriginal':measured(original),'frozenRawTarget':measured(raw),'canonicalReplacement':measured(art),'requiredSourceSHA256':sha(S/'dish-cucumber.png'),'historicalUVSourceSHA256':sha(R/'original-artwork.png'),'bottomOriginCanonicalUVRect':[0,0,art.width,art.height],'textureReplacementState':'PENDING same corresponding native customer editor/judge pair rounds; not approved or recaptured here.','nativeConsumerPolicy':'alpha>0 in character_composition.py. Canonical source is sole authorized rectangle crop, preserving all inner RGBA; its alpha>0 bounds fill whole635x511. Rebuild/pack the texture and version UV/aspect/bottom plate registration together, preserve palm attachment, actions, camera, body design and rig.'}
validation['technicalChecks']['cell32PreviewScale']={'logicalCellWidth':32,'registeredFrame':[48,80],'foodWidthExact':132/8,'foodRoundedOutputApprox':17,'method':'Resize entire384x640 registered frame to48x80; no food fitting.'}
validation['frozenCriteriaSHA256']=sha(O/'reviews/criteria.json')
save_json(C/'validation.json',validation)
recipe={'pipeline':'existing-imagegen-2d','project':'source/round01/dish-cucumber.png','provenance':'source/round01/provenance.json','preparationRecipe':'source/round01/prepare_sources.py','publisher':'source/round01/publish.py','process':['Retain immutable raw fixed target and exact prompt/reference/source provenance.','Lossless rectangle crop ONCE at full raw alpha>8 bounds169,876,804,1387; retain all interior RGBA.','Canonical635x511 PNG is actual editable raster artwork and downstream dependency.','Publisher does NO additional crop; uniform Lanczos resize to132x106.','Transparent384x640 fullframe centered by original Python round rule at192,496.','Four static facing exports share exactly identical camera-facing pixels;1x1 original atlases.','Previews composite only; no painting,warping,grading,background-removal or fabricated3D.'],'dependencies':{'runtime':'Python3 with Pillow','images':'All under source/round01/resources, copied originals with full hashes in provenance.','downstreamCanonicalArtwork':'source/round01/dish-cucumber.png','affectedUses':['standalone cucumber atlas','preference bubble cucumber recipe clips via same source40logical food','all native customer captures containing packed cucumber texture','cucumber starter-meal customer runtime variants (Rosa,Ellis,Samir,June)'],'pending':'Bubble composition and native heldsource/UV replacement/new immutable dependent rounds must be reviewed before final Godot cutover. Existing native screenshots remain old baked art and are marked so.'}}
save_json(S/'recipe.json',recipe)
resource_list=[r['path']for r in prov['resources']]+['source/round01/resources/context-library.json','source/round01/provenance.json','source/round01/prepare_sources.py','source/round01/publish.py','source/round01/recipe.json','source/round01/verify.py','source/round01/dish-cucumber.png']
delivery={'asset':'dish-cucumber','round':'round01','pipeline':'existing-imagegen-2d','representation':'existing raster artwork plus deterministic2D publisher; no Blender dish model','project':'source/round01/dish-cucumber.png','recipe':'source/round01/publish.py','recipeManifest':'source/round01/recipe.json','verificationRecipe':'source/round01/verify.py','reproductionEvidence':'candidates/round01/reproduction.json','captureRecipe':'source/round01/publish.py','packagingRecipe':'source/round01/publish.py','preparationRecipe':'source/round01/prepare_sources.py','provenance':'source/round01/provenance.json','validation':rel(C/'validation.json'),'heroes':heroes,'rawFrames':raw_records,'atlases':atlases,'previews':previews,'resources':sorted(set(resource_list)),'source':{'pipeline':'imagegen-2d','artwork':'source/round01/dish-cucumber.png','sha256':sha(S/'dish-cucumber.png'),'rawArtwork':'source/round01/resources/fixed-target-raw.png','rawSHA256':sha(R/'fixed-target-raw.png'),'originalSource':'source/round01/resources/original-artwork.png','originalSourceSHA256':sha(R/'original-artwork.png'),'originalBackup':'source/round01/resources/original-backup.png','exactPrompt':'source/round01/resources/exact-imagegen-target-prompt.txt','modelScript':'source/round01/publish.py','canonicalCrop':{'box':list(box),'count':1,'interiorRGBAUnchanged':True,'publisherRecrops':False}},'dependencyDisclosure':recipe['dependencies'],'notes':'Exact fixed warm-soft target adopted as existing2D raster. Canonical project is sole lossless alpha>8 rectangle crop; fullraw bytes retained. No new generation or artistic pixel edit. Technical evidence only; independent judge review required. No downstream held or bubble recapture approval is claimed.'}
save_json(C/'delivery.json',delivery);save_json(O/'delivery.json',delivery)
print(json.dumps({'project':delivery['project'],'validation':delivery['validation'],'delivery':rel(C/'delivery.json'),'foodSize':food.size,'frameBounds':alpha.getbbox(),'componentsAlpha0':comps0,'componentsAlpha8':comps8,'sourceComponentsAlpha8':source_comps,'previews':len(previews)},indent=2))
