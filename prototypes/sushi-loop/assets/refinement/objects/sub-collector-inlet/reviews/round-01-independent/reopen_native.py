import bpy,json,pathlib,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path(__file__).resolve().parent;E=O.parent.parent;C=E/'candidates/round-01';R=O/'resources';D=O/'native';D.mkdir(exist_ok=True);s=bpy.data.scenes.get('Collector registered standalone') or bpy.context.scene
# Select saved scene by its actual refined collection; never invoke builder.
s=next(sc for sc in bpy.data.scenes if any(c.name=='REFINED__sub-collector-inlet' for c in sc.collection.children));bpy.context.window.scene=s;col=bpy.data.collections['REFINED__sub-collector-inlet'];root=bpy.data.objects['collector__root']
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def bb(ps):return [[min(p[i] for p in ps) for i in range(len(ps[0]))],[max(p[i] for p in ps) for i in range(len(ps[0]))]]
def apply(clip,di,fr):
 for suffix in ['guard_rock','mouth_pulse','mouth_sleeve']:
  ob=bpy.data.objects['collector__'+suffix];a=bpy.data.actions[f'INLET_NATIVE__{clip}__collector__{suffix}'];ob.animation_data_create();ob.animation_data.action=a;ob.animation_data.action_slot=next(x for x in a.slots if x.identifier=='OB'+ob.name)
  for t in ob.animation_data.nla_tracks:t.mute=True
 root.rotation_euler.z={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[di];s.frame_set(math.floor(fr),subframe=fr-math.floor(fr));bpy.context.view_layer.update()
def measure():
 dg=bpy.context.evaluated_depsgraph_get();ps=[];parts=[];finger=[]
 for ob in sorted(col.all_objects,key=lambda x:x.name):
  d={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'loc':list(ob.location),'rotation':list(ob.rotation_euler),'scale':list(ob.scale),'matrixBasis':[list(r) for r in ob.matrix_basis],'parentInverse':[list(r) for r in ob.matrix_parent_inverse]}
  if ob.type=='MESH':
   eo=ob.evaluated_get(dg);me=eo.to_mesh();v=[eo.matrix_world@v.co for v in me.vertices];ps+=v;parts.append({'name':ob.name,'bounds':bb(v),'matrix':[list(r) for r in eo.matrix_world]});d['evalVertices']=[list(v.co) for v in me.vertices];d['corners']=[list(n.vector) for n in me.corner_normals];d['uv']={u.name:[list(t.uv) for t in u.data] for u in me.uv_layers};d['polygons']=[list(f.vertices) for f in me.polygons];d['materials']=[m.name for m in me.materials];eo.to_mesh_clear()
  finger.append(d)
 xy=[]
 for p in ps:
  v=world_to_camera_view(s,s.camera,p);xy.append([v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y])
 return {'bounds':bb(ps),'pixelBounds':bb(xy),'parts':parts,'stateSHA256':hashlib.sha256(json.dumps(finger,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
records=[]
for clip in ['idle','active']:
 for di in 'NESW':
  for fr in range(1,2 if clip=='idle' else 14):
   apply(clip,di,fr);m=measure();p=D/f'{clip}-{di}-{fr:02d}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'clip':clip,'direction':di,'frame':fr,'image':str(p.relative_to(E)),'sha256':sha(p),**m})
# Fresh same-pose controls, unchanged rendering settings and source.
controls=[]
for di in 'NESW':
 for fr in [1,13]:
  for repeat in ['a','b']:
   apply('active',di,fr);m=measure();p=D/f'control-{di}-{fr}-{repeat}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);controls.append({'direction':di,'frame':fr,'repeat':repeat,'image':str(p.relative_to(E)),'sha256':sha(p),'stateSHA256':m['stateSHA256']})
# Continuous evaluated ground/footprint sweep; source channels use linear interpolation.
sweep=[]
for k in range(241):
 f=1+k/20;apply('active','S',f);m=measure();sweep.append({'frame':f,'bounds':m['bounds']})
cam=s.camera;v=world_to_camera_view(s,cam,Vector((0,0,0)));actions=[]
for a in bpy.data.actions:
 if not a.name.startswith('INLET_NATIVE'):continue
 cs=[]
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:cs.append({'path':fc.data_path,'index':fc.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in fc.keyframe_points]})
 actions.append({'name':a.name,'curves':cs})
report={'projectSHA256':sha(R/'round-01.blend'),'blender':bpy.app.version_string,'builderInvoked':False,'scene':s.name,'camera':{'matrix':[list(x) for x in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'rootPx':[v.x*s.render.resolution_x,(1-v.y)*s.render.resolution_y]},'settings':{'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'filterSize':s.render.filter_size,'dither':s.render.dither_intensity,'fps':s.render.fps,'resolution':[s.render.resolution_x,s.render.resolution_y],'lights':[{'name':o.name,'energy':o.data.energy,'position':list(o.location),'size':o.data.size} for o in s.objects if o.type=='LIGHT'],'libraries':[l.filepath for l in bpy.data.libraries]},'records':records,'freshSamePoseControls':controls,'sweep':sweep,'actions':actions}
(O/'native-reopened.json').write_text(json.dumps(report,indent=2)+'\n');print('INDEPENDENT_NATIVE_COMPLETE',len(records),len(controls),len(sweep))
