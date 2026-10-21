import bpy, json, math
from pathlib import Path
from mathutils import Vector

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
record=json.loads((EXP/'inputs/source-rig.json').read_text())
cols=[c for c in bpy.data.collections if c.name.startswith('S33_FB_belt-straight-w')]
objs=list({o.name:o for c in cols for o in c.all_objects}.values())
scene=bpy.context.scene
out={'blender':bpy.app.version_string,'scene':scene.name,'activeCamera':scene.camera.name if scene.camera else None,'collections':[c.name for c in cols],'objects':[]}
def mat(m): return [[float(x) for x in row] for row in m]
for o in objs:
    o.hide_viewport=False; o.hide_render=False; o.hide_set(False)
    out['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':mat(o.matrix_world),'dimensions':list(o.dimensions),'materials':[x.name if x else None for x in o.data.materials] if o.type=='MESH' else [],'vertices':len(o.data.vertices) if o.type=='MESH' else None,'uvLayers':[{ 'name':u.name,'range':[[min(d.uv[k] for d in u.data),max(d.uv[k] for d in u.data)] for k in (0,1)]} for u in o.data.uv_layers] if o.type=='MESH' else [],'modifiers':[(m.name,m.type) for m in o.modifiers]})
def unhide(lc):
    lc.exclude=False;lc.hide_viewport=False
    for x in lc.children: unhide(x)
unhide(bpy.context.view_layer.layer_collection)
for c in cols: c.hide_render=False;c.hide_viewport=False
bpy.context.view_layer.update()
actionrec=record['clips']['running']['actions'][0]
nt=bpy.data.materials[actionrec['materialOwnerName']].node_tree
action=bpy.data.actions[actionrec['action']]
before=nt.animation_data.action.name if nt.animation_data and nt.animation_data.action else None
nt.animation_data_create();nt.animation_data.action=action
nt.animation_data.action_slot=next(s for s in action.slots if s.identifier==actionrec['slotIdentifier'])
out['nodeAction']={'beforeBoundAction':before,'action':action.name,'slot':nt.animation_data.action_slot.identifier,'curves':[],'phase':{}}
for layer in action.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    out['nodeAction']['curves'].append({'path':fc.data_path,'index':fc.array_index,'points':[[float(k.co[0]),float(k.co[1]),k.interpolation] for k in fc.keyframe_points]})
for frame in (1,2,7,13,24,25):
 scene.frame_set(frame);bpy.context.view_layer.update()
 out['nodeAction']['phase'][str(frame)]={n.name:float(n.outputs[0].default_value) for n in nt.nodes if n.bl_idname=='ShaderNodeValue'}
out['materials']=[]
for m in {m.name:m for o in objs if o.type=='MESH' for m in o.data.materials if m}.values():
 out['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'op':getattr(n,'operation',None),'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and isinstance(s.default_value,(int,float,tuple,list,Vector))}} for n in m.node_tree.nodes] if m.use_nodes else []})
out['worldBounds']={}
out['evaluatedTransforms']={o.name:{'matrix':mat(o.matrix_world),'localRotation':list(o.rotation_euler)} for o in objs}
out['deck']={}
for o in objs:
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices]
  out['worldBounds'][o.name]=[[min(p[k] for p in pts),max(p[k] for p in pts)] for k in range(3)]
  if 'connected_straight_deck' in o.name:
   uv=o.data.uv_layers.active
   out['deck']={'localVertices':[list(v.co) for v in o.data.vertices],'worldVertices':[list(o.matrix_world@v.co) for v in o.data.vertices],'uvLoops':[{'vertex':l.vertex_index,'uv':list(uv.data[l.index].uv)} for l in o.data.loops],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in nt.links]}
(HERE/'independent-source-inspection-v1.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
