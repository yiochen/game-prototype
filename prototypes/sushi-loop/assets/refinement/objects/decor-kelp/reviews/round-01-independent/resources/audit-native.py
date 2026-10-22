import bpy,json,sys,math,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE.parent/'evidence';source=ROOT/'source/round-01.blend'
# Scene and all owning collections are selected from the actual saved file.
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;col=bpy.data.collections['S33 production concept kelp-fan'];root=bpy.data.objects['S33 production concept kelp-fan root']
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=lc.collection!=col
col.hide_viewport=False;col.hide_render=False
objects=list(col.all_objects);meshes=[o for o in objects if o.type=='MESH']
spec=importlib.util.spec_from_file_location('independent_frozen_projection',ROOT/'reviews/preparation-v1/resources/concept_decoration_geometry.py');law=importlib.util.module_from_spec(spec);spec.loader.exec_module(law)
def world(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];polys=[tuple(p.vertices)for p in me.polygons];ev.to_mesh_clear();return vs,polys
def tree(vp):return BVHTree.FromPolygons(*vp)
def inside(t,p):
 d=Vector((.913,.287,.289)).normalized();start=p.copy();n=0
 for _ in range(100):
  hit,normal,index,dist=t.ray_cast(start,d,100)
  if hit is None:break
  n+=1;start=hit+d*2e-6
 return n%2==1
inventory=[]
for o in objects:
 row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'role':o.get('role'),'matrix':[[*r]for r in o.matrix_world],'constraints':[x.type for x in o.constraints]}
 if o.type=='MESH':
  edgeUses={tuple(sorted(e.vertices)):0 for e in o.data.edges}
  for p in o.data.polygons:
   for a,b in zip(p.vertices,list(p.vertices[1:])+[p.vertices[0]]):edgeUses[tuple(sorted((a,b)))]+=1
  row.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),nonmanifoldEdges=sum(n!=2 for n in edgeUses.values()),UVs=[u.name for u in o.data.uv_layers],modifiers=[m.type for m in o.modifiers],shapeKeys=bool(o.data.shape_keys),capIndices=list(o.get('capRingIndices',[])))
 if o.animation_data:
  row['drivers']=[x.data_path for x in o.animation_data.drivers];row['action']=o.animation_data.action.name if o.animation_data.action else None
 inventory.append(row)
materials=[]
for m in {m for o in meshes for m in o.data.materials if m}:
 materials.append({'name':m.name,'textures':[n.image.filepath if n.image else None for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],'animation':bool(m.node_tree.animation_data),'nodes':[n.type for n in m.node_tree.nodes]})
records=[];closures=[];fixedData={o.name:[v.co.copy()for v in o.data.vertices]for o in meshes}
for d,a in {'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}.items():
 first=None
 for frame in range(1,14):
  sc.frame_set(frame);root.rotation_euler=(0,0,a);bpy.context.view_layer.update();pre={o.name:world(o)for o in meshes};pts=[v for vs,polys in pre.values()for v in vs];bases=[tree(pre[o.name])for o in meshes if o.get('role')=='grounded-cobalt'];contacts=[]
  for o in meshes:
   if o.get('role')not in ['primary-frond','attached-fork']:continue
   cap=[pre[o.name][0][i]for i in o['capRingIndices']];cap.append(sum(cap,Vector())/len(cap));ts=bases if o.get('role')=='primary-frond'else[tree(pre[o['primary']])];flags=[any(inside(t,p)for t in ts)for p in cap];contacts.append({'owner':o.name,'nPoints':len(cap),'allEmbedded':all(flags)})
  row={'direction':d,'frame':frame,'rootRotation':[*root.rotation_euler],'rootLocation':[*root.location],'rootScale':[*root.scale],'envelope':[[min(v[i]for v in pts),max(v[i]for v in pts)]for i in range(3)],'contacts':contacts}
  if first is None:first=pre
  if frame==13:closures.append({'direction':d,'maximumWorldDelta':max((x-y).length for name,(vs,ps)in pre.items()for x,y in zip(vs,first[name][0]))})
  with law.capture_projection(col,'ordinary35'):
   maxerr=0;post={o.name:world(o)for o in meshes}
   for name,(vs,ps)in pre.items():
    for before,after in zip(vs,post[name][0]):
     expected=before.copy();b=max(0,1-max(0,before.z)/.42)**2;expected.y*=1+(1/math.sin(math.radians(35))-1)*b;maxerr=max(maxerr,(after-expected).length)
   row['maxSourceLawVsEvaluatedError']=maxerr;row['captureEnvelope']=[[min(v[i]for vs,ps in post.values()for v in vs),max(v[i]for vs,ps in post.values()for v in vs)]for i in range(3)]
  row['restorationMaxDataError']=max((v.co-fixedData[o.name][i]).length for o in meshes for i,v in enumerate(o.data.vertices));records.append(row)
result={'asset':'decor-kelp','blender':bpy.app.version_string,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'scene':sc.name,'camera':{'name':sc.camera.name,'type':sc.camera.data.type,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'worldMatrix':[[*r]for r in sc.camera.matrix_world],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y]},'inventory':inventory,'materials':materials,'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'path':x.filepath,'packed':bool(x.packed_file)}for x in bpy.data.images],'lights':[{'location':[*o.location],'power':o.data.energy,'size':o.data.size,'rotation':[*o.rotation_euler]}for o in sc.objects if o.type=='LIGHT'],'records':records,'closures':closures,'scope':'Independent actual saved-source52-phase evaluation. Finite root/fork cap vertices+centers tested by odd-ray BVHs against actual transformed solids. Source-derived ordinary35 adapter measured against independently computed formula, then restored. No model save or generation.'}
(OUT/'independent-native-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'objects':len(objects),'meshes':len(meshes),'materials':len(materials),'samples':len(records),'contactFailures':sum(not c['allEmbedded']for r in records for c in r['contacts']),'closure':closures,'lawMax':max(r['maxSourceLawVsEvaluatedError']for r in records),'restorationMax':max(r['restorationMaxDataError']for r in records)}))
