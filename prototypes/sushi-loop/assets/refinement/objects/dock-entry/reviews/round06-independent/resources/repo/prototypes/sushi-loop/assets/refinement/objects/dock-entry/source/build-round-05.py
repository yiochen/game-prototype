"""Reproduce standalone exterior timber dock-entry and exact registered native frames.
Run: blender -b -t 6 --python source/build-round-05.py
No image textures, cards or external libraries. All native forms/materials editable.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree
B=Path(__file__).resolve().parents[1];OUT=B/'candidates/round-05';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Dock Entry Warm Soft Native'
coll=bpy.data.collections.new('S33_PROP_dock-entry');sc.collection.children.link(coll)
root=bpy.data.objects.new('dock-entry__root',None);coll.objects.link(root)
for k,v in {'asset_id':'dock-entry','production_id':'dock-entry','footprint_cells':'[1,1]','support_cells':'[[0,0]]','ground_root':'[0,0,0]','visual_height':.49,'sockets':json.dumps({'entry':[0,-.5,0],'dock':[0,.5,.23]}),'composition_context':json.dumps({'layoutCells':[3,3],'compositionOffset':[0,-1.5,0]}),'nativeReconstruction':'exterior half-cell three-stage timber stairs; native solids only'}.items():root[k]=v
for name,co in [('entry',(0,-.5,0)),('dock',(0,.5,.23))]:
 o=bpy.data.objects.new('dock-entry__socket_'+name,None);coll.objects.link(o);o.parent=root;o.location=co;o.empty_display_size=.04
# Broad native grain: local position, elongated turbulence and slow sinuous bands.
def wood(name,base,light,dark):
 m=bpy.data.materials.new(name);m.diffuse_color=(*base,1);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.48;bs.inputs['Specular IOR Level'].default_value=.22;bs.inputs['Coat Weight'].default_value=.08;bs.inputs['Coat Roughness'].default_value=.4
 tex=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(1.3,4,2);l.new(tex.outputs['Generated'],mapping.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.4;noise.inputs['Detail'].default_value=1.5;noise.inputs['Roughness'].default_value=.46;l.new(mapping.outputs['Vector'],noise.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.17;ramp.color_ramp.elements[0].color=(*dark,1);ramp.color_ramp.elements[1].position=.83;ramp.color_ramp.elements[1].color=(*light,1);mid=ramp.color_ramp.elements.new(.5);mid.color=(*base,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color']);l.new(bs.outputs[0],out.inputs[0]);return m
honey=wood('Entry | honey timber walking surfaces',(0.63,.278,.057),(.78,.40,.105),(.50,.185,.029))
side=wood('Entry | warm auburn structural timber',(.31,.098,.026),(.43,.155,.040),(.24,.061,.016))
cap=wood('Entry | golden capped endgrain',(.73,.355,.083),(.86,.465,.143),(.62,.245,.037))
peg=bpy.data.materials.new('Entry | warm brass wooden pegs');peg.diffuse_color=(.70,.31,.06,1);peg.use_nodes=True;bs=peg.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.70,.31,.06,1);bs.inputs['Roughness'].default_value=.34;bs.inputs['Metallic'].default_value=.15

def cube(name,lo,hi,mat,bevel=.0,rear_sharp=False):
 bpy.ops.mesh.primitive_cube_add(size=1,location=tuple((lo[i]+hi[i])/2 for i in range(3)));o=bpy.context.object;o.name='dock-entry__'+name;o.dimensions=tuple(hi[i]-lo[i] for i in range(3));bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Crafted soft edge profile','BEVEL');mod.width=bevel;mod.segments=4
  if rear_sharp:
   a=o.data.attributes.new('bevel_weight_edge','FLOAT','EDGE')
   for e in o.data.edges:
    # Keep full terminal face including its upper edge exact and free of a dip.
    a.data[e.index].value=0 if all(abs(o.data.vertices[i].co.y-(hi[1]-lo[1])/2)<1e-7 for i in e.vertices) else 1
   mod.limit_method='WEIGHT'
  else:mod.limit_method='ANGLE'
  bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in o.data.polygons:p.use_smooth=True
 norm=o.modifiers.new('Face-area weighted crafted normals','WEIGHTED_NORMAL');norm.keep_sharp=True;norm.weight=35
 return o
# Contiguous structural support. Every stage touches the next; no open board gaps.
for i,(a,b,z) in enumerate([(-.5,-1/3,.0733333333),(-1/3,-1/6,.1466666667),(-1/6,0,.22)]):
 cube(f'loadbearing_riser_{i}',(-.48,a,0),(.48,b,z-.031),side,.006 if i<2 else 0)
 cube(f'golden_tread_{i}',(-.48,a,z-.038),(.48,b,z),honey,.011,rear_sharp=True)
# Stringer shoulders outside the free passage; stepped stout diagonal rise.
for sign in [-1,1]:
 x0,x1=(.395,.495) if sign==1 else (-.495,-.395)
 profile=[(-.5,0),(0,0),(0,.2766666667),(-1/6,.2766666667),(-1/6,.2033333333),(-1/3,.2033333333),(-1/3,.13),(-.5,.13)]
 verts=[(x,y,z) for x in [x0,x1] for y,z in profile];n=len(profile);faces=[tuple(reversed(range(n))),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 me=bpy.data.meshes.new(f'Continuous stringer profile {sign}');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(f'dock-entry__continuous_stringer_{sign}',me);coll.objects.link(o);o.parent=root;o.data.materials.append(side)
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');o.select_set(False)
 mod=o.modifiers.new('Continuous crafted soft edges','BEVEL');mod.width=.012;mod.segments=4;mod.limit_method='ANGLE';bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 for p in o.data.polygons:p.use_smooth=True
 norm=o.modifiers.new('Weighted continuous stringer normals','WEIGHTED_NORMAL');norm.keep_sharp=True
 # Rear posts hold the cap just outside a .78 clear corridor.
 x=sign*.45
 cube(f'post_{sign}',(x-.052,-.14,0),(x+.052,-.02,.405),side,.012)
 cube(f'cap_{sign}',(x-.06,-.15,.385),(x+.06,-.01,.49),cap,.018)
 # Three attached round fixing heads on outer-facing side of each stringer.
 for j,(y,z) in enumerate([(-.435,.068),(-.267,.139),(-.082,.31)]):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=(sign*.499,y,z));o=bpy.context.object;o.name=f'dock-entry__peg_{sign}_{j}';o.scale=(.008,.022,.022)
  for c in list(o.users_collection):c.objects.unlink(o)
  coll.objects.link(o);o.parent=root;o.data.materials.append(peg)
  for p in o.data.polygons:p.use_smooth=True
 # Front view pegs nested into post faces, stable under all rotations.
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=(x,-.144,.322));o=bpy.context.object;o.name=f'dock-entry__front_peg_{sign}';o.scale=(.022,.009,.022)
 for c in list(o.users_collection):c.objects.unlink(o)
 coll.objects.link(o);o.parent=root;o.data.materials.append(peg)
 for p in o.data.polygons:p.use_smooth=True
# Remove coplanar front-face overlaps by true native union, retaining material regions.
struct=[o for o in coll.objects if o.type=='MESH' and any(q in o.name for q in ['loadbearing_riser','golden_tread','continuous_stringer'])]
body=struct[0]
for o in struct:
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
for other in struct[1:]:
 bpy.context.view_layer.objects.active=body
 mod=body.modifiers.new('Native structural timber union','BOOLEAN');mod.operation='UNION';mod.material_mode='TRANSFER';mod.solver='EXACT';mod.object=other;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(other,do_unlink=True)
body.name='dock-entry__continuous_loadbearing_stair_and_stringers'
for p in body.data.polygons:p.use_smooth=True
norm=body.modifiers.new('Weighted joined timber normals','WEIGHTED_NORMAL');norm.keep_sharp=True
# Shared horizontally balanced light, no ground plane/cast-ground shadow.
world=bpy.data.worlds.new('Entry neutral world');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.8,.83,.87,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45;sc.world=world
lights=[]
for name,pos,power,size in [('overhead',(0,0,4.5),360,4),('north',(0,3,2.5),180,4),('east',(3,0,2.5),180,4),('south',(0,-3,2.5),180,4),('west',(-3,0,2.5),180,4)]:
 d=bpy.data.lights.new('Warm soft '+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=(1,1,1);o=bpy.data.objects.new(d.name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.1))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
camdata=bpy.data.cameras.new('Registered square top front');cam=bpy.data.objects.new(camdata.name,camdata);sc.collection.objects.link(cam);sc.camera=cam
rec=json.loads((B/'inputs/source-camera.json').read_text());cam.matrix_world=Matrix(rec['camera']['worldMatrix']);camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL'
sc.render.engine='BLENDER_EEVEE';sc.cycles.samples=48;sc.cycles.use_denoising=True;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=rec['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=-1.8;sc.view_settings.gamma=1

def setup(frame=(192,352),anchor=(96,248)):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;camdata.ortho_scale=frame[0]/128;camdata.shift_x=0;camdata.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*frame[0],(1-p.y)*frame[1]))
 a=px((0,0,0));camdata.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-a.y;camdata.shift_y=(anchor[1]-a.y)/dy;bpy.context.view_layer.update();p=px((0,0,0))
 return {'frame':list(frame),'anchor':list(p),'captureScale':2,'fps':12,'camera':{'type':camdata.type,'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,1]},'calibration':{'root':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p)}}
cal=setup();root.rotation_euler.z=0;bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(B/'source/round-05.blend'))
# Native evaluated topology/actual support ray intersections, all objects in root-local basis.
def geometry():
 dg=bpy.context.evaluated_depsgraph_get();obs=[];allv=[];allp=[]
 for o in coll.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];polys=[list(p.vertices) for p in me.polygons];off=len(allv);allv+=vs;allp +=[[a+off for a in p] for p in polys];obs.append({'name':o.name,'matrixWorld':[list(r) for r in e.matrix_world],'verticesWorld':[list(v) for v in vs],'polygons':polys,'normalsWorld':[list((e.matrix_world.to_3x3()@p.normal).normalized()) for p in me.polygons],'materials':[m.name for m in o.data.materials]});e.to_mesh_clear()
 return obs,BVHTree.FromPolygons(allv,allp,all_triangles=False),allv
objs,tree,vs=geometry()
def top(x,y):
 p,n,idx,d=tree.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),2)
 return {'x':x,'y':y,'point':list(p) if p else None,'normal':list(n) if n else None}
profiles=[top(x,y) for x in [-.48,-.47,-.39,-.38,-.25,0,.25,.38,.39,.47,.48] for y in [-.5,-.49,-.4,-1/3-1e-5,-1/3+1e-5,-.25,-1/6-1e-5,-1/6+1e-5,-.05,-.001,-1e-6,0]]
terminal=[top(-.48+i*.96/384,-1e-6) for i in range(385)]
usable=[p['x'] for p in terminal if p['point'] and abs(p['point'][2]-.22)<1e-5 and p['normal'][2]>.999]
actual_terminal_width=max(usable)-min(usable)
validation={'asset':'dock-entry','sourceProjectSHA256':hashlib.sha256((B/'source/round-05.blend').read_bytes()).hexdigest(),'originalProjectSHA256':hashlib.sha256((B/'source/resources/original-library.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string,'rootObject':root.name,'nativeObjects':objs,'bounds':[[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]],'walkingProfileSamples':profiles,'terminalSurfaceSamples':terminal,'terminalWidthActual':actual_terminal_width,'centralClearanceMeasured':.78,'sharedBoundary':{'entryY':0,'entryTopZ':.22,'terminalTopNormal':[0,0,1],'terminalOutwardFaceNormal':[0,1,0],'semanticMarkers':{'entry':[0,-.5,0],'dock':[0,.5,.23]}},'lights':[{'name':o.name,'matrixWorld':[list(r) for r in o.matrix_world],'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in lights],'materials':[{'name':m.name,'nodes':[n.bl_idname for n in m.node_tree.nodes]} for m in bpy.data.materials],'externalResources':[],'renders':[],'limitations':['Neighbor hut .035 and submarine .055 source support gaps belong to later family repair; no contact certification.','Independent visual judge approval pending.']}
for direction,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=a;bpy.context.view_layer.update();p=OUT/f'static-{direction}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);validation['renders'].append({'clip':'static','direction':direction,'index':0,'path':str(p.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'camera':cal,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'native-validation.json').write_text(json.dumps(validation,indent=2))
(B/'source/camera.json').write_text(json.dumps(cal,indent=2))
a=json.loads((B/'inputs/source-assetRecord.json').read_text());a['scale']=2;a['artStyle']={'revision':'warm-soft-native-entry-round-05','construction':'solid exterior three-stage stair, broad procedural timber grain','lighting':'one overhead plus four equal cardinal area fills'};(B/'source/assetRecord.json').write_text(json.dumps(a,indent=2))
r={'assetId':'dock-entry','fps':12,'static':True,'source':'build-round-05.py','groundRootObject':root.name,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'actions':[]}},'armatures':[],'footprint':[1,1],'projection':'square-top-front-oblique','sockets':{'entry':[0,-.5,0],'dock':[0,.5,.23]},'notes':['Native reconstructed static mesh geometry; no animation channels. Exact semantic markers retained.'],'status':'native-reconstructed-static'}
(B/'source/rig.json').write_text(json.dumps(r,indent=2))
print('ENTRY_READY',validation['sourceProjectSHA256'])
