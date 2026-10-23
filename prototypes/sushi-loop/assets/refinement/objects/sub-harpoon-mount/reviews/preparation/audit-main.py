import bpy,json,pathlib
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parent;sc=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];root.rotation_euler=(0,0,0);root.location=(0,0,0)
actions=json.loads(root['nativeActions'])
for owner,an in actions['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();seats=[];objects=[]
def bb(vs):return [[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]]
for o in sc.objects:
 if o.type!='MESH':continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];objects.append({'name':o.name,'hidden':o.hide_render,'bounds':bb(pts)})
 if o.name=='body__harpoon_contact_seat':
  for f in me.polygons:
   n=(eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()
   if n.z>.999:seats.append({'object':o.name,'normal':list(n),'vertices':[list(pts[i]) for i in f.vertices],'bounds':bb([pts[i] for i in f.vertices]),'area':float(f.area)})
 eo.to_mesh_clear()
m=bpy.data.objects['MOUNT__sub-harpoon-mount'];inv=m.matrix_world.inverted()
for f in seats:f['localVertices']=[list(inv@Vector(v)) for v in f['vertices']]
(P/'independent-frozen-main-audit.json').write_text(json.dumps({'sourceSHA256':'c8462a4072c8ce12f2afcc6907a02d705dcd7df6858f7d790bb2a1dcc5d7fb0e','mainClip':'upgraded-dock-ready frame1 neutral','rootMatrix':[list(r) for r in root.matrix_world],'mountActualMatrix':[list(r) for r in m.matrix_world],'finiteSeatFaces':seats,'nativeObjects':objects,'mainActions':actions['upgraded-dock-ready']},indent=2)+'\n')
