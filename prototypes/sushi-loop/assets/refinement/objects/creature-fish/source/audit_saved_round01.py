import bpy,sys,json,hashlib,struct
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent/'candidates/round-01';sys.path.insert(0,str(P));import fish_round01 as rt
def val(v):
 if isinstance(v,(int,float,str,bool)):return v
 try:return list(v)
 except:return str(v)
coll=bpy.data.collections[rt.COLL];own=list(coll.all_objects);materials=sorted({s.material for o in own if o.type=='MESH' for s in o.material_slots if s.material},key=lambda x:x.name)
record={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'buildHash':bpy.app.build_hash.decode(),'scene':bpy.context.scene.name,'camera':rt.camera_record(),
 'externalLibraries':[x.filepath for x in bpy.data.libraries],'externalImageTextures':[{'name':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)} for m in materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],
 'ownedObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'smoothPolygons':sum(p.use_smooth for p in o.data.polygons) if o.type=='MESH' else None,'hideViewport':o.hide_viewport,'hideRender':o.hide_render} for o in own],
 'boneRotationModes':{b.name:b.rotation_mode for b in bpy.data.objects[rt.ARM].pose.bones},
 'retainedActions':[{'name':a.name,'frameRange':list(a.frame_range),'fakeUser':a.use_fake_user,'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions],
 'materials':[{'name':m.name,'diffuseColor':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:val(i.default_value) for i in n.inputs if hasattr(i,'default_value') and not i.is_linked}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]} for m in materials],
 'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'shape':o.data.shape,'size':o.data.size,'matrix':rt.mat(o.matrix_world)} for o in bpy.context.scene.objects if o.type=='LIGHT'],
 'colorManagement':{'viewTransform':bpy.context.scene.view_settings.view_transform,'look':bpy.context.scene.view_settings.look,'exposure':bpy.context.scene.view_settings.exposure,'gamma':bpy.context.scene.view_settings.gamma,'compositing':bpy.context.scene.render.use_compositing,'dither':bpy.context.scene.render.dither_intensity},
 'modelSavedOrRenderedDuringAudit':False}
assert len(record['retainedActions'])==11
assert all(x['fakeUser'] for x in record['retainedActions'])
assert all(m=='XYZ' for m in record['boneRotationModes'].values())
assert not record['externalLibraries'] and not record['externalImageTextures']
(O/'editable-source-audit.json').write_text(json.dumps(record,indent=2)+'\n');print('FISH_EDITABLE_AUDIT_COMPLETE',record['projectSHA256'],flush=True)
