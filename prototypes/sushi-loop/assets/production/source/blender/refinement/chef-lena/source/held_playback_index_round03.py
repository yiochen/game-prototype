from pathlib import Path
P=Path(__file__).parent;C=P.parent/'candidates/round-03'
s='''<!doctype html><meta charset="utf-8"><title>Lena canonical held-food native12fps</title><style>body{margin:20px;background:#ece8dd;color:#263342;font:14px system-ui}h1{font-size:22px}.grid{display:grid;grid-template-columns:repeat(4,192px);gap:12px}figure{margin:0}video{width:192px;height:320px;background:#7c7c7c}button{padding:10px;margin:4px}a{color:#224e79}</style><h1>Lena · canonical food · actual native12fps</h1><p>Four unchanged facings. Hold loops, load stops on original held endpoint. Same registered192×320 frames.</p><button onclick="document.querySelectorAll('video').forEach(v=>{v.currentTime=0;v.play()})">Replay all eight from start</button><button onclick="document.querySelectorAll('video').forEach(v=>v.pause())">Pause</button><p><a href="playback.html">All sixteen clips and source/candidate serving contexts</a></p><div class="grid">'''
for clip in ['hold','load']:
 for d in ['N','E','S','W']:s+=f'<figure><figcaption>{clip}-{d} ·12fps ·{"loop" if clip=="hold" else "stops"}</figcaption><video controls muted playsinline preload="auto" data-id="{clip}-{d}" {"loop" if clip=="hold" else ""} src="playback/{clip}-{d}.mp4"></video></figure>'
s+='</div><h2>All paired phases and exact native contact crops</h2>'
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:s+=f'<a href="paired/all12-{clip}-{d}.png">{clip}-{d} paired12</a> · '
s+='<p>Background and contact evidence:</p>'
for bg in ['light','gray','dark']:
 for clip in ['hold','load']:
  for d in ['N','E','S','W']:
   s+=f'<a href="sheets/{clip}-{d}-{bg}.png">{clip}-{d}-{bg} all12</a> · '
   for i in [0,5,11]:s+=f'<a href="paired/contact-{clip}-{d}-{i:02d}-{bg}.png">contact{i:02d}</a> · '
 s+='<br>'
(C/'held-playback.html').write_text(s)
