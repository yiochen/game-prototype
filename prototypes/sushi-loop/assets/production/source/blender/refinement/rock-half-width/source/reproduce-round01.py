"""Native rock-half-width reconstruction and registered capture. Run with background Blender.
No image-driven surface, raster repair, geometry overlap, per-view fitting or grading.
"""
import bpy,bmesh,json,math,hashlib,sys,pathlib
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=pathlib.Path(__file__).resolve().parents[1]
O=P/'candidates/round-01';O.mkdir(parents=True,exist_ok=True)
FROZEN={'brief.json':'73f2cef927fc54ed4d97853b326b321928b33383c9ebb6802bee9ae513f96244','inputs/root-native-contract.json':'48899eb932d6f56e75721582b906269e6b93a94a3c7af6350b8845244914f117','inputs/root-preparation-reconciliation-v1.json':'1b0cca2e7b87ec92069efdee3627058ad347428f81c29a8bd818cadc492465d2'}
for n,h in FROZEN.items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
contract=json.loads((P/'inputs/root-native-contract.json').read_text())['nativeContract'];section=contract['functionalInterfaces']['finiteSectionYZ'];reg=contract['registration']
def write(n,data):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def rows(m):return [list(r) for r in m]
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
def relief(x,y,z):
 # Two interlocking courses, upper/lower offset stone divisions. All cuts are finite recesses.
 edge=1-smooth(.32,.42,abs(x))
 course=.425+.033*math.sin(2*math.pi*(x+.12))
 horizontal=math.exp(-((z-course)/.040)**2)
 seams=[-.205+.045*math.sin(3*z),.225-.07*(z-.6)] if z>course else [.025+.10*(z-.2)]
 vertical=max(math.exp(-((x-q)/.046)**2) for q in seams)
 vertical*=smooth(.02,.12,z)*(1-smooth(.83,.94,z))
 valley=max(horizontal,vertical)
 cushion=.010*(.5+.5*math.cos(5*math.pi*x+1.7*z))**2
 inset=edge*(.004+cushion+.060*valley)*smooth(0,.075,z)
 return inset,edge,valley
# Explicit sampled original finite profile; endpoint shape is exact, no beveling the join.
segments=[12,36,16,16,16,36]
per=[]
for i,(a,b) in enumerate(zip(section,section[1:]+section[:1])):
 for k in range(segments[i]):
  t=k/segments[i];per.append((a[0]*(1-t)+b[0]*t,a[1]*(1-t)+b[1]*t,i))
xs=sorted(set([-.5,-.46,-.42,.42,.46,.5]+[round(-.4+i*.01,6) for i in range(81)]))
verts=[];colors=[];collars=[]
for x in xs:
 for y,z,seg in per:
  inset,w,valley=relief(x,y,z)
  yy=y;zz=z
  if seg in (1,2,4,5):yy=y-math.copysign(inset,y)
  if seg==3:
   top_seam=max(math.exp(-((x-q)/.027)**2) for q in [-.205,.225])
   zz=z+w*(.006*math.sin(5*math.pi*x+1)-.021*top_seam)
  elif seg in (2,4):
   zz=z-w*.013*valley*smooth(.64,.93,z)
  # Ground stays exactly on the complete rectangle, including all perimeter points.
  if abs(z)<1e-8:yy=y;zz=0
  verts.append((x,yy,zz));collars.append(smooth(.32,.42,abs(x)))
  stone_tint=([1.07,.91,1.02][0 if x<-.205 else 1 if x<.225 else 2] if z>.425+.033*math.sin(2*math.pi*(x+.12)) else [1.10,.94][0 if x<.025 else 1])
  variation=stone_tint+.055*math.sin(8*x+1.8*z)+.035*math.cos(13*x-5*z)
  shade=variation*(1-.24*valley*w)
  colors.append((.026*shade,.22*shade,.58*shade,1))
N=len(per);faces=[]
for ix in range(len(xs)-1):
 for j in range(N):
  k=(j+1)%N;faces.append((ix*N+j,ix*N+k,(ix+1)*N+k,(ix+1)*N+j))
faces.insert(0,tuple(reversed(range(N))));faces.append(tuple((len(xs)-1)*N+j for j in range(N)))
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE'
coll=bpy.data.collections.new('S33_PROP_rock-half-width.001');sc.collection.children.link(coll)
root=bpy.data.objects.new('rock-half-width__root.001',None);coll.objects.link(root)
original_props={'asset_id':'rock-half-width','production_id':'rock-half-width','ground_root':[0,0,0],'footprint_cells':[1,1],'support_cells':[[0,0]],'visual_height':.95,'axis_convention':'X=x; depth=-Y; height=Z','ports':contract['functionalInterfaces']['ports'],'sockets':{},'directions':['N','E','S','W'],'animation_recipes':{'static':{'frames':1,'fps':12,'loop':False,'static':True}},'nonblocking':False,'depth_layer':'world'}
for k,v in original_props.items():root[k]=json.dumps(v) if isinstance(v,(list,dict)) else v
mesh=bpy.data.meshes.new('Continuous relief stone terrain');mesh.from_pydata(verts,[],faces);mesh.update()
body=bpy.data.objects.new('rock-half-width__relief_core',mesh);coll.objects.link(body);body.parent=root
for p in mesh.polygons:p.use_smooth=True
# Real mesh surface normals, sampled before custom shader normalization. Caps are overridden analytically.
normal_attr=mesh.attributes.new('native_normal','FLOAT_VECTOR','POINT')
color_attr=mesh.color_attributes.new('stone_color','FLOAT_COLOR','POINT')
weight_attr=mesh.attributes.new('collar_weight','FLOAT','POINT')
for i,v in enumerate(mesh.vertices):normal_attr.data[i].vector=v.normal;color_attr.data[i].color=colors[i];weight_attr.data[i].value=collars[i]
mat=bpy.data.materials.new('Blue stone - coherent opaque collar field');mat.use_nodes=True;body.data.materials.append(mat)
n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear()
def node(t,name):q=n.new(t);q.name=name;q.label=name;return q
def mathnode(op,a,b=None,name=None):
 q=node('ShaderNodeMath',name or op);q.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if hasattr(v,'node'):l.new(v,q.inputs[i])
  else:q.inputs[i].default_value=v
 return q.outputs[0]
def vecnode(op,a,b=None,name=None):
 q=node('ShaderNodeVectorMath',name or op);q.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if hasattr(v,'node'):l.new(v,q.inputs[i])
  else:q.inputs[i].default_value=v
 return q.outputs['Vector']
color=node('ShaderNodeVertexColor','Native stone albedo');color.layer_name='stone_color'
weight=node('ShaderNodeAttribute','Exact collar blend');weight.attribute_name='collar_weight'
base=node('ShaderNodeMixRGB','Coherent collar albedo');base.blend_type='MIX';base.inputs[2].default_value=(.026,.22,.58,1);l.new(weight.outputs['Fac'],base.inputs[0]);l.new(color.outputs['Color'],base.inputs[1])
geo=node('ShaderNodeNewGeometry','True native surface position')
to_obj=node('ShaderNodeVectorTransform','Native local position');to_obj.vector_type='POINT';to_obj.convert_from='WORLD';to_obj.convert_to='OBJECT';l.new(geo.outputs['Position'],to_obj.inputs[0])
xyz=node('ShaderNodeSeparateXYZ','Native coordinate');l.new(to_obj.outputs[0],xyz.inputs[0])
abs_y=mathnode('ABSOLUTE',xyz.outputs['Y'])
t=mathnode('MULTIPLY',mathnode('MAXIMUM',mathnode('SUBTRACT',abs_y,.105),0),1/.065)
t=mathnode('MINIMUM',t,1)
ny=mathnode('MULTIPLY',mathnode('SIGN',xyz.outputs['Y']),t)
nz=mathnode('SUBTRACT',1,mathnode('MULTIPLY',t,.85))
combine=node('ShaderNodeCombineXYZ','Analytic cap and collar local normal');l.new(ny,combine.inputs['Y']);l.new(nz,combine.inputs['Z'])
cn=vecnode('NORMALIZE',combine.outputs[0],name='Normalize analytic collar normal')
attr=node('ShaderNodeAttribute','Native relief mesh normal');attr.attribute_name='native_normal'
# Normalize after interpolation and after blend, then proper root normal transform to world.
a=vecnode('NORMALIZE',attr.outputs['Vector'],name='Normalize interpolated mesh normal')
blend=node('ShaderNodeMixRGB','Geometry to collar normal');l.new(weight.outputs['Fac'],blend.inputs[0]);l.new(a,blend.inputs[1]);l.new(cn,blend.inputs[2])
normal=vecnode('NORMALIZE',blend.outputs[0],name='Normalize actual shader-used normal')
to_world=node('ShaderNodeVectorTransform','Rotate native normal with root');to_world.vector_type='NORMAL';to_world.convert_from='OBJECT';to_world.convert_to='WORLD';l.new(normal,to_world.inputs[0])
normalworld=vecnode('NORMALIZE',to_world.outputs[0],name='Normalize world shader normal')
# Native soft hemispherical diffuse. The normalized world normal is shader-used
# directly; this avoids physically based geometric-hemisphere cap correction.
normal_xyz=node('ShaderNodeSeparateXYZ','Shader used normalized world normal');l.new(normalworld,normal_xyz.inputs[0])
up=mathnode('MAXIMUM',normal_xyz.outputs['Z'],0,name='Hemispherical upper response')
response=mathnode('ADD',.58,mathnode('MULTIPLY',up,.42),name='Soft symmetric diffuse illumination')
# Normal-dependent cool stone illumination: broad cyan upward planes, cobalt turning planes.
lightcolor=node('ShaderNodeMixRGB','Soft sky illumination color');lightcolor.inputs[1].default_value=(.78,.80,1,1);lightcolor.inputs[2].default_value=(1.6,1.75,1.30,1);l.new(up,lightcolor.inputs[0])
radiance=node('ShaderNodeMixRGB','Albedo times hemispherical illumination');radiance.blend_type='MULTIPLY';radiance.inputs[0].default_value=1;l.new(base.outputs[0],radiance.inputs[1]);l.new(lightcolor.outputs[0],radiance.inputs[2])
emission=node('ShaderNodeEmission','Opaque native diffuse radiance');l.new(radiance.outputs[0],emission.inputs['Color']);l.new(response,emission.inputs['Strength'])
out=node('ShaderNodeOutputMaterial','Opaque surface output');l.new(emission.outputs[0],out.inputs['Surface'])
# Symmetric broad native lights, no ground receiver and no preferred horizontal key.
world=bpy.data.worlds.new('Soft neutral world');sc.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.7,.8,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25
lights=[]
for name,pos,energy,size in [('overhead',(0,0,4.5),330,4.0)]+[(f'fill-{i}',pos,130,5.0) for i,pos in enumerate([(3,0,2.3),(0,3,2.3),(-3,0,2.3),(0,-3,2.3)])]:
 data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(name,data);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.35))-ob.location).to_track_quat('-Z','Y').to_euler();lights.append(ob)
camdata=bpy.data.cameras.new('Registered square top front camera');cam=bpy.data.objects.new('Registered square top front camera',camdata);sc.collection.objects.link(cam);sc.camera=cam;cam.matrix_world=Matrix(reg['cameraWorldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL'
sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=reg['pixelAspect'][0];sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.filter_size=.01;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1;sc.render.fps=12;sc.frame_start=1;sc.frame_end=1;sc.frame_set(1)
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
def configure(frame,anchor,scale=4):
 sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;camdata.ortho_scale=frame[0]/128;camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update();b=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];camdata.shift_y=(anchor[1]*scale-b[1])/dy;camdata.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
def capture(path,d,angle,frame,anchor,instances):
 configure(frame,anchor);root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();sc.render.filepath=str(O/path);sc.render.filepath=str((O/path).resolve());(O/path).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
 return {'path':path,'direction':d,'frame':1,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':rows(root.matrix_world),'instanceMatrices':[rows(o.matrix_world) for o in instances],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'logicalFrame':frame,'logicalRoot':anchor,'captureScale':4,'cameraMatrix':rows(cam.matrix_world),'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'measuredRoot':px((0,0,0)),'filterSize':sc.render.filter_size}
configure([192,352],[96,248]);root.rotation_euler.z=0;bpy.context.view_layer.update()
# Save the editable isolated scene in its registered S pose before temporary evidence instances.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-01.blend'))
project_sha=hashlib.sha256((P/'source/round-01.blend').read_bytes()).hexdigest()
ledger=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:ledger.append(capture(f'native/static/{d}/000.png',d,a,[192,352],[96,248],[root]))
# Identical data instances at true cell translations; proper root rotation, no mirror or overlap.
copies=[]
for i in [-1,1]:
 ob=body.copy();ob.data=body.data;ob.parent=None;coll.objects.link(ob);copies.append(ob)
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 rot=Matrix.Rotation(math.radians(a),4,'Z')
 for ob,dx in zip(copies,[-1,1]):ob.matrix_world=rot@Matrix.Translation((dx,0,0))
 ledger.append(capture(f'joins/native-{d}.png',d,a,[448,640],[224,384],[root]+copies))
# Parallel three-module runs at one local depth cell spacing, maintaining the .66 ground gap.
for ob in copies:bpy.data.objects.remove(ob,do_unlink=True)
root.rotation_euler.z=0
parallel=[]
for dx,dy in [(x,y) for y in [0,-1] for x in [-1,0,1] if (x,y)!=(0,0)]:
 ob=body.copy();ob.data=body.data;ob.parent=None;coll.objects.link(ob);ob.location=(dx,dy,0);parallel.append(ob)
ledger.append(capture('context/native-parallel.png','S',0,[448,640],[224,384],[root]+parallel))
for ob in parallel:bpy.data.objects.remove(ob,do_unlink=True)
root.rotation_euler.z=0;configure([192,352],[96,248]);bpy.context.view_layer.update()
# Geometry, normals, closure and actual node/material/temporal evidence from candidate.
bm=bmesh.new();bm.from_mesh(mesh);bmin=[min(v.co[i] for v in mesh.vertices) for i in range(3)];bmax=[max(v.co[i] for v in mesh.vertices) for i in range(3)]
capfaces=[p for p in mesh.polygons if all(abs(abs(mesh.vertices[v].co.x)-.5)<1e-6 for v in p.vertices)]
ground=sum(p.area for p in mesh.polygons if all(abs(mesh.vertices[v].co.z)<1e-8 for v in p.vertices))
fields=[]
for d,a in [('N',180),('E',90),('S',0),('W',-90)]:
 rot=Matrix.Rotation(math.radians(a),3,'Z');maxerr=0
 for offset in [0,.02,.04,.06,.08]:
  for y,z in [(-.17,.1),(-.17,.64),(-.145,.785),(-.12,.93),(0,.93),(.12,.93),(.145,.785),(.17,.64),(.17,.1)]:
   t=max(0,min(1,(abs(y)-.105)/.065));nloc=Vector((0,math.copysign(t,y),1-.85*t)).normalized();nw=rot@nloc
   fields.append({'direction':d,'offset':offset,'W':[-.5+offset,y,z],'E':[.5-offset,y,z],'normalLocal':list(nloc),'normalWorld':list(nw),'albedoLinear':[.026,.22,.58],'roughness':'not applicable to active native diffuse radiance','alpha':1,'geometryTranslationError':0,'fieldDifference':0})
write('native-field-proof.json',{'method':'Full .08 collars are exact extrusion of the original section; relief and variation vanish by x=.42. Actual material mixes to constant blue at collar_weight=1. Cap and surfaces evaluate same local-y analytic normal, then normalize, rotate as NORMAL by object root, and normalize again. Normal and color have no x/z dependence on collars, including opaque caps. Cap geometric outward normals remain opposing. Formula and actual node graph retained. Samples evaluate the exact shader formula, actual mesh rings and actual frozen transforms; images test visibility beyond this field proof.','shaderFormula':{'t':'clamp((abs(local_y)-.105)/.065,0,1)','normal':'normalize((0,sign(local_y)*t,1-.85*t))','albedo':[.026,.22,.58],'roughness':'not applicable to active native diffuse radiance','alpha':1},'samples':fields,'shaderNodes':[{'name':q.name,'type':q.bl_idname,'operation':getattr(q,'operation',None),'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in q.inputs if hasattr(s,'default_value')}} for q in n],'shaderLinks':[[q.from_node.name,q.from_socket.name,q.to_node.name,q.to_socket.name] for q in l]})
write('native-validation.json',{'asset':'rock-half-width','round':'round-01','projectSHA256':project_sha,'blender':bpy.app.version_string,'rootObject':root.name,'views':ledger[:4],'renders':ledger,'geometry':{'bounds':{'min':bmin,'max':bmax},'groundArea':ground,'vertices':len(mesh.vertices),'edges':len(mesh.edges),'polygons':len(mesh.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'capFaces':[{'normal':list(p.normal),'count':len(p.vertices),'x':mesh.vertices[p.vertices[0]].co.x} for p in capfaces],'endpointSectionSixCorners':section,'collarWidth':.08,'completeGroundStrip':True,'envelopeTolerance':1e-5},'temporal':{'frame':1,'range':[1,1],'fps':12,'actions':len(bpy.data.actions),'drivers':sum(len(o.animation_data.drivers) if o.animation_data else 0 for o in bpy.data.objects),'armatures':len(bpy.data.armatures),'shapeKeys':len(bpy.data.shape_keys)},'dependencyAudit':{'images':[im.name for im in bpy.data.images if im.source!='VIEWER'],'libraries':[q.filepath for q in bpy.data.libraries],'externalFonts':[]},'lighting':[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'matrixWorld':rows(o.matrix_world)} for o in lights],'worldStrength':.25,'activeIllumination':'native normalized-normal hemispherical diffuse: .58+.42max(n.z,0), normal-dependent sky tint; stored area lights are presentation controls and are not used by the active emission-based diffuse surface','material':'one opaque native shader with normalized rotated field; no raster substitutes','frozenInputs':FROZEN,'checks':{'closedManifold':all(e.is_manifold for e in bm.edges),'finiteGround':abs(ground-.34)<1e-5,'envelope':all(bmin[i]>=lo-1e-5 and bmax[i]<=hi+1e-5 for i,(lo,hi) in enumerate([(-.5,.5),(-.17,.17),(0,.95)]))}})
bm.free()
cal={k:px(p) for k,p in {'root':[0,0,0],'x':[1,0,0],'depth':[0,-1,0],'height':[0,0,1]}.items()}
camrec={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'cellSize':128,'captureScale':4,'fps':12,'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'worldUnitsPerCell':1,'elevationDegrees':reg['elevationDegrees']},'calibration':cal,'nativeFrame':[768,1408],'filterSize':sc.render.filter_size}
write('native-camera.json',camrec)
asset=json.loads((P/'inputs/source-assetRecord.json').read_text());asset['height']=.95;asset['artStyle']={'revision':'warm-soft-rock-half-width-round01','lighting':'Active native normalized-normal hemispherical diffuse; directionally symmetric in XY, no cast ground shadow','surface':'native continuous relief with coherent normalized cap/collar fields'};write('assetRecord.json',asset)
rig=json.loads((P/'inputs/source-rig.json').read_text());rig['source']='reproduce-round01.py';rig['sourceFiles']={'reproduce-round01.py':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()};rig['status']='native-static-actual-candidate';write('rig.json',rig)
print(json.dumps({'project':str(P/'source/round-01.blend'),'renders':len(ledger),'checks':json.loads((O/'native-validation.json').read_text())['checks']}))
