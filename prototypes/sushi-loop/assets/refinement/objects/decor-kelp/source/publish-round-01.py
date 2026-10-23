"""Whole-canvas publication and compact readable evidence, never fitted or repaired."""
from pathlib import Path
import json,hashlib,struct,zlib,sys,shutil,subprocess
import PIL
from PIL import Image,ImageDraw,ImageChops,ImageSequence
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;OUT=OBJ/'candidates/round-01';RES=BASE/'round-01-resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists(),str(p);p.write_text(json.dumps(d,indent=2)+'\n')
dirs=['N','E','S','W'];frames={};raw=[];native=[];atlases=[];reduction=[];closures=[]
for d in dirs:
    fs=[]
    for i in range(12):
        src=OUT/'native/idle'/d/f'{i:03d}.png';dst=OUT/'frames/idle'/d/f'{i:03d}.png';dst.parent.mkdir(parents=True,exist_ok=True)
        im=Image.open(src).convert('RGBA');assert im.size==(768,1920)
        small=im.resize((384,960),Image.Resampling.LANCZOS);small.save(dst);fs.append(small)
        native.append({'clip':'idle','direction':d,'index':i,'path':str(src.relative_to(OBJ))})
        raw.append({'clip':'idle','direction':d,'index':i,'path':str(dst.relative_to(OBJ))})
        reduction.append({'source':str(src.relative_to(OBJ)),'sourceSHA256':sha(src),'published':str(dst.relative_to(OBJ)),'publishedSHA256':sha(dst),'uniformCanvasLANCZOS':True,'dimensions':[[768,1920],[384,960]]})
    frames[d]=fs
    atlas=Image.new('RGBA',(2304,1920));rects=[]
    for i,im in enumerate(fs):
        x=i%6*384;y=i//6*960;atlas.paste(im,(x,y));rects.append([x,y,384,960])
    dst=OUT/'atlases'/f'idle-{d}.png';dst.parent.mkdir(exist_ok=True);atlas.save(dst)
    atlases.append({'clip':'idle','direction':d,'path':str(dst.relative_to(OBJ)),'columns':6,'rows':2,'size':[2304,1920],'rects':rects,'sha256':sha(dst)})
    close=Image.open(OUT/'native-closure/idle'/d/'012.png').convert('RGBA')
    first=Image.open(OUT/'native/idle'/d/'000.png').convert('RGBA')
    delta=ImageChops.difference(first,close);closures.append({'direction':d,'nativeClosingFrame13':True,'decodedDifferentChannels':sum(v!=0 for v in delta.tobytes()),'maximumChannelDelta':max(delta.tobytes())})

def sheet(path,ims,cols,scale=1,bg=(37,62,66,255),labels=None):
    w,h=ims[0].size;rows=(len(ims)+cols-1)//cols;bar=20 if labels else 0
    out=Image.new('RGBA',(w*cols,(h+bar)*rows),bg);dr=ImageDraw.Draw(out)
    for i,im in enumerate(ims):
        x=i%cols*w;y=i//cols*(h+bar)
        out.alpha_composite(im,(x,y+bar))
        if labels:dr.text((x+4,y+3),labels[i],fill='white')
    out.save(path);return out

sheet(OUT/'four-view-sheet.png',[frames[d][0]for d in dirs],4,labels=dirs)
sheet(OUT/'native-four-view-sheet.png',[Image.open(OUT/'native/idle'/d/'000.png').convert('RGBA')for d in dirs],4,labels=dirs)
logical=[frames[d][0].resize((192,480),Image.Resampling.LANCZOS)for d in dirs]
backgrounds=[('#ecebdc','light'),('#808986','gray'),('#162b30','dark')]
bg_sheet=Image.new('RGBA',(768,1500));draw=ImageDraw.Draw(bg_sheet)
for row,(color,label) in enumerate(backgrounds):
    for col,(d,im) in enumerate(zip(dirs,logical)):
        tile=Image.new('RGBA',(192,500),color);tile.alpha_composite(im,(0,20));ImageDraw.Draw(tile).text((4,3),d+' '+label,fill='black' if row==0 else 'white');bg_sheet.paste(tile,(col*192,row*500))
bg_sheet.save(OUT/'logical-backgrounds.png')
for d in dirs:sheet(OUT/f'phases-{d}.png',[im.resize((192,480),Image.Resampling.LANCZOS)for im in frames[d]],6,labels=[d+' '+str(i)for i in range(12)])
sheet(OUT/'closure-sheet.png',[frames[d][i]for d in dirs for i in [11,0]]+[Image.open(OUT/'native-closure/idle'/d/'012.png').convert('RGBA').resize((384,960),Image.Resampling.LANCZOS)for d in dirs],4,labels=[d+' last unique'for d in dirs for _ in []] or [d+' '+('last unique' if i==11 else 'first')for d in dirs for i in [11,0]]+[d+' closure13'for d in dirs])

# Exact RGBA animated PNG, delay1/12 rather than centisecond-rounded GIF timing.
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def apng(path,ims):
    w,h=ims[0].size;data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'acTL',struct.pack('>II',len(ims),0));seq=0
    for i,im in enumerate(ims):
        data+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',seq,w,h,0,0,1,12,0,0));seq+=1
        raw=im.tobytes();packed=zlib.compress(b''.join(b'\0'+raw[y*w*4:(y+1)*w*4]for y in range(h)),6)
        if i==0:data+=chunk(b'IDAT',packed)
        else:data+=chunk(b'fdAT',struct.pack('>I',seq)+packed);seq+=1
    data+=chunk(b'IEND',b'');path.write_bytes(data)
playbacks=[]
for d in dirs:
    path=OUT/f'idle-{d}.png';apng(path,frames[d]);check=Image.open(path);assert check.n_frames==12
    for i in range(12):check.seek(i);assert check.convert('RGBA').tobytes()==frames[d][i].tobytes()
    playbacks.append({'direction':d,'path':str(path.relative_to(OBJ)),'format':'lossless RGBA APNG','frames':12,'frameDelay':[1,12],'seconds':1,'decodedFramesExactPublishedBytes':True})

# Registered integer native-grid 3x3 scenery density; whole composition reduction only.
repeat=Image.new('RGBA',(896,1472),'#168599')
for y in range(3):
    for x in range(3):repeat.alpha_composite(frames['S'][0],(x*256,y*256))
repeat.resize((448,736),Image.Resampling.LANCZOS).save(OUT/'repeated.png')

ledger=json.loads((OUT/'native-validation.json').read_text());camera=ledger['nativeCamera']
published=json.loads(json.dumps(camera));published.update(captureScale=2,nativeFrame=[768,1920],publishedFrame=[384,960],nativeCaptureScale=4,projection='height-dependent-35-square-footing')
published['calibration']={k:[v/2 for v in vec]for k,vec in camera['calibration'].items()}
published['nativeMeasurement']=camera
published['normalization']='Uniform entire native4x canvas LANCZOS reduction to published2x; source float error retained, no root nudge.'
write(OUT/'published-camera.json',published)
write(OUT/'assetRecord.json',{'id':'decor-kelp','scene':'S33 Native Asset Library Export','collection':'S33 production concept kelp-fan','root':'S33 production concept kelp-fan root','frame':[192,480],'anchor':[96,384],'scale':2,'projection':'height-dependent-35-square-footing','footprint':[1,1],'heightBudget':2.12,'role':'nonblocking layer2 scenery','artStyle':'Warm softly lit cartoon','sourceSHA256':sha(BASE/'round-01.blend'),'construction':json.loads((BASE/'round-01-construction.json').read_text())})
shutil.copy2(BASE/'round-01-rig.json',OUT/'rig.json')
write(OUT/'publication-proof.json',{'method':'Uniform entire native4x canvas LANCZOS to2x; exact lossless atlas placement; no crop/fit/warp/alpha or RGB repair. Preview-only logical sheets use uniform LANCZOS, background composites preserve actual transparent frame; published frames remain unchanged.','frames':reduction,'closurePixels':closures,'playbacks':playbacks,'repeatedPlacement':{'native2xCanvas':[896,1472],'commonFrame':[384,960],'groundRoot':[192,768],'gridRootPitch':[256,256],'placements':'x,y=0..2 each; S frame0; row-major painter order','previewWholeCanvasReduction':[448,736]}})
write(OUT/'frame-delivery.json',{'rawFrames':raw,'nativeRawFrames':native,'atlases':atlases,'playbacks':playbacks})

# Freeze actual imported Pillow modules and native dependency closure, not a runtime tree.
files=[];native_libs=[];pillow_root=Path(PIL.__file__).parent.parent
for name,module in list(sys.modules.items()):
    p=getattr(module,'__file__',None)
    if p and name.startswith('PIL') and Path(p).suffix!='.pyc' and Path(p).is_file():
        p=Path(p);dst=RES/'python-modules-used'/p.relative_to(pillow_root);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);files.append(str(dst.relative_to(OBJ)))
        if p.suffix=='.so':native_libs.append(p)
visited=set()
while native_libs:
    p=native_libs.pop()
    if p in visited:continue
    visited.add(p)
    for line in subprocess.check_output(['otool','-L',str(p)],text=True).splitlines()[1:]:
        dep=line.strip().split(' (')[0]
        if dep.startswith('@loader_path/'):
            source=(p.parent/dep[len('@loader_path/'):]).resolve()
            if source.is_file():
                dst=RES/'python-modules-used'/source.relative_to(pillow_root);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst);files.append(str(dst.relative_to(OBJ)));native_libs.append(source)
write(OUT/'python-module-closure.json',{'python':sys.version,'executable':sys.executable,'Pillow':PIL.__version__,'method':'Actual imported Pillow modules for PNG/APNG read/write, whole resize, composition/drawing and decoded frame differences; recursive @loader_path native dependency closure; stdlib/system/executable external.','files':[{'path':p,'sha256':sha(OBJ/p)}for p in sorted(set(files))]})
print('KELP_PUBLICATION_COMPLETE',len(raw),'frames',len(playbacks),'lossless exact12fps playbacks')
