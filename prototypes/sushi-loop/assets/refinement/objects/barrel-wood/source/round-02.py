"""Exact native barrel refinement recipe. Run: blender --background --python source/round-02.py.
Reads frozen original library; writes only this object's source/ and candidates/round-02/.
"""
import bpy, math, json, hashlib, bmesh
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent.parent
BRIEF=json.loads((BASE/'brief.json').read_text()); SOURCE=(BASE/BRIEF['source']['project']).resolve()
OUT=BASE/'candidates/round-02'; OUT.mkdir(parents=True,exist_ok=True)
RECORDS=OUT/'records';RECORDS.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
collection=bpy.data.collections['S33_PROP_barrel-wood'];root=bpy.data.objects['barrel-wood__root']
original_names=[o.name for o in collection.all_objects]
root.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
def measured(objects):
 def authored_matrix(o):return authored_matrix(o.parent)@o.matrix_basis if o.parent else o.matrix_basis
 points=[authored_matrix(o)@v.co for o in objects if o.type=='MESH' for v in o.data.vertices]
 return {'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]}
source_bounds=measured(collection.all_objects)
source_meshes={o.name:{'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'uvLayers':[x.name for x in o.data.uv_layers]} for o in collection.all_objects if o.type=='MESH'}
# Isolate the actual named barrel from the library; preserve original native meshes and hierarchy.
for o in list(bpy.data.objects):
 if o.name not in original_names:bpy.data.objects.remove(o,do_unlink=True)
sc=bpy.data.scenes.new('Barrel Warm Soft Round 02')
sc.collection.children.link(collection)
for old in list(bpy.data.scenes):
 if old!=sc:bpy.data.scenes.remove(old)
bpy.context.window.scene=sc
collection.hide_render=False;collection.hide_viewport=False
for o in collection.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
# Scene uses actual physical shaders, with no original height-darkening/emission treatment.
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def rgba(hexstr):return tuple(linear(int(hexstr[i:i+2],16)/255) for i in (0,2,4))+(1,)
def material(name,color,rough=.62,spec=.22):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear()
 p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=rgba(color);p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=spec
 output=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],output.inputs['Surface']);return m
wood=[material('Warm honey stave %02d'%i,h) for i,h in enumerate(['DFA047','E3A54D','D99A43','E1A149'])]
lid_mat=material('Honey lid - colored broad soft highlight','E6B566',.67,.18)
seam_mat=material('Warm wood recess','A46B2D',.82,.12)
navy=material('Soft navy iron','15366B',.5,.1)
# Every original open stave gains inward thickness and real soft edge geometry.
def bevel(o,width,segments=3):
 m=o.modifiers.new('Soft manufactured edge','BEVEL');m.width=width;m.segments=segments;m.limit_method='ANGLE';m.angle_limit=math.radians(5);m.harden_normals=True
 return m
for o in list(collection.all_objects):
 if o.type!='MESH':continue
 o.data=o.data.copy();o.data.materials.clear()
 if '__bulging_stave_' in o.name:
  i=int(o.name.rsplit('_',1)[1]);o.data.materials.append(wood[(i*3)%4])
  sol=o.modifiers.new('Native stave inward thickness','SOLIDIFY');sol.thickness=.025;sol.offset=-1;sol.use_even_offset=True
  bevel(o,.008)
  for p in o.data.polygons:p.use_smooth=True
 elif '__iron_band_' in o.name:
  o.data.materials.append(navy);bevel(o,.007,4)
  for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.5
 elif '__lid_seam_' in o.name:
  o.location.z=.825;o.data.materials.append(seam_mat);bevel(o,.0025,3)
 else:
  o.data.materials.append(lid_mat if o.name.endswith('__lid') else wood[2]);bevel(o,.005,3)
# Resolve the existing five lid planks into real beveled solids, following the original
# four native seam positions and the exact original 14-gon outer boundary.
lid=bpy.data.objects['barrel-wood__lid']
outline=[(v.co.x,v.co.y) for v in lid.data.vertices if v.co.z>0]
# Source's alternating cylinder vertices follow clockwise boundary; top cap rebuild uses reverse winding.
def clip_x(poly,x,keep_above):
 result=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ina=(a[0]>=x) if keep_above else (a[0]<=x);inb=(b[0]>=x) if keep_above else (b[0]<=x)
  if ina:result.append(a)
  if ina!=inb:
   t=(x-a[0])/(b[0]-a[0]);result.append((x,a[1]+t*(b[1]-a[1])))
 return result
vs=[];fs=[];mi=[]
limits=[-.5,-.17,-.055,.075,.19,.5]
plank_mats=[material('Native lid plank %d'%i,h,.65,.16) for i,h in enumerate(['E2AE5C','E8B665','E5B15F','E9B768','E3AE5B'])]
for i in range(5):
 poly=clip_x(clip_x(outline,limits[i]+(.002 if i else 0),True),limits[i+1]-(.002 if i<4 else 0),False)
 n=len(poly);k=len(vs)
 vs.extend([(x,y,-.016) for x,y in poly]);vs.extend([(x,y,.021) for x,y in poly])
 # Source outline is clockwise from top. Bottom clockwise and top counterclockwise.
 fs.append(tuple(k+j for j in range(n)));mi.append(i)
 fs.append(tuple(k+n+j for j in reversed(range(n))));mi.append(i)
 for j in range(n):fs.append((k+j,k+n+j,k+n+(j+1)%n,k+(j+1)%n));mi.append(i)
mesh=bpy.data.meshes.new('Original 14-gon lid - five native plank solids');mesh.from_pydata(vs,[],fs);mesh.update();lid.data=mesh
for m in plank_mats:mesh.materials.append(m)
for p,idx in zip(mesh.polygons,mi):p.material_index=idx
for m in list(lid.modifiers):lid.modifiers.remove(m)
bevel(lid,.005,3)
# A shallow internal liner closes the original open seams while leaving the 14 native staves intact.
verts=[];faces=[]
profile=[(.025,.335),(.18,.398),(.425,.435),(.67,.398),(.81,.335)]
for z,r in profile:
 for j in range(28):
  a=j*2*math.pi/28;verts.append(((r-.014)*math.cos(a),(r-.014)*math.sin(a),z))
for k in range(4):
 for j in range(28):faces.append((k*28+j,k*28+(j+1)%28,(k+1)*28+(j+1)%28,(k+1)*28+j))
faces.extend([tuple(reversed(range(28))),tuple(range(112,140))])
mesh=bpy.data.meshes.new('Native stave recess backing');mesh.from_pydata(verts,[],faces);mesh.update()
liner=bpy.data.objects.new('barrel-wood__internal_seam_liner',mesh);collection.objects.link(liner);liner.parent=root;liner.data.materials.append(seam_mat)
for p in mesh.polygons:p.use_smooth=True
# Registered camera is reconstructed from the source camera record, not unrelated active library camera.
record=json.loads((BASE/'inputs/source-camera.json').read_text())
camdata=bpy.data.cameras.new('Registered square top-front camera');cam=bpy.data.objects.new('Registered square top-front camera',camdata);sc.collection.objects.link(cam);sc.camera=cam
cam.matrix_world=Matrix(record['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=1.5
sc.render.resolution_x=384;sc.render.resolution_y=704;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=record['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1
camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*384,(1-p.y)*704))
base=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();delta=px((0,0,0)).y-base.y
camdata.shift_y=(496-base.y)/delta;bpy.context.view_layer.update()
# Broad symmetric light; no ground plane, shadow catcher, horizontal key, or view-dependent treatment.
world=bpy.data.worlds.new('Soft neutral ambient');world.use_nodes=True
bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.22;sc.world=world
lights=[]
def area(name,pos,energy,size):
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.shape='DISK';d.size=size
 ob=bpy.data.objects.new(name,d);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.42))-ob.location).to_track_quat('-Z','Y').to_euler()
 lights.append({'name':name,'position':list(pos),'watts':energy,'size':size,'shape':'DISK'})
area('Centered broad overhead',(0,0,4.5),110,4)
for j in range(4):
 a=j*math.pi/2;area('Symmetric soft fill %d'%j,(3*math.cos(a),3*math.sin(a),1.7),50,4)
sc.render.engine='CYCLES';sc.cycles.samples=64;sc.cycles.use_denoising=True
sc.cycles.max_bounces=8;sc.cycles.diffuse_bounces=4;sc.cycles.glossy_bounces=4
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=100;sc.render.dither_intensity=0
sc.render.fps=12;sc.frame_start=1;sc.frame_end=1;sc.frame_set(1)
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
sc.use_nodes=False
root['artStyle']='warm-soft-cartoon-barrel-v1';root['source_capture_scale']=2
# Native static clips and rig stay unchanged.
project=BASE/'source/round-02.blend'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(project),compress=True)
root0=px((0,0,0));camera_record={'projection':'top-down-oblique-square-grid','frame':[192,352],'nativeFrame':[384,704],'anchor':[96,248],'cellSize':128,'captureScale':2,'fps':12,'axes':record['axes'],'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'worldUnitsPerCell':1,'elevationDegrees':record['camera']['elevationDegrees'],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y]},'calibration':{'root':list(root0),'unitX':list(px((1,0,0))-root0),'unitDepth':list(px((0,-1,0))-root0),'unitHeight':list(px((0,0,1))-root0)},'artStyle':{'revision':'warm-soft-cartoon-barrel-v1','lighting':'centered broad overhead and four equal cardinal fills; neutral ambient','horizontalSymmetry':4}}
(RECORDS/'camera.json').write_text(json.dumps(camera_record,indent=2)+'\n')
asset_record=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset_record['scale']=2;asset_record['artStyle']={'revision':'warm-soft-cartoon-barrel-v1','roughnessWood':.62,'roughnessNavy':.5,'lighting':'symmetric broad soft light','nativeSource':True}
(RECORDS/'asset.json').write_text(json.dumps(asset_record,indent=2)+'\n')
(RECORDS/'rig.json').write_bytes((BASE/'inputs/source-rig.json').read_bytes())
# Measured evaluated mesh topology, alpha and camera evidence.
def topology():
 dg=bpy.context.evaluated_depsgraph_get();items=[];points=[]
 for o in collection.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
  items.append({'name':o.name,'baseVertices':len(o.data.vertices),'baseFaces':len(o.data.polygons),'evaluatedVertices':len(me.vertices),'evaluatedFaces':len(me.polygons),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'negativeScale':o.matrix_world.determinant()<0,'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers]})
  points.extend([o.matrix_world@v.co for v in me.vertices]);bm.free();ev.to_mesh_clear()
 return items,{'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]}
geometry,bounds=topology();views={}
for facing,zrot in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=zrot;bpy.context.view_layer.update()
 path=OUT/(facing+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 views[facing]={'rootRotationZ':zrot,'frame':1,'path':str(path.relative_to(BASE)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rootPixel':list(px(root.matrix_world.translation))}
root.rotation_euler.z=0;bpy.context.view_layer.update()
validation={'asset':'barrel-wood','round':2,'nativeRender':True,'blenderVersion':bpy.app.version_string,'sourceProject':str(SOURCE),'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'project':str(project.relative_to(BASE)),'projectSHA256':hashlib.sha256(project.read_bytes()).hexdigest(),'camera':camera_record,'root':{'name':root.name,'location':list(root.location),'scale':list(root.scale),'static':True,'nativeClips':json.loads(root['animation_recipes'])},'sourceBounds':source_bounds,'evaluatedBounds':bounds,'sourceMeshes':source_meshes,'geometry':geometry,'materials':{'woodHex':['DFA047','E3A54D','D99A43','E1A149'],'lidHex':'E6B566','navyHex':'183B72','recessHex':'A46B2D'},'lighting':{'symmetry':4,'worldStrength':.22,'areaLights':lights,'groundShadowReceiver':False},'render':{'engine':'CYCLES','samples':64,'viewTransform':'Standard','exposure':0,'compositor':False,'transparent':True},'views':views,'dependencies':{'libraries':[],'externalImages':[],'packed':True},'preserved':{'footprint':[1,1],'heightCatalog':.85,'logicalFrame':[192,352],'logicalRoot':[96,248],'sourceScale':2,'frames':1,'fps':12,'loop':False,'sockets':{},'ports':{},'originalObjectNamesPreserved':all(n in bpy.data.objects for n in original_names)},'notes':['Added inward solidify to original open staves and shallow hidden wood backing to close native seam voids.','Original 14-gon lid split along its original four seam positions into five native plank solids; four seam objects retained as recessed backing.','Bevels provide real silhouette changes confined inside native mesh envelope.','No per-view fitting, recoloring, retouching or texture cards.']}
assert abs(root0.x-192)<.01 and abs(root0.y-496)<.01
assert all(abs(bounds[k][i]-source_bounds[k][i])<.008 for k in ('min','max') for i in range(3)),(bounds,source_bounds)
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print('BARREL_NATIVE_ROUND_READY',str(OUT))
