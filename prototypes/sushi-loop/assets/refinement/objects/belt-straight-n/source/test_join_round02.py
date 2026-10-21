import bpy,pathlib,math,json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-02.blend'));s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-straight-n.001'];root=next(o for o in c.objects if '__root.' in o.name);original=list(c.objects);clones=[]
for i in [-1,1]:
 mapping={}
 for o in original:
  q=o.copy();c.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 clones.append((i,mapping[root]))
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
for direction,rot in [('N',math.pi),('E',math.pi/2)]:
 root.rotation_euler.z=rot
 for i,q in clones:q.rotation_euler.z=rot;q.location=(0,i,0) if direction=='N' else (i,0,0)
 s.frame_set(1);bpy.context.view_layer.update()
 cal={n:[world_to_camera_view(s,s.camera,Vector(pt)).x*896,(1-world_to_camera_view(s,s.camera,Vector(pt)).y)*1216] for n,pt in {'root':(0,0,0),'x':(1,0,0),'depth':(0,-1,0),'z':(0,0,1)}.items()}
 print('CAL',direction,cal);s.render.filepath=str(P/'candidates/round-02'/('native-'+direction+'-00.png'));bpy.ops.render.render(write_still=True)
