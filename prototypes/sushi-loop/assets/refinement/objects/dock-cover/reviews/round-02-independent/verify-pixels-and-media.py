from pathlib import Path
import hashlib,json,subprocess,math
import numpy as np
from PIL import Image,ImageDraw
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-cover');C=O/'candidates/round-02';R=O/'reviews/round-02-independent';P=json.loads((C/'packet.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cache={};records=[]
for group in ['files','candidateRenders','previews']:
 for alias,r in P[group].items():
  p=(C/r['path']).resolve()
  if p not in cache:cache[p]=sha(p)
  assert cache[p]==r['sha256'],(group,alias,p)
  records.append({'group':group,'alias':alias,'path':str(p.relative_to(O))if p.is_relative_to(O)else str(p),'sha256':cache[p]})
(R/'packet-hash-check.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'records':records,'uniqueFiles':len(cache),'allMatch':True},indent=2)+'\n')
raw=[]
for cl in ['covered','uncover']:
 for d in 'NESW':
  sh=Image.new('RGB',(4*368,3*376),(128,128,128));a=Image.open(C/'atlases'/f'{cl}-{d}.png').convert('RGBA');assert a.size==(7360,4224)
  for i in range(12):
   p=C/'frames'/f'{cl}-{d}'/f'{i:03d}.png';im=Image.open(p).convert('RGBA');assert im.size==(1472,1408);q=a.crop((i%5*1472,i//5*1408,i%5*1472+1472,i//5*1408+1408));assert q.tobytes()==im.tobytes();bg=Image.new('RGBA',im.size,(128,128,128,255));bg.alpha_composite(im);sh.paste(bg.convert('RGB').resize((368,352),Image.Resampling.LANCZOS),((i%4)*368,(i//4)*376+24));ImageDraw.Draw(sh).text(((i%4)*368+8,(i//4)*376+5),f'{cl}-{d} {i}',fill='white');raw.append({'path':str(p.relative_to(O)),'sha256':sha(p),'atlasCropExactRGBA':True,'decodedRGBASHA256':hashlib.sha256(im.tobytes()).hexdigest()})
  for i in [12,13,14]:assert a.crop((i%5*1472,i//5*1408,i%5*1472+1472,i//5*1408+1408)).getbbox()is None
  sh.save(R/f'all12-{cl}-{d}.png')
replay=json.loads((R/'native-independent.json').read_text())
for v in replay['replays']:
 a=Image.open(O/v['path']).convert('RGBA');b=Image.open(O/v['reference']).convert('RGBA');v['exactDecodedRGBA']=a.tobytes()==b.tobytes();v['maximumRGBAChannelDifference']=int(np.max(np.abs(np.asarray(a).astype(int)-np.asarray(b).astype(int))));assert v['exactDecodedRGBA']
(R/'native-replay-pixel-comparison.json').write_text(json.dumps({'sourceSHA256':replay['sourceSHA256'],'replays':replay['replays']},indent=2)+'\n')
media=[]
for alias,ref in P['previews'].items():
 p=C/ref['path']
 if p.suffix!='.mp4':continue
 probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]));s=probe['streams'][0];w,h=s['width'],s['height'];assert s['avg_frame_rate']=='12/1'and int(s['nb_frames'])==48
 proc=subprocess.Popen(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(p),'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE);frames=[];rows=[];tw,th=(184,176)if w==736 else(256,272);sh=Image.new('RGB',(4*tw,12*(th+18)),(100,100,100))
 for i in range(48):
  data=proc.stdout.read(w*h*3);assert len(data)==w*h*3;im=Image.frombytes('RGB',(w,h),data);frames.append(im);sh.paste(im.resize((tw,th),Image.Resampling.LANCZOS),((i%4)*tw,(i//4)*(th+18)+18));ImageDraw.Draw(sh).text(((i%4)*tw+4,(i//4)*(th+18)+2),str(i),fill='white');expected=i%12 if 'covered' in alias else min(i,11);q=np.asarray(frames[expected]).astype(int);delta=np.abs(np.asarray(im).astype(int)-q);rows.append({'index':i,'timeSeconds':i/12,'expectedSourceIndex':expected,'decodedRGBSHA256':hashlib.sha256(data).hexdigest(),'repeatReferenceMeanAbsRGB':float(delta.mean()),'repeatReferenceMaxAbsRGB':int(delta.max())})
 assert proc.wait()==0
 dest=R/f'movie-all48-{alias}.png';sh.save(dest)
 if w!=736:
  for start in [0,6]:
   sheet=Image.new('RGB',(3*640,2*704),(100,100,100))
   for j,im in enumerate(frames[start:start+6]):sheet.paste(im.resize((640,680),Image.Resampling.LANCZOS),((j%3)*640,(j//3)*704+24));ImageDraw.Draw(sheet).text(((j%3)*640+8,(j//3)*704+6),f'{alias} frame {start+j}',fill='white')
   sheet.save(R/f'movie-first12-{alias}-{start:02d}.png')
 media.append({'alias':alias,'path':ref['path'],'sha256':sha(p),'probe':{k:s[k]for k in ['width','height','avg_frame_rate','nb_frames','duration']},'all48FrameContactSheet':str(dest.relative_to(O)),'frames':rows})
(R/'pixel-and-media-evidence.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'rawFrames':raw,'media':media,'aliasMapping':{'previews/human-uncover-12.png':['human-approach','terminal-reveal']},'decodedEveryMovieFrame':True,'allRawAtlasCropsAndUnusedSlotsPass':True},indent=2)+'\n')
print('PASS',len(cache),'packet files',len(raw),'exact raw/atlas crops',len(media),'movies/480 decoded frames; replay2 exactRGBA')
