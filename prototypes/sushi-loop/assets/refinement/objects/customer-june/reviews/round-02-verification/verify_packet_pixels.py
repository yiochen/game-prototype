import json,hashlib,struct,zlib
from pathlib import Path
from PIL import Image
import numpy as np
P=Path(__file__).parent;O=P.parents[1];C=O/'candidates/round-02';packet=json.loads((C/'packet.json').read_text());errors=[];files=[];seen={}
for key,item in packet['files'].items():
 path=(C/item['path']).resolve()
 if path not in seen:seen[path]=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
 ok=seen[path]==item['sha256'];files.append({'key':key,'path':str(path),'expected':item['sha256'],'actual':seen[path],'pass':ok})
 if not ok:errors.append(key)
atlases=[];apng=[]
for mode in ['main','runtime']:
 for a in sorted((C/mode/'atlases').glob('*.png')):
  atlas=Image.open(a).convert('RGBA');matches=[]
  for f in range(12):
   raw=C/mode/'frames'/a.stem/(f'{f:03}.png');r=np.asarray(Image.open(raw).convert('RGBA'));q=np.asarray(atlas.crop((f%6*384,f//6*640,f%6*384+384,f//6*640+640)));matches.append(np.array_equal(r,q))
  atlases.append({'path':str(a),'size':list(atlas.size),'cellEqualsNativeFrame':matches});anim=C/'playback'/a.name;im=Image.open(anim);matches=[];durations=[]
  for f in range(im.n_frames):
   im.seek(f);matches.append(np.array_equal(np.asarray(im.convert('RGBA')),np.asarray(Image.open(C/mode/'frames'/a.stem/(f'{f:03}.png')).convert('RGBA'))));durations.append(im.info.get('duration'))
  chunks=[];data=anim.read_bytes();i=8
  while i<len(data):
   n=struct.unpack('>I',data[i:i+4])[0];typ=data[i+4:i+8];v=data[i+8:i+8+n]
   if typ==b'fcTL':chunks.append({'delayNum':struct.unpack('>H',v[20:22])[0],'delayDen':struct.unpack('>H',v[22:24])[0]})
   i+=n+12
  apng.append({'path':str(anim),'nFrames':im.n_frames,'loop':im.info.get('loop'),'framesEqualNative':matches,'durationsMs':durations,'exactDelayChunks':chunks})
report={'packetSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'declaredEntries':len(files),'uniqueFiles':len(seen),'files':files,'hashErrors':errors,'atlases':atlases,'apng':apng,'allAtlasCellsMatchNative':all(all(a['cellEqualsNativeFrame']) for a in atlases),'allAPNGFramesMatchNative':all(all(a['framesEqualNative']) for a in apng),'allAPNGExact12FPS':all(c['delayNum']*12==c['delayDen'] for a in apng for c in a['exactDelayChunks'])}
(P/'packet-pixels-verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ['files','atlases','apng']})
# Six standalone review pages; each owns eight actual APNGs with exact original loop flags.
clips=['stand','walk','seated-wait','eat','sit-down','stand-up','happy','restless','puzzled','panic','eat-salmon','seated-wait-empty']
for i in range(6):
 html='<meta charset="utf-8"><title>June judge temporal review</title><style>body{font:14px system-ui;background:#aaa9a5}section{display:grid;grid-template-columns:repeat(4,192px)}figure{margin:0;background:#f7efdc}img{width:192px;height:320px}h2{margin:6px}</style>'
 for clip in clips[i*2:i*2+2]:
  html+=f'<h2>{clip}</h2><section>'
  for d in ['S','E','N','W']:html+=f'<figure><img src="../../candidates/round-02/playback/{clip}-{d}.png"><figcaption>{d} · {clip}</figcaption></figure>'
  html+='</section>'
 (P/(f'playback-page-{i}.html')).write_text(html)
