
from pathlib import Path
from PIL import Image,ImageDraw
import json
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-01';A=O/'previews'
rows=[]
for kind in ['frames','connected']:
 for d in ['N','E','S','W']:
  frames=[]
  for step in range(48):
   im=Image.open(O/kind/f'running-{d}-{step%24:02}.png').convert('RGBA'); size=(192,352) if kind=='frames' else (448,608)
   bg=Image.new('RGBA',size,'#ece9df');bg.alpha_composite(im.resize(size,Image.Resampling.BOX));frames.append(bg)
  out=A/f'{kind}-running-{d}.webp';frames[0].save(out,save_all=True,append_images=frames[1:],duration=[83,83,84]*16,loop=0,lossless=True)
  rows.append({'kind':kind,'direction':d,'path':out.relative_to(P).as_posix(),'frames':Image.open(out).n_frames,'requestedTimingMilliseconds':[83,83,84]*16,'seconds':4,'loop':True,'sampling':'Uniform whole-frame BOX only for diagnostic playback; production frames untouched.'})
(A/'motion-inspection.html').write_text('<!doctype html><meta charset="utf-8"><title>Native corner E→N motion</title><style>body{background:#ece9df;font:16px sans-serif;color:#23323b}img{max-width:48vw}figure{display:inline-block;margin:8px}</style><h1>Corner E→N · original 24 phases · 12fps · two loops</h1>'+''.join(f'<figure><figcaption>{r["kind"]} {r["direction"]}</figcaption><img src="{Path(r["path"]).name}"></figure>' for r in rows))
# A tightly localized diagnostic of the largest native RGB residual.
a=Image.open(O/'independent/running-W-00.png');b=Image.open(O/'connected/running-W-00.png');bounds=(342,996,410,1048);im=Image.new('RGBA',(68*3*6,70*6),'#ece9df');dr=ImageDraw.Draw(im)
for j,(label,src) in enumerate([('independent',a),('connected',b),('amplified residual',Image.open(O/'residuals/RGB-alpha-localized-W-00.png'))]):
 dr.text((j*68*6+4,4),label,fill='#23323b');im.alpha_composite(src.crop(bounds).resize((68*6,52*6),Image.Resampling.NEAREST),(j*68*6,30))
im.save(A/'localized-foot-row-residual.png')
(O/'playback-records.json').write_text(json.dumps({'format':'lossless animated WebP, millisecond timing','records':rows,'GIFnote':'Optional legacy GIF previews use centisecond timing; WebP and actual consumers carry authoritative12fps timing.','nativeResidualLocation':'Largest fullRGB residual19 occurs only on W lower foot bevel sample row1021,x358..394; alpha exact; native joinROI RGB<=1. Exact amplified residual and crop retained; no raster adjustment.'},indent=2))
