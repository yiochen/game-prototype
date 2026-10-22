import bpy,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;OBJ=P.parents[1];rec=json.loads((OBJ/'inputs/source-rig.json').read_text());root=bpy.data.objects[rec['groundRootObject']];out=[]
for name,kind,axis,maximize,bone in [('pelvis.001','seat',2,False,'pelvis'),('palm_L.001','palm',2,True,'hand_L'),('palm_R.001','palm',2,True,'hand_R'),('thumb_L.001','thumb',2,True,'hand_L'),('thumb_R.001','thumb',2,True,'hand_R'),('minimal_foot_L','sole',2,False,'foot_L'),('minimal_foot_R','sole',2,False,'foot_R')]:
 o=bpy.data.objects['customer_ellis__'+name];coords=[root.matrix_world.inverted()@o.matrix_world@v.co for v in o.data.vertices];bound=(max if maximize else min)(v[axis] for v in coords);points=[v for v in coords if abs(v[axis]-bound)<1e-6];point=sum(points,Vector())/len(points);out.append({'suffix':'customer_ellis__'+name,'kind':kind,'bone':bone,'point':list(point),'extremeFaceVertexCount':len(points)})
o=bpy.data.objects['customer_ellis__head.001'];front=min((root.matrix_world.inverted()@o.matrix_world@v.co).y for v in o.data.vertices);mouth=json.loads(root['sockets'])['mouth'];out.append({'suffix':o.name,'kind':'mouth','bone':'head','point':[mouth[0],front,mouth[2]]})
(P/'original-surface-witnesses.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
