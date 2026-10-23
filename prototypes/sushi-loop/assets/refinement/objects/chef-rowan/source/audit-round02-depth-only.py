"""Saved-source semantic and all192 camera-ray/projection comparison to exact round01."""
import bpy,math,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-02';OUT.mkdir(exist_ok=True)
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());recipe=json.loads((HERE/'round-02-recipe.json').read_text());D=recipe['depthWorldCells']
spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def flat(o):
 result={}
 for p in o.bl_rna.properties:
  if p.identifier=='rna_type' or p.is_readonly:continue
  try:
   v=getattr(o,p.identifier)
   if p.type in ['BOOLEAN','INT','FLOAT','STRING','ENUM']:result[p.identifier]=list(v) if p.is_array else sorted(v) if isinstance(v,set) else v
   elif p.type=='POINTER':result[p.identifier]=v.name if isinstance(v,bpy.types.ID) else None
  except (AttributeError,TypeError,ValueError):pass
 return result

def custom(o):return {k:o[k].to_list() if hasattr(o[k],'to_list') else o[k].to_dict() if hasattr(o[k],'to_dict') else o[k] for k in o.keys() if k!='_RNA_UI' and not (o.name.endswith('__image_plane') and k=='camera_ray_depth_bias_world_cells')}
def drivers(o):
 return [dict(path=f.data_path,index=f.array_index,expression='GLOBAL_RAY_COEFFICIENT' if o.name.endswith('__image_plane') and f.data_path=='location' else f.driver.expression,type=f.driver.type,variables=[dict(settings=flat(v),targets=[flat(t) for t in v.targets]) for v in f.driver.variables]) for f in o.animation_data.drivers] if o.animation_data else []
def node_tree(t):
 return dict(nodes=[dict(name=n.name,type=n.bl_idname,settings=flat(n),inputs=[dict(name=s.name,identifier=s.identifier,value=list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value) for s in n.inputs if hasattr(s,'default_value')]) for n in t.nodes],links=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links]) if t else None

def semantic():
 root=bpy.data.objects[rig['groundRootObject']];plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane'];arm=bpy.data.objects[rig['armatures'][0]['object']]
 objs=[]
 for o in bpy.context.scene.objects:
  props=flat(o)
  if o==plane:
   for k in ['location','matrix_local','matrix_world','matrix_basis']:props.pop(k,None)
  objs.append(dict(name=o.name,settings=props,custom=custom(o),parentInverse=[list(r) for r in o.matrix_parent_inverse],modifiers=[flat(m) for m in o.modifiers],constraints=[flat(c) for c in o.constraints],groups=[flat(g) for g in o.vertex_groups],drivers=drivers(o)))
 meshes=[dict(name=m.name,vertices=[dict(co=list(v.co),weights=[(g.group,g.weight) for g in v.groups]) for v in m.vertices],edges=[list(e.vertices) for e in m.edges],polygons=[dict(vertices=list(p.vertices),material=p.material_index,smooth=p.use_smooth) for p in m.polygons],uv=[dict(name=l.name,values=[list(v.uv) for v in l.data]) for l in m.uv_layers],materials=[m.name for m in m.materials],attributes=[(a.name,a.data_type,a.domain) for a in m.attributes]) for m in bpy.data.meshes]
 actions=[dict(name=a.name,settings=flat(a),slots=[flat(s) for s in a.slots],fcurves=[dict(path=f.data_path,index=f.array_index,settings=flat(f),keys=[flat(k) for k in f.keyframe_points],modifiers=[flat(m) for m in f.modifiers]) for f in native._fcurves(a)]) for a in bpy.data.actions]
 bones=[dict(name=b.name,settings=flat(b),matrix=[list(r) for r in b.matrix_local],head=list(b.head_local),tail=list(b.tail_local),parent=b.parent.name if b.parent else None) for b in arm.data.bones]
 materials=[dict(name=m.name,settings=flat(m),nodes=node_tree(m.node_tree)) for m in bpy.data.materials]
 lights=[dict(name=l.name,settings=flat(l),nodes=node_tree(l.node_tree)) for l in bpy.data.lights]
 cameras=[dict(name=c.name,settings=flat(c)) for c in bpy.data.cameras]
 worlds=[dict(name=w.name,settings=flat(w),nodes=node_tree(w.node_tree)) for w in bpy.data.worlds]
 scene=bpy.context.scene
 return dict(objects=objs,meshes=meshes,actions=actions,bones=bones,materials=materials,lights=lights,cameras=cameras,worlds=worlds,render=flat(scene.render),view=flat(scene.view_settings),display=flat(scene.display_settings),frame=dict(start=scene.frame_start,end=scene.frame_end,fps=scene.render.fps),images=[dict(name=i.name,settings=flat(i),packedSHA256=hashlib.sha256(bytes(i.packed_file.data)).hexdigest() if i.packed_file else None) for i in bpy.data.images if i.source in ['FILE','TILED']])

def measure(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];arm=bpy.data.objects[rig['armatures'][0]['object']]
 snapshot=json.loads(json.dumps(semantic(),default=lambda v:list(v)));col.hide_viewport=False;col.hide_render=False
 def vis(lc):
  lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
  for c in lc.children:vis(c)
 vis(bpy.context.view_layer.layer_collection);arm.hide_set(False);bpy.context.view_layer.update()
 food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[food.name+'__image_plane'];utensil=bpy.data.objects[root.name+'__utensil'];asset=dict(root=root,collection=col)
 records=[]
 for clip in rig['clips']:
  for direction in ['N','E','S','W']:
   for frame in range(1,13):
    native.apply_clip(asset,rig,clip,frame,direction,scene);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pm=plane.evaluated_get(dg).matrix_world
    points=[pm@v.co for v in plane.data.vertices]+[pm@Vector((0,0,0))]
    def project(v):
     p=world_to_camera_view(scene,scene.camera,v);return [p.x*384,(1-p.y)*640]
    body=[]
    for o in col.objects:
     if o.type=='MESH' and o!=plane:
      eo=o.evaluated_get(dg);mesh=eo.to_mesh();body.append(dict(name=o.name,vertices=[[float(x) for x in eo.matrix_world@v.co] for v in mesh.vertices],visible=not o.hide_render));eo.to_mesh_clear()
    matrices={o.name:[list(r) for r in o.evaluated_get(dg).matrix_world] for o in [root,arm,food,utensil]}
    matrices['pose']=[[list(r) for r in p.matrix] for p in arm.evaluated_get(dg).pose.bones]
    records.append(dict(clip=clip,direction=direction,frame=frame,index=frame-1,worldPoints=[list(p) for p in points],projectedNativePixels=[project(p) for p in points],bodyKnifeWorldGeometrySHA256=h(body),rigFoodUtensilSHA256=h(matrices),foodVisible=not plane.hide_render,worldWidth=(pm.to_3x3()@Vector((.28,0,0))).length,worldHeight=(pm.to_3x3()@Vector((0,.28*505/731,0))).length,worldRotation=[list(r) for r in pm.to_3x3().normalized()]))
 return snapshot,records
baseline=OBJ/'inputs/baseline-round01.blend';candidate=HERE/'round-02.blend'
a,old=measure(baseline);b,new=measure(candidate)
sections={k:dict(baselineSHA256=h(a[k]),candidateSHA256=h(b[k]),equal=a[k]==b[k]) for k in a}
if a!=b:
 (OUT/'depth-semantic-debug.json').write_text(json.dumps(dict(baseline=a,candidate=b),indent=2)+'\n')
ray=Vector((0,-math.cos(math.radians(35)),math.sin(math.radians(35))));expected=(D-.6)*ray
records=[]
for x,y in zip(old,new):
 delta=[Vector(n)-Vector(o) for o,n in zip(x['worldPoints'],y['worldPoints'])]
 records.append(dict(clip=y['clip'],direction=y['direction'],index=y['index'],frame=y['frame'],depthWorldCells=D,projectedNativePixels=y['projectedNativePixels'],baselineProjectedNativePixels=x['projectedNativePixels'],maximumNativePixelError=max(abs(a-b) for p,q in zip(x['projectedNativePixels'],y['projectedNativePixels']) for a,b in zip(p,q)),maximumRayDisplacementError=max((d-expected).length for d in delta),bodyKnifeGeometryEqual=x['bodyKnifeWorldGeometrySHA256']==y['bodyKnifeWorldGeometrySHA256'],rigFoodUtensilEqual=x['rigFoodUtensilSHA256']==y['rigFoodUtensilSHA256'],visibilityEqual=x['foodVisible']==y['foodVisible'],width=y['worldWidth'],height=y['worldHeight'],orientationError=max(abs(x['worldRotation'][i][j]-y['worldRotation'][i][j]) for i in range(3) for j in range(3))))
checks=[dict(name='all semantic sections exactly round01 except permitted plane ray offset/provenance',passed=all(v['equal'] for v in sections.values())),dict(name='192 measured comparisons',passed=len(records)==192),dict(name='all projected quad corners and platebottom invariant within .0001 native pixels',passed=max(r['maximumNativePixelError'] for r in records)<.0001),dict(name='all displacement equals one shared exact camera ray scalar',passed=max(r['maximumRayDisplacementError'] for r in records)<1e-6),dict(name='all evaluated body and native knife geometry exactly equal',passed=all(r['bodyKnifeGeometryEqual'] for r in records)),dict(name='all evaluated rig/root/food/utensil matrices exactly equal',passed=all(r['rigFoodUtensilEqual'] for r in records)),dict(name='visibility unchanged all192',passed=all(r['visibilityEqual'] for r in records)),dict(name='canonical aspect/width/orientation invariant all192',passed=all(abs(r['width']-.35)<1e-6 and abs(r['height']-.35*505/731)<1e-6 and r['orientationError']<1e-6 for r in records))]
result=dict(activeBrief='brief-v3-food-depth.json',baseline='inputs/baseline-round01.blend',baselineSHA256=sha(baseline),source='source/round-02.blend',sourceSHA256=sha(candidate),depthWorldCells=D,priorDepth=.6,localHorizontalCoefficient=recipe['localHorizontalCoefficient'],localPlaneZ=recipe['localPlaneZ'],worldCameraRay=list(ray),allowedDifferences=['plane.location.z','plane existing locationX/Y driver common coefficient','plane existing camera_ray_depth_bias_world_cells provenance'],semanticSections=sections,checks=checks,allChecksPassed=all(c['passed'] for c in checks),records=records)
(OUT/'depth-only-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
assert result['allChecksPassed']
