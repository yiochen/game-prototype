from pathlib import Path
import json,hashlib,subprocess
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;B=R.parents[1];C=B/'candidates/round-02';p=json.loads((C/'packet.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def im(p):return Image.open(p).convert('RGBA')
def bg(i):
 b=Image.new('RGBA',i.size,'#e5e2d8');b.alpha_composite(i.convert('RGBA'));return b.convert('RGB')
rows=[];videos=[]
for rt in [False,True]:
 f=C/'runtimeVariants' if rt else C
 for clip in (['hold-cucumber','load-cucumber'] if rt else ['idle','work','hold','load']):
  overview=Image.open(f/'contact-sheets'/f'{clip}-all48.png').convert('RGB')
  for di,d in enumerate(['N','E','S','W']):
   atlas=im(f/'atlases'/f'{clip}-{d}.png');sheet=Image.open(f/'contact-sheets'/f'{clip}-{d}.png').convert('RGB');assert atlas.size==(2304,1280)
   for i in range(12):
    path=f/'frames'/f'{clip}-{d}'/f'{i:03d}.png';v=im(path);assert v.size==(384,640)
    assert atlas.crop((i%6*384,i//6*640,(i%6+1)*384,(i//6+1)*640)).tobytes()==v.tobytes()
    assert sheet.crop((i%6*192,i//6*352+28,i%6*192+192,i//6*352+348)).tobytes()==bg(v.resize((192,320),Image.Resampling.LANCZOS)).tobytes()
    assert overview.crop((i*96,di*176+16,i*96+96,di*176+176)).tobytes()==bg(v.resize((96,160),Image.Resampling.LANCZOS)).tobytes()
    rows.append({'path':str(path.relative_to(C)),'sha256':sha(path)})
   vp=f/'playbacks'/f'{clip}-{d}.mp4';probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=r_frame_rate,nb_frames,width,height,duration','-of','json',str(vp)]))['streams'][0];assert probe['r_frame_rate']=='12/1' and int(probe['nb_frames'])==12;videos.append({'path':str(vp.relative_to(C)),'loop':not clip.startswith('load'),'probe':probe})
# Hash all packet closure entries again here as independently recomputable evidence.
checks=[]
for bucket in ['files','candidateRenders','previews']:
 for key,v in p[bucket].items():
  file=(C/v['path']).resolve();assert file.exists(),file;assert sha(file)==v['sha256'],file;checks.append(str(file))
out={'packetSHA256':sha(C/'packet.json'),'boundItems':len(checks),'hashFailures':0,'mainFrames':192,'runtimeFrames':96,'allAtlasCellsRawRGBAExact':True,'allContactSheetAndOverviewSpritePixelsExact':True,'nativeAndPublishedResolution':[384,640],'nativeAndPublishedScale':2,'frames':rows,'videos':videos}
(R/'pixel-audit.json').write_text(json.dumps(out,indent=2)+'\n')
# Honest body RGB residual inspection surface: exact unaltered pixels and a labeled diagnostic gain.
d=json.loads((C/'food-dependent-rgb-diagnostics.json').read_text());rr=[]
for case in d['cases']:
 food,clip,di,i=[case[k] for k in ['food','clip','direction','index']];sf=C/('runtimeVariants' if food=='cucumber' else '')/'frames'/f'{clip}-{di}'/f'{i:03d}.png';old=B/case['approvedOldPixels']['path'];v2=C/'replay/canonical-v2'/food/f'{clip}-{di}-{i:03d}.png'
 if not v2.exists():
  matches=list(C.rglob(f'{clip}-{di}-{i:03d}.png'));v2=next(x for x in matches if 'canonical-v2' in str(x))
 a=np.asarray(im(old)).astype(np.int16);v=np.asarray(im(v2)).astype(np.int16);b=np.asarray(im(sf)).astype(np.int16);mask=(a[:,:,3]==255)&(v[:,:,3]==255)&(b[:,:,3]==255);(x0,y0),(x1,y1)=case['excludedFoodQuadUnionBoundsNativePx'];mask[y0:y1,x0:x1]=False
 delta=np.abs(a[:,:,:3]-b[:,:,:3]);dv=np.abs(v[:,:,:3]-b[:,:,:3]);rr.append({'case':f'{food}/{clip}-{di}-{i:03d}','maxOldRGB':int(delta[mask].max()),'meanOldRGB':float(delta[mask].mean()),'maxV2RGB':int(dv[mask].max()),'meanV2RGB':float(dv[mask].mean()),'opaqueOutsideQuadPixels':int(mask.sum()),'paths':[str(x.relative_to(C)) if x.is_relative_to(C) else str(x.relative_to(B)) for x in [old,v2,sf]]})
 if (di=='N' and i==0) or (di=='S' and i==0 and clip.startswith('hold')):
  canvas=Image.new('RGB',(1536,680),'#e5e2d8');dr=ImageDraw.Draw(canvas)
  for k,(img,label) in enumerate([(im(old),'approved old food'),(im(v2),'same canonical / old depth'),(im(sf),'submitted v3'),(Image.fromarray(np.uint8(np.minimum(255,delta*12))),'RGB abs delta x12 (diagnostic)')]):canvas.paste(bg(img),(k*384,30));dr.text((k*384+8,6),label,fill='#20343c')
  canvas.save(R/f'RGB-{food}-{clip}-{di}-{i:03d}.png')
(R/'rgb-audit.json').write_text(json.dumps({'coverage':len(rr),'notAll288Bound':True,'method':'Opaque shared pixels outside editor documented conservative union of all food quads; recomputed direct native RGBA. Gain only diagnostic, never candidate pixels.','cases':rr},indent=2)+'\n')
(R/'turn-playback.html').write_text('''<!doctype html><title>Omar judge turn replay</title><style>body{background:#e5e2d8;font:16px system-ui}main{display:flex;gap:30px}video{width:384px;height:640px}</style><button id="play">Play both 12fps turns</button><main><figure><figcaption>Salmon turn, original 27 frames at 12fps</figcaption><video src="../../candidates/round-02/playbacks/semantic-turn.mp4" controls muted loop></video></figure><figure><figcaption>Cucumber turn, original 27 frames at 12fps</figcaption><video src="../../candidates/round-02/runtimeVariants/playbacks/semantic-turn.mp4" controls muted loop></video></figure></main><script>document.querySelector('button').onclick=()=>document.querySelectorAll('video').forEach(v=>{v.currentTime=0;v.play()})</script>''')
print('PIXEL AUDIT COMPLETE',len(rows),'frames',len(checks),'packet entries',len(rr),'RGB cases')
