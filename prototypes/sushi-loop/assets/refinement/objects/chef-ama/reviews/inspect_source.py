import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
EXP=ROOT/'prototypes/sushi-loop/assets/refinement/objects/chef-ama'
rig=json.loads((EXP/'inputs/source-rig.json').read_text())
root=bpy.data.objects[rig['groundRootObject']]
collection=next(c for c in bpy.data.collections if root in list(c.all_objects))
sc=bpy.data.scenes.new('Ama Judge Readonly Inspection')
sc.collection.children.link(collection)
bpy.context.window.scene=sc
collection.hide_render=False;collection.hide_viewport=False
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False
bpy.context.view_layer.update()
source=ROOT/'prototypes/sushi-loop/assets/production/source/blender'
sys.path.insert(0,str(source))
import native_actions as NA
asset={'id':'chef-ama','root':root,'collection':collection}
def compact(o):
 return {'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'hideRender':o.hide_render,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type} for c in o.constraints]}
def bounds(objects):
 pts=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  if o.type!='MESH' or o.hide_render:continue
  ev=o.evaluated_get(dg)
  pts.extend(ev.matrix_world@Vector(c) for c in ev.bound_box)
 return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]] if pts else None
out={'sourcePath':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'assetCollection':collection.name,'root':compact(root),'objects':[compact(o) for o in collection.all_objects],'sceneNames':[s.name for s in bpy.data.scenes],'clips':{},'notes':['Read-only in-memory isolated scene. No source .blend saved. Actual evaluated native actions inspected.']}
for clip in rig['clips']:
 rec=[]
 for f in range(1,13):
  NA.apply_clip(asset,rig,clip,f,'S',sc)
  dg=bpy.context.evaluated_depsgraph_get();arm=next(o for o in collection.all_objects if o.type=='ARMATURE')
  poses={b.name:list((arm.evaluated_get(dg).matrix_world@b.matrix).translation) for b in arm.evaluated_get(dg).pose.bones if any(v in b.name for v in ['foot','hand','ground','head'])}
  rec.append({'frame':f,'visibleBounds':bounds(collection.all_objects),'poseContactsWorld':poses,'visibleMeshes':[o.name for o in collection.all_objects if o.type=='MESH' and not o.hide_render]})
 out['clips'][clip]={'frames':rec,'actions':[{'name':a['action'],'exists':a['action'] in bpy.data.actions} for a in rig['clips'][clip]['actions']]}
(EXP/'reviews/source-inspection.json').write_text(json.dumps(out,indent=2)+'\n')
print('JUDGE_SOURCE_INSPECTION',json.dumps({'root':out['root'],'collection':out['assetCollection'],'objectCount':len(out['objects']),'meshCount':sum(o['type']=='MESH' for o in out['objects']),'clips':{k:{'boundsFrame1':v['frames'][0]['visibleBounds'],'actionCount':len(v['actions']),'allActionsPresent':all(a['exists'] for a in v['actions'])} for k,v in out['clips'].items()}},indent=2))
