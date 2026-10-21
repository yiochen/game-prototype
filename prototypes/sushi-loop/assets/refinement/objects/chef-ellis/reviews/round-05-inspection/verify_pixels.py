from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageColor
obj=Path.cwd()/'prototypes/sushi-loop/assets/refinement/objects/chef-ellis';p=obj/'candidates/round-05';out=obj/'reviews/round-05-inspection';d=json.loads((p/'delivery.snapshot.json').read_text());bad=[];cellCount=0;bodyDelta=[]
for a in d['atlases']:
 im=Image.open(obj/a['path']).convert('RGBA')
 for i,r in enumerate(a['rects']):
  f=Image.open(p/'frames'/f"{a['clip']}-{a['direction']}"/f'{i:03}.png').convert('RGBA');x,y,w,h=r
  if im.crop((x,y,x+w,y+h)).tobytes()!=f.tobytes():bad.append(['atlas',a['clip'],a['direction'],i])
  for bg,code in {'light':'#f5f4ed','gray':'#9a9e9b','dark':'#263238'}.items():
   ss=Image.open(p/'contact-sheets'/f"{a['clip']}-{a['direction']}-{bg}.png").convert('RGB');small=f.resize((192,320),Image.Resampling.LANCZOS);comp=Image.new('RGBA',small.size,ImageColor.getrgb(code)+(255,));comp.alpha_composite(small);crop=ss.crop((i%6*192,i//6*352+30,i%6*192+192,i//6*352+350))
   if crop.tobytes()!=comp.convert('RGB').tobytes():bad.append(['sheet',a['clip'],a['direction'],i,bg])
   cellCount+=1
  if a['clip'] in ['idle','work']:
   b=Image.open(obj/'candidates/round-04/frames'/f"{a['clip']}-{a['direction']}"/f'{i:03}.png').convert('RGBA');diff=np.abs(np.asarray(f,dtype=int)-np.asarray(b,dtype=int));bodyDelta.append({'clip':a['clip'],'direction':a['direction'],'index':i,'maxRGBA':int(diff.max()),'changedPixels':int(np.count_nonzero(np.any(diff,axis=2)))})
packet=json.loads((p/'packet.json').read_text());aggs=[]
for clip in ['idle','work','hold']:
 ims=[Image.open(p/packet['previews'][f'closure-{clip}-{dr}']['path']).convert('RGB') for dr in ['N','E','S','W']];ss=Image.new('RGB',(1152,704))
 for i,im in enumerate(ims):ss.paste(im,(i%2*576,i//2*352))
 q=out/f'closures-{clip}.png';ss.save(q);aggs.append({'path':str(q),'sourcePaths':[packet['previews'][f'closure-{clip}-{dr}']['path'] for dr in ['N','E','S','W']]})
closure=[]
for row in json.loads((p/'complete-validation.json').read_text())['closureValidation']:
 a=np.asarray(Image.open(obj/row['path']).convert('RGBA'),dtype=int);b=np.asarray(Image.open(p/'frames'/f"{row['clip']}-{row['direction']}"/'000.png').convert('RGBA'),dtype=int);diff=np.abs(a-b);closure.append({'clip':row['clip'],'direction':row['direction'],'maxRGBA':int(diff.max()),'pixels':int(np.count_nonzero(np.any(diff,axis=2)))})
vid=[]
for clip in ['idle','work','hold','load']:
 for dr in ['N','E','S','W']:
  path=p/'playbacks'/f'{clip}-{dr}.mp4';probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_frames,duration','-of','json',str(path)]))['streams'][0];raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-f','rawvideo','-pix_fmt','rgb24','-']);a=np.frombuffer(raw,np.uint8).reshape(-1,640,384,3);means=[]
  for i,fr in enumerate(a):
   im=Image.open(p/'frames'/f'{clip}-{dr}'/f'{i:03}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(154,158,155,255));bg.alpha_composite(im);means.append(float(np.abs(fr.astype(float)-np.asarray(bg.convert('RGB'),dtype=float)).mean()))
  vid.append({'path':str(path.relative_to(p)),'probe':probe,'decodedFrames':len(a),'meanRGBErrorPerIndexedFrame':means})
r={'atlasComparisons':192,'sheetCellComparisons':cellCount,'failures':bad,'idleWorkBodyPixelParity':bodyDelta,'closurePixels':closure,'closureAggregates':aggs,'videos':vid};(out/'pixel-verification.json').write_text(json.dumps(r,indent=2)+'\n');print('Pixels',192,cellCount,'failures',bad,'unchangedbodymax',max(x['maxRGBA'] for x in bodyDelta),'closuremax',max(x['maxRGBA'] for x in closure),'videos',len(vid))
