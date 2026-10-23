import bpy, json, hashlib
from pathlib import Path
RAW=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend')
OUT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/portal-entry/source/initial-native-actions-probe.json')
assert hashlib.sha256(RAW.read_bytes()).hexdigest()=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
scene=bpy.data.scenes['S33 Native Asset Library Export']
coll=bpy.data.collections['S33_PROP_portal_rim.003']
root=bpy.data.objects['portal_rim__root.003']
def val(v):
 if v is None or isinstance(v,(str,int,float,bool)):return v
 if hasattr(v,'to_list'):return val(v.to_list())
 try:return [val(x) for x in v]
 except TypeError:return str(v)
record=json.loads(root['native_action_record'])
actions=[]
for clip,names in record['clips'].items():
 for name in names:
  a=bpy.data.actions.get(name)
  entry={'clip':clip,'declared_name':name,'present':a is not None}
  if a:
   entry.update({'name':a.name,'users':a.users,'use_fake_user':a.use_fake_user,'library':a.library.filepath if a.library else None,'frame_range':val(a.frame_range),'custom_properties':{k:val(a[k]) for k in a.keys()},'slots':[{'identifier':s.identifier,'target_id_type':s.target_id_type} for s in a.slots],'layers':[]})
   for l in a.layers:
    ld={'name':l.name,'strips':[]}
    for s in l.strips:
     sd={'type':s.type,'channelbags':[]}
     for cb in getattr(s,'channelbags',[]):
      sd['channelbags'].append({'slot_handle':cb.slot_handle,'fcurves':[{'data_path':f.data_path,'array_index':f.array_index,'keyframes':[{'co':val(k.co),'interpolation':k.interpolation} for k in f.keyframe_points]} for f in cb.fcurves]})
     ld['strips'].append(sd)
    entry['layers'].append(ld)
  actions.append(entry)
mods=[]
for o in sorted(coll.all_objects,key=lambda x:x.name):
 for m in o.modifiers:
  mods.append({'object':o.name,'name':m.name,'type':m.type,'width':m.width if m.type=='BEVEL' else None,'segments':m.segments if m.type=='BEVEL' else None,'affect':m.affect if m.type=='BEVEL' else None,'limit_method':m.limit_method if m.type=='BEVEL' else None})
materials=sorted({s.material for o in coll.all_objects for s in o.material_slots if s.material},key=lambda m:m.name)
mats=[]
for m in materials:
 nodes=[]
 if m.node_tree:
  for n in m.node_tree.nodes:
   if n.type in ('VALTORGB','MAP_RANGE','MATH','VECT_MATH','MIX_RGB'):
    nd={'name':n.name,'type':n.type,'inputs':[{'name':i.name,'identifier':i.identifier,'default_value':val(i.default_value),'linked':i.is_linked} for i in n.inputs if hasattr(i,'default_value')]}
    for attr in ('operation','blend_type','interpolation_type','clamp','use_clamp'):
     if hasattr(n,attr):nd[attr]=val(getattr(n,attr))
    if n.type=='VALTORGB':nd['color_ramp']={'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':val(e.color)} for e in n.color_ramp.elements]}
    nodes.append(nd)
 mats.append({'name':m.name,'node_parameters':nodes})
result={'scope':'Supplemental untouched raw own action/datablock and material parameter inspection only. No action assignment, frame change, capture, modeling or saves.','raw_sha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'raw_scene':scene.name,'raw_frame_current':scene.frame_current,'root_native_action_record':record,'declared_actions':actions,'modifiers':mods,'material_parameters':mats}
with OUT.open('x') as f:json.dump(result,f,indent=2,sort_keys=True)
print(json.dumps({'output':str(OUT),'bytes':OUT.stat().st_size,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'declared_action_count':len(actions),'present_actions':sum(a['present'] for a in actions),'modifiers':mods}))
