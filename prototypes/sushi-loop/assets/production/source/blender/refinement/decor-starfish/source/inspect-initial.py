import bpy,json,pathlib,math
from mathutils import Vector
out=pathlib.Path(__file__).parent
bpy.context.view_layer.update()
rows=[]
for col in bpy.data.collections:
 if 'starfish' in col.name.lower():
  objs=[]
  for o in col.all_objects:
   d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':[list(r) for r in o.matrix_world],'properties':dict(o.items())}
   if o.type=='MESH':
    v=[o.matrix_world@x.co for x in o.data.vertices];e={tuple(sorted(x.vertices)):0 for x in o.data.edges}
    for poly in o.data.polygons:
     ids=list(poly.vertices)
     for i,a in enumerate(ids):
      k=tuple(sorted((a,ids[(i+1)%len(ids)])));e[k]=e.get(k,0)+1
    d.update(vertices=len(v),polygons=len(o.data.polygons),bounds=[[min(x[i] for x in v),max(x[i] for x in v)] for i in range(3)],boundaryEdges=sum(n==1 for n in e.values()),nonmanifoldEdges=sum(n!=2 for n in e.values()),materials=[m.name for m in o.data.materials])
   objs.append(d)
  rows.append({'collection':col.name,'objects':objs})
json.dump({'blender':bpy.app.version_string,'scenes':[{'name':s.name,'activeCamera':s.camera.name if s.camera else None,'resolution':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]} for s in bpy.data.scenes],'collections':rows},open(out/'initial-native-inspection.json','w'),indent=2)
