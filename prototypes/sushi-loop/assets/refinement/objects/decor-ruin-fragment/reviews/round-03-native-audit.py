import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
out=Path(__file__).parent/'round-03-independent-native'
sc=bpy.context.scene;root=bpy.data.objects['decor-ruin-fragment__ground_root'];col=bpy.data.collections['decor-ruin-fragment']
bpy.context.view_layer.update()
meshes=[o for o in col.all_objects if o.type=='MESH']
points=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
mats=[]
for m in bpy.data.materials:
 nodes=[]
 for n in m.node_tree.nodes if m.use_nodes else []:
  rec={'name':n.name,'type':n.type}
  if n.type=='BSDF_PRINCIPLED':rec['principled']={k:list(n.inputs[k].default_value) if k=='Base Color' else n.inputs[k].default_value for k in ['Base Color','Roughness','Specular IOR Level','Metallic']}
  if n.type=='TEX_IMAGE':rec['image']=n.image.name if n.image else None
  if n.type=='RGB':rec['rgb']=list(n.outputs[0].default_value)
  nodes.append(rec)
 mats.append({'name':m.name,'nodes':nodes})
report={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scenes':[s.name for s in bpy.data.scenes],'activeScene':sc.name,'camera':sc.camera.name,'collections':[c.name for c in bpy.data.collections],'root':{'location':list(root.location),'scale':list(root.scale),'matrix':[list(r) for r in root.matrix_world]},'objectCount':len(col.all_objects),'meshCount':len(meshes),'nativeBounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]},'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'vertexCount':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'modifiers':[m.type for m in o.modifiers],'animationData':bool(o.animation_data)} for o in col.all_objects],'materials':mats,'linkedLibraries':[x.filepath for x in bpy.data.libraries],'imageData':[{'name':x.name,'source':x.source} for x in bpy.data.images if x.type!='RENDER_RESULT'],'actions':len(bpy.data.actions),'armatures':len(bpy.data.armatures),'lights':[{'name':o.name,'energy':o.data.energy,'location':list(o.location),'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'compositorSources':[{'type':n.type,'scene':n.scene.name if n.type=='R_LAYERS' and n.scene else None} for n in sc.compositing_node_group.nodes]}
(out/'independent-source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['projectSHA256','scenes','activeScene','camera','root','objectCount','meshCount','nativeBounds','linkedLibraries','imageData','actions','armatures','compositorSources']},indent=2))
