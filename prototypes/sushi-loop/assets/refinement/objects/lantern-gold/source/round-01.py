"""Exact native lantern refinement recipe. Blender --background --python this.py [-- --study]."""
import bpy, json, pathlib, math, hashlib, sys, bmesh
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=pathlib.Path(__file__).resolve().parent.parent
STUDY='--study' in sys.argv
ROUND='study' if STUDY else 'round-01'
OUT=HERE/'candidates'/ROUND
OUT.mkdir(parents=True,exist_ok=True)
brief=json.loads((HERE/'brief.json').read_text())
camera_source=json.loads((HERE/'inputs/source-camera.json').read_text())
rig=json.loads((HERE/'inputs/source-rig.json').read_text())
src=(HERE/brief['source']['project']).resolve()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,v):pathlib.Path(p).write_text(json.dumps(v,indent=2)+'\n')
def vv(v):return [float(x) for x in v]
def mm(m):return [vv(r) for r in m]
bpy.ops.wm.open_mainfile(filepath=str(src))
col=bpy.data.collections['S33_PROP_lantern.001']
sc=bpy.data.scenes.new('Lantern Gold Warm Soft Native')
sc.collection.children.link(col)
col.hide_viewport=False;col.hide_render=False
bpy.context.window.scene=sc
bpy.context.window.view_layer=sc.view_layers[0]
owned=set(col.all_objects)
for o in owned:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
root=bpy.data.objects[rig['groundRootObject']]
for t in rig['clips']['idle']['actions']:
 o=bpy.data.objects[t['ownerName']];o.animation_data_create();o.animation_data.action=bpy.data.actions[t['action']]
 if t.get('slotIdentifier'):o.animation_data.action_slot=next(s for s in o.animation_data.action.slots if s.identifier==t['slotIdentifier'])
 for track in o.animation_data.nla_tracks:track.mute=True
def pose(direction,frame):
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[direction]
 sc.frame_set(frame);sc.view_layers[0].update()
def geometry(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
 pts=[ev.matrix_world@v.co for v in mesh.vertices]
 bm=bmesh.new();bm.from_mesh(mesh)
 result={'vertices':len(mesh.vertices),'edges':len(mesh.edges),'polygons':len(mesh.polygons),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'looseVertices':sum(not v.link_edges for v in bm.verts),'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'matrixWorld':mm(o.matrix_world),'localMatrix':mm(o.matrix_local),'uvLayers':[v.name for v in o.data.uv_layers]}
 bm.free();ev.to_mesh_clear();return result
def snapshot(direction,frame):
 pose(direction,frame)
 return {o.name:geometry(o) if o.type=='MESH' else {'matrixWorld':mm(o.matrix_world),'localMatrix':mm(o.matrix_local)} for o in sorted(owned,key=lambda o:o.name)}
def action_record():
 records=[]
 for t in rig['clips']['idle']['actions']:
  a=bpy.data.actions[t['action']]
  curves=[c for l in a.layers for st in l.strips for bag in st.channelbags for c in bag.fcurves]
  val=[{'path':f.data_path,'index':f.array_index,'keys':[vv(k.co) for k in f.keyframe_points],'interpolation':[k.interpolation for k in f.keyframe_points]} for f in curves]
  records.append({**t,'channels':val,'dataSha256':hashlib.sha256(json.dumps(val,sort_keys=True).encode()).hexdigest()})
 return records
source_actions=action_record()
baseline={d:[snapshot(d,f) for f in range(1,14)] for d in 'NESW'}
write(HERE/'source'/f'{ROUND}-baseline.json',{'sourceSha256':sha(src),'originalActionRecords':source_actions,'measurements':baseline})
pose('S',1)
# Remove all unrelated project datablocks; the original remains untouched.
for old in list(bpy.data.scenes):
 if old!=sc:bpy.data.scenes.remove(old)
for o in list(bpy.data.objects):
 if o not in owned:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c!=col:bpy.data.collections.remove(c)
for m in list(bpy.data.materials):
 if m.users==0:bpy.data.materials.remove(m)
def material(name,color,rough=.6,spec=.22,emission=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 nodes=m.node_tree.nodes;nodes.clear()
 out=nodes.new('ShaderNodeOutputMaterial');p=nodes.new('ShaderNodeBsdfPrincipled')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec
 p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface'])
 return m
paper=material('Warm soft golden paper',(1,.54,.065),.65,.18,.25)
gold=material('Warm soft amber golden ribs',(.80,.38,.020),.51,.24,.018)
wood=material('Warm soft bracket wood',(.38,.15,.041),.65,.22)
darkwood=material('Warm soft cap and plinth wood',(.22,.080,.023),.7,.18)
metal=material('Warm soft bronze hook',(.095,.057,.030),.7,.18)
for o in sorted(owned,key=lambda o:o.name):
 if o.type!='MESH':continue
 o.data=o.data.copy()
 o.data.materials.clear()
 o.data.materials.append(paper if 'glow_body' in o.name else gold if '__rib_' in o.name else darkwood if ('__cap_' in o.name or '__plinth' in o.name) else metal if '__hanging_hook' in o.name else wood)
 for p in o.data.polygons:p.use_smooth=True
 bevel=next((m for m in o.modifiers if m.type=='BEVEL'),None)
 if bevel is None:
  bevel=o.modifiers.new('Soft native edge curvature','BEVEL')
  bevel.width=.010 if 'glow_body' in o.name else .006 if '__rib_' in o.name else .007 if '__cap_' in o.name else .003
 bevel.segments=4;bevel.limit_method='ANGLE';bevel.angle_limit=.35;bevel.harden_normals=True
 bevel.use_clamp_overlap=True
 normal=o.modifiers.new('Weighted structural face normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=35
cam=bpy.data.objects.new('Lantern fixed registered camera',bpy.data.cameras.new('Lantern fixed registered camera'))
sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.clip_start=.1;cam.data.clip_end=1000
cam.matrix_world=Matrix(camera_source['camera']['worldMatrix'])
sc.render.resolution_x=384;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=camera_source['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=camera_source['camera']['pixelAspect'][1]
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*384,(1-p.y)*768))
sc.view_layers[0].update();cam.data.shift_y=0;base=px((0,0,0));cam.data.shift_y=1;sc.view_layers[0].update();dy=px((0,0,0)).y-base.y
cam.data.shift_y=(576-base.y)/dy;cam.data.shift_x=0;sc.view_layers[0].update()
sc.world=bpy.data.worlds.new('Neutral soft ambient');sc.world.use_nodes=True
bg=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.25
def area(name,loc,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=(1,1,1)
 o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location+Vector((0,0,.65))).to_track_quat('-Z','Y').to_euler();return o
area('Broad centered overhead',(0,0,4.5),160,4)
for i in range(8):
 a=i*math.tau/8;area(f'Symmetric neutral fill {i}',(3*math.cos(a),3*math.sin(a),2.0),24,4)
sc.render.engine='CYCLES';sc.cycles.samples=48;sc.cycles.use_denoising=True;sc.cycles.seed=41;sc.cycles.use_animated_seed=False
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for dev in prefs.devices:dev.use=dev.type=='METAL'
sc.cycles.device='GPU'
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30
sc.render.fps=12;sc.frame_start=1;sc.frame_end=12;sc.render.dither_intensity=0;sc.render.use_file_extension=True;sc.render.use_persistent_data=True
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.render.use_compositing=False;sc.render.use_sequencer=False
for a in list(bpy.data.actions):
 if not any(t['action']==a.name for t in rig['clips']['idle']['actions']):bpy.data.actions.remove(a)
for m in list(bpy.data.materials):
 if m.users==0:bpy.data.materials.remove(m)
for image in list(bpy.data.images):bpy.data.images.remove(image)
for lib in bpy.data.libraries:assert False,lib.filepath
pose('S',1)
camera={**camera_source,'captureScale':2,'calibration':{'root':vv(px((0,0,0))),'unitX':vv(px((1,0,0))-px((0,0,0))),'unitDepth':vv(px((0,-1,0))-px((0,0,0))),'unitHeight':vv(px((0,0,1))-px((0,0,0)))}}
camera['camera']={**camera_source['camera'],'worldMatrix':mm(cam.matrix_world),'projectionMatrix':mm(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=768,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'orthoScale':cam.data.ortho_scale,'shiftX':cam.data.shift_x,'shiftY':cam.data.shift_y}
camera['artStyle']={'revision':'warm-soft-lantern-round-01','lights':'Neutral broad overhead and eight equal radial fills; neutral world; no ground plane','compositor':False}
write(OUT/'camera.json',camera)
asset=json.loads((HERE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['sourceScale']=2;asset['artStyle']=camera['artStyle'];write(OUT/'asset.json',asset)
write(OUT/'rig.json',rig)
current={d:[snapshot(d,f) for f in range(1,14)] for d in 'NESW'}
bound_deltas=[];matrix_deltas=[];topology={}
for d in 'NESW':
 for i in range(13):
  for n,v in current[d][i].items():
   old=baseline[d][i][n]
   matrix_deltas.append(max(abs(v['matrixWorld'][r][c]-old['matrixWorld'][r][c]) for r in range(4) for c in range(4)))
   if 'bounds' in v:
    # Positive values mean candidate escaped the corresponding source world AABB.
    bound_deltas.extend([old['bounds'][0][j]-v['bounds'][0][j] for j in range(3)]+[v['bounds'][1][j]-old['bounds'][1][j] for j in range(3)])
    topology.setdefault(n,set()).add((v['vertices'],v['edges'],v['polygons']))
validation={'asset':'lantern-gold','round':ROUND,'blender':bpy.app.version_string,'sourceSha256':sha(src),'backupSha256':sha((HERE/brief['source']['backup']).resolve()),'sourceUnmodified':True,'camera':camera,'rootObject':root.name,'sockets':{},'footprint':[1,1],'registeredHeight':1.34,'nativeGeometryMeasurements':current,'sourceMeasurements':f'source/{ROUND}-baseline.json','maxWorldMatrixDelta':max(matrix_deltas),'maxSourceEnvelopeEscape':max(bound_deltas),'topologyStable':all(len(v)==1 for v in topology.values()),'evaluatedTopology':{n:list(v) for n,v in topology.items()},'sourceActions':source_actions,'candidateActions':action_record(),'exactActionsPreserved':source_actions==action_record(),'loopClosure':{d:max(abs(current[d][0][n]['matrixWorld'][r][c]-current[d][12][n]['matrixWorld'][r][c]) for n in current[d][0] for r in range(4) for c in range(4)) for d in 'NESW'},'render':{'engine':sc.render.engine,'cyclesDevice':sc.cycles.device,'computeDeviceType':prefs.compute_device_type,'devices':[{'name':d.name,'type':d.type,'enabled':d.use} for d in prefs.devices],'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'viewTransform':sc.view_settings.view_transform,'filmTransparent':sc.render.film_transparent,'colorMode':sc.render.image_settings.color_mode,'resolution':[384,768],'fps':12,'frameRange':[1,12],'closureKeyExcluded':13,'fixedSeed':41,'compositor':sc.render.use_compositing},'lights':[{'name':o.name,'location':vv(o.location),'energy':o.data.energy,'size':o.data.size,'color':vv(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'dependencies':{'images':[],'linkedLibraries':[],'packed':True},'nativeOnly':True,'noGroundPlane':True}
assert validation['maxWorldMatrixDelta']<1e-6
assert validation['maxSourceEnvelopeEscape']<1e-6
assert validation['topologyStable'] and validation['exactActionsPreserved']
pose('S',1)
sc['assetId']='lantern-gold';sc['round']=ROUND;sc['captureScale']=2;sc['nativeFrames']=12
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'source'/f'{ROUND}.blend'),compress=True)
validation['projectSha256']=sha(HERE/'source'/f'{ROUND}.blend')
write(OUT/'validation-native.json',validation)
for d in 'NESW':
 for i in (range(1) if STUDY else range(12)):
  pose(d,i+1)
  p=OUT/'raw'/f'idle-{d}'/f'{i:03}.png';p.parent.mkdir(parents=True,exist_ok=True)
  sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name)
  print('LANTERN_RENDER',d,i,str(p),flush=True)
print('LANTERN_COMPLETE',ROUND,flush=True)
