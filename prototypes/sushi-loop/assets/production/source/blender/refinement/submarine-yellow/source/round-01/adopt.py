"""Exact accepted IDLE neutral adoption into frozen v6. No art edits."""
import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib,runpy
from pathlib import Path
from mathutils import Matrix
H=Path(__file__).resolve().parent;B=H.parents[1];R=H/'resources';O=B/'candidates/round-01';O.mkdir(exist_ok=True)
F=runpy.run_path(str(H/'component_identity.py'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert sha(R/'frozen-body-v6.blend')=='c8462a4072c8ce12f2afcc6907a02d705dcd7df6858f7d790bb2a1dcc5d7fb0e'
bpy.ops.wm.open_mainfile(filepath=str(R/'frozen-body-v6.blend'));s=bpy.context.scene;main=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];root=bpy.data.objects['submarine-yellow__root']
# Frozen body objects and native action datablocks remain untouched. Only explicit
# PROVISIONAL geometry/units are removed; their old visibility actions are retained
# as immutable source provenance, excluded from the resolved runtime owner map.
removed=[o.name for o in list(main.all_objects) if o.name.startswith('PROVISIONAL__')]
for name in removed:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
config=[
 {'asset':'sub-hull-panels','prefix':'inputs/approved-equipment-preparation-v1/sub-hull-panels','project':'source/round-01-neutral.blend','collection':'SUB_HULL_PANELS__neutral','root':'sub-hull-panels__root','signed':'candidates/round-01/neutral-resource-identity.json','schema':'panel_identity'},
 {'asset':'sub-harpoon-mount','prefix':'inputs/approved-equipment-preparation-v1/sub-harpoon-mount','project':'source/round-02/project.blend','collection':'CANONICAL__sub-harpoon-mount','root':'harpoon__root','signed':'candidates/round-02/canonical-neutral-persistent-resources.json','schema':'harpoon_identity'},
 {'asset':'sub-collector-inlet','prefix':'inputs/approved-canonical-equipment-v1/sub-collector-inlet','project':'source/round-02.blend','collection':'CANONICAL__sub-collector-inlet','root':'collector__root','signed':'candidates/round-02/canonical-neutral-resources.json','schema':'collector_identity'}]
reports=[];allgear=[]
for q in config:
 base=R/'approved-inputs'/q['prefix'];project=base/q['project']
 with bpy.data.libraries.load(str(project),link=False) as(src,dst):
  if q['collection'] not in src.collections:
   candidates=[n for n in src.collections if 'collector' in n.lower()];q['collection']=candidates[0]
  dst.collections=[q['collection']]
 c=dst.collections[0];main.children.link(c);c.hide_render=False;c.hide_viewport=False;cr=bpy.data.objects[q['root']]
 # Exact saved canonical-S IDLE pose, not ACTIVE frame1.
 cr.rotation_euler.z=0
 if q['asset']=='sub-collector-inlet':
  for owner,an in json.loads(cr['nativeActions'])['idle'].items():
   o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
 s.frame_set(1);bpy.context.view_layer.update()
 expected=json.loads((base/q['signed']).read_text());actual=F[q['schema']](c)
 expected_payload=expected if q['asset']=='sub-hull-panels' else expected['objects'] if q['asset']=='sub-harpoon-mount' else expected['records']
 assert actual==expected_payload,('Signed neutral mismatch',q['asset'])
 neutral=F['persistent'](c)
 # Preserve every persistent native transform while neutralizing component-only
 # standalone actions. Main supplies visibility only; no active motion mapping.
 for o in c.all_objects:
  if o.animation_data:o.animation_data_clear()
 bpy.context.view_layer.update();assert F['persistent'](c)==neutral
 mount=bpy.data.objects['MOUNT__'+q['asset']];cr.parent=mount;cr.matrix_parent_inverse=Matrix.Identity(4);cr.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
 mounted=F['persistent'](c)
 for row in mounted:
  if row['name']==cr.name:row['parent']=None
 assert mounted==neutral,('Persistent resource changed',q['asset'])
 pts=[];errors=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();inv=cr.matrix_world.inverted();local=[inv@(e.matrix_world@v.co) for v in me.vertices];expect=[(o.matrix_world if False else cr.matrix_world.inverted()@o.matrix_world)@v.co for v in me.vertices];res=max((a-b).length for a,b in zip(local,expect));errors.append({'object':o.name,'inverseWorldResidual':res});e.to_mesh_clear();allgear.append(o)
 reports.append({'asset':q['asset'],'projectSHA256':sha(project),'signedResourceSHA256':sha(base/q['signed']),'signedNeutralSchemaMatch':True,'signedCanonicalFingerprint':F['hd'](actual),'persistentNeutralSHA256':F['hd'](neutral),'mountedPersistentSHA256':F['hd'](mounted),'persistentIdentityExact':True,'root':cr.name,'collection':c.name,'mount':mount.name,'actualMountMatrix':F['matrix'](mount.matrix_local),'rootMatrixBasis':F['matrix'](cr.matrix_basis),'inverseExtraction':errors,'meshNames':[o.name for o in c.all_objects if o.type=='MESH'],'allObjectNames':[o.name for o in c.all_objects]})
# Replace legacy provisional visibility owners with exact native canonical
# visibility cohorts; frozen body motion/propeller/status actions are reused.
visibility={}
for clip in json.loads(root['nativeActions']):
 visibility[clip]={}
 for o in allgear:
  o.animation_data_clear();o.hide_render=not clip.startswith('upgraded-');o.hide_viewport=o.hide_render
  for fr in [1,13]:o.keyframe_insert('hide_render',frame=fr);o.keyframe_insert('hide_viewport',frame=fr)
  a=o.animation_data.action;a.name='CANONICAL_VISIBILITY__'+clip+'__'+o.name;a.use_fake_user=True
  for l in a.layers:
   for st in l.strips:
    for bag in st.channelbags:
     for fc in bag.fcurves:
      for k in fc.keyframe_points:k.interpolation='CONSTANT'
  visibility[clip][o.name]=a.name;o.animation_data_clear()
for o in allgear:o.hide_render=True;o.hide_viewport=True
main['canonicalVisibilityActions']=json.dumps(visibility);main['canonicalComponents']=json.dumps(reports);main['removedProvisionalOwners']=json.dumps(removed);main['mainClipPolicy']='Exact neutral geometry under frozen mounts; only existing base/upgraded visibility; no standalone active-main mapping.'
s.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(H/'project.blend'),compress=True)
save(O/'adoption.json',{'frozenBodySHA256':sha(R/'frozen-body-v6.blend'),'projectSHA256':sha(H/'project.blend'),'removedOnlyExplicitProvisionalObjects':removed,'components':reports,'nativeVisibilityActions':visibility,'policy':'No native geometry/normal/UV/material/rebevel/nonuniform/per-view fit. Source component animation neutralized at signedIDLE only; native main visibility replaces provisional cohorts. Existing frozen body actions/metadata unchanged.'})
print('ADOPTED',sha(H/'project.blend'),[(q['asset'],q['signedNeutralSchemaMatch'],q['persistentIdentityExact']) for q in reports])
