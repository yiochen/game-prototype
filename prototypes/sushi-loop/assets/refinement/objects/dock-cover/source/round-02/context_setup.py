"""FINAL EXACT CONTEXT memory-only exact-fixture study. Never saves joined scenes."""
import bpy,json,math,hashlib,sys,importlib.util
from pathlib import Path
from mathutils import Vector,Matrix
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parents[1];OUT=O/'candidates/round-02';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=load('cover_finite_geometry',H/'native_geometry.py');native=load('cover_rosa_native',H/'resources/native_actions.py')
bpy.ops.wm.open_mainfile(filepath=str(H/'cover.blend'));sc=bpy.context.scene;cover=bpy.data.collections['WarmSoft_dock-cover'];cr=bpy.data.objects['dock-cover__root'];cloth=bpy.data.objects['dock-cover__attached_canvas_hems_and_stitches'];sk=cloth.data.shape_keys;rig=json.loads((H/'rig.json').read_text());dirs={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
fixtures={};sourceHashes={}
def append(aid,path,colname,loc,actions=False):
 with bpy.data.libraries.load(str(path),link=False)as(src,dst):
  dst.collections=[colname]
  if actions:dst.actions=src.actions
 c=dst.collections[0];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;r=next(o for o in c.all_objects if o.type=='EMPTY'and o.parent is None);r.location=loc;r.rotation_euler=(0,0,0);fixtures[aid]={'collection':c,'root':r,'sourceRoot':loc};sourceHashes[aid]=sha(path);return c,r
fc,fr=append('floor',O/'inputs/approved-dock-family-v1/dock-floor/project.blend','WarmSoft_dock-floor',(0,0,0))
ec,er=append('entry',O/'inputs/approved-dock-family-v1/dock-entry/project.blend','S33_PROP_dock-entry',(0,-1.5,0))
hc,hr=append('hut',O/'inputs/approved-dock-family-v1/workshop-hut/project.blend','WarmSoft_workshop-hut',(.78,.35,.23))
subc,sr=append('sub',O/'inputs/approved-final-main-v1/project.blend','WarmSoft_submarine-yellow_stage1',(-.7,-.42,.23),True);subactions=json.loads(sr['nativeActions'])
RH=O/'inputs/shared-world-pose-v1/resources/source/resources/approved-human-v3';rrig=json.loads((RH/'rig.json').read_text());rp=RH/'customer-rosa-approved.blend'
with bpy.data.libraries.load(str(rp),link=False)as(src,dst):dst.collections=['S33_CHARACTER_customer_rosa.001'];dst.actions=sorted({t['action']for c in ['stand','walk']for t in rrig['clips'][c]['actions']})
rc=dst.collections[0];sc.collection.children.link(rc);rr=bpy.data.objects[rrig['groundRootObject']];sourceHashes['rosa']=sha(rp);plan=json.loads((O/'inputs/shared-world-pose-v1/plan.json').read_text())
assert all(abs(v-1.25)<1e-9 for v in rr.scale)
def coverpose(clip,f,d='S'):
 sk.animation_data.action=None
 for k in sk.key_blocks:k.value=0
 sk.animation_data.action=bpy.data.actions[rig['clips'][clip]['action']]
 if sk.animation_data.action.slots:sk.animation_data.action_slot=sk.animation_data.action.slots[0]
 R=Matrix.Rotation(dirs[d],3,'Z');cr.location=(0,0,.23);cr.rotation_euler.z=dirs[d]
 for a in fixtures.values():a['root'].location=R@Vector(a['sourceRoot']);a['root'].rotation_euler.z=dirs[d]
 sc.frame_set(math.floor(f),subframe=f%1);bpy.context.view_layer.update()
main_native=load('cover_final_main_native',H/'resources/main_native_common.py')
def subpose(clip):
 main_native.apply(clip,sc.frame_current+sc.frame_subframe,'S',(-.7,-.42,.23))
# Frozen exact authored1.25 human meshes for each of nine discrete approved source poses.
actorSnapshots={};materials={}
for case in plan['cases']:
 native.apply_clip({'root':rr,'collection':rc},rrig,case['actorClip'],case['nativeFrame'],'S',sc);rr.location=(*case['sourceFacingXY'],case['solvedRootZ']);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();c=bpy.data.collections.new('Rosa exact stance '+case['id']);sc.collection.children.link(c)
 for ob in rc.all_objects:
  if ob.type!='MESH'or ob.hide_render or not ob.visible_camera:continue
  ev=ob.evaluated_get(dg);me=bpy.data.meshes.new_from_object(ev,depsgraph=dg);sn=bpy.data.objects.new('stance__'+case['id']+'__'+ob.name,me);c.objects.link(sn);sn.matrix_world=ev.matrix_world.copy();sn['original_world_matrix']=[v for row in sn.matrix_world for v in row]
  for j,m in enumerate(sn.data.materials):
   if m:
    key=(case['id'],m.name)
    if key not in materials:
     mm=m.copy();mm.animation_data_clear()
     if mm.node_tree:mm.node_tree.animation_data_clear()
     materials[key]=mm
    sn.data.materials[j]=materials[key]
 c.hide_render=True;actorSnapshots[case['id']]=c
rc.hide_render=True
for ob in rc.all_objects:ob.hide_render=True
subpose('upgraded-dock-ready');coverpose('covered',1)
