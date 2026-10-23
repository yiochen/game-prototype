import bpy, json, sys, importlib.util, hashlib
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[3]/'production/source/blender'
# This inspection operates on a byte-identical backup, and never saves over it.
rig=json.loads((HERE.parent/'inputs/source-rig.json').read_text())
assetrec=json.loads((HERE.parent/'inputs/source-assetRecord.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in bpy.data.collections if root in list(c.objects))
scene=bpy.data.scenes.new('Mateo independent technical inspection')
scene.collection.children.link(collection)
bpy.context.window.scene=scene
collection.hide_render=False;collection.hide_viewport=False
for o in collection.all_objects:o.hide_set(False)
spec=importlib.util.spec_from_file_location('mateo_native_actions',str(HERE/'native_actions.py'))
actions=importlib.util.module_from_spec(spec);spec.loader.exec_module(actions)
asset=dict(assetrec,root=root,collection=collection)

def plain(v):
    if isinstance(v,(str,int,float,bool)) or v is None:return v
    if hasattr(v,'to_dict'):return {k:plain(x) for k,x in v.to_dict().items()}
    try:return [plain(x) for x in v]
    except:return str(v)
def bounds(o):
    dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg)
    if o.type!='MESH':return None
    me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices]
    rec={'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)],'centroid':[sum(p[i] for p in pts)/len(pts) for i in range(3)],'verts':len(me.vertices),'edges':len(me.edges),'faces':len(me.polygons)} if pts else None
    ev.to_mesh_clear();return rec
objects=[]
for o in sorted(collection.all_objects,key=lambda o:o.name):
    objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parentType':o.parent_type,'parentBone':o.parent_bone,'matrixBasis':plain(o.matrix_basis),'matrixParentInverse':plain(o.matrix_parent_inverse),'modifiers':[{'name':m.name,'type':m.type,'visible':m.show_render,'properties':{p.identifier:plain(getattr(m,p.identifier)) for p in m.bl_rna.properties if p.identifier in ('width','segments','levels','render_levels','angle_limit','limit_method','object')}} for m in o.modifiers],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'vertexGroups':[{'name':v.name,'index':v.index} for v in o.vertex_groups],'mesh':{'verts':len(o.data.vertices),'faces':len(o.data.polygons),'uvLayers':[l.name for l in o.data.uv_layers]} if o.type=='MESH' else None,'customProperties':{k:plain(o[k]) for k in o.keys()}})
arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
bones=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrixLocal':plain(b.matrix_local),'deform':b.use_deform} for b in arm.data.bones]
poses=[]
for clip,cd in rig['clips'].items():
 for d in ['S','E','N','W']:
  for index in range(cd['frames']):
   actions.apply_clip(asset,rig,clip,index+1,d,scene)
   poses.append({'clip':clip,'direction':d,'index':index,'rootRotation':list(root.rotation_euler),'objects':{o.name:{'bounds':bounds(o),'matrixWorld':plain(o.matrix_world),'hidden':o.hide_render} for o in collection.all_objects},'bones':{p.name:plain(arm.matrix_world@p.matrix) for p in arm.pose.bones}})
out={'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collection':collection.name,'root':root.name,'armature':arm.name,'objects':objects,'restBones':bones,'poses':poses,'actions':{c:rig['clips'][c]['actions'] for c in rig['clips']},'images':[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'size':list(im.size)} for im in bpy.data.images]}
out['actionFingerprints']={}
for cd in rig['clips'].values():
 for target in cd['actions']:
  action=bpy.data.actions[target['action']]
  curves=[{'path':fc.data_path,'index':fc.array_index,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'handleLeft':list(k.handle_left),'handleRight':list(k.handle_right)} for k in fc.keyframe_points]} for fc in actions._fcurves(action)]
  out['actionFingerprints'][action.name]=hashlib.sha256(json.dumps(curves,sort_keys=True).encode()).hexdigest()
out['packedImageHashes']={im.name:hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in bpy.data.images if im.packed_file}
out['lockedPropMeshes']={o.name:{'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'uv':{l.name:[list(x.uv) for x in l.data] for l in o.data.uv_layers},'drivers':[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression,'variables':[(v.name,v.targets[0].id.name,v.targets[0].data_path) for v in f.driver.variables]} for f in o.animation_data.drivers] if o.animation_data else []} for o in collection.all_objects if o.type=='MESH' and '__ground_root' in o.name}
(HERE/'source-native-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print('MATEO_AUDIT',json.dumps({'objects':len(objects),'frames':len(poses),'bones':len(bones),'collection':collection.name,'imageDependencies':out['images']}))
