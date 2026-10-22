
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
(A/'motion-inspection.html').write_text('<!doctype html><meta charset="utf-8"><title>belt-corner-s-e native motion</title><style>body{background:#ece9df;font:16px sans-serif;color:#23323b}img{max-width:48vw}figure{display:inline-block;margin:8px}</style><h1>belt-corner-s-e · original 24 phases · 12fps · two loops</h1>'+''.join(f'<figure><figcaption>{r["kind"]} {r["direction"]}</figcaption><img src="{Path(r["path"]).name}"></figure>' for r in rows))
(O/'playback-records.json').write_text(json.dumps({'format':'lossless animatedWebP, millisecond timing','records':rows},indent=2))
