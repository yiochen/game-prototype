"""Uniform whole-canvas publication and deterministic coverage evidence."""
from pathlib import Path
import sys,json,hashlib,copy,shutil,math
from PIL import Image,ImageDraw,ImageChops,ImageStat
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,data):(OUT/name).write_text(json.dumps(data,indent=2)+'\n')
def rec(p,**kw):return {'path':p.relative_to(BASE).as_posix(),'sha256':sha(p),**kw}
data=json.loads((OUT/'native-validation.json').read_text());R=data['captureRecords'];assert len(R)==432
H=json.loads((OUT/'closure-hold-records.json').read_text())['captureRecords']
catalog=json.loads((BASE/'source/round-01-resources/inputs/catalog-object.json').read_text())
frames=[];atlases=[];raw=[];coverage=[];allphase=[]
colors=[(248,246,240,255),(136,142,146,255),(23,39,54,255)]
for clip in catalog['clips']:
    cid=clip['id'];sheet=Image.new('RGB',(12*192,4*376),(220,218,211));draw=ImageDraw.Draw(sheet)
    for row,d in enumerate(['N','E','S','W']):
        atlas=Image.new('RGBA',(2304,1408))
        for i in range(12):
            r=next(r for r in R if r['clip']==cid and r['direction']==d and r['index']==i);src=BASE/r['path'];assert sha(src)==r['sha256'];im=Image.open(src).convert('RGBA');assert im.size==(768,1408)
            pub=im.resize((384,704),Image.Resampling.LANCZOS);p=OUT/'frames'/cid/d/f'{i:03}.png';p.parent.mkdir(parents=True,exist_ok=True);pub.save(p)
            atlas.paste(pub,((i%6)*384,(i//6)*704));frames.append(rec(p,clip=cid,direction=d,index=i,dimensions=[384,704]));raw.append(rec(src,clip=cid,direction=d,index=i,dimensions=[768,1408]))
            logical=pub.resize((192,352),Image.Resampling.LANCZOS);bg=Image.new('RGBA',logical.size,colors[(row+i)%3]);bg.alpha_composite(logical);sheet.paste(bg.convert('RGB'),(i*192,row*376+24));draw.text((i*192+4,row*376+5),f'{cid} {d} phase{i}',fill=(22,39,53));coverage.append({'sheet':f'candidates/round-01/sheets/allphase-{cid}.png','rect':[i*192,row*376+24,192,352],'source':r['path'],'sourceSHA256':r['sha256'],'published':p.relative_to(BASE).as_posix(),'publishedSHA256':sha(p),'processing':'Full registered whole-canvas logical192x352, no fit/crop/warp. Presentation background only.'})
        ap=OUT/'atlases'/f'{cid}-{d}.png';ap.parent.mkdir(exist_ok=True);atlas.save(ap);rects=[[i%6*384,i//6*704,384,704] for i in range(12)]
        atlases.append(rec(ap,clip=cid,direction=d,columns=6,rows=2,size=[2304,1408],rects=rects))
        clip['directions'][d].update(image='../candidates/round-01/atlases/'+ap.name,frameSize=[192,352],root=[96,248],sourceScale=2,frames=12,columns=6,rows=2,atlasSize=[2304,1408],rects=rects)
        for i in range(12):assert atlas.crop((rects[i][0],rects[i][1],rects[i][0]+384,rects[i][1]+704)).tobytes()==Image.open(BASE/next(f['path'] for f in frames if f['clip']==cid and f['direction']==d and f['index']==i)).convert('RGBA').tobytes()
    sp=OUT/'sheets'/f'allphase-{cid}.png';sp.parent.mkdir(exist_ok=True);sheet.save(sp);allphase.append(rec(sp,clip=cid,coverage=48,logicalCell=[192,352]))
write('consumer-object.json',catalog)
write('frame-atlas-manifest.json',{'pathBase':'object-root','nativeRawFrames':raw,'rawFrames':frames,'atlases':atlases,'sampling':'One whole768x1408 native canvas to384x704 published canvas with Pillow LANCZOS; exact atlas cells without alpha/RGB processing.'})
write('sheets/coverage-map.json',coverage)
# All three rest variants/four facings at logical scale; separate phone .45 uses identical canvases.
for scale,name in [(1,'four-view-sheet'),(.45,'phone-family')]:
    w,h=round(192*scale),round(352*scale);canvas=Image.new('RGB',(w*4,(h+24)*3),(220,218,211));draw=ImageDraw.Draw(canvas)
    for row,clip in enumerate(['shimmer','b-shimmer','c-shimmer']):
        for col,d in enumerate(['N','E','S','W']):
            p=OUT/'frames'/clip/d/'000.png';im=Image.open(p).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);bg=Image.new('RGBA',im.size,colors[(row+col)%3]);bg.alpha_composite(im);canvas.paste(bg.convert('RGB'),(col*w,row*(h+24)+24));draw.text((col*w+3,row*(h+24)+5),f'{clip} {d}',fill=(22,39,53))
    canvas.save(OUT/'sheets'/f'{name}.png')
# Enlarged native registered full canvases of representatives; no source crop or occupied-bound fitting.
big=Image.new('RGB',(3*384,704+24),(136,142,146));bd=ImageDraw.Draw(big)
for col,clip in enumerate(['shimmer','b-shimmer','c-shimmer']):
    im=Image.open(OUT/'frames'/clip/'S/000.png').convert('RGBA');bg=Image.new('RGBA',im.size,colors[1]);bg.alpha_composite(im);big.paste(bg.convert('RGB'),(col*384,24));bd.text((col*384+5,5),clip+' S native /2',fill='white')
big.save(OUT/'sheets/representative-detail.png')
# True native closing/held frames decoded against submitted frames, not filenames.
timing=[]
def delta(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
for h in H:
    target=0 if not h['clip'].endswith('collect') else 11;r=next(r for r in R if r['clip']==h['clip'] and r['direction']==h['direction'] and r['index']==target)
    a=Image.open(BASE/h['path']).convert('RGBA');b=Image.open(BASE/r['path']).convert('RGBA');difference=ImageChops.difference(a,b);eq=a.tobytes()==b.tobytes();md=delta(h['motionMatrix'],r['motionMatrix']);assert md<1e-6,(h['clip'],h['direction'],h['sourceFrame'],md)
    changes=[(i%768,i//768,p) for i,p in enumerate(difference.getdata()) if any(p)]
    timing.append({'clip':h['clip'],'direction':h['direction'],'nativeFrame':h['sourceFrame'],'referenceIndex':target,'sameDecodedRGBA':eq,'decodedMaxRGBA':[v[1] for v in difference.getextrema()],'decodedMeanRGBA':ImageStat.Stat(difference).mean,'changedPixels':len(changes),'changedPixelBounds':None if not changes else [min(p[0] for p in changes),min(p[1] for p in changes),max(p[0] for p in changes)+1,max(p[1] for p in changes)+1],'first64ChangedPixelCoordinatesAndRGBA':changes[:64],'evaluatedBoundsMaxResidual':max(abs(h['bounds'][k][i]-r['bounds'][k][i]) for k in ['min','max'] for i in range(3)),'activeMeshNamesEqual':[o['name'] for o in h['activeMeshes']]==[o['name'] for o in r['activeMeshes']],'motionMatrixMaxResidual':md,'path':h['path'],'sha256':h['sha256'],'residualNote':'Unmodified EEVEE render; exact rigid native transform closure/hold. Frame-dependent AA sampling is a likely explanation for localized byte residuals, not a visible-boundary acceptance waiver; original judge assesses playback.'})
write('timing-validation.json',{'nativeClosuresAndHeldTerminals':timing,'all48RenderedAndCompared':len(timing),'note':'Six loops13=1. Three collect12=13=24. Published last unique slot12 is not forced equal slot1.'})
cam=json.loads((OUT/'native-camera.json').read_text());pubcam=copy.deepcopy(cam);pubcam['captureScale']=2;pubcam['nativeCaptureScale']=4;pubcam['nativeFrame']=[768,1408];pubcam['publishedFrame']=[384,704]
pubcam['calibration']={k:[x/2 for x in v] for k,v in cam['calibration'].items()};pubcam['publication']='Uniform whole authored4x to2x LANCZOS; no fit, crop, shift, recolor or alpha repair.';write('published-camera.json',pubcam)
asset=json.loads((BASE/'source/round-01-resources/inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']={'revision':'salvage-metal-round01','lighting':'Symmetric broad overhead110W plus four equal55W cardinal fills, neutral world.24; no ground plane or cast shadow.','material':'Native rounded steel/wood geometry, principled matte/soft sheen, no external textures.','colorManagement':'Standard/None/exposure0/gamma1','nativeFilter':'EEVEE32 samples,filter1.5,dither0'};asset['measuredNativeBoundsManifest']='candidates/round-01/native-validation.json';asset['nominalFunctionalHeightUnchanged']=.62;write('assetRecord.json',asset)
summary={'asset':'salvage-metal','status':'native measurement evidence; independent visual verdict pending','nativeValidation':'candidates/round-01/native-validation.json','timingValidation':'candidates/round-01/timing-validation.json','sourceSHA256':data['sourceSHA256'],'requiredPhaseSlots':432,'renderedPhaseSlots':len(R),'nativeFrame':[768,1408],'publishedFrame':[384,704],'minimumLoopGroundArea':min(r['finiteGroundArea'] for r in R if not r['clip'].endswith('collect')),'maxAttachmentResidual':max(r['attachmentMaxResidual'] for r in R),'maxRootPixelError':max(abs(r['camera']['calibration']['root'][i]-[384,992][i]) for r in R for i in range(2)),'publication':'Whole-canvas LANCZOS; every decoded atlas rect exactly equals declared published frame.','geometryBudgets':'Asserted from actual evaluated native vertices everyphase at capturetime; rest ±.45/Z0–.70, collect±.45/Z0–1.30. No belowground/clipping.','views':[{'direction':d,'rootRotationDegrees':{'N':180,'E':90,'S':0,'W':-90}[d],'rootMatrix':next(r['rootMatrix'] for r in R if r['direction']==d)} for d in ['N','E','S','W']]};write('validation.json',summary)
# Freeze actual imported Pillow modules only, without copying a runtime tree.
closure=[];dest=BASE/'source/round-01-resources/python-modules'
for name,module in list(sys.modules.items()):
    f=getattr(module,'__file__',None)
    if name.startswith('PIL') and f and Path(f).is_file():
        src=Path(f).resolve();rel=Path(*name.split('.'));rel=(rel if hasattr(module,'__path__') else rel.parent)/src.name;t=dest/rel;t.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,t);closure.append({'module':name,'path':t.relative_to(BASE).as_posix(),'sha256':sha(t),'originalPath':str(src)})
write('python-module-closure.json',{'runtime':sys.executable,'version':sys.version,'files':closure})
print('PUBLISHED_ALL432',len(frames),len(atlases),'timing',len(timing))
