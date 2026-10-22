from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
O=Path(__file__).resolve().parent;B=O/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry/candidates/round-07';D=O/'diagnostics';p=json.loads((B/'packet.json').read_text());items=list(p['previews'].items());entries=[]
for start in range(0,len(items),4):
 s=Image.new('RGB',(1320,1040),'#a7a7a7');dr=ImageDraw.Draw(s)
 for index,(name,v) in enumerate(items[start:start+4]):
  f=(B/v['path']).resolve();assert hashlib.sha256(f.read_bytes()).hexdigest()==v['sha256'];im=Image.open(f).convert('RGBA');panel=Image.new('RGBA',im.size,'#a7a7a7');panel.alpha_composite(im);panel=panel.convert('RGB');panel.thumbnail((640,490));x=(index%2)*660;y=(index//2)*520;s.paste(panel,(x+(660-panel.width)//2,y+25));dr.text((x+5,y+5),name,fill='black');entries.append({'packetPreview':name,'packetPath':v['path'],'sha256':v['sha256'],'sheet':f'diagnostics/packet-previews-{start//4+1}.png'})
 s.save(D/f'packet-previews-{start//4+1}.png')
(O/'packet-preview-inspection-index.json').write_text(json.dumps({'candidatePacketSHA256':'5e4a1c313176fc0e0474474a0fbc800b3ddd321d9c4076e71da39620a617ba70','method':'Exact hash-verified preview input, alpha composited on gray for transparent images, uniform whole-image thumbnail into labeled sheet. Supplemented by direct intended-size current native/consumer evidence.','entries':entries},indent=2)+'\n')
