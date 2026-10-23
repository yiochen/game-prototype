import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib,bmesh
from pathlib import Path
BASE=Path(__file__).resolve().parent.parent
project=Path(bpy.data.filepath);before=hashlib.sha256(project.read_bytes()).hexdigest()
root=bpy.data.objects['safe-passage__root'];col=root.users_collection[0];records=[]
for o in sorted(col.all_objects,key=lambda o:o.name):
 if o.type!='MESH':continue
 me=o.data;bm=bmesh.new();bm.from_mesh(me)
 incidence={str(n):sum(len(e.link_faces)==n for e in bm.edges) for n in sorted({len(e.link_faces) for e in bm.edges})}
 records.append({'object':o.name,'role':o.get('role'),'vertices':len(me.vertices),'polygons':len(me.polygons),'edgeFaceIncidence':incidence,'closedManifold':all(e.is_manifold for e in bm.edges),'signedNativeMeshVolume':bm.calc_volume(signed=True),'localMatrixDeterminant':o.matrix_local.to_3x3().determinant(),'shapeKeys':me.shape_keys is not None,'assignedAction':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
 bm.free()
after=hashlib.sha256(project.read_bytes()).hexdigest();assert after==before
assert all(r['closedManifold'] and r['signedNativeMeshVolume']>0 and r['localMatrixDeterminant']>0 for r in records)
report={'asset':'safe-passage','sourceSHA256':before,'sourceUnchanged':before==after,'scope':'Clean saved-source native topology/normal orientation probe; no render/model save','objects':records,'allClosedManifoldPositiveVolume':True,'allProperLocalTransforms':True}
p=BASE/'candidates/round-01/native-topology.json'
with p.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'objects':len(records),'allClosedManifoldPositiveVolume':True,'allProperLocalTransforms':True,'sourceSHA256':before}))
