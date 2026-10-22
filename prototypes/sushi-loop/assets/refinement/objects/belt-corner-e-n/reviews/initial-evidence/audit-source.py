import bpy,json,math,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[2]; W=next(p for p in B.parents if (p/'prototypes.json').exists()); S=W/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
rows=lambda m:[[float(x) for x in r]for r in m]
vec=lambda v:[float(x)for x in v]
def props(o):return {k:o[k] if isinstance(o[k],(str,int,float,bool)) else str(o[k])for k in o.keys()}
def audit(project,ident,collection):
 bpy.ops.wm.open_mainfile(filepath=str(project));s=bpy.context.scene;coll=bpy.data.collections[collection];coll.hide_viewport=False;coll.hide_render=False
 def reveal(l):
  l.exclude=False;l.hide_viewport=False
  for c in l.children:reveal(c)
 reveal(bpy.context.view_layer.layer_collection)
 for o in coll.all_objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update()
 if ident=='belt-corner-e-n':
  rec=json.loads((B/'inputs/source-rig.json').read_text())['clips']['running']['actions'][0];m=bpy.data.materials[rec['materialOwnerName']];m.node_tree.animation_data_create();m.node_tree.animation_data.action=bpy.data.actions[rec['action']];m.node_tree.animation_data.action_slot=next(sl for sl in bpy.data.actions[rec['action']].slots if sl.identifier==rec['slotIdentifier']);s.frame_set(1)
 root=next(o for o in coll.objects if '__root' in o.name);orient=next(o for o in coll.objects if '__orientation' in o.name);meshes=[o for o in coll.all_objects if o.type=='MESH'];bpy.context.view_layer.update();r={'project':str(project),'sha256':hashlib.sha256(project.read_bytes()).hexdigest(),'collection':coll.name,'activeScene':s.name,'activeCamera':s.camera.name if s.camera else None,'activeCameraWorld':rows(s.camera.matrix_world)if s.camera else None,'renderResolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'fps':s.render.fps,'root':{'name':root.name,'matrix':rows(root.matrix_world),'properties':props(root)},'orientation':{'name':orient.name,'matrixLocal':rows(orient.matrix_local),'rotationEuler':vec(orient.rotation_euler)},'meshes':[],'phase':{}}
 bounds=[]
 for o in meshes:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vs=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices];bounds+=vs
  item={'name':o.name,'vertices':len(o.data.vertices),'evaluatedVertices':len(me.vertices),'polygons':len(o.data.polygons),'matrixLocal':rows(o.matrix_local),'bounds':[[min(v[i]for v in vs)for i in range(3)],[max(v[i]for v in vs)for i in range(3)]],'modifiers':[{'name':m.name,'type':m.type,**({'width':m.width,'segments':m.segments}if m.type=='BEVEL'else{})}for m in o.modifiers],'materials':[m.name for m in o.data.materials]}
  if 'connected_turn_deck' in o.name:
   uv=o.data.uv_layers.active;by={}
   for po in o.data.polygons:
    for li in po.loop_indices:
     vi=o.data.loops[li].vertex_index;by[vi]={'vertex':vec(o.data.vertices[vi].co),'uv':vec(uv.data[li].uv),'rootVertex':vec(root.matrix_world.inverted()@o.matrix_world@o.data.vertices[vi].co)}
   item['deckUV']=by
  if 'rail' in o.name:item['terminalVertices']=[vec(root.matrix_world.inverted()@o.matrix_world@v.co)for v in o.data.vertices if abs(v.co.y-.5)<1e-5 or abs(v.co.x-.5)<1e-5]
  r['meshes'].append(item);ev.to_mesh_clear()
  for m in o.data.materials:
   if m.node_tree and m.node_tree.nodes.get('Value'):
    n=m.node_tree.nodes['Value'];r['phase']['material']=m.name;r['phase']['keys']=[]
    for f in range(1,26):s.frame_set(f);r['phase']['keys'].append([f,float(n.outputs[0].default_value)])
    r['phase']['action']=m.node_tree.animation_data.action.name if m.node_tree.animation_data and m.node_tree.animation_data.action else None
    r['phase']['nodeGraph']=[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':[{'name':i.name,'value':vec(i.default_value)if hasattr(i,'default_value')and hasattr(i.default_value,'__len__')else i.default_value if hasattr(i,'default_value')and isinstance(i.default_value,(int,float,bool,str))else None}for i in n.inputs]}for n in m.node_tree.nodes]
 r['bounds']=[[min(v[i]for v in bounds)for i in range(3)],[max(v[i]for v in bounds)for i in range(3)]]
 return r
r={'source':audit(S,'belt-corner-e-n','S33_FB_belt-corner-e-n.001')};f=json.loads((B/'inputs/family-settings.json').read_text());r['family']=audit(Path(f['project']['path']),'belt-straight-n',f['project']['collection']);(B/'reviews/initial-evidence/native-audit-evaluable.json').write_text(json.dumps(r,indent=2));print('JUDGE_AUDIT',json.dumps({k:{a:v[a]for a in ['sha256','activeScene','activeCamera','renderResolution','pixelAspect','fps','orientation','bounds']}for k,v in r.items()}))
