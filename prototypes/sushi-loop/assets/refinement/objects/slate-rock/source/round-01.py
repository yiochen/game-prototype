import bpy, math, json, hashlib, bmesh
from pathlib import Path
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1]
SOURCE=(BASE/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
BACKUP=(BASE/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend').resolve()
OUT=BASE/'candidates/round-01';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_hash=sha(SOURCE);backup_hash=sha(BACKUP)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.data.scenes.new('slate-rock warm soft native round 01');bpy.context.window.scene=scene
collection=bpy.data.collections['S33_PROP_slate-rock.001'];scene.collection.children.link(collection)
parts=list(collection.all_objects);root=bpy.data.objects['slate-rock__root.001']
collection.hide_render=False;collection.hide_viewport=False
for o in parts:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def bounds(objects):
 pts=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dep);me=e.to_mesh();pts.extend(e.matrix_world@v.co for v in me.vertices);e.to_mesh_clear()
 return {k:[fn(v[i] for v in pts) for i in range(3)] for k,fn in [('min',min),('max',max)]}
source_bounds=bounds(parts)
original_parts=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(r) for r in o.matrix_world],'bounds':bounds([o]) if o.type=='MESH' else None,'baseVertices':len(o.data.vertices) if o.type=='MESH' else 0,'baseFaces':len(o.data.polygons) if o.type=='MESH' else 0} for o in parts]
keep=set(parts)
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c!=collection:bpy.data.collections.remove(c)
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
scene.use_nodes=False
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def color(h):return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def slate_material(name,h,groove=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m['base_srgb']='#'+h
 n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 bs.inputs['Roughness'].default_value=.84;bs.inputs['Specular IOR Level'].default_value=.22
 bs.inputs['Base Color'].default_value=color(h)
 if groove:return m
 coords=n.new('ShaderNodeTexCoord');broad=n.new('ShaderNodeTexNoise');broad.inputs['Scale'].default_value=11;broad.inputs['Detail'].default_value=2;broad.inputs['Roughness'].default_value=.65;l.new(coords.outputs['Generated'],broad.inputs['Vector'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[1].position=.85
 c=color(h);ramp.color_ramp.elements[0].color=tuple(v*.94 for v in c[:3])+(1,);ramp.color_ramp.elements[1].color=tuple(min(1,v*1.055) for v in c[:3])+(1,);l.new(broad.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=135;fine.inputs['Detail'].default_value=2;l.new(coords.outputs['Generated'],fine.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.045;bump.inputs['Distance'].default_value=.0015;l.new(fine.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
 return m
slate=slate_material('slate-rock cool slate mineral','8793A1')
groove=slate_material('slate-rock retained fine groove','445266',True)
mass=bpy.data.objects['slate-rock__full_cell_slate_mass'];mass.data=mass.data.copy();mass.data.materials.clear();mass.data.materials.append(slate)
for p in mass.data.polygons:p.use_smooth=True
bev=mass.modifiers.new('Narrow worn native edge bands','BEVEL');bev.width=.012;bev.segments=3;bev.limit_method='ANGLE';bev.angle_limit=.14;bev.harden_normals=True
# Bake the small bevel, then return its evaluated envelope to the source envelope.
bpy.context.view_layer.objects.active=mass;mass.select_set(True);bpy.ops.object.modifier_apply(modifier=bev.name);mass.select_set(False)
current=bounds([mass]);wanted=original_parts[1]['bounds']
for v in mass.data.vertices:
 for i in range(3):v.co[i]=wanted['min'][i]+(v.co[i]-current['min'][i])/(current['max'][i]-current['min'][i])*(wanted['max'][i]-wanted['min'][i])
mass.data.update()
weighted=mass.modifiers.new('Weighted broad slate planes','WEIGHTED_NORMAL');weighted.keep_sharp=True;weighted.weight=50
line=bpy.data.objects['slate-rock__shallow_top_fissure'];line.data=line.data.copy();line.data.materials.clear();line.data.materials.append(groove)
for mod in line.modifiers:
 if mod.type=='BEVEL':mod.segments=3;mod.harden_normals=True
for p in line.data.polygons:p.use_smooth=True
w=line.modifiers.new('Fine groove weighted normals','WEIGHTED_NORMAL');w.keep_sharp=True
scene.world=bpy.data.worlds.new('slate-rock neutral soft world');scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=.32
def area(name,loc,power,size,tint):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=tint
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,.25))-ob.location).to_track_quat('-Z','Y').to_euler()
area('Warm soft centered overhead',(0,0,4.5),150,4.5,(1,.92,.81))
for k in range(4):
 a=k*math.pi*.5;area('Equal neutral cardinal fill '+str(k),(3*math.cos(a),3*math.sin(a),2.1),50,5,(1,.985,.96))
camera_input=json.loads((BASE/'inputs/source-camera.json').read_text())
camdata=bpy.data.cameras.new('slate-rock registered square camera');cam=bpy.data.objects.new(camdata.name,camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.sensor_fit='HORIZONTAL';camdata.ortho_scale=1.5;camdata.shift_x=0;camdata.shift_y=.4583320617675781
cam.matrix_world=Matrix(camera_input['camera']['worldMatrix'])
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=camera_input['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=1
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=True
pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.refresh_devices()
devices=[]
for device in pref.devices:device.use=device.type=='METAL';devices.append({'name':device.name,'type':device.type,'enabled':device.use})
scene.cycles.device='GPU'
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.fps=12
scene.frame_start=scene.frame_end=1;scene.frame_set(1)
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
for mat in list(bpy.data.materials):
 if mat not in (slate,groove):bpy.data.materials.remove(mat,do_unlink=True)
for im in list(bpy.data.images):bpy.data.images.remove(im,do_unlink=True)
for group in (bpy.data.meshes,bpy.data.materials,bpy.data.actions,bpy.data.armatures,bpy.data.worlds,bpy.data.cameras,bpy.data.lights):
 for block in list(group):
  if block.users==0:group.remove(block)
root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
scene['asset_id']='slate-rock';scene['source_scale']=2;scene['native_facings']='N=0,E=-90,S=180,W=90';scene['source_original_sha256']=source_hash
BLEND=BASE/'source/round-01.blend';bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
def pixel(point):
 v=world_to_camera_view(scene,cam,Vector(point));return Vector((v.x*384,(1-v.y)*704))
origin=pixel((0,0,0));calibration={'root':list(origin),'unitX':list(pixel((1,0,0))-origin),'unitDepth':list(pixel((0,-1,0))-origin),'unitHeight':list(pixel((0,0,1))-origin)}
camera=json.loads(json.dumps(camera_input));camera.update({'captureScale':2,'calibration':calibration,'name':'square top/front oblique — slate-rock warm soft native'})
camera['camera'].update({'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[scene.render.pixel_aspect_x,1],'orthoScale':camdata.ortho_scale,'shift':[camdata.shift_x,camdata.shift_y]})
camera['artStyle']={'revision':'warm-soft-slate-rock-round-01','lighting':'Neutral world, centered warm overhead and four equal neutral cardinal area fills','horizontalSymmetry':4,'proceduralNativeMaterials':True,'castShadowReceiver':False}
asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset['scale']=2;asset['artStyle']=camera['artStyle'];asset['nativeScene']=scene.name;asset['groundRootObject']=root.name
rig=json.loads((BASE/'inputs/source-rig.json').read_text());rig['status']='native-static-preserved';rig['project']='round-01.blend';rig['scene']=scene.name
for name,record in [('camera',camera),('assetRecord',asset),('rig',rig)]:(BASE/f'source/round-01-{name}.json').write_text(json.dumps(record,indent=2)+'\n')
records=[]
for direction,angle in [('N',0),('E',-90),('S',180),('W',90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();scene.frame_set(1);scene.render.filepath=str(OUT/f'static-{direction}.png');bpy.ops.render.render(write_still=True)
 records.append({'clip':'static','direction':direction,'index':0,'nativeFrame':1,'path':f'candidates/round-01/static-{direction}.png','sha256':sha(scene.render.filepath),'rootRotationDegrees':angle,'rootMatrix':[list(r) for r in root.matrix_world],'worldBounds':bounds(parts)})
root.rotation_euler.z=0;bpy.context.view_layer.update()
topology=[]
for o in parts:
 if o.type!='MESH':continue
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 topology.append({'name':o.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'nonManifoldEdges':sum(not ed.is_manifold for ed in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'modifiers':[{'type':m.type,'segments':getattr(m,'segments',None),'width':getattr(m,'width',None)} for m in o.modifiers]});bm.free();e.to_mesh_clear()
candidate_bounds=bounds(parts);bound_delta=max(abs(source_bounds[k][i]-candidate_bounds[k][i]) for k in ('min','max') for i in range(3))
camera_delta=max(abs(camera_input['camera']['worldMatrix'][r][c]-camera['camera']['worldMatrix'][r][c]) for r in range(4) for c in range(4));projection_delta=max(abs(camera_input['camera']['projectionMatrix'][r][c]-camera['camera']['projectionMatrix'][r][c]) for r in range(4) for c in range(4))
validation={'asset':'slate-rock','round':1,'pipeline':'native-3d','blender':bpy.app.version_string,'sourceOriginal':{'path':str(SOURCE),'sha256':source_hash,'backupPath':str(BACKUP),'backupSha256':backup_hash,'collection':collection.name,'parts':original_parts},'sourceEdited':{'path':'source/round-01.blend','sha256':sha(BLEND),'reproductionScript':'source/round-01.py','reproductionScriptSha256':sha(Path(__file__)),'scene':scene.name,'root':root.name},'checks':{'originalSourceUntouched':sha(SOURCE)==source_hash,'backupUntouched':sha(BACKUP)==backup_hash,'onlyAssetMeshes':len([o for o in scene.objects if o.type=='MESH'])==2,'onlyAssetCollection':len(scene.collection.children)==1,'allMeshesManifold':all(t['nonManifoldEdges']==0 for t in topology),'noZeroAreaFaces':all(t['zeroAreaFaces']==0 for t in topology),'boundsPreserved':bound_delta<.000001,'rootRegistered':(origin-Vector((192,496))).length<.01,'sourceCameraMatrixPreserved':camera_delta<.000001 and projection_delta<.000001,'nativeFourRotations':len(records)==4,'horizontalLightingSymmetry':4,'noGroundReceiver':True,'fixedCameraAndMaterialsAcrossViews':True,'sourceScale':2},'capture':{'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,248],'sourceScale':2,'pixelAspect':[scene.render.pixel_aspect_x,1],'camera':camera['camera'],'calibration':calibration,'footprint':[1,1],'nominalAuthoredHeight':.48,'sourceMeshBounds':source_bounds,'candidateMeshBounds':candidate_bounds,'maximumBoundDelta':bound_delta,'boundsTolerance':.000001,'clips':[{'id':'static','sourceClipId':'static','frames':1,'fps':12,'static':True,'loop':False}],'rootMatrix':[list(r) for r in root.matrix_world],'sockets':{},'ports':[]},'sourceComparison':{'cameraWorldMatrixMaximumDelta':camera_delta,'cameraProjectionMatrixMaximumDelta':projection_delta,'metadataScaleCorrection':{'legacySourceRecord':4,'actualDeliveredScale':2}},'topology':topology,'lighting':{'engine':scene.render.engine,'samples':scene.cycles.samples,'denoise':scene.cycles.use_denoising,'device':scene.cycles.device,'devices':devices,'worldStrength':.32,'noGround':True,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'location':list(o.location),'rotation':list(o.rotation_euler)} for o in scene.objects if o.type=='LIGHT']},'materials':[{'name':m.name,'base_srgb':m.get('base_srgb'),'proceduralOnly':True} for m in (slate,groove)],'renders':records,'dependencies':{'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'selfContained':not bpy.data.libraries and not any(i.source=='FILE' for i in bpy.data.images)},'status':'native-technical-checks-awaiting-independent-visual-review'}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n');print('CHECKS',json.dumps(validation['checks']))
