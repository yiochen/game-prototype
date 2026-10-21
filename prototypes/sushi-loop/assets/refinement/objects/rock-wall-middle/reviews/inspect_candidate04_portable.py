import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parent/'round04-independent-portable'
OUT.mkdir(exist_ok=True)
sc=bpy.context.scene
root=bpy.data.objects['rock-wall-middle__root']
root.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
def vec(v):return [float(x) for x in v]
def bound(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
meshes=[o for o in sc.objects if o.type=='MESH']
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
side=bpy.data.objects['rock-wall-middle__continuous_carved_stone']
me=side.data
w=sorted([v for v in me.vertices if abs(v.co.x+.5)<1e-7],key=lambda v:(round(v.co.y,7),round(v.co.z,7)))
e=sorted([v for v in me.vertices if abs(v.co.x-.5)<1e-7],key=lambda v:(round(v.co.y,7),round(v.co.z,7)))
prof=[Vector(v) for v in [[-.5,0],[.5,0],[.5,.67],[.45,1.04],[.31,1.15],[-.31,1.15],[-.45,1.04],[-.5,.67]]]
def distseg(p,a,b):
 d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-a-t*d).length
col=me.color_attributes['stone_albedo']
cam=sc.camera
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return Vector((v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y))
zero=px((0,0,0))
report={'project':bpy.data.filepath,'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'rootMatrix':[vec(r) for r in root.matrix_world],'bounds':bound(points),'meshObjects':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materialNames':[m.name for m in o.data.materials],'matrix':[vec(r) for r in o.matrix_world]} for o in meshes], 'camera':{'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'worldMatrix':[vec(r) for r in cam.matrix_world],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'root':vec(zero),'unitX':vec(px((1,0,0))-zero),'unitDepth':vec(px((0,-1,0))-zero),'unitHeight':vec(px((0,0,1))-zero)},'connectors':{'westCount':len(w),'eastCount':len(e),'maxPairYZDelta':max(math.dist((a.co.y,a.co.z),(b.co.y,b.co.z)) for a,b in zip(w,e)),'maxProfileDistance':max(min(distseg(Vector((v.co.y,v.co.z)),prof[i],prof[(i+1)%8]) for i in range(8)) for v in w+e),'maxPairColorDelta':max(abs(col.data[a.index].color[i]-col.data[b.index].color[i]) for a,b in zip(w,e) for i in range(4))},'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'file':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'rotation':vec(o.rotation_euler),'shadow':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT'],'engine':sc.render.engine,'samples':sc.cycles.samples,'frames':[]}
for d,angle in {'N':180,'E':90,'S':0,'W':-90}.items():
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update()
 sc.render.filepath=str(OUT/f'native-{d}.png');bpy.ops.render.render(write_still=True)
 report['frames'].append({'direction':d,'rootMatrix':[vec(r) for r in root.matrix_world],'path':sc.render.filepath})
(OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('JUDGE_REPLAY_COMPLETE',str(OUT))
