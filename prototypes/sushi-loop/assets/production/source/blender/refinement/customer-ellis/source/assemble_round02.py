"""Whole-frame atlas assembly and honest temporal/context review evidence."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json,hashlib,subprocess,concurrent.futures,shutil
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-02'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
brief=json.loads((OBJ/'brief.json').read_text());clips=brief['delivery']['requiredClips']
runtimeRec=json.loads((HERE/'resources/runtime-rig.json').read_text())
runtime=[{'id':k,'sourceClipId':k,'frames':12,'fps':12,'loop':v['loop'],'frameOrder':list(range(12))} for k,v in runtimeRec['clips'].items()]
font=ImageFont.load_default(size=16)
evidence={'frames':[],'atlases':[],'clips':[],'contexts':[],'registration':{'nativeFrame':[384,640],'logicalFrame':[192,320],'root':[96,248],'sourceScale':2,'atlasLayout':[6,2],'atlasSize':[2304,1280]},'alphaFailures':[],'atlasCopyFailures':[]}
jobs=[];viewer=[]
for mode,records,folder in [('main',clips,'frames'),('runtime',runtime,'runtime-frames')]:
 for c in records:
  item={'id':c['id'],'sourceClipId':c['sourceClipId'],'frames':12,'fps':12,'loop':c['loop'],'directions':{}}
  for direction in 'NESW':
   name=c['id']+'-'+direction;frames=[OUT/folder/name/f'{i:03}.png' for i in range(12)]
   assert all(p.is_file() for p in frames),(name,'missing frame')
   atlas=Image.new('RGBA',(2304,1280));sheet=Image.new('RGB',(1152,680),(235,231,221));draw=ImageDraw.Draw(sheet);draw.text((8,8),name+' | all 12 native frames at logical size; 12 fps',fill=(32,38,45),font=font)
   for i,p in enumerate(frames):
    im=Image.open(p).convert('RGBA');assert im.size==(384,640)
    atlas.paste(im,((i%6)*384,(i//6)*640))
    logical=im.resize((192,320),Image.Resampling.LANCZOS);sheet.paste(logical,((i%6)*192,32+(i//6)*320),logical)
    alpha=im.getchannel('A');box=alpha.getbbox();edges=[alpha.crop((0,0,384,1)).getextrema()[1],alpha.crop((0,639,384,640)).getextrema()[1],alpha.crop((0,0,1,640)).getextrema()[1],alpha.crop((383,0,384,640)).getextrema()[1]]
    if any(edges):evidence['alphaFailures'].append({'frame':str(p.relative_to(OBJ)),'edgeMaximum':edges})
    evidence['frames'].append({'mode':mode,'path':str(p.relative_to(OBJ)),'sha256':sha(p),'alphaBounds':box})
   ap=OUT/('atlases' if mode=='main' else 'runtime-atlases')/(name+'.png');ap.parent.mkdir(exist_ok=True);atlas.save(ap,compress_level=6)
   for i,p in enumerate(frames):
    crop=atlas.crop(((i%6)*384,(i//6)*640,(i%6+1)*384,(i//6+1)*640))
    if crop.tobytes()!=Image.open(p).convert('RGBA').tobytes():evidence['atlasCopyFailures'].append(str(p))
   sp=OUT/'contact-sheets'/(name+'.png');sp.parent.mkdir(exist_ok=True);sheet.save(sp)
   vp=OUT/'playback'/(name+'.webm');vp.parent.mkdir(exist_ok=True)
   jobs.append((frames[0].parent,vp,c,direction,mode))
   evidence['atlases'].append({'mode':mode,'id':c['id'],'direction':direction,'path':str(ap.relative_to(OBJ)),'sha256':sha(ap),'wholeFrameExactPixelCopies':True,'columns':6,'rows':2,'rects':[[i%6*384,i//6*640,384,640] for i in range(12)]})
   item['directions'][direction]={'atlas':str(ap.relative_to(OUT)),'video':str(vp.relative_to(OUT)),'sheet':str(sp.relative_to(OUT))}
  viewer.append(item)
def encode(job):
 src,dst,c,direction,mode=job
 cmd=['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','12','-i',str(src/'%03d.png'),'-frames:v','12','-c:v','libvpx-vp9','-lossless','1','-pix_fmt','yuva420p','-auto-alt-ref','0','-threads','2',str(dst)]
 subprocess.run(cmd,check=True)
 info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dst)],text=True))
 stream=info['streams'][0];assert stream['r_frame_rate']=='12/1',stream
 return {'mode':mode,'id':c['id'],'direction':direction,'path':str(dst.relative_to(OBJ)),'sha256':sha(dst),'frameCount':12,'fps':'12/1','duration':info['format']['duration'],'loop':c['loop'],'codec':'VP9 alpha WebM','ffprobe':info}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:evidence['clips']=list(ex.map(encode,jobs))
# Four facings, registered full canvases, on all three backgrounds.
for background,color in [('light',(245,240,226)),('gray',(128,128,128)),('dark',(28,34,42))]:
 canvas=Image.new('RGB',(768,680),color);d=ImageDraw.Draw(canvas);d.text((12,8),'Ellis stand | '+background+' | native full frame at logical size',font=font,fill=(220,220,220) if background=='dark' else (20,30,40))
 for i,direction in enumerate('NESW'):
  im=Image.open(OUT/'frames'/('stand-'+direction)/'004.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);canvas.paste(im,(i*192,32),im)
  im=Image.open(OUT/'frames'/('eat-'+direction)/'004.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);canvas.paste(im,(i*192,352),im)
 p=OUT/(background+'-background.png');canvas.save(p);evidence['contexts'].append({'type':'background','path':str(p.relative_to(OBJ)),'sha256':sha(p)})
# Independent sprite composition, sharing the exact logical ground root.
for c,folder in [('seated-wait','frames'),('eat','frames'),('eat-salmon','runtime-frames'),('seated-wait-empty','runtime-frames')]:
 canvas=Image.new('RGB',(768,392),(237,228,208));d=ImageDraw.Draw(canvas);d.text((10,8),c+' | independently registered stool + actor | root (96,248)',font=font,fill=(25,35,45))
 for i,direction in enumerate('NESW'):
  stool=Image.open(HERE/'resources/context'/('stool-wood-'+direction+'.png')).convert('RGBA').resize((192,352),Image.Resampling.LANCZOS)
  actor=Image.open(OUT/folder/(c+'-'+direction)/'004.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS)
  canvas.paste(stool,(i*192,32),stool);canvas.paste(actor,(i*192,32),actor)
 p=OUT/(c+'-stool-context.png');canvas.save(p);evidence['contexts'].append({'type':'registered-stool','path':str(p.relative_to(OBJ)),'sha256':sha(p),'root':[96,248],'perViewFitting':False})
(OUT/'viewer-data.json').write_text(json.dumps(viewer,indent=2)+'\n')
(OUT/'export-validation.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('ELLIS_ASSEMBLY_COMPLETE',len(evidence['frames']),len(evidence['atlases']),len(evidence['clips']),'edge failures',len(evidence['alphaFailures']),'copies',len(evidence['atlasCopyFailures']),flush=True)
