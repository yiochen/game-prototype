"""Portable, read-only source-only audit. Run blender -b --python this_file.
Arrays are held in memory only; output is hashes/counts/maxima, never vertex dumps.
"""
import bpy,json,sys,hashlib,math,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-04';sys.path.insert(0,str(P));import native_actions_round02 as native
R=json.loads((P/'rig-round02.json').read_text());FOOD='chef_lena__ground_root.002__held_dish-salmon__image_plane'
sha=lambda b:hashlib.sha256(b).hexdigest()
def jhash(x):return sha(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def arr(items,attr,n,dtype=np.float32):
 a=np.empty(len(items)*n,dtype=dtype);items.foreach_get(attr,a);return a.reshape((-1,n)) if n>1 else a

def simple(x):
 if x is None or isinstance(x,(str,bool,int,float)):return x
 if isinstance(x,bpy.types.ID):return [x.bl_rna.identifier,x.name]
 try:return [simple(v) for v in x]
 except:return str(x)
def rna(x):
 out={}
 for p in x.bl_rna.properties:
  k=p.identifier
  if k=='rna_type' or p.is_readonly or p.type=='COLLECTION':continue
  try:
   val=getattr(x,k)
   if p.type=='POINTER' and val is not None and not isinstance(val,bpy.types.ID):out[k]=rna(val)
   else:out[k]=simple(val)
  except (TypeError,ValueError,AttributeError):pass
 return out

def tree(t,ignore_image=False):
 return {'nodes':[{'name':n.name,'rna':{k:v for k,v in rna(n).items() if not(ignore_image and k=='image')},'inputs':[(s.identifier,s.name,simple(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,s.name,simple(s.default_value)) for s in n.outputs if hasattr(s,'default_value')]} for n in sorted(t.nodes,key=lambda n:n.name)],'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links)}
def drivers(o):
 return [{'path':f.data_path,'index':f.array_index,'type':f.driver.type,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path,'boneTarget':t.bone_target,'transformType':t.transform_type,'transformSpace':t.transform_space} for t in v.targets]} for v in f.driver.variables]} for f in (o.animation_data.drivers if o.animation_data else [])]
def arrayhash(a):return sha(a.tobytes())
def topology(me):return {'counts':[len(me.vertices),len(me.edges),len(me.polygons),len(me.loops)],'edgeVertices':arrayhash(arr(me.edges,'vertices',2,np.int32)),'loopVertices':arrayhash(arr(me.loops,'vertex_index',1,np.int32)),'polyStarts':arrayhash(arr(me.polygons,'loop_start',1,np.int32)),'polyTotals':arrayhash(arr(me.polygons,'loop_total',1,np.int32)),'polyMaterial':arrayhash(arr(me.polygons,'material_index',1,np.int32)),'smooth':arrayhash(arr(me.polygons,'use_smooth',1,np.bool_))}
def select(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.data.scenes['Lena warm soft round02'];bpy.context.window.scene=sc;co=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];asset={'collection':co,'root':root,'armature':arm};native.apply_clip(asset,R,'idle',1,'S',sc);return sc,co,root,arm,asset

def semantic(sc,co,root,arm):
 objects={};materials={};foodmat=bpy.data.objects[FOOD].data.materials[0]
 for o in sorted(sc.objects,key=lambda o:o.name):
  d={'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'basis':simple(o.matrix_basis),'parentInverse':simple(o.matrix_parent_inverse),'rotationMode':o.rotation_mode,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'drivers':drivers(o),'constraints':[rna(c) for c in o.constraints],'custom':{k:simple(o[k]) for k in o.keys()}}
  if o.type=='MESH':
   me=o.data;d['dataRNA']=rna(me);d['dataCustom']={k:simple(me[k]) for k in me.keys()};d['topology']=topology(me);d['coordinates']=arrayhash(arr(me.vertices,'co',3));d['normals']=arrayhash(arr(me.vertices,'normal',3));d['groups']=[g.name for g in o.vertex_groups];d['weights']=jhash([[(g.group,g.weight) for g in v.groups] for v in me.vertices]);d['modifiers']=[rna(m) for m in o.modifiers];d['materials']=[m.name for m in me.materials];d['uv']={uv.name:arrayhash(arr(uv.data,'uv',2)) for uv in me.uv_layers};d['shapeKeys']={k.name:{'value':k.value,'coordinates':arrayhash(arr(k.data,'co',3)),'relative':k.relative_key.name,'interpolation':k.interpolation} for k in me.shape_keys.key_blocks} if me.shape_keys else None
   for m in me.materials:
    if m:materials[m.name]={'rna':rna(m),'tree':tree(m.node_tree,ignore_image=m==foodmat) if m.use_nodes else None}
  elif o.type=='ARMATURE':d['dataRNA']=rna(arm.data);d['dataCustom']={k:simple(arm.data[k]) for k in arm.data.keys()};d['bones']={b.name:{'matrix':simple(b.matrix_local),'head':simple(b.head_local),'tail':simple(b.tail_local),'parent':b.parent.name if b.parent else None,'deform':b.use_deform,'rna':rna(b)} for b in arm.data.bones}
  elif o.type in ('LIGHT','CAMERA'):d['data']=rna(o.data)
  objects[o.name]=d
 actions={}
 for config in R['clips'].values():
  for target in config['actions']:
   ac=bpy.data.actions[target['action']];actions[ac.name]=[{'dataPath':fc.data_path,'index':fc.array_index,'extrapolation':fc.extrapolation,'keys':[(simple(k.co),k.interpolation,k.easing,simple(k.handle_left),simple(k.handle_right),k.handle_left_type,k.handle_right_type) for k in fc.keyframe_points],'modifiers':[rna(m) for m in fc.modifiers]} for fc in native._fcurves(ac)]
 return {'objects':objects,'materials':materials,'actions':actions,'world':{'rna':rna(sc.world),'tree':tree(sc.world.node_tree)},'cameraObject':sc.camera.name,'render':rna(sc.render),'cycles':rna(sc.cycles),'view':rna(sc.view_settings),'compositor':tree(sc.compositing_node_group) if getattr(sc,'compositing_node_group',None) else None}

def capture(sc,co,root,arm):
 props=[o for o in co.all_objects if '__held_' in o.name or '__knife_' in o.name or '__utensil' in o.name];visibility={o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in props}
 for o in props:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();meshes={}
 for o in sorted(co.all_objects,key=lambda o:o.name):
  if o.type!='MESH' or o.name==FOOD:continue
  e=o.evaluated_get(dg);me=e.to_mesh();local=arr(me.vertices,'co',3);normals=arr(me.vertices,'normal',3);mat=np.array(e.matrix_world,dtype=np.float32);world=local@mat[:3,:3].T+mat[:3,3];wn=normals@np.linalg.inv(mat[:3,:3]);length=np.linalg.norm(wn,axis=1,keepdims=True);wn=np.divide(wn,length,out=np.zeros_like(wn),where=length!=0)
  meshes[o.name]={'local':local,'world':world,'normal':normals,'worldNormal':wn,'topology':topology(me),'matrix':mat};e.to_mesh_clear()
 ae=arm.evaluated_get(dg);pose=np.array([ae.matrix_world@b.matrix for b in ae.pose.bones],dtype=np.float32);boneNames=[b.name for b in ae.pose.bones]
 plane=bpy.data.objects[FOOD];e=plane.evaluated_get(dg);corners=[e.matrix_world@v.co for v in e.data.vertices];px=[]
 for q in corners:
  n=world_to_camera_view(sc,sc.camera,q);px.append([n.x*384,(1-n.y)*640])
 food={'worldCorners':[list(v) for v in corners],'pixelCorners':px,'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'matrix':simple(e.matrix_world),'visible':not visibility[FOOD][0] and not visibility[plane.parent.name][0],'visibility':visibility,'rootMatrix':simple(root.matrix_world),'boneNames':boneNames,'boneDeterminants':[float((ae.matrix_world@b.matrix).determinant()) for b in ae.pose.bones]}
 for o in props:o.hide_render,o.hide_viewport,h=visibility[o.name];o.hide_set(h)
 bpy.context.view_layer.update()
 return meshes,pose,food

def summarymesh(d):return {'counts':d['topology']['counts'],'topologySHA256':jhash(d['topology']),**{k+'SHA256':arrayhash(d[k]) for k in ['local','world','normal','worldNormal','matrix']}}
