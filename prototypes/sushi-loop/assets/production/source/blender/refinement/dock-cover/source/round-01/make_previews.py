from pathlib import Path
import json,hashlib,subprocess
from PIL import Image,ImageDraw,ImageChops
H=Path(__file__).resolve().parent;O=H.parents[1];OUT=O/'candidates/round-01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();a=json.load(open(OUT/'native-phase-audit.json'));records=[];raw=[];previews=[]
for clip in ['covered','uncover']:
 for d in ['N','E','S','W']:
  atlas=Image.new('RGBA',(7360,4224));r=[];pv=OUT/'playback-frames'/f'{clip}-{d}';pv.mkdir(parents=True,exist_ok=True)
  for i in range(12):
   path=OUT/'frames'/f'{clip}-{d}'/f'{i:03d}.png';im=Image.open(path).convert('RGBA');assert im.size==(1472,1408);xy=(i%5*1472,i//5*1408);atlas.paste(im,xy);r.append([*xy,1472,1408]);bg=Image.new('RGBA',im.size,(45,48,52,255));bg.alpha_composite(im);bg.resize((736,704),Image.Resampling.LANCZOS).convert('RGB').save(pv/f'{i:03d}.png');raw.append({'clip':clip,'direction':d,'index':i,'path':str(path.relative_to(O)),'sha256':sha(path),'size':list(im.size),'alphaBounds':im.getchannel('A').getbbox(),'borderAlphaMax':max(im.getchannel('A').getpixel(pt)for pt in [(0,0),(1471,0),(0,1407),(1471,1407)])})
  path=OUT/'atlases'/f'{clip}-{d}.png';path.parent.mkdir(exist_ok=True);atlas.save(path,optimize=True);assert not atlas.crop((2944,2816,7360,4224)).getbbox();records.append({'clip':clip,'direction':d,'path':str(path.relative_to(O)),'sha256':sha(path),'columns':5,'rows':3,'size':list(atlas.size),'rects':r,'fps':12,'loop':clip=='covered','frameOrder':list(range(12))})
  path=OUT/'playback'/f'{clip}-{d}.mp4';path.parent.mkdir(exist_ok=True)
  cmd=['/opt/homebrew/bin/ffmpeg','-v','error','-y']
  if clip=='covered':cmd+=['-stream_loop','3']
  cmd+=['-framerate','12','-i',str(pv/'%03d.png')]
  if clip=='covered':cmd+=['-t','4']
  else:cmd+=['-vf','tpad=stop_mode=clone:stop_duration=3']
  cmd+=['-r','12','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(path)];subprocess.run(cmd,check=True)
  probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-of','json',str(path)]))['streams'][0];previews.append({'path':str(path.relative_to(O)),'sha256':sha(path),'clip':clip,'direction':d,'fps':probe['r_frame_rate'],'frames':probe['nb_frames'],'duration':probe['duration'],'presentation':'gray background, uniform 50% reduction of whole registered native frame; preview only'})
# Registered 4-view comparison sheets for three phases, full transparent frame remains separate.
for clip,index in [('covered',0),('uncover',5),('uncover',11)]:
 sh=Image.new('RGB',(1472,1448),(224,219,205));dr=ImageDraw.Draw(sh)
 for j,d in enumerate(['N','E','S','W']):
  im=Image.open(OUT/'frames'/f'{clip}-{d}'/f'{index:03d}.png').convert('RGBA').resize((736,704),Image.Resampling.LANCZOS);x=(j%2)*736;y=(j//2)*724;sh.paste(im,(x,y),im);dr.text((x+12,y+8),f'{clip} {d} / frame{index+1}',fill=(40,35,28))
 sh.save(OUT/f'{clip}-{index+1:02d}-four-view.png')
# All96 use-size reads on each background and scale, no alpha crop or view fit.
for pitch,name in [(128,'logical'),(55.7142857,'phone'),(31.3392857,'landscape')]:
 for bg,bgname in [((245,241,229),'light'),((126,130,135),'gray'),((27,31,38),'dark')]:
  w=round(736*pitch/128);h=round(704*pitch/128);sh=Image.new('RGB',(w*12,h*8),bg)
  for n,r in enumerate(raw):
   im=Image.open(O/r['path']).convert('RGBA').resize((w,h),Image.Resampling.LANCZOS);sh.paste(im,((n%12)*w,(n//12)*h),im)
  path=OUT/'readability'/f'all96-{name}-{bgname}.png';path.parent.mkdir(exist_ok=True);sh.save(path,optimize=True)
# Data records remain stage-limited.
(OUT/'atlas-records.json').write_text(json.dumps(records,indent=2)+'\n');(OUT/'raw-frame-records.json').write_text(json.dumps(raw,indent=2)+'\n');(OUT/'playback-records.json').write_text(json.dumps(previews,indent=2)+'\n')
html='<html><meta charset="utf-8"><title>Dock cover preliminary v1 native playback</title><style>body{background:#25282e;color:#eee;font:16px system-ui}main{display:grid;grid-template-columns:repeat(4,1fr)}video{width:100%}h2{font-size:16px}</style><h1>Preliminary native cover clips</h1><p>12fps. Covered repeats four cycles; uncover runs once and holds its terminal for three seconds. Physical family/consumer approval pending.</p><main>'
for r in previews:html+=f'<section><h2>{r["clip"]} {r["direction"]}</h2><video src="playback/{r["clip"]}-{r["direction"]}.mp4" controls autoplay loop muted playsinline></video></section>'
html+='</main></html>';(OUT/'playback.html').write_text(html)
print('ATLAS/PREVIEW COMPLETE',len(records),len(raw),len(previews))
