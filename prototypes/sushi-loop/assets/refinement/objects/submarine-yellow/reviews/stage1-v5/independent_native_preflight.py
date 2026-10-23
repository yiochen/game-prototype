import bpy,json,math,hashlib,pathlib,itertools
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
OUT=pathlib.Path(__file__).resolve().parent;SRC=OUT/'resources/source/stage1-v5/submarine-stage1.blend';CAND=OUT/'resources/candidates/stage1-v5';sc=bpy.context.scene
root=bpy.data.objects['submarine-yellow__root'];col=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];objects=list(col.all_objects);meshes=[o for o in objects if o.type=='MESH'];registry=json.loads(root['nativeActions']);clips=json.loads(root['clips']);motion=bpy.data.objects['submarine-yellow__body_motion'];lamp=bpy.data.objects['body__status_cyan_lens']
def vv(v):return [float(x) for x in v]
def box(pts):return [[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
def assign(clip,f,d):
 for owner,name in registry[clip].items():
  ob=bpy.data.objects[owner];ob.animation_data_create();a=bpy.data.actions[name];ob.animation_data.action=a
  if len(a.slots)==1:ob.animation_data.action_slot=a.slots[0]
  else:raise RuntimeError('Ambiguous slots '+name)
 root.location=(0,0,0);root.rotation_euler.z={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d];sc.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update()
assign('dock-ready',1,'S');dg=bpy.context.evaluated_depsgraph_get();local={};geometry=[]
for o in meshes:
 assert not o.data.shape_keys,o.name
 assert not o.data.animation_data,o.name
 assert not o.modifiers,o.name
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[v.co.copy() for v in me.vertices];local[o.name]=pts;geometry.append({'name':o.name,'vertices':len(pts),'materials':[m.name for m in me.materials],'parent':o.parent.name if o.parent else None,'rawMeshSHA256':hashlib.sha256(json.dumps({'v':[vv(v.co) for v in me.vertices],'f':[list(p.vertices) for p in me.polygons],'n':[vv(p.normal) for p in me.polygons],'uv':[[vv(d.uv) for d in u.data] for u in me.uv_layers]},separators=(',',':')).encode()).hexdigest()});eo.to_mesh_clear()
cam=sc.camera
project=lambda pt:[world_to_camera_view(sc,cam,Vector(pt)).x*sc.render.resolution_x,(1-world_to_camera_view(sc,cam,Vector(pt)).y)*sc.render.resolution_y]
settings={'blender':bpy.app.version_string,'sourceSHA256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'meshCount':len(meshes),'rootMatrix':[vv(r) for r in root.matrix_world],'camera':{'matrix':[vv(r) for r in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'root':project((0,0,0)),'unitX':project((1,0,0)),'unitY':project((0,1,0)),'unitZ':project((0,0,1))},'render':{'engine':sc.render.engine,'filter':sc.render.filter_size,'transparent':sc.render.film_transparent,'fps':sc.render.fps,'samples':sc.eevee.taa_render_samples},'lights':[{'name':o.name,'type':o.data.type,'location':vv(o.location),'power':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT'],'resources':{'images':[{'name':x.name,'source':x.source,'path':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images],'libraries':[x.filepath for x in bpy.data.libraries]},'mounts':{o.name:[vv(r) for r in o.matrix_local] for o in objects if o.name.startswith('MOUNT__')},'legacyReferences':{n:vv(bpy.data.objects[n].location) for n in ['sub_harpoon','sub_collector']},'clips':clips,'geometry':geometry}
channelpaths=set()
for c,owners in registry.items():
 for own,an in owners.items():
  ac=bpy.data.actions[an]
  for layer in ac.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:channelpaths.add(fc.data_path)
assert channelpaths <= {'location','rotation_euler','scale','hide_render','hide_viewport'},channelpaths
records=[];closures=[];viol=[];diff=[];expected=json.loads((CAND/'saved-action-phases.json').read_text())['phases'];emap={(x['clip'],x['direction'],x['frame']):x for x in expected}
for c in registry:
 for d in ['N','E','S','W']:
  first=None
  for step in range(25):
   f=1+step*.5;assign(c,f,d);dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();pts=[];parts=[]
   for o in meshes:
    if o.hide_render:continue
    eo=o.evaluated_get(dg);m=inv@eo.matrix_world;pp=[m@v for v in local[o.name]];pts+=pp;parts.append(o.name)
   b=box(pts);ref=emap[(c,d,f)];err=max(abs(b[s][i]-ref['canonicalBounds'][s][i]) for s in range(2) for i in range(3));
   if err>1e-6 or set(parts)!=set(ref['visibleMeshNames']):diff.append({'clip':c,'direction':d,'frame':f,'boundsMaxError':err,'visibilityEqual':set(parts)==set(ref['visibleMeshNames'])})
   cap=.56 if 'dock-' in c else .61
   if b[0][0]<-cap-1e-6 or b[1][0]>cap+1e-6 or b[0][1]<-.64-1e-6 or b[1][1]>.68+1e-6 or b[0][2]<.01-1e-6 or b[1][2]>1.12+1e-6:viol.append({'clip':c,'direction':d,'frame':f,'bounds':b})
   records.append({'clip':c,'direction':d,'frame':f,'bounds':b,'visibleCount':len(parts),'motionLocation':vv(motion.location),'statusVisible':not lamp.hide_render,'statusScale':vv(lamp.scale),'suppliedBoundsMaxError':err})
   if step==0:first=pts
   if step==24 and clips[c]['loop']:closures.append({'clip':c,'direction':d,'sameVertexCount':len(first)==len(pts),'maxVertexDelta':max((a-b).length for a,b in zip(first,pts))})
 print('AUDITED',c,flush=True)
(OUT/'independent-native-settings.json').write_text(json.dumps(settings,indent=2)+'\n');(OUT/'independent-native-phases.json').write_text(json.dumps({'phaseCount':len(records),'cachedMeshJustification':'All native local meshes checked no modifiers/shape keys/data animation; action paths restricted to transforms/visibility. Each phase uses evaluated world matrices and actual visibility.','actualActionPaths':sorted(channelpaths),'phases':records,'closures':closures,'suppliedEvidenceDifferences':diff,'envelopeViolations':viol},separators=(',',':'))+'\n')
# Independent saved-source replay, two representatives only; selected original captures remain authoritative.
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
for d in ['S','N']:
 assign('dock-ready',1,d);sc.render.filepath=str(OUT/('independent-replay-dock-ready-'+d+'.png'));bpy.ops.render.render(write_still=True)
print('RESULT',json.dumps({'phaseCount':len(records),'differences':len(diff),'violations':len(viol),'loopClosures':len(closures),'maxClosureDelta':max(x['maxVertexDelta'] for x in closures)}),flush=True)
