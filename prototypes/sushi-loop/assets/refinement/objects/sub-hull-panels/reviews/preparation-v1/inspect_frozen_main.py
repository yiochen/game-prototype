import bpy,json,pathlib,math
from mathutils import Vector,Matrix
out=pathlib.Path(__file__).resolve().parent;sc=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root']
print('ROOT_PROPS',dict(root.items()));print('SCENE',sc.name)
print('OBJECTS',[(o.name,o.parent.name if o.parent else None,o.type) for o in sc.objects])
actions=json.loads(root['nativeActions'])
print('CLIPS',list(actions))
for owner,an in actions['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
root.location=(0,0,0);root.rotation_euler=(0,0,0);sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def bb(pts):return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
seats=[]
for o in sc.objects:
 if o.type!='MESH' or 'panel_contact_seat' not in o.name:continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];faces=[]
 for f in me.polygons:
  n=(eo.matrix_world.to_3x3().inverted().transposed()@f.normal).normalized()
  if n.z>.999:
   vs=[pts[i] for i in f.vertices];faces.append({'normal':list(n),'vertices':[list(v) for v in vs],'bounds':bb(vs),'area':float(f.area)})
 seats.append({'name':o.name,'bounds':bb(pts),'actualFiniteFaces':faces});eo.to_mesh_clear()
mount=bpy.data.objects['MOUNT__sub-hull-panels'];expected=Matrix(json.loads((out/'resources/frozen-main-v1/manifest.json').read_text())['componentMount']['matrixLocal'])
result={'source':'resources/frozen-main-v1/project.blend','exactRootMatrix':[list(r) for r in root.matrix_world],'mountMatrix':[list(r) for r in mount.matrix_local],'mountMatrixMaximumError':max(abs(mount.matrix_local[r][c]-expected[r][c]) for r in range(4) for c in range(4)),'finitePanelSeats':seats,'nativeMainClips':actions,'visibleOriginalMainObjects':[o.name for o in sc.objects if o.type=='MESH' and not o.hide_render],'mainObjects':[{'name':o.name,'parent':o.parent.name if o.parent else None,'props':{k:str(v) for k,v in o.items()}} for o in sc.objects]}
(out/'frozen-main-inspection.json').write_text(json.dumps(result,indent=2));print('FINITE_SEATS',seats)
