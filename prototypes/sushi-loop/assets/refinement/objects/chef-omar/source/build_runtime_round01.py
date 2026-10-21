"""Carry the exact refined actor mesh/materials into original native cucumber behavior."""
import bpy,json,sys,hashlib,copy
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).parent; BASE=P.parent; sys.path.insert(0,str(P))
import native_actions_round01 as native
from audit_common_round01 import contacts, food_signature
sc=next(s for s in bpy.data.scenes if s.get('meal_variants')); bpy.context.window.scene=sc
root=bpy.data.objects['S11 cucumber chef_omar__ground_root.001']
arm=bpy.data.objects['S11 cucumber chef_omar__armature.001']
coll=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects))
coll.hide_render=False;coll.hide_viewport=False; bpy.context.view_layer.update()
(P/'runtime-source-food-round01.json').write_text(json.dumps(food_signature(coll),indent=2))
rig=copy.deepcopy(json.loads((P/'rig-round01.json').read_text()));rig['groundRootObject']=root.name
rig['clips']={new:copy.deepcopy(rig['clips'][old]) for new,old in [('hold-cucumber','hold'),('load-cucumber','load')]}
for c in rig['clips'].values():
 for t in c['actions']:
  t['ownerName']='S11 cucumber '+t['ownerName']; t['action']='S11 cucumber '+t['action']
  assert t['ownerName'] in bpy.data.objects and t['action'] in bpy.data.actions, t
(P/'runtime-rig-round01.json').write_text(json.dumps(rig,indent=2))
asset={'collection':coll,'root':root,'armature':arm}
source=[]
for clip in rig['clips']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,clip,f,d,sc)
   source.append({'clip':clip,'direction':d,'index':f-1,**contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get())})
(P/'runtime-source-contacts-round01.json').write_text(json.dumps(source,separators=(',',':')))
rest={b.name:{'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None,'deform':b.use_deform} for b in arm.data.bones}
(P/'runtime-source-rest-round01.json').write_text(json.dumps(rest,indent=2))
actions={t['action'] for c in rig['clips'].values() for t in c['actions']}
action_hashes={name:hashlib.sha256(json.dumps([(c.data_path,c.array_index,[(list(k.co),k.interpolation) for k in c.keyframe_points]) for c in native._fcurves(bpy.data.actions[name])],sort_keys=True).encode()).hexdigest() for name in actions}
camera_source={'worldMatrix':[list(r) for r in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]}
with bpy.data.libraries.load(str(P/'round-01.blend'),link=False) as (available,loaded):
 loaded.scenes=['Omar warm soft round01']
refscene=loaded.scenes[0]
bpy.context.window.scene=refscene; bpy.context.view_layer.update()
bpy.context.window.scene=sc; bpy.context.view_layer.update()
refroot=bpy.data.objects['chef_omar__ground_root.001'];refarm=bpy.data.objects['chef_omar__armature.001']
refcoll=bpy.data.collections['S33_CHARACTER_chef_omar.001']
def body(o):return o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name
new=[]
for o in list(coll.all_objects):
 if body(o):bpy.data.objects.remove(o,do_unlink=True)
for src in list(refcoll.all_objects):
 if body(src):
  o=src.copy();o.data=src.data.copy();o.name='S11 cucumber '+src.name
  coll.objects.link(o);o.parent=root;o.matrix_parent_inverse=Matrix.Identity(4)
  for mod in o.modifiers:
   if mod.type=='ARMATURE':mod.object=arm
  new.append(o)
for suffix in ['knife_handle','knife_blade']:
 orig=next(o for o in coll.all_objects if '__'+suffix in o.name)
 src=next(o for o in refcoll.all_objects if '__'+suffix in o.name)
 orig.data=src.data.copy()
# Original native camera registration, matching common refined scene treatment at runtimeScale2.
sc.name='Omar cucumber warm soft round01';sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100
for prop in ['engine','film_transparent','filter_size','use_compositing','use_sequencer','dither_intensity','pixel_aspect_x','pixel_aspect_y']:
 setattr(sc.render,prop,getattr(refscene.render,prop))
for prop in ['samples','use_denoising','use_adaptive_sampling','adaptive_threshold','max_bounces','transparent_max_bounces','pixel_filter_type','device']:
 setattr(sc.cycles,prop,getattr(refscene.cycles,prop))
for prop in ['view_transform','look','exposure','gamma']:setattr(sc.view_settings,prop,getattr(refscene.view_settings,prop))
sc.world=refscene.world
for o in list(sc.objects):
 if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
for src in refscene.objects:
 if src.type=='LIGHT':
  o=src.copy();o.data=src.data.copy();sc.collection.objects.link(o)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=30;sc.render.fps=12
sc.camera.data.sensor_fit=refscene.camera.data.sensor_fit;sc.camera.data.ortho_scale=refscene.camera.data.ortho_scale
sc.camera.data.shift_x=refscene.camera.data.shift_x;sc.camera.data.shift_y=refscene.camera.data.shift_y
expected_camera=json.loads((P/'recipe-round01.json').read_text())['camera']['worldMatrix']
assert max(abs(sc.camera.matrix_world[i][j]-expected_camera[i][j]) for i in range(4) for j in range(4))<1e-6, [camera_source,expected_camera]
native.apply_clip(asset,rig,'hold-cucumber',1,'S',sc);bpy.context.view_layer.update()
plane=next(o for o in coll.all_objects if '__image_plane' in o.name)
image=next(n.image for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
assert image.packed_file
dep=P/'dependencies/dish-cucumber.png';dep.write_bytes(image.packed_file.data);image.filepath='//dependencies/dish-cucumber.png'
assert hashlib.sha256(dep.read_bytes()).hexdigest()=='dd6d82508f72b2d9019f1619e5f1fe878a5ad22935ab8c86d7a79b4434f64776'
root['refinement_round']=1;root['refinement_catalog_actor']='round-01.blend exact rest mesh/material transfer'
ids={sc}|{bpy.data.actions[n] for n in actions}
bpy.data.libraries.write(str(P/'runtime-round-01.blend'),ids,fake_user=True,compress=True)
def meshhash(o):
 return hashlib.sha256(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'materials':[m.name for m in o.data.materials]},separators=(',',':')).encode()).hexdigest()
parity={o.name:{'catalogMeshSHA256':meshhash(bpy.data.objects[o.name.removeprefix('S11 cucumber ')]),'runtimeMeshSHA256':meshhash(o)} for o in new}
recipe={'asset':'chef-omar','round':1,'scene':sc.name,'collection':coll.name,'root':root.name,'armature':arm.name,'originalRuntimeProject':'inputs/runtime-variants/chef-cucumber.blend','originalRuntimeSHA256':'03e3331c7138d36b5277b55c3ab56775181a55271d682e0fc544c62cfaf368ac','catalogSource':'source/round-01.blend','catalogSourceSHA256':hashlib.sha256((P/'round-01.blend').read_bytes()).hexdigest(),'sourceCamera':camera_source,'camera':json.loads((P/'recipe-round01.json').read_text())['camera'],'renderer':json.loads((P/'recipe-round01.json').read_text())['renderer'],'originalActionSHA256':action_hashes,'actorMeshMaterialParity':parity,'packedCucumberSHA256':hashlib.sha256(dep.read_bytes()).hexdigest(),'notes':['Preserved original runtime root/armature/rest, native hold/load actions/visibility/food plane mesh/UV/drivers','Replaced body rest meshes with exact catalog refined actor data; armature modifiers point to original runtime rig','Original camera matrix and logical registration preserved; common native384x640 capture','Supplemental clips never enter catalog atlas map']}
assert all(v['catalogMeshSHA256']==v['runtimeMeshSHA256'] for v in parity.values())
(P/'runtime-recipe-round01.json').write_text(json.dumps(recipe,indent=2));print('RUNTIME BUILT',len(new),flush=True)
