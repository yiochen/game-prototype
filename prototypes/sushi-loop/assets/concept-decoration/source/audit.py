import json,hashlib,sys,math
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);m=json.loads((root/'study.json').read_text());out={'nativeProjectSHA256':m['nativeProjectSHA256'],'sourceHash':m['sourceHash'],'captures':0,'objects':{}}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/m['nativeProject'])==m['nativeProjectSHA256'];assert sha(root/'source/create_and_capture.py')==m['sourceHash']
for item in m['objects']:
 x1,y1,x2,y2=item['referenceCrop'];assert 0<=x1<x2<=1024 and 0<=y1<y2<=1536
 g=json.loads((root/item['geometry']).read_text());assert sha(root/item['geometry'])==item['geometrySHA256']
 assert min(g['min'][:2])>=-.501 and max(g['max'][:2])<=.501
 assert all(.98<=n<=1.002 for n in g['dimensions'][:2]),(item['id'],g['dimensions'])
 canvas=Image.new('1',(512,512));draw=ImageDraw.Draw(canvas)
 for part in g['objects']:
  for face in part['faces']:draw.polygon([((part['vertices'][i][0]+.5)*512,(part['vertices'][i][1]+.5)*512) for i in face],fill=1)
 coverage=sum(canvas.get_flattened_data())/(512*512)
 assert coverage>.70,(item['id'],coverage)
 o={'planCoverage':coverage,'dimensions':g['dimensions'],'profiles':{}};out['objects'][item['id']]=o
 for profile,data in item['profiles'].items():
  values=[];captures=[];factor=math.cos(math.radians(35)) if profile=='ordinary35' else .7;depth=math.sin(math.radians(35)) if profile=='ordinary35' else 1
  for direction,path in data['images'].items():
   receipt=json.loads((root/data['receipts'][direction]).read_text());assert sha(root/path)==receipt['imageSHA256'];assert sha(root/receipt['captureGeometry'])==receipt['captureGeometrySHA256']
   assert receipt['nativeProjectSHA256']==m['nativeProjectSHA256'];assert receipt['frameSize']==m['frameSize'] and receipt['root']==m['root']
   cg=json.loads((root/receipt['captureGeometry']).read_text());vertices=[v for p in cg['objects'] for v in p['vertices']]
   projected=[-v[1]*depth-v[2]*factor for v in vertices];height=max(projected)-min(projected)
   assert height<=3,(item['id'],profile,direction,height)
   c=receipt['camera']['calibration']
   for key,expected in [('root',m['root']),('x',[128,0]),('depth',[0,128*depth]),('height',[0,-128*factor])]:assert max(abs(a-b) for a,b in zip(c[key],expected))<.01
   im=Image.open(root/path);a=im.getchannel('A');box=a.getbbox();assert im.size==(768,3072);assert box and min(box[:2])>2 and box[2]<im.width-2 and box[3]<im.height-2
   assert (box[3]-box[1])/(128*m['sourceScale'])<=3.01
   ground=[v for v in vertices if abs(v[2])<1e-5];ground_depth=[-v[1]*depth for v in ground]
   native_receipt=json.loads((root/item['profiles']['oblique70']['receipts'][direction]).read_text());native=json.loads((root/native_receipt['captureGeometry']).read_text())
   native_ground=[v[1] for p in native['objects'] for v in p['vertices'] if abs(v[2])<1e-5]
   assert abs((max(ground_depth)-min(ground_depth))-(max(native_ground)-min(native_ground)))<1e-5,(item['id'],profile,direction,'square footing')
   values.append(height);captures.append({'direction':direction,'height':height,'imageSHA256':receipt['imageSHA256']});out['captures']+=1
  o['profiles'][profile]={'maxProjectedHeight':max(values),'verticalRise':item['height']*factor,'captures':captures}
assert out['captures']==98
(root/'measurements.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'captures':out['captures'],'objects':[(i,round(o['planCoverage'],3),round(max(p['maxProjectedHeight'] for p in o['profiles'].values()),3)) for i,o in out['objects'].items()]}))
