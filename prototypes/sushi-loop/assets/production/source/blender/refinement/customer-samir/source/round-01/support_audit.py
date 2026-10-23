import bpy,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
D=Path(__file__).resolve().parent;RES=D/'resources';P=D.parent.parent
MODE=next((x for x in sys.argv if x in ['main','runtime']),'main');TAG='candidate' if '--candidate' in sys.argv else 'source'
rig=json.loads((RES/('source-'+MODE+'-rig.json')).read_text());root=bpy.data.objects[rig['groundRootObject']];collection=next(c for c in bpy.data.collections if root in list(c.all_objects));scene=next(s for s in bpy.data.scenes if root in list(s.objects));bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
for c in scene.collection.children:c.hide_viewport=c!=collection;c.hide_render=c!=collection
for l in scene.view_layers:
 def visit(q):
  q.exclude=False;q.hide_viewport=False
  for c in q.children:visit(c)
 visit(l.layer_collection)
collection.hide_viewport=False;arm=next(o for o in collection.all_objects if o.type=='ARMATURE');asset={'root':root,'collection':collection}
spec=importlib.util.spec_from_file_location('samir_native',RES/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
parts={o.name.split('customer_samir__')[1].split('.')[0]:o for o in collection.all_objects if o.type=='MESH' and 'customer_samir__' in o.name}
supports={'left-foot':('minimal_foot_L','foot_L',(-.115,-.02,0)),'right-foot':('minimal_foot_R','foot_R',(.115,-.02,0)),'seat':('pelvis','pelvis',(0,.006,.070000008)),'left-palm':('palm_L','hand_L',(-.267,-.025,.216999993)),'right-palm':('palm_R','hand_R',(.267,-.025,.216999993)),'left-thumb':('thumb_L','hand_L',(-.229,-.081,.183)),'right-thumb':('thumb_R','hand_R',(.229,-.081,.183)),'mouth':('smile','head',(0,-.256999999,.537799984))}
rows=[]
for clip in rig['clips']:
 for direction in ['S','E','N','W']:
  for frame in range(1,13):
   native.apply_clip(asset,rig,clip,frame,direction,scene);dg=bpy.context.evaluated_depsgraph_get();points={}
   for label,(name,bone,point) in supports.items():
    target=arm.matrix_world@arm.pose.bones[bone].matrix@arm.data.bones[bone].matrix_local.inverted()@Vector(point)
    e=parts[name].evaluated_get(dg);me=e.to_mesh();verts=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];tree=BVHTree.FromPolygons(verts,faces,all_triangles=False);hit=tree.find_nearest(target);e.to_mesh_clear()
    points[label]={'authoredSurfaceProbeWorld':list(target),'nearestRemodeledSurfaceWorld':list(hit[0]),'distanceWorld':hit[3]}
   rows.append({'clip':clip,'direction':direction,'frame':frame,'supports':points})
OUT=P/'candidates/round-01'/('support-'+MODE+'-'+TAG+'.json');OUT.write_text(json.dumps({'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'mode':MODE,'tag':TAG,'definition':'Eight functional surface probes are source-defined rest-space points on foot soles, seat underside, palm support faces and mouth. Compare nearest posed native surface on the corresponding anatomical mesh, independent of exact rig/contact transforms.','samples':rows},indent=2)+'\n');print(OUT)
