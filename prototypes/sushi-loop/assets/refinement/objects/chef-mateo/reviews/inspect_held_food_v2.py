import bpy,json,hashlib,pathlib,sys,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parent.parent
brief=json.loads((B/'brief-v2-held-food.json').read_text());project=(B/brief['source']['project']).resolve();sys.path.insert(0,str(B/'source'));import native_actions as N
bpy.ops.wm.open_mainfile(filepath=str(project));scene=bpy.context.scene;record=json.loads((B/'inputs/source-rig.json').read_text());root=bpy.data.objects[record['groundRootObject']];col=next(c for c in bpy.data.collections if root.name in c.objects);asset={'root':root,'collection':col};plane=next(o for o in col.all_objects if '__held_dish-salmon__image_plane' in o.name);prop=plane.parent;arm=next(o for o in col.all_objects if o.type=='ARMATURE');cam=scene.camera

def plain(v):
 if isinstance(v,(str,bool,int,float)) or v is None:return v
 try:return [plain(x) for x in v]
 except:return str(v)
def props(o):return {k:plain(o[k]) for k in o.keys() if k!='_RNA_UI'}
def drivers(o):
 return [{'dataPath':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':getattr(t.id,'name',None),'dataPath':t.data_path,'transformType':t.transform_type,'transformSpace':t.transform_space} for t in v.targets]} for v in f.driver.variables]} for f in o.animation_data.drivers] if o.animation_data else []
def project2(v):
 q=world_to_camera_view(scene,cam,v);return [(q.x*scene.render.resolution_x),((1-q.y)*scene.render.resolution_y)]
material=plane.data.materials[0];image=next(n.image for n in material.node_tree.nodes if n.type=='TEX_IMAGE');packed=bytes(image.packed_file.data);(B/'reviews/held-food-v2-old-packed-salmon.png').write_bytes(packed)
loops=[{'vertexIndex':plane.data.loops[l].vertex_index,'uv':plain(plane.data.uv_layers.active.data[l].uv)} for p in plane.data.polygons for l in p.loop_indices]
out={'scope':'Read-only exact approved native source inspection; no candidate created.','project':str(project),'projectSHA256':hashlib.sha256(project.read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'scene':scene.name,'collection':col.name,'root':{'name':root.name,'matrixWorld':plain(root.matrix_world),'custom':props(root)},'camera':{'name':cam.name,'matrixWorld':plain(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'projectedRoot':project2(root.matrix_world.translation)},'food':{'name':plane.name,'vertices':[[v.index,plain(v.co)] for v in plane.data.vertices],'loops':loops,'matrixLocal':plain(plane.matrix_local),'rotationEuler':plain(plane.rotation_euler),'custom':props(plane),'drivers':drivers(plane),'propName':prop.name,'propCustom':props(prop),'propDrivers':drivers(prop),'material':{'name':material.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'image':n.image.name if n.type=='TEX_IMAGE' else None,'extension':n.extension if n.type=='TEX_IMAGE' else None,'interpolation':n.interpolation if n.type=='TEX_IMAGE' else None} for n in material.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in material.node_tree.links]},'image':{'name':image.name,'size':plain(image.size),'sha256':hashlib.sha256(packed).hexdigest(),'fileFormat':image.file_format,'alphaMode':image.alpha_mode,'colorSpace':image.colorspace_settings.name,'filepath':image.filepath,'packed':True},'visibility':{'visibleCamera':plane.visible_camera,'visibleDiffuse':plane.visible_diffuse,'visibleGlossy':plane.visible_glossy,'visibleTransmission':plane.visible_transmission,'visibleShadow':plane.visible_shadow}},'samples':[]}
for clip in record['clips']:
 for direction in ['S','E','N','W']:
  for frame in range(1,13):
   N.apply_clip(asset,record,clip,frame,direction,scene);dep=bpy.context.evaluated_depsgraph_get();ep=plane.evaluated_get(dep);me=ep.to_mesh();corners=[ep.matrix_world@v.co for v in me.vertices];ep.to_mesh_clear();palms={}
   for side in ['L','R']:
    palm=next(o for o in col.all_objects if '__palm_'+side+'.' in o.name);eo=palm.evaluated_get(dep);em=eo.to_mesh();verts=[eo.matrix_world@v.co for v in em.vertices];eo.to_mesh_clear();palms[side]=sum(verts,Vector())/len(verts)
   # UV lower edge is geometry corners0/1 in the original vertex ordering.
   bottom=(corners[0]+corners[1])*0.5;anchor=prop.evaluated_get(dep).matrix_world.translation
   forward=cam.matrix_world.to_3x3()@Vector((0,0,-1));toward=-forward.normalized();bias=bottom-anchor
   out['samples'].append({'clip':clip,'direction':direction,'frame':frame,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'visible':not plane.hide_render and not prop.hide_render,'propRootWorld':plain(anchor),'propRootProjected':project2(anchor),'planeMatrixWorld':plain(ep.matrix_world),'cornersWorld':[plain(v) for v in corners],'cornersProjected':[project2(v) for v in corners],'bottomQuadWorld':plain(bottom),'bottomQuadProjected':project2(bottom),'bottomMinusPropRoot':plain(bias),'biasAlongCameraToward':bias.dot(toward),'biasOrthogonalMagnitude':(bias-toward*bias.dot(toward)).length,'palmsWorld':{k:plain(v) for k,v in palms.items()},'palmsProjected':{k:project2(v) for k,v in palms.items()},'worldQuadWidth':(corners[1]-corners[0]).length,'worldQuadHeight':(corners[3]-corners[0]).length})
(B/'reviews/held-food-v2-native-evidence.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'projectSHA256':out['projectSHA256'],'camera':out['camera'],'food':out['food'],'firstHoldS':next(s for s in out['samples'] if s['clip']=='hold' and s['direction']=='S'),'samples':len(out['samples'])},indent=2))
