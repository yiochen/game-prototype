import json,hashlib,sys,math
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(sys.argv[1]);m=json.loads((root/'study.json').read_text());out={'ok':True,'objects':[],'captures':0};errors=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(root/m['nativeProject'])==m['nativeProjectSHA256']
assert sha(root/'source/create_and_capture.py')==m['sourceHash']
for obj in m['objects']:
 g=json.loads((root/obj['geometry']).read_text());assert sha(root/obj['geometry'])==obj['geometrySHA256']
 im=Image.new('1',(256,256));d=ImageDraw.Draw(im)
 for part in g['objects']:
  for face in part['faces']:
   points=[((part['vertices'][i][0]+.5)*256,(part['vertices'][i][1]+.5)*256) for i in face]
   d.polygon(points,fill=1)
 coverage=sum(im.getdata())/65536
 assert coverage>=.80,(obj['id'],coverage)
 assert all(abs(v-1)<1e-5 for v in g['dimensions'][:2])
 if 'targetProjectedHeight' in obj:assert abs(obj['height']*m['heightRatio']-obj['targetProjectedHeight'])<1e-5
 preserved_count=0
 if 'baseHeight' in obj and obj['heightBand']!='ground':
  base=next(p for p in g['objects'] if p['name'].endswith(' flat crown rock base'))
  crown=[base['vertices'][i] for i in base['faces'][-1]]
  assert max(abs(v[2]-obj['baseHeight']) for v in crown)<1e-5
  area=abs(sum(crown[i][0]*crown[(i+1)%len(crown)][1]-crown[(i+1)%len(crown)][0]*crown[i][1] for i in range(len(crown))))/2
  assert area>.80,(obj['id'],'narrow crown',area)
  if obj['preservedParts']:
   historic=json.loads((root/'original/geometry'/f"{obj['id']}.json").read_text())
   original_manifest=json.loads((root/'original/study.json').read_text())
   original_item=next(i for i in original_manifest['objects'] if i['id']==obj['id'])
   assert sha(root/'original/geometry'/f"{obj['id']}.json")==original_item['geometrySHA256']
   for part in obj['preservedParts']:
    old=next(p for p in historic['objects'] if p['name'].endswith(' '+part['part']))
    now=next(p for p in g['objects'] if p['name'].endswith(' '+part['part']))
    assert old['faces']==now['faces']==part['faces']
    assert len(old['vertices'])==len(now['vertices'])
    for v,w in zip(old['vertices'],now['vertices']):
     assert max(abs(w[i]-v[i]-part['translation'][i]) for i in range(3))<1e-5,(obj['id'],part['part'])
    preserved_count+=1
 rec={'preservedPartsChecked':preserved_count,'id':obj['id'],'footprintCoverage':round(coverage,4),'height':obj['height'],'captures':[]}
 for facing,path in obj['images'].items():
  receipt=json.loads((root/obj['receipts'][facing]).read_text());png=Image.open(root/path);a=png.getchannel('A');box=a.getbbox()
  assert png.size==tuple(v*4 for v in m['frameSize'])
  assert box and min(box[:2])>2 and box[2]<png.width-2 and box[3]<png.height-2
  assert sha(root/path)==receipt['imageSHA256']
  cal=receipt['camera']['calibration']
  for k,wanted in [('root',m['root']),('x',[128,0]),('depth',[0,128]),('height',[0,-89.6])]:
   assert max(abs(v-w) for v,w in zip(cal[k],wanted))<.01,(obj['id'],k)
  assert min(receipt['bounds']['min'][:2])>=-.501 and max(receipt['bounds']['max'][:2])<=.501
  rec['captures'].append(facing);out['captures']+=1
 out['objects'].append(rec)
assert out['captures']==21
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
