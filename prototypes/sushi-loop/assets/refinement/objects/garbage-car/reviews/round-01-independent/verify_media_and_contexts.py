from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,hashlib,numpy as np
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-car');C=P/'candidates/round-01';O=P/'reviews/round-01-independent';R=P/'source/resources/context'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def back(im,size,color='f5f2e9'):
 out=Image.new('RGBA',size,'#'+color);out.alpha_composite(im.resize(size,Image.Resampling.LANCZOS));return out.convert('RGB')
def raw(clip,d,i):return Image.open(C/f'frames/{clip}-{d}/{i:03d}.png').convert('RGBA')
videos=[]
for clip in ['highlighted','clearance']:
 for d in ['N','E','S','W']:
  p=C/f'previews/{clip}-{d}-12fps.mp4';probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,avg_frame_rate,nb_frames,width,height,duration','-of','json',str(p)]))['streams'][0]
  expected=[back(raw(clip,d,i),(576,832)) for i in range(12)];order=list(range(12))
  if clip=='clearance':expected+=([expected[-1]]*12)+[Image.new('RGB',(576,832),'#f5f2e9')]*12;order+=[11]*12+[None]*12
  ap=C/f'previews/{clip}-{d}-12fps.png';im=Image.open(ap);apng=[]
  for i,e in enumerate(expected):im.seek(i);apng.append({'index':i,'durationMilliseconds':im.info.get('duration'),'exactExpectedRGB':im.convert('RGB').tobytes()==e.tobytes()})
  decoded=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','-']);frames=np.frombuffer(decoded,dtype=np.uint8).reshape((-1,832,576,3));errors=[float(np.abs(v.astype(float)-np.asarray(e).astype(float)).mean()) for v,e in zip(frames,expected)]
  videos.append({'path':str(p.relative_to(P)),'sha256':sha(p),'ffprobe':probe,'decodedFrameCount':len(frames),'frameOrder':order,'frameRGBMAEvsNativeComposite':errors,'APNG':str(ap.relative_to(P)),'APNGFrames':im.n_frames,'APNGExactCompositeChecks':apng})
floor=Image.open(R/'floor-cream-static-S.png').convert('RGBA');human=Image.open(R/'chef-lena-idle-S.png').convert('RGBA').crop((0,0,384,640))
def grid(cells,pitch):
 origin=(pitch,pitch*4);im=Image.new('RGBA',((cells[0]+2)*pitch,(cells[1]+5)*pitch),'#f5f2e9');f=floor.resize((pitch,pitch),Image.Resampling.LANCZOS)
 for y in range(cells[1]):
  for x in range(cells[0]):im.alpha_composite(f,(origin[0]+x*pitch,origin[1]+y*pitch))
 return im,origin
def place(dst,img,point,anchor,pitch):
 factor=pitch/256;img=img.resize((round(img.width*factor),round(img.height*factor)),Image.Resampling.LANCZOS);dest=(round(pitch+point[0]*pitch-anchor[0]*pitch/128),round(4*pitch+point[1]*pitch-anchor[1]*pitch/128));dst.alpha_composite(img,dest)
def check(path,im):
 actual=Image.open(path).convert('RGB');checks.append({'path':str(path.relative_to(P)),'sha256':sha(path),'exactReproducedRGB':actual.tobytes()==im.convert('RGB').tobytes()})
for pitch in [128,55]:
 for d in ['N','E','S','W']:
  im,_=grid((6,3),pitch);point=(1.5,1) if d in ['N','S'] else (1,1.5);place(im,raw('idle',d,0),point,(288,544),pitch);place(im,human,(4.5,.5),(96,248),pitch);check(C/f'previews/human-{d}-cell{pitch}.png',im)
 im,_=grid((8,6),pitch)
 for x,y in [(0,0),(4,0),(0,3)]:place(im,raw('idle','S',0),(x+1.5,y+1),(288,544),pitch)
 check(C/f'previews/repeated-cell{pitch}.png',im)
for d in ['N','E','S','W']:
 for i in range(12):
  im,_=grid((6,3),128);point=(1.5,1) if d in ['N','S'] else (1,1.5);place(im,raw('clearance',d,i),point,(288,544),128);check(C/f'previews/floor-reveal/{d}-{i:02d}.png',im)
 removed,_=grid((6,3),128);check(C/f'previews/floor-reveal/{d}-postclip-removed.png',removed)
closure=Image.new('RGB',(4*288,2*440),'#808080');draw=ImageDraw.Draw(closure)
for j,d in enumerate(['N','E','S','W']):
 for k,(desc,path) in enumerate([('highlighted first',C/f'frames/highlighted-{d}/000.png'),('highlighted key13',C/f'diagnostics/highlighted-{d}-key13.png')]):
  im=Image.open(path).convert('RGBA').resize((288,416),Image.Resampling.LANCZOS);closure.paste(im,(288*j,440*k+24),im);draw.text((288*j+4,440*k+5),desc+' '+d,fill='white')
closure.save(O/'key13-comparison.png')
result={'videos':videos,'contexts':checks,'contextFailureCount':sum(not x['exactReproducedRGB'] for x in checks),'APNGFailureCount':sum(not x['exactExpectedRGB'] for v in videos for x in v['APNGExactCompositeChecks']),'contextResourceHashes':{p.name:sha(p) for p in R.glob('*') if p.is_file()},'noPixelIdentityAssumedBetweenIndependentNativeRenders':True}
(O/'media-context-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('video/APNG pairs',len(videos),'contexts',len(checks),'contextfailures',result['contextFailureCount'],'APNGfailures',result['APNGFailureCount'],'maxVideoMAE',max(max(v['frameRGBMAEvsNativeComposite']) for v in videos))
