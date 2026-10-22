import bpy,hashlib,json,struct
from pathlib import Path
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';records={}
for rd in ['round-04','round-05']:
 bpy.ops.wm.open_mainfile(filepath=str(B/f'source/{rd}.blend'));rs={}
 for ob in bpy.data.collections['rock-wall-corner__asset'].objects:
  if ob.type!='MESH':continue
  me=ob.data;ca=me.color_attributes['stone_albedo'];rs[ob.name]={'coordinatesSHA256':hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in me.vertices)).hexdigest(),'topologySHA256':hashlib.sha256(b''.join(struct.pack('I',len(p.vertices))+b''.join(struct.pack('I',v) for v in p.vertices) for p in me.polygons)).hexdigest(),'albedoSHA256':hashlib.sha256(b''.join(struct.pack('ffff',*c.color) for c in ca.data)).hexdigest(),'storedLoopNormalsSHA256':hashlib.sha256(b''.join(struct.pack('fff',*n.vector) for n in me.corner_normals)).hexdigest()}
 records[rd]=rs
report={'sources':['source/round-04.blend','source/round-05.blend'],'method':'Read actual reopened native vertex coordinates, polygon indices, native stone_albedo and stored face-corner normals; no source edits.','meshes':{n:{'coordinatesIdentical':p['coordinatesSHA256']==records['round-05'][n]['coordinatesSHA256'],'topologyIdentical':p['topologySHA256']==records['round-05'][n]['topologySHA256'],'albedoIdentical':p['albedoSHA256']==records['round-05'][n]['albedoSHA256'],'nativeNormalsIdentical':p['storedLoopNormalsSHA256']==records['round-05'][n]['storedLoopNormalsSHA256']} for n,p in records['round-04'].items()},'actualHashes':records}
(O/'native-round04-round05-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['meshes']))
