import bpy,json,hashlib
from pathlib import Path
base=Path(__file__).resolve().parent.parent
scene=bpy.context.scene
root=bpy.data.objects['crate-wood__root']
collection=next(c for c in scene.collection.children if root.name in c.all_objects)
bpy.context.view_layer.update()
meshes=[]
for o in collection.all_objects:
 if o.type!='MESH':continue
 deps=bpy.context.evaluated_depsgraph_get();eo=o.evaluated_get(deps);mesh=eo.to_mesh()
 pts=[eo.matrix_world@v.co for v in mesh.vertices]
 meshes.append({'name':o.name,'parent':o.parent.name if o.parent else None,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'uvLayers':[u.name for u in o.data.uv_layers],'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'materials':[m.name for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers]});eo.to_mesh_clear()
materials=[]
for m in {m for o in collection.all_objects if o.type=='MESH' for m in o.data.materials}:
 shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 materials.append({'name':m.name,'base_srgb':m.get('base_srgb'),'roughness':shader.inputs['Roughness'].default_value,'specularIORLevel':shader.inputs['Specular IOR Level'].default_value,'coatWeight':shader.inputs['Coat Weight'].default_value,'nodeTypes':[n.type for n in m.node_tree.nodes]})
world=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
report={'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blender':bpy.app.version_string,'scene':scene.name,'collection':collection.name,'root':{'name':root.name,'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale)},'meshes':meshes,'materials':materials,'lights':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'power':o.data.energy,'size':o.data.size,'shape':o.data.shape} for o in scene.objects if o.type=='LIGHT'],'render':{'engine':scene.render.engine,'samples':scene.cycles.samples,'denoising':scene.cycles.use_denoising,'worldStrength':world.inputs['Strength'].default_value,'useCompositing':scene.render.use_compositing,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma},'dependencies':{'images':[i.filepath for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]}}
(base/'source/initial-native-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
