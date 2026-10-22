"""Independent actual evaluated native cohorts; exact snapshot copies in memory only."""
import runpy,sys,json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parent;G=runpy.run_path(str(P/'physical_scene_entry.py'));globals().update(G)
AH=R/'inputs/approved-hut-v1/project.blend';assert sha(AH)=='1594c02e736a4c6c9ecbbb03d26c140aceb002d474a55eb19bea15808794403b'
with bpy.data.libraries.load(str(AH),link=False)as(a,b):
 print('APPROVED_HUT_COLLECTIONS',a.collections,flush=True);b.collections=[n for n in a.collections if n not in ['Collection']]
acs=[]
for c in b.collections:
 sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 if any(o.type=='MESH'for o in c.all_objects):acs.append(c)
ac=next(c for c in acs if any(o.parent is None and o.type=='EMPTY'for o in c.all_objects));ar=next(o for o in ac.all_objects if o.parent is None and o.type=='EMPTY');ar.location=(.78,.35,.23);ar.rotation_euler=(0,0,0);bpy.context.view_layer.update()
# Source companions are already evaluated at exact frame12. Capture actual dependency graph,
# including their immutable transforms/material state; actor evaluation can then use frame7.
pose();bpy.context.view_layer.update();snapshots={};snapshotAudit=[]
def freeze_col(aid,col):
 dg=bpy.context.evaluated_depsgraph_get();dst=bpy.data.collections.new('V4_EVALUATED_'+aid);sc.collection.children.link(dst);wrapper=bpy.data.objects.new('V4_COHORT_ROOT_'+aid,None);dst.objects.link(wrapper);rows=[]
 for ob in col.all_objects:
  if ob.type!='MESH' or ob.hide_render:continue
  ev=ob.evaluated_get(dg);mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=dg);cp=bpy.data.objects.new('V4_'+aid+'__'+ob.name,mesh);dst.objects.link(cp);cp.matrix_world=ev.matrix_world.copy();cp.parent=wrapper
  for i,mat in enumerate(mesh.materials):
   if mat:
    mc=mat.copy();mc.animation_data_clear()
    if mc.use_nodes and mc.node_tree:mc.node_tree.animation_data_clear()
    mesh.materials[i]=mc
  before=[tuple(ev.matrix_world@v.co)for v in ev.data.vertices] if ev.type=='MESH' else[]
  # evaluated_get.data can have original topology with modifiers; use to_mesh for exact comparison.
  em=ev.to_mesh();before=[tuple(ev.matrix_world@v.co)for v in em.vertices];ev.to_mesh_clear();after=[tuple(cp.matrix_world@v.co)for v in mesh.vertices];err=max((Vector(x)-Vector(y)).length for x,y in zip(before,after))if before else 0
  assert len(before)==len(after)and err<1e-9
  rows.append({'sourceObject':ob.name,'snapshotObject':cp.name,'vertices':len(after),'maximumWorldVertexError':err,'sourceMatrix':[list(r)for r in ev.matrix_world],'materialCopies':[m.name for m in mesh.materials if m],'worldVertexSHA256':hashlib.sha256(json.dumps(after,separators=(',',':')).encode()).hexdigest()})
 col.hide_render=True;col.hide_viewport=True
 snapshots[aid]={'collection':dst,'root':wrapper};snapshotAudit.append({'id':aid,'sourceCollection':col.name,'nativeClip':'uncover'if aid=='dock-cover'else'dock-ready'if aid=='submarine-yellow'else'static','nativeFrame':12 if aid in ['dock-cover','submarine-yellow']else 1,'objects':rows})
for aid,q in companions.items():freeze_col(aid,q['collection'])
freeze_col('approved-workshop-hut',ac)
_base_pose=pose
def pose(x=0,y=0,z=0,d='S',clip='stand',frame=12):
 _base_pose(x,y,z,d,clip,frame);a={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
 for q in snapshots.values():q['root'].rotation_euler.z=a
 bpy.context.view_layer.update()
sourceHashes['approvedHut']=sha(AH)
