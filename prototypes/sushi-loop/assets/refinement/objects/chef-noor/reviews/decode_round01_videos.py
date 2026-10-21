from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,numpy as np
b=Path('prototypes/sushi-loop/assets/refinement/objects/chef-noor');c=b/'candidates/round-01';out=b/'reviews';p=json.loads((c/'packet.json').read_text());report=[]
allc=Image.new('RGB',(1536,8*184),'#efebe1');dc=ImageDraw.Draw(allc);mid=Image.new('RGB',(1024,688),'#efebe1');dm=ImageDraw.Draw(mid);contextrow=0
for name,r in p['previews'].items():
 if not r['path'].endswith('.mp4'):continue
 f=c/r['path'];probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_entries','stream=width,height','-of','json',str(f)]));w=probe['streams'][0]['width'];h=probe['streams'][0]['height']
 data=subprocess.check_output(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(f),'-f','rawvideo','-pix_fmt','rgb24','-']);a=np.frombuffer(data,dtype=np.uint8).reshape((-1,h,w,3));rec={'path':r['path'],'decodedFrameCount':len(a),'size':[w,h]};assert len(a)==12
 if r['path'].startswith('playback/'):
  ident=Path(r['path']).stem;errs=[]
  for i,frame in enumerate(a):
   im=Image.open(c/'frames'/ident/f'{i:03d}.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);flat=Image.new('RGBA',im.size,'#7c7c7c');flat.alpha_composite(im);q=np.asarray(flat.convert('RGB'));errs.append(float(np.mean(np.abs(frame.astype(float)-q.astype(float)))))
  rec['frameMeanAbsoluteRGBDifferencesToNativeComposite']=errs
 else:
  row=contextrow;contextrow+=1
  for i,frame in enumerate(a):
   im=Image.fromarray(frame);allc.paste(im.resize((128,160),Image.Resampling.LANCZOS),(i*128,row*184+24));dc.text((i*128+2,row*184+3),f'{name} {i}',fill='#1D2430')
  d=name[-1];col=['N','E','S','W'].index(d);row=0 if name.startswith('source') else 1;mid.paste(Image.fromarray(a[5]).resize((256,320),Image.Resampling.LANCZOS),(col*256,row*344+24));dm.text((col*256+3,row*344+4),name+' frame5',fill='#1D2430')
 report.append(rec)
allc.save(out/'round01-contexts-decoded-allframes.png');mid.save(out/'round01-contexts-decoded-frame5.png');(out/'round01-video-decoding.json').write_text(json.dumps(report,indent=2)+'\n');print('decoded',len(report),'videos; max native video mean RGB error',max(max(r.get('frameMeanAbsoluteRGBDifferencesToNativeComposite',[0])) for r in report))
