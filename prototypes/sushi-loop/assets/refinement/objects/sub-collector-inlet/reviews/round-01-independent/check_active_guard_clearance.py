import bpy,pathlib,json
from mathutils.bvhtree import BVHTree
O=pathlib.Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(O/'resources/round-01.blend'));s=bpy.context.scene;root=bpy.data.objects['collector__root'];root.rotation_euler.z=0
for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
 ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__active__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=a.slots[0]
def geo(name,dg):
 ob=bpy.data.objects[name];eo=ob.evaluated_get(dg);me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];ps=[list(p.vertices) for p in me.polygons];bv=BVHTree.FromPolygons(vs,ps,all_triangles=False);eo.to_mesh_clear();return vs,bv
records=[]
for fr in range(1,13):
 s.frame_set(fr);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pair=[]
 for moving in ['collector__guard_cage','collector__guard_bar_-0.15','collector__guard_bar_0','collector__guard_bar_0.15']:
  vs,bv=geo(moving,dg)
  for fixed in ['collector__mouth_surround','collector__hollow_enamel_shell','collector__dark_mouth']:
   fs,fv=geo(fixed,dg);ov=bv.overlap(fv);inside=[]
   for p in vs:
    q,n,index,d=fv.find_nearest(p)
    if (p-q).dot(n)<-1e-6:inside.append({'p':list(p),'depth':d})
   if ov or inside:pair.append({'moving':moving,'fixed':fixed,'surfacePairs':len(ov),'insideVertices':len(inside),'deepestNearestSigned':max((p['depth'] for p in inside),default=0),'deepestSamples':sorted(inside,key=lambda x:x['depth'],reverse=True)[:3]})
  
 records.append({'frame':fr,'guardRotationX':bpy.data.objects['collector__guard_rock'].rotation_euler.x,'contacts':pair})
(O/'active-guard-clearance.json').write_text(json.dumps({'purpose':'Resolve visually observed inward guard upper rail occlusion: actual evaluated surface intersections and nearest-oriented-surface containment diagnostics. Surface pair counts alone are not a verdict; source images inspected separately.','records':records},indent=2)+'\n');print(json.dumps(records,indent=2)[:14000])
