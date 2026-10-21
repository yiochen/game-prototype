import bpy, math, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

B=Path(__file__).resolve().parents[1]
OUT=B/'reviews/round01-native-replay';OUT.mkdir(exist_ok=True)
portable=B/'reviews/round01-relocated/asset.blend';portable.parent.mkdir(exist_ok=True)
source=B/'source/round-01.blend';shutil.copyfile(source,portable)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(portable))
sc=bpy.context.scene;root=bpy.data.objects['rock-wall-edge__root'];coll=bpy.data.collections['rock-wall-edge__asset'];cam=sc.camera
bpy.context.view_layer.update()
meshes=[o for o in coll.all_objects if o.type=='MESH']
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
def mat(m):return [list(row) for row in m]
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
def boundaries(me):
 ca=me.color_attributes['stone_albedo'];result={}
 for sign in [-1,1]:
  vs=sorted([v for v in me.vertices if abs(v.co.x-sign*.5)<1e-7],key=lambda v:(round(v.co.y,7),round(v.co.z,7)))
  loops={v.index:[] for v in vs}
  for l in me.loops:
   if l.vertex_index in loops: loops[l.vertex_index].append(tuple(me.corner_normals[l.index].vector))
  result[sign]=[{'p':tuple(v.co),'color':tuple(ca.data[v.index].color),'normals':loops[v.index]} for v in vs]
 return result
side=next(o for o in meshes if 'continuous_carved' in o.name)
edge=boundaries(side.data)
# Full bottom coverage measured from actual native planar polygons, without relying on audit labels.
bottom=[]
for ob in meshes:
 me=ob.data;me.calc_loop_triangles()
 for tri in me.loop_triangles:
  vs=[ob.matrix_world@me.vertices[i].co for i in tri.vertices]
  if all(abs(v.z)<1e-8 for v in vs):bottom.append(vs)
area=sum(abs((v[1]-v[0]).cross(v[2]-v[0]).z)*.5 for v in bottom)
def inside(p,t):
 signs=[]
 for i in range(3):
  a=t[i];b=t[(i+1)%3];signs.append((b.x-a.x)*(p[1]-a.y)-(b.y-a.y)*(p[0]-a.x))
 return min(signs)>=-1e-9 or max(signs)<=1e-9
missing=[]
for ix in range(41):
 for iy in range(41):
  p=(-.5+ix/40,-.5+iy/40)
  if not any(inside(p,t) for t in bottom):missing.append(p)
compositor=getattr(sc,'node_tree',None) or getattr(sc,'compositing_node_group',None)
audit={'projectSHA256':sha(portable),'exactSourceCopy':sha(portable)==sha(source),'scene':sc.name,'rootMatrix':mat(root.matrix_world),'rootScale':list(root.scale),'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]},'meshObjects':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'modifiers':[m.type for m in o.modifiers]} for o in meshes],'contact':{'planarTriangleArea':area,'triangleCount':len(bottom),'gridSamples':41*41,'uncoveredGroundSamples':missing,'planarTriangleBounds':{'min':[min(v[i] for t in bottom for v in t) for i in range(3)],'max':[max(v[i] for t in bottom for v in t) for i in range(3)]}},'camera':{'matrix':mat(cam.matrix_world),'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'size':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'rootPixel':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in range(2)],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in range(2)],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in range(2)]},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'shadow':o.data.use_shadow,'matrix':mat(o.matrix_world)} for o in sc.objects if o.type=='LIGHT'],'materials':[{'name':m.name,'nodes':[n.type for n in m.node_tree.nodes]} for m in {m for o in meshes for m in o.data.materials}],'compositor':{'nodes':[n.bl_idname for n in compositor.nodes] if compositor else []},'resourceClosure':{'fileImages':[{'name':i.name,'path':i.filepath} for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]},'views':{}}
# Append the approved native middle only as an audit dependency after recording source closure.
reference=B/'inputs/approved-middle/project.blend'
with bpy.data.libraries.load(str(reference),link=False) as (a,z):z.objects=['rock-wall-middle__continuous_carved_stone']
ref=z.objects[0];middle=boundaries(ref.data)
def compare(a,b):
 assert len(a)==len(b)
 return {'vertices':len(a),'maxYZDelta':max(max(abs(x['p'][i]-y['p'][i]) for i in [1,2]) for x,y in zip(a,b)),'maxAlbedoDelta':max(max(abs(x['color'][i]-y['color'][i]) for i in range(4)) for x,y in zip(a,b)),'maxActualCornerNormalDelta':max(max(min((Vector(n)-Vector(m)).length for m in y['normals']) for n in x['normals']) for x,y in zip(a,b))}
audit['connectorComparisons']={str(s):{'sameApprovedCut':compare(edge[s],middle[s]),'oppositeApprovedCutAtMixedJoin':compare(edge[s],middle[-s]),'actualPlaneXRange':[min(v['p'][0] for v in edge[s]),max(v['p'][0] for v in edge[s])]} for s in [-1,1]}
bpy.data.objects.remove(ref,do_unlink=True)
for direction,deg in {'N':180,'E':90,'S':0,'W':-90}.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update()
 audit['views'][direction]={'rootMatrix':mat(root.matrix_world),'rootPixel':px((0,0,0))}
 sc.render.filepath=str(OUT/f'native-static-{direction}.png');bpy.ops.render.render(write_still=True)
(OUT/'audit.json').write_text(json.dumps(audit,indent=2))
print('INDEPENDENT_REPLAY_DONE',str(OUT))
