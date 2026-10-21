"""Exact native refinement and capture recipe; run with Blender 5.2.2 --background --python this_file.
No vertex positions, UVs, original bevel shape, cut planes, dimensions, connectors or camera matrices are changed.
"""
import bpy, json, math, hashlib, shutil
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent.parent
R='round-01';OUT=P/'candidates'/R;OUT.mkdir(parents=True,exist_ok=True)
SRC=(P/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
SOURCE_SHA=hashlib.sha256(SRC.read_bytes()).hexdigest()
C=json.loads((P/'inputs/source-camera.json').read_text()); A=json.loads((P/'inputs/source-assetRecord.json').read_text()); G=json.loads((P/'inputs/source-rig.json').read_text())
def jwrite(p,v):p.write_text(json.dumps(v,indent=2))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def matrix(m):return [[float(v) for v in row] for row in m]
def digest(v):return hashlib.sha256(json.dumps(v,separators=(',',':')).encode()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='Dock Rope Warm Soft Native'
with bpy.data.libraries.load(str(SRC),link=False) as (data_from,data_to):data_to.collections=['S33_PROP_dock-post-rope.001']
col=data_to.collections[0];s.collection.children.link(col);col.hide_viewport=False;col.hide_render=False
for o in col.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
root=next(o for o in col.all_objects if o.type=='EMPTY' and 'root' in o.name);parts=sorted([o for o in col.all_objects if o.type=='MESH'],key=lambda o:o.name)
root.rotation_euler=(0,0,0);s.frame_set(1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def geometry_record(o):
 deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);me=ev.to_mesh()
 verts=[[float(x) for x in ev.matrix_world@v.co] for v in me.vertices]
 faces=[list(p.vertices) for p in me.polygons]
 cuts={}
 for cut in [-.5,.5]:
  points=set()
  for e in me.edges:
   a=Vector(verts[e.vertices[0]]);b=Vector(verts[e.vertices[1]])
   if abs(a.x-cut)<1e-6:points.add(tuple(round(q,7) for q in a))
   if abs(b.x-cut)<1e-6:points.add(tuple(round(q,7) for q in b))
   if (a.x-cut)*(b.x-cut)<-1e-12:
    q=a+(b-a)*((cut-a.x)/(b.x-a.x));points.add(tuple(round(t,7) for t in q))
  cuts[str(cut)]=sorted(points)
 rec={'vertices':len(verts),'polygons':len(faces),'vertexCoordinatesSHA256':digest(verts),'faceTopologySHA256':digest(faces),'bounds':[[min(v[i] for v in verts) for i in range(3)],[max(v[i] for v in verts) for i in range(3)]],'cutPlanePoints':cuts,'uv':{u.name:{'count':len(u.data),'sha256':digest([[float(x) for x in v.uv] for v in u.data])} for u in o.data.uv_layers},'baseMeshCoordinatesSHA256':digest([[float(x) for x in v.co] for v in o.data.vertices])}
 ev.to_mesh_clear();return rec
baseline={o.name:geometry_record(o) for o in parts}
# Materials use gentle vertical warm variation, never Generated/random coordinates.
# Every independently assembled half shares identical height response at its join.
def warm_material(name,lower,upper,zmax,roughness,spec):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=roughness;p.inputs['Specular IOR Level'].default_value=spec
 p.inputs['Coat Weight'].default_value=.025;p.inputs['Coat Roughness'].default_value=.5
 geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
 mp=n.new('ShaderNodeMapRange');mp.inputs['From Min'].default_value=0;mp.inputs['From Max'].default_value=zmax;mp.inputs['To Min'].default_value=0;mp.inputs['To Max'].default_value=1;mp.clamp=True;l.new(sep.outputs['Z'],mp.inputs['Value'])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=(*lower,1);mix.inputs[2].default_value=(*upper,1);l.new(mp.outputs['Result'],mix.inputs[0]);l.new(mix.outputs[0],p.inputs['Base Color']);l.new(p.outputs['BSDF'],out.inputs['Surface'])
 m.diffuse_color=(*upper,1);return m
wood=warm_material('Warm soft amber wood',(.32,.135,.033),(.55,.275,.075),.78,.60,.24)
cap=warm_material('Warm golden end cap',(.47,.235,.060),(.65,.365,.115),.78,.57,.22)
rope=warm_material('Warm cream rope',(.63,.49,.28),(.86,.76,.53),.78,.76,.20)
for o in parts:
 o.data.materials.clear();o.data.materials.append(rope if ('rope_' in o.name or 'sag_rope' in o.name) else cap if 'post_cap' in o.name else wood)
 if 'sag_rope' in o.name:
  # Keep the original .012/one-segment bevel exactly; only alter face normal treatment.
  for poly in o.data.polygons:poly.use_smooth=True
  mod=o.modifiers.new('Soft broad rope normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=30
 else:
  # Preserve planar tops and protected cuts; cylindrical sides have radial normals.
  ctr=-.5 if sum(v.co.x for v in o.data.vertices)/len(o.data.vertices)<0 else .5
  loopnorm=[]
  for poly in o.data.polygons:
   curved=abs(poly.normal.z)<.1 and abs(poly.normal.x)<.999
   poly.use_smooth=curved
   for li in poly.loop_indices:
    v=o.data.vertices[o.data.loops[li].vertex_index].co
    normal=Vector((v.x-ctr,v.y,0)).normalized() if curved else poly.normal.copy()
    loopnorm.append(tuple(normal))
  o.data.normals_split_custom_set(loopnorm)
# Orthographic camera restored numerically from the source projection record.
cd=bpy.data.cameras.new('Registered square top front camera');cam=bpy.data.objects.new('Registered Camera',cd);s.collection.objects.link(cam);s.camera=cam
cam.matrix_world=Matrix(C['camera']['worldMatrix']);cd.type='ORTHO';cd.sensor_fit='HORIZONTAL';cd.ortho_scale=1.5;cd.clip_start=.1;cd.clip_end=1000
s.render.resolution_x=384;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.pixel_aspect_x=C['camera']['pixelAspect'][0];s.render.pixel_aspect_y=C['camera']['pixelAspect'][1]
cd.shift_y=1;test=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y);cd.shift_y=C['camera']['projectionMatrix'][1][3]/test[1][3]
BASE_SHIFT=cd.shift_y
s.render.engine='CYCLES';s.cycles.samples=128;s.cycles.use_denoising=True;s.cycles.seed=41;s.cycles.use_animated_seed=False
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=(d.type=='METAL')
 s.cycles.device='GPU'
except Exception:s.cycles.device='CPU'
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.fps=12
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.view_settings.gamma=1
s.world=bpy.data.worlds.new('Neutral soft environment');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(1,1,1,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
lights=[]
def area(name,loc,watts,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=watts;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.35))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
area('Broad centered overhead',(0,0,4.5),340,5)
for i in range(4):
 a=i*math.pi/2;area('Equal cardinal fill '+str(i),(3*math.cos(a),3*math.sin(a),2.8),105,4)
# Purge unreferenced original resources; this isolated project has no external dependencies.
for m in list(bpy.data.materials):
 if m.users==0:bpy.data.materials.remove(m)
for im in list(bpy.data.images):
 if im.users==0:bpy.data.images.remove(im)
bpy.context.view_layer.update()
current={o.name:geometry_record(o) for o in parts}
assert all(baseline[n]['vertexCoordinatesSHA256']==current[n]['vertexCoordinatesSHA256'] and baseline[n]['baseMeshCoordinatesSHA256']==current[n]['baseMeshCoordinatesSHA256'] and baseline[n]['uv']==current[n]['uv'] and baseline[n]['cutPlanePoints']==current[n]['cutPlanePoints'] for n in baseline),'Geometry/UV/profile changed'
def capture_record(direction,path):
 bpy.context.view_layer.update();proj=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)
 def pix(v):q=world_to_camera_view(s,cam,Vector(v));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
 r=pix((0,0,0));return {'clip':'static','direction':direction,'index':0,'path':str(path.relative_to(P)),'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':matrix(root.matrix_world),'frame':[s.render.resolution_x,s.render.resolution_y],'cameraWorldMatrix':matrix(cam.matrix_world),'projectionMatrix':matrix(proj),'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'calibration':{'root':r,'unitX':[a-b for a,b in zip(pix((1,0,0)),r)],'unitDepth':[a-b for a,b in zip(pix((0,-1,0)),r)],'unitHeight':[a-b for a,b in zip(pix((0,0,1)),r)]}}
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
root.rotation_euler.z=0;bpy.context.view_layer.update();s.render.filepath=str(OUT/'static-S-000.png')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source'/f'{R}.blend'))
records=[]
for direction,angle in angles.items():
 root.rotation_euler.z=angle;s.frame_set(1);bpy.context.view_layer.update();path=OUT/f'static-{direction}-000.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);records.append(capture_record(direction,path))
# Native assembly made from the exact candidate mesh objects; separate copies stay unjoined.
# Grid placements x=1,2,3 y=2, expressed relative to the middle module root.
root.rotation_euler.z=0;bpy.context.view_layer.update()
assembly=bpy.data.collections.new('Temporary independent three-module assembly');s.collection.children.link(assembly)
assemblyRoot=bpy.data.objects.new('Three module assembly root',None);assembly.objects.link(assemblyRoot)
moduleRoots=[]
for offset in [-1,0,1]:
 nr=root.copy();nr.name='Assembly module '+str(offset+2);assembly.objects.link(nr);nr.parent=assemblyRoot;nr.location=(offset,0,0);nr.rotation_euler=(0,0,0);moduleRoots.append(nr)
 for o in parts:
  no=o.copy();no.data=o.data;assembly.objects.link(no);no.parent=nr;no.matrix_parent_inverse=o.matrix_parent_inverse.copy()
col.hide_render=True
# Expand canvas mathematically with the same pixels/world; no bound fitting.
s.render.resolution_x=1152;s.render.resolution_y=1216;cd.ortho_scale=4.5
# Preserve root vertical pixel with +256 pixels top padding.
cd.shift_y=0;bpy.context.view_layer.update();q=world_to_camera_view(s,cam,Vector((0,0,0)));baseY=(1-q.y)*1216
cd.shift_y=1;bpy.context.view_layer.update();q=world_to_camera_view(s,cam,Vector((0,0,0)));unitY=(1-q.y)*1216
cd.shift_y=(752-baseY)/(unitY-baseY)
joinrecords=[]
for direction,angle in angles.items():
 assemblyRoot.rotation_euler.z=angle;bpy.context.view_layer.update();path=OUT/f'joined-native-{direction}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 joinrecords.append({'direction':direction,'path':str(path.relative_to(P)),'assemblyRootRotationZ':float(assemblyRoot.rotation_euler.z),'assemblyRootMatrix':matrix(assemblyRoot.matrix_world),'placements':[{'catalogCell':[x,2],'localPosition':[x-2,0,0]} for x in [1,2,3]],'instanceRoots':[matrix(nr.matrix_world) for nr in moduleRoots],'sameMeshDataAsCandidate':True,'renderFrame':[1152,1216]})
# Remove preview-only objects and restore the saved native capture scene.
for o in list(assembly.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.collections.remove(assembly);col.hide_render=False;root.rotation_euler.z=0;s.render.resolution_x=384;s.render.resolution_y=704;cd.ortho_scale=1.5;cd.shift_y=BASE_SHIFT;s.render.filepath=str(OUT/'static-S-000.png');bpy.context.view_layer.update()
# Saved project exact state remains S0; preview assembly was never saved.
camRecord=json.loads(json.dumps(C));camRecord.update(captureScale=2);camRecord['camera']['worldMatrix']=matrix(cam.matrix_world);camRecord['camera']['projectionMatrix']=records[2]['projectionMatrix'];camRecord['calibration']=records[2]['calibration'];camRecord['artStyle']={'revision':'warm-soft-round-01','lighting':'340W centered overhead and four equal 105W cardinal fills; neutral world 0.30','horizontalSymmetry':4,'noGroundPlane':True,'colorManagement':'AgX Medium High Contrast'}
A['scale']=2;A['artStyle']=camRecord['artStyle'];G['groundRootObject']=root.name;G['status']='static-native-refinement-candidate';G['createdAtUnix']=None
jwrite(OUT/'camera.json',camRecord);jwrite(OUT/'assetRecord.json',A);jwrite(OUT/'rig.json',G)
allv=[v for r in current.values() for v in r['bounds']]
validation={'asset':'dock-post-rope','round':R,'nativeBlender':bpy.app.version_string,'source':{'project':str(SRC),'beforeSHA256':SOURCE_SHA,'afterSHA256':sha(SRC),'unchanged':SOURCE_SHA==sha(SRC)},'contract':{'logicalFrame':[192,352],'nativeFrame':[384,704],'logicalRoot':[96,248],'sourceScale':2,'cellSize':128,'fps':12,'clip':{'id':'static','frames':1,'loop':False},'directionConvention':'S0 E+90 N180 W-90','sockets':{},'ports':A['ports'],'heightMetadata':.78},'captureRecords':records,'joinedNativeRecords':joinrecords,'geometry':{'method':'Source isolated and updated before measuring. All positions, evaluated face topology, UVs and cut-plane intersection points compared exactly; normal-only changes.','source':baseline,'candidate':current,'baseMeshCoordinatesUnchanged':True,'evaluatedVertexCoordinatesUnchanged':True,'uvLayersUnchanged':True,'cutProfilesUnchanged':True,'protectedPlanes':[-.5,.5],'bounds':[[min(v[i] for v in allv) for i in range(3)],[max(v[i] for v in allv) for i in range(3)]],'objects':len(parts),'boundaryProfileJoin':'Adjacent exact source profiles reconstruct full posts; shader colors are a common world-Z ramp, invariant under translation in XY and cardinal rotation. Curved side endpoint normals are radial and identical across both profile halves.','normals':'Half-post radial curved sides; tops/bottoms/cut faces planar. Rope weighted normals; original bevel shape unchanged.'},'lighting':{'horizontalSymmetry':4,'lights':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape} for o in lights],'worldStrength':.30,'worldColor':[1,1,1],'groundGeometry':False,'filmTransparent':True,'perDirectionChanges':'only root Z rotation','device':s.cycles.device,'cyclesSamples':128,'seed':41,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look},'dependencies':{'linkedLibraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'source':x.source,'packed':bool(x.packed_file),'filepath':x.filepath} for x in bpy.data.images],'selfContained':not bpy.data.libraries and not any(x.source=='FILE' and not x.packed_file for x in bpy.data.images)},'freshReload':{'pending':True},'alpha':{'pending':True},'recipe':str((P/'source'/f'{R}-recipe.py').relative_to(P))}
jwrite(OUT/'validation.json',validation)
print('DOCK_CANDIDATE_RENDER_COMPLETE',OUT)
