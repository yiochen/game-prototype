import bpy,json,pathlib,importlib.util,math
from mathutils import Vector
base=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
out=base/'prototypes/sushi-loop/assets/refinement/objects/chef-dalia/reviews'
record=json.loads((out.parent/'inputs/source-rig.json').read_text())
root=bpy.data.objects.get(record['groundRootObject'])
cs=[c for c in bpy.data.collections if root in list(c.all_objects)]
result={'blenderVersion':bpy.app.version_string,'root':root.name,'rootParent':root.parent.name if root.parent else None,'collections':[{'name':c.name,'objects':len(c.all_objects)} for c in cs], 'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'materials':[m.name for m in o.data.materials if m] if hasattr(o.data,'materials') else [],'hideRender':o.hide_render} for o in min(cs,key=lambda c:len(c.all_objects)).all_objects]}
(out/'source-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result)[:2000])
col=min(cs,key=lambda c:len(c.all_objects))
sc=bpy.data.scenes.new('Dalia independent source audit'); sc.collection.children.link(col);bpy.context.window.scene=sc
col.hide_viewport=False;col.hide_render=False
for o in col.all_objects:
 o.hide_viewport=False;o.hide_set(False)
modpath=base/'prototypes/sushi-loop/assets/production/source/blender/revisions/d88e53edef8e7c73/native_actions.py'
spec=importlib.util.spec_from_file_location('dalia_original_native_actions',modpath);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
arm=bpy.data.objects.get(record['armatures'][0]['object']);asset={'root':root,'collection':col,'armature':arm}
meshes=[o for o in col.all_objects if o.type=='MESH']
def bounds(points):
 return {'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]} if points else None
def geom(o,dg):
 eo=o.evaluated_get(dg);me=eo.to_mesh();pts=[eo.matrix_world@v.co for v in me.vertices];result={'bounds':bounds(pts),'vertexCount':len(me.vertices),'polygonCount':len(me.polygons),'center':list(sum(pts,Vector())/len(pts)) if pts else None,'hideRender':o.hide_render};eo.to_mesh_clear();return result,pts
frames=[];loopclosure=[]
for clip in record['clips']:
 for direction in ['S','E','N','W']:
  for f in range(1,13):
   native.apply_clip(asset,record,clip,f,direction,sc);dg=bpy.context.evaluated_depsgraph_get();allpts=[];bodypts=[];parts={}
   for o in meshes:
    g,pts=geom(o,dg)
    if not o.hide_render:
     allpts+=pts
     if '__held_' not in o.name and '__knife' not in o.name:bodypts+=pts
    if any(s in o.name for s in ['minimal_foot','palm_','thumb_','__held_dish','__knife','__cap.','__head.']):parts[o.name]=g
   ae=arm.evaluated_get(dg)
   frames.append({'clip':clip,'direction':direction,'index':f-1,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'bodyBounds':bounds(bodypts),'visibleBounds':bounds(allpts),'parts':parts,'handBones':{s:{'head':list(ae.matrix_world@ae.pose.bones['hand_'+s].head),'tail':list(ae.matrix_world@ae.pose.bones['hand_'+s].tail)} for s in ['L','R']},'dishRootMatrix':[list(r) for r in bpy.data.objects[record['groundRootObject']+'__held_dish-salmon'].matrix_world]})
# inspect one canonical closing key for declared loops; do not treat load as a loop
for clip,r in record['clips'].items():
 if not r['loop']:continue
 native.apply_clip(asset,record,clip,13,'S',sc);dg=bpy.context.evaluated_depsgraph_get();loopclosure.append({'clip':clip,'frame':13,'parts':{o.name:geom(o,dg)[0] for o in meshes}})
external=[]
for o in meshes:
 for m in o.data.materials:
  if m and m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:external.append({'object':o.name,'material':m.name,'image':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)})
result={'sourceProject':'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','collection':col.name,'blenderVersion':bpy.app.version_string,'isolation':'New scene linked intended collection; viewport enabled for evaluated native rig; no source saved','declaredHeight':1.3750000298023224,'nativeHelper':str(modpath.relative_to(base)),'frames':frames,'loopClosureFrame13':loopclosure,'imagesUsedByOwnedMaterials':external,'customProperties':{o.name:{k:str(o[k]) for k in o.keys()} for o in [root,arm,bpy.data.objects[record['groundRootObject']+'__held_dish-salmon']]}}
(out/'source-evaluated-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('AUDITED',len(frames),'frames')
