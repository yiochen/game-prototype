from pathlib import Path
import bpy,math,json,runpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
p=Path(__file__).with_name('native-closure.py');t=p.read_text();exec(t[:t.index("out=[]")]+"out=[]",globals())
with bpy.data.libraries.load(str(F),link=False)as(a,b):b.collections=['S33_FB_belt-straight-n.001']
fc=b.collections[0];s.collection.children.link(fc);fc.hide_render=False;fc.hide_viewport=False
for ob in fc.all_objects:ob.hide_viewport=False;ob.hide_set(False)
bpy.context.view_layer.update()
def clone(coll,label,loc,angle):
 dest=bpy.data.collections.new(label);s.collection.children.link(dest);copies={o:o.copy()for o in coll.all_objects}
 for o,c in copies.items():dest.objects.link(c);c.hide_render=False;c.hide_viewport=False;c.hide_set(False);c.parent=copies.get(o.parent);c.matrix_parent_inverse=o.matrix_parent_inverse.copy();c.matrix_basis=o.matrix_basis.copy()
 r=next(o for o in copies.values()if '__root'in o.name);r.location=loc;r.rotation_euler.z=angle
 return r
r1=clone(fc,'Independent actual approved incoming family',(1,0,0),math.pi/2);r2=clone(fc,'Independent actual approved outgoing family',(0,1,0),0);s.collection.children.unlink(fc)
# Retain camera world basis and pixel aspect. Only expand presentation canvas;
# solve its ortho span/shift to retain exact256px/world cell at the registered root.
s.render.resolution_x=1152;s.render.resolution_y=1152
cam=s.camera
def px(v):
 p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*1152,(1-p.y)*1152))
bpy.context.view_layer.update();cam.data.ortho_scale*=((px((1,0,0))-px((0,0,0))).x/256)
for attr,axis,target in [('shift_x',0,390),('shift_y',1,800)]:
 old=getattr(cam.data,attr);base=px((0,0,0))[axis];setattr(cam.data,attr,old+.01);slope=(px((0,0,0))[axis]-base)/.01;setattr(cam.data,attr,old+(target-base)/slope)
s.cycles.samples=32;rec=[]
for d,ang in [('S',0),('N',math.pi)]:
 root.rotation_euler.z=ang
 if d=='N':r1.location=(-1,0,0);r2.location=(0,-1,0);r1.rotation_euler.z=-math.pi/2;r2.rotation_euler.z=math.pi
 s.frame_set(1);bpy.context.view_layer.update();s.render.filepath=str(O/f'baseline-native-mixed-{d}.png');bpy.ops.render.render(write_still=True);rec.append({'direction':d,'path':str(Path(s.render.filepath).relative_to(B))})
(O/'native-mixed.json').write_text(json.dumps({'role':'Independent baseline only. Genuine original corner meshes with approved native straight copies, open exact ports. This is not candidate geometry and source and family material treatment intentionally differs. Not a welded/unbroken equivalence proof.','cellPitch':256,'cameraWorldBasisRetained':True,'renders':rec},indent=2))
