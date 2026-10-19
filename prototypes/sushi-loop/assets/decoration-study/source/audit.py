import json,hashlib,sys,math
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);m=json.loads((root/'study.json').read_text());out={'ok':True,'objects':[],'captures':0}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/m['nativeProject'])==m['nativeProjectSHA256']
assert sha(root/'source/create_and_capture.py')==m['sourceHash']
for obj in m['objects']:
 g=json.loads((root/obj['geometry']).read_text());assert sha(root/obj['geometry'])==obj['geometrySHA256']
 im=Image.new('1',(256,256));draw=ImageDraw.Draw(im)
 for part in g['objects']:
  for face in part['faces']:draw.polygon([((part['vertices'][i][0]+.5)*256,(part['vertices'][i][1]+.5)*256) for i in face],fill=1)
 coverage=sum(im.get_flattened_data())/65536
 assert coverage>=.8,(obj['id'],coverage)
 assert all(abs(v-1)<1e-5 for v in g['dimensions'][:2])
 assert obj['height']*math.cos(math.radians(35))<3
 if obj['heightBand']!='ground':
  assert {d['band'] for d in obj['decorations']}=={'bottom','middle','top'}
  for name in ['back crag','middle ledge','front shelf']:
   rock=next(p for p in g['objects'] if p['name'].endswith(' '+name));crown=[v[2] for v in rock['vertices'][-9:]]
   assert .015<max(crown)-min(crown)<.19,(obj['id'],name,'uneven crown')
   # The shoulder width changes substantially, unlike the former cut pillars.
   radii=[]
   for j in range(6):
    vv=rock['vertices'][j*8:(j+1)*8];radii.append(max(v[0] for v in vv)-min(v[0] for v in vv))
   assert min(radii)/max(radii)<.82
 rec={'id':obj['id'],'coverage':round(coverage,4),'maxVerticalRise':round(obj['height']*math.cos(math.radians(35)),4),'captures':[]}
 for profile,data in obj['profiles'].items():
  for facing,path in data['images'].items():
   receipt=json.loads((root/data['receipts'][facing]).read_text());png=Image.open(root/path);alpha=png.getchannel('A');box=alpha.getbbox()
   assert png.size==tuple(v*m['sourceScale'] for v in m['frameSize'])
   assert box and min(box[:2])>2 and box[2]<png.width-2 and box[3]<png.height-2
   assert sha(root/path)==receipt['imageSHA256']
   assert sha(root/receipt['captureGeometry'])==receipt['captureGeometrySHA256']
   capture=json.loads((root/receipt['captureGeometry']).read_text())
   c=receipt['camera'];depth=math.sin(math.radians(35)) if profile=='ordinary35' else 1;up=math.cos(math.radians(35)) if profile=='ordinary35' else .7
   for key,expected in [('root',m['root']),('x',[128,0]),('depth',[0,128*depth]),('height',[0,-128*up])]:
    assert max(abs(v-w) for v,w in zip(c['calibration'][key],expected))<.01,(obj['id'],profile,key)
   assert min(receipt['bounds']['min'][:2])>=-.501 and max(receipt['bounds']['max'][:2])<=.501
   ground=[v for p in capture['objects'] for v in p['vertices'] if abs(v[2])<1e-5]
   # End-to-end projected ground reaches both tile edges, including the low camera.
   projected=[-v[1]*depth for v in ground]
   assert abs(max(projected)-.5)<1e-5 and abs(min(projected)+.5)<1e-5,(obj['id'],profile,facing)
   frontCoverage=None
   if obj['heightBand']!='ground':
    y=round((m['root'][1]+.49*m['cellSize'])*m['sourceScale']);lo=round((m['root'][0]-.5*m['cellSize'])*m['sourceScale']);hi=round((m['root'][0]+.5*m['cellSize'])*m['sourceScale'])
    frontCoverage=sum(alpha.getpixel((x,y))>128 for x in range(lo,hi))/(hi-lo)
    assert frontCoverage>.30,(obj['id'],profile,facing,frontCoverage)
   rec['captures'].append({'view':profile+'/'+facing,'frontEdgeCoverage':frontCoverage});out['captures']+=1
 out['objects'].append(rec)
assert out['captures']==41
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
