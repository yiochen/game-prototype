"""Read-only native invariants/measurement shared by Mateo canonical-food round03."""
import bpy,json,hashlib,math,importlib.util,sys,array,struct
sys.dont_write_bytecode=True
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round03';RES=HERE/'round03-resources'
BRIEF=OBJ/'brief-v3-held-food-semantic-contact.json'
assert hashlib.sha256(BRIEF.read_bytes()).hexdigest()=='e699452c13c421593cf1d1de45a8449222376b7cb6d71ad310b7337d4427c7ac'
brief=json.loads(BRIEF.read_text());mapping=brief['constraints']['heldFoodSemanticMapping'];rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
spec=importlib.util.spec_from_file_location('mateo_round03_actions',HERE/'native_actions.py');N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 if isinstance(v,bpy.types.ID):return {'idType':type(v).__name__,'name':v.name}
 if isinstance(v,bpy.types.bpy_struct):return rna_properties(v,skip=('id_data',))
 if hasattr(v,'to_dict'):return {k:plain(x) for k,x in v.to_dict().items()}
 try:return [plain(x) for x in v]
 except:return str(v)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def owned():
 sc=bpy.data.scenes['Mateo warm soft native round02'];bpy.context.window.scene=sc
 root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));arm=next(o for o in col.all_objects if o.type=='ARMATURE');food=bpy.data.objects[root.name+'__held_dish-salmon__image_plane']
 return sc,{'root':root,'collection':col},arm,food
def pixel(sc,p):
 q=world_to_camera_view(sc,sc.camera,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def drivers(owner):
 return [{'path':f.data_path,'index':f.array_index,'type':f.driver.type,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':getattr(t.id,'name',None),'path':t.data_path,'transformType':t.transform_type,'transformSpace':t.transform_space} for t in v.targets]} for v in f.driver.variables]} for f in owner.animation_data.drivers] if owner.animation_data else []
def normals(me):
 a=array.array('f',[0.])*(len(me.corner_normals)*3);me.corner_normals.foreach_get('vector',a);return a.tobytes()
def mesh_hash(o):
 me=o.data;h=hashlib.sha256();a=array.array('f',[0.])*(len(me.vertices)*3);me.vertices.foreach_get('co',a);h.update(a.tobytes());h.update(normals(me))
 h.update(json.dumps({'faces':[(list(p.vertices),p.material_index,p.use_smooth) for p in me.polygons],'edges':[list(e.vertices) for e in me.edges],'uv':{uv.name:[list(v.uv) for v in uv.data] for uv in me.uv_layers},'weights':[[(g.group,g.weight) for g in v.groups] for v in me.vertices],'groups':[(g.name,g.index) for g in o.vertex_groups],'materials':[m.name for m in me.materials]},sort_keys=True).encode());return h.hexdigest()
def rna_properties(x,skip=()):
 out={}
 for p in x.bl_rna.properties:
  if p.identifier in {'rna_type','users','session_uid','is_updated','is_updated_data','is_updated_transform','is_evaluated','is_editable','is_library_indirect','is_missing','tag',*skip}:continue
  if p.type in {'BOOLEAN','INT','FLOAT','STRING','ENUM','POINTER'}:
   try:out[p.identifier]=plain(getattr(x,p.identifier))
   except:pass
 return out
def node_tree(tree,food_material=False):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'rna':rna_properties(n,skip=('id_data','image','type','bl_rna','internal_links','inputs','outputs','parent','rna_type','dimensions','select','location','width','height','label')),'inputs':[(s.identifier,plain(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,plain(s.default_value)) for s in n.outputs if hasattr(s,'default_value')],'image':('AUTHORIZED_FOOD_BINDING' if food_material else plain(n.image)) if n.type=='TEX_IMAGE' else None} for n in tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links]}
def object_def(o):
 return {'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixBasis':('ANIMATED_EVALUATED_IN_192_SAMPLES' if o.animation_data else plain(o.matrix_basis)),'matrixParentInverse':plain(o.matrix_parent_inverse),'rotationMode':o.rotation_mode,'modifiers':[rna_properties(m) for m in o.modifiers],'drivers':drivers(o),'constraints':[rna_properties(c) for c in o.constraints],'custom':{k:plain(o[k]) for k in o.keys()}}
def invariants(sc,asset,arm,food):
 objects=list(asset['collection'].all_objects);mats={m for o in objects if o.type=='MESH' for m in o.data.materials};foodmat=food.data.materials[0]
 meshes={o.name:mesh_hash(o) for o in objects if o.type=='MESH' and o!=food}
 objectdef={o.name:object_def(o) for o in objects}
 materials={m.name:digest({'rna':rna_properties(m,skip=('id_data','node_tree','preview','original','animation_data')),'tree':node_tree(m.node_tree,m==foodmat)}) for m in mats}
 actions={}
 for cd in rig['clips'].values():
  for t in cd['actions']:
   action=bpy.data.actions[t['action']];actions[action.name]=digest([{'path':f.data_path,'index':f.array_index,'keys':[{'co':plain(k.co),'left':plain(k.handle_left),'right':plain(k.handle_right),'interpolation':k.interpolation} for k in f.keyframe_points]} for f in N._fcurves(action)])
 rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':plain(b.head_local),'tail':plain(b.tail_local),'matrix':plain(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
 settings={'render':rna_properties(sc.render,skip=('filepath','frame_path','engine','bake','image_settings','ffmpeg','views','stamp_note_text')),'engine':sc.render.engine,'imageSettings':rna_properties(sc.render.image_settings),'view':rna_properties(sc.view_settings,skip=('curve_mapping','white_balance_whitepoint')),'display':rna_properties(sc.display_settings),'cycles':rna_properties(sc.cycles),'world':{'rna':rna_properties(sc.world,skip=('node_tree','preview','original','animation_data')),'nodes':node_tree(sc.world.node_tree)},'camera':{'worldMatrix':plain(sc.camera.matrix_world),'data':rna_properties(sc.camera.data,skip=('dof','background_images','stereo','display_background_images','show_background_images','sensor_width','sensor_height'))},'lights':{o.name:{'matrix':plain(o.matrix_world),'data':rna_properties(o.data,skip=('node_tree','preview','original','animation_data'))} for o in sc.objects if o.type=='LIGHT'}}
 return {'bodyKnifeMeshes':meshes,'objects':{n:digest(x) for n,x in objectdef.items()},'materials':materials,'restRig':digest(rest),'actions':actions,'captureLightingRenderSettings':digest(settings),'settings':settings,'foodTopology':{'faces':[list(p.vertices) for p in food.data.polygons],'normalDirections':[[round(x,6) for x in n.vector] for n in food.data.corner_normals],'materials':[m.name for m in food.data.materials]}}
def evaluate(sc,asset,arm,food,clip,direction,index):
 N.apply_clip(asset,rig,clip,index+1,direction,sc);dg=bpy.context.evaluated_depsgraph_get();h=hashlib.sha256();bounds=[];centers={};feet={};topo={}
 for o in asset['collection'].all_objects:
  if o.type!='MESH' or o==food:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();a=array.array('f',[0.])*(len(me.vertices)*3);me.vertices.foreach_get('co',a);h.update(o.name.encode());h.update(a.tobytes());h.update(normals(me));h.update(struct.pack('16f',*(x for row in ev.matrix_world for x in row)));h.update(struct.pack('3I',len(me.vertices),len(me.edges),len(me.polygons)))
  pts=[ev.matrix_world@v.co for v in me.vertices];box={'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
  if '__ground_root' not in o.name:bounds.append(box)
  for side in ['L','R']:
   if o.name=='chef_mateo__palm_'+side+'.001':centers[side]=plain(sum(pts,Vector())/len(pts))
   if o.name=='chef_mateo__minimal_foot_'+side:feet[side]=box['min'][2]
  topo[o.name]=[len(me.vertices),len(me.edges),len(me.polygons)];ev.to_mesh_clear()
 ef=food.evaluated_get(dg);matrix=ef.matrix_world.copy();corners=[matrix@v.co for v in food.data.vertices]
 return {'clip':clip,'direction':direction,'index':index,'rootRotationZ':asset['root'].rotation_euler.z,'bodyEvaluatedSHA256':h.hexdigest(),'bodyBounds':{'min':[min(b['min'][i] for b in bounds) for i in range(3)],'max':[max(b['max'][i] for b in bounds) for i in range(3)]},'palms':centers,'feetMinZ':feet,'bonesSHA256':digest({p.name:plain(arm.matrix_world@p.matrix) for p in arm.pose.bones}),'knifeMatrix':plain(bpy.data.objects[asset['root'].name+'__utensil'].matrix_world),'foodPlaneMatrix':plain(matrix),'foodPropMatrix':plain(food.parent.evaluated_get(dg).matrix_world),'foodVisible':not food.hide_render and not food.parent.hide_render,'foodHiddenFlags':[food.hide_render,food.hide_viewport,food.parent.hide_render,food.parent.hide_viewport],'cornersWorld':[plain(v) for v in corners],'cornersProjected':[pixel(sc,v) for v in corners],'topologySHA256':digest(topo)}
def module_device():
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 return [{'name':d.name,'type':d.type,'enabled':d.use} for d in prefs.devices]
