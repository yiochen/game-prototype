import bpy,sys,json,math,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;R=H/'resources'
def load(n):
 s=importlib.util.spec_from_file_location('safe_contacts_'+n,R/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((R/'source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects))
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for c in [col,*list(col.children_recursive)]:c.hide_render=False;c.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update();native=load('native_actions');asset={'collection':col,'root':root};native.apply_clip(asset,rig,'ambient',frame=1,direction='S',scene=sc)
contacts=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 verts=[o.matrix_world@v.co for v in o.data.vertices];points=[]
 for edge in o.data.edges:
  a,b=[verts[i] for i in edge.vertices]
  if abs(a.z)<1e-7:points.append([a.x,a.y,0])
  if a.z*b.z<0:
   t=-a.z/(b.z-a.z);p=a+(b-a)*t;points.append([p.x,p.y,0])
 contacts.append({'object':o.name,'rawZ0IntersectionPoints':points,'rawZRange':[min(v.z for v in verts),max(v.z for v in verts)],'groundRelation':'intersects native z=0' if points else 'above native z=0' if min(v.z for v in verts)>0 else 'below native z=0','modifiers':[{'name':m.name,'type':m.type,'limit_method':getattr(m,'limit_method',None),'angle_limit':getattr(m,'angle_limit',None)} for m in o.modifiers]})
actions=[]
for target in rig['clips']['ambient']['actions']:
 a=bpy.data.actions[target['action']];curves=native._fcurves(a)
 actions.append({'owner':target['ownerName'],'action':a.name,'actualFrameRange':list(a.frame_range),'channels':[{'dataPath':f.data_path,'arrayIndex':f.array_index,'keys':[[p.co.x,p.co.y,p.interpolation] for p in f.keyframe_points]} for f in curves]})
(H/'contacts-actions.json').write_text(json.dumps({'measurement':'Fresh enabled original S frame1; raw authored edge intersections with world z=0. No full-cell support inferred. Not contact collision certification.','contacts':contacts,'actions':actions,'armatures':[],'shapeKeys':[],'ports':[],'sockets':{},'functionalRegistration':'nonblocking flank module; no attached family joins'},indent=2)+'\n')
print('SAFE_CONTACTS_ACTIONS_COMPLETE')
