import bpy,json,pathlib,hashlib,importlib.util,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-dalia');out=b/'reviews/round02-food-evidence';out.mkdir(exist_ok=True)
record=json.loads((b/'inputs/source-rig.json').read_text());sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects[record['groundRootObject']];col=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects));arm=bpy.data.objects[record['armatures'][0]['object']]
# Intended collection remains in its approved scene; unexclude collection and enable evaluable object viewport only. Never save.
def enable(l):
 if col==l.collection:l.exclude=False;l.hide_viewport=False
 for ch in l.children:enable(ch)
enable(bpy.context.view_layer.layer_collection);col.hide_viewport=False
for ob in col.all_objects:ob.hide_viewport=False;ob.hide_set(False)
foodroot=bpy.data.objects[record['groundRootObject']+'__held_dish-salmon'];plane=bpy.data.objects[foodroot.name+'__image_plane'];m=plane.data.materials[0];im=next(n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
packed=bytes(im.packed_file.data);(out/'candidate-packed-canonical-salmon.png').write_bytes(packed)
def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return list(v)
 except:return str(v)
def driverrec(o):
 return [{'dataPath':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path,'bone':t.bone_target,'transformSpace':t.transform_space,'transformType':t.transform_type} for t in v.targets]} for v in f.driver.variables]} for f in o.animation_data.drivers] if o.animation_data else []
def node(n):
 d={'name':n.name,'type':n.bl_idname,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'outputs':{s.name:plain(s.default_value) for s in n.outputs if hasattr(s,'default_value')}}
 for k in ['interpolation','extension','projection']:
  if hasattr(n,k):d[k]=getattr(n,k)
 if getattr(n,'image',None):d['image']=n.image.name
 return d
initial={'asset':'chef-dalia','stage':'round02-independent-sealed-candidate-native-audit','sourceProject':bpy.data.filepath,'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'collection':col.name,'camera':{'name':cam.name,'matrixWorld':[list(z) for z in cam.matrix_world],'projectionMatrix':[list(z) for z in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filmTransparent':sc.render.film_transparent},'sourceFood':{'rootName':foodroot.name,'planeName':plane.name,'vertices':[list(v.co) for v in plane.data.vertices],'polygons':[list(f.vertices) for f in plane.data.polygons],'UV':[[list(plane.data.uv_layers.active.data[li].uv) for li in f.loop_indices] for f in plane.data.polygons],'rootParent':foodroot.parent.name,'planeParent':plane.parent.name,'planeLocalRotation':list(plane.rotation_euler),'planeScale':list(plane.scale),'planeDrivers':driverrec(plane),'foodRootDrivers':driverrec(foodroot),'rootScale':list(root.scale),'packedImage':{'name':im.name,'size':list(im.size),'SHA256':hashlib.sha256(packed).hexdigest(),'alphaMode':im.alpha_mode,'colorspace':im.colorspace_settings.name,'filepath':im.filepath},'material':{'name':m.name,'nodes':[node(n) for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links],'surfaceRenderMethod':getattr(m,'surface_render_method',None),'useTransparentShadow':getattr(m,'use_transparent_shadow',None),'diffuseColor':list(m.diffuse_color)}},'render':{'engine':sc.render.engine,'cyclesSeed':sc.cycles.seed,'cyclesAnimatedSeed':sc.cycles.use_animated_seed,'samples':sc.cycles.samples,'device':sc.cycles.device,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'resolutionPercentage':sc.render.resolution_percentage},'lightRig':[{'name':o.name,'position':list(o.matrix_world.translation),'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None)} for o in sc.objects if o.type=='LIGHT'],'sourceLinkedLibraries':[l.filepath for l in bpy.data.libraries]}
spec=importlib.util.spec_from_file_location('dalia_food_original_native',b/'source/native_actions_round01.py');na=importlib.util.module_from_spec(spec);spec.loader.exec_module(na);asset={'root':root,'collection':col,'armature':arm}
def project(w):
 a=world_to_camera_view(sc,cam,Vector(w));return [a.x*384,(1-a.y)*640,a.z]
def center(ob,dg):
 eo=ob.evaluated_get(dg);return list(sum((eo.matrix_world@v.co for v in eo.data.vertices),Vector())/len(eo.data.vertices))
frames=[]
for clip in ['idle','work','hold','load']:
 for di in ['N','E','S','W']:
  for fi in range(12):
   na.apply_clip(asset,record,clip,fi+1,di,sc);visibility={'planeHideRender':plane.hide_render,'planeHideViewport':plane.hide_viewport,'foodRootHideRender':foodroot.hide_render,'foodRootHideViewport':foodroot.hide_viewport};foodroot.hide_viewport=False;foodroot.hide_set(False);plane.hide_viewport=False;plane.hide_set(False);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pe=plane.evaluated_get(dg);ae=arm.evaluated_get(dg)
   palm={s:center(bpy.data.objects['chef_dalia__palm_'+s+'.001'],dg) for s in ['L','R']};pc=[(palm['L'][i]+palm['R'][i])/2 for i in range(3)]
   frames.append({'clip':clip,'direction':di,'index':fi,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(z) for z in root.matrix_world],'foodRootMatrix':[list(z) for z in foodroot.matrix_world],'planeMatrix':[list(z) for z in pe.matrix_world],'planeLocalLocation':list(plane.location),'planeRotation':list(plane.rotation_euler),'planeVerticesWorld':[list(pe.matrix_world@v.co) for v in pe.data.vertices],'planeCornersProjected':[project(pe.matrix_world@v.co) for v in pe.data.vertices],'sourceVisibility':visibility,'planeHideRender':visibility['planeHideRender'],'palmCentroidsWorld':palm,'palmMeanWorld':pc,'palmMeanProjected':project(pc),'palmBoundsWorld':{s:[[min((ob.evaluated_get(dg).matrix_world@Vector(c))[i] for c in ob.evaluated_get(dg).bound_box),max((ob.evaluated_get(dg).matrix_world@Vector(c))[i] for c in ob.evaluated_get(dg).bound_box)] for i in range(3)] for s,ob in [(s,bpy.data.objects['chef_dalia__palm_'+s+'.001']) for s in ['L','R']]},'nativeHandBones':{s:{'head':list(ae.matrix_world@ae.pose.bones['hand_'+s].head),'tail':list(ae.matrix_world@ae.pose.bones['hand_'+s].tail)} for s in ['L','R']},'nativeMouthRestMetadata':json.loads(root['sockets']).get('mouth'),'evaluatedSmileMeshCentroidWorld':center(bpy.data.objects['chef_dalia__R01_friendly_smile'],dg),'evaluatedBoneMatricesWorld':{bone.name:[list(z) for z in (ae.matrix_world@bone.matrix)] for bone in ae.pose.bones}})
initial['hiddenFrameEvaluation']='Recorded authored render/viewport visibility before temporarily enabling food viewport evaluation. hide_render was never changed; this avoids stale hidden-object identity matrices in diagnostic maps.';initial['frames']=frames;(b/'reviews/round02-independent-food-native-audit.json').write_text(json.dumps(initial,indent=2)+'\n');print('Independent candidate native phases',len(frames),'SHA',initial['sourceSHA256'])
