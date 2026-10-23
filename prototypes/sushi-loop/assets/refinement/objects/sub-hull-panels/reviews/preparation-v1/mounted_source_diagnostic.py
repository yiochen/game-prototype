import bpy,json,pathlib,math,hashlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
out=pathlib.Path(__file__).resolve().parent;(out/'mounted-source-diagnostic').mkdir(exist_ok=True);sc=bpy.context.scene
root=bpy.data.objects['submarine-yellow__root'];acts=json.loads(root['nativeActions'])
for owner,name in acts['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];a=bpy.data.actions[name];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
root.rotation_euler=(0,0,0);sc.frame_set(1)
with bpy.data.libraries.load(str(out/'source-replay/original-collection.blend'),link=False) as (a,b):
 b.collections=['S33_PROP_hull_panel.001'];b.actions=[n for n in a.actions if n.startswith('S33_NATIVE__sub-hull-panels__idle__')]
coll=b.collections[0];sc.collection.children.link(coll)
rr=next(o for o in coll.objects if o.type=='EMPTY');rr.parent=bpy.data.objects['MOUNT__sub-hull-panels'];rr.location=(0,0,0);rr.rotation_euler=(0,0,0);rr.scale=(1,1,1)
rig=json.loads((out/'resources/experiment/inputs/source-rig.json').read_text())
for target in rig['clips']['idle']['actions']:
 o=bpy.data.objects[target['ownerName']];a=bpy.data.actions[target['action']];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
for o in coll.objects:o.hide_set(False);o.hide_render=False;o.hide_viewport=False
for o in sc.objects:
 if o.name.startswith('PROVISIONAL__panel'):o.hide_render=True
sc.frame_set(1)
for o in sc.objects:
 if o.name.startswith('PROVISIONAL__panel'):
  o.animation_data_clear();o.hide_render=True
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def geometry(o):
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];polys=[list(p.vertices) for p in me.polygons];eo.to_mesh_clear();return pts,polys
source=[o for o in coll.objects if o.type=='MESH'];bounds={}
for o in source:
 pts,_=geometry(o);bounds[o.name]=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
collisions=[]
for a in source:
 av,ap=geometry(a);tree=BVHTree.FromPolygons(av,ap,all_triangles=False)
 for b in sc.objects:
  if b.type!='MESH' or not b.name.startswith('body__periscope'):continue
  bv,bp=geometry(b);pairs=tree.overlap(BVHTree.FromPolygons(bv,bp,all_triangles=False))
  if pairs:collisions.append({'source':a.name,'frozenBody':b.name,'intersectingSurfacePairs':len(pairs)})
manifest={'scope':'Exact OLD neutral source mounted without reshaping at frozen .5 transform. Deliberately nonconforming diagnostic, not candidate art, fixture body static, other equipment provisional.','originalNeutralCollectionSHA256':hashlib.sha256((out/'source-replay/original-collection.blend').read_bytes()).hexdigest(),'mainSourceSHA256':hashlib.sha256((out/'resources/frozen-main-v1/project.blend').read_bytes()).hexdigest(),'mountMatrix':[list(r) for r in rr.parent.matrix_local],'oldMountedMeshBounds':bounds,'periscopeTriangleSurfaceIntersections':collisions,'finiteContactConclusion':'Old plate footprint X ±.145 cannot reach the two finite seat patches |X| .181..249. Its planar underside is at world Z .665, .015 above seat Z .650. Thus it has zero finite face contact on either seat.','renders':[]}
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=ang;bpy.context.view_layer.update();path=out/'mounted-source-diagnostic'/f'old-source-mounted-{d}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);manifest['renders'].append({'direction':d,'path':str(path.relative_to(out)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(out/'mounted-source-diagnostic/diagnostic.json').write_text(json.dumps(manifest,indent=2));print('DONE',collisions)
