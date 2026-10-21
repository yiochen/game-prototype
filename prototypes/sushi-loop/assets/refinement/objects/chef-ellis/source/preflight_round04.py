import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-04';REP=OUT/'representatives';REP.mkdir(exist_ok=True);sys.path.insert(0,str(P));import native_actions_round04 as native
from audit_common_round04 import geometry,contacts
sc=bpy.data.scenes['Ellis warm soft round04'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];arm=bpy.data.objects['chef_ellis__armature.001'];asset={'collection':coll,'root':root,'armature':arm};rig=json.loads((P/'rig-round04.json').read_text());reference={(r['clip'],r['direction'],r['index']):r for r in json.loads((P/'source-contacts-round04.json').read_text())}
assert not coll.hide_viewport and not coll.hide_render
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=False;lc.hide_viewport=False
for o in coll.all_objects:o.hide_set(False)
rows=[];maxbone=maxpalm=maxprop=0
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,clip,f,d,sc);dg=bpy.context.evaluated_depsgraph_get();ct=contacts(coll,root,arm,dg);ref=reference[(clip,d,f-1)]
   maxbone=max(maxbone,max(abs(ct['bones'][n]['matrix'][i][j]-ref['bones'][n]['matrix'][i][j]) for n in ct['bones'] for i in range(4) for j in range(4)));maxprop=max(maxprop,max(abs(ct['props'][n]['matrix'][i][j]-ref['props'][n]['matrix'][i][j]) for n in ct['props'] for i in range(4) for j in range(4)));maxpalm=max(maxpalm,max((Vector(ct['palms'][s])-Vector(ref['palms'][s])).length for s in ['L','R']))
   gs={o.name:geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name};bounds=[[min(g['bounds'][i][0] for g in gs.values()),max(g['bounds'][i][1] for g in gs.values())] for i in range(3)];rows.append({'clip':clip,'direction':d,'index':f-1,'bodyBounds':bounds})
bounds=[[min(r['bodyBounds'][i][0] for r in rows),max(r['bodyBounds'][i][1] for r in rows)] for i in range(3)]
assert max(abs(x) for dim in bounds[:2] for x in dim)<.500001,bounds
assert maxbone==0 and maxprop==0 and maxpalm<1e-6
materials={}
for o in coll.all_objects:
 if o.type=='MESH':materials[o.name]=[m.name for m in o.data.materials]
handle=bpy.data.objects['chef_ellis__ground_root.001__knife_handle'];blade=bpy.data.objects['chef_ellis__ground_root.001__knife_blade'];assert 'wood' in handle.data.materials[0].name and 'metal' in blade.data.materials[0].name
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception:pass
reps=[]
for clip,f in [('work',4),('hold',6),('load',6),('load',12)]:
 for d in ['N','E','S','W']:
  native.apply_clip(asset,rig,clip,f,d,sc);path=REP/(clip+'-'+d+'-'+str(f)+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);reps.append({'clip':clip,'direction':d,'sourceFrame':f,'path':str(path.relative_to(BASE))})
report={'ok':True,'samples':rows,'physicalEnvelope':bounds,'all192WithinOneCell':True,'boneMatrixMaxError':maxbone,'attachmentMatrixMaxError':maxprop,'palmCentroidMaxError':maxpalm,'knifeMaterials':{'handle':handle.data.materials[0].name,'blade':blade.data.materials[0].name},'allMaterialAssignments':materials,'representativeRenders':reps,'status':'Technical preflight passed; representative visual inspection required before fullcapture'};(OUT/'preflight.json').write_text(json.dumps(report,indent=2));print('PREFLIGHT_DONE',json.dumps({k:report[k] for k in ['physicalEnvelope','boneMatrixMaxError','attachmentMatrixMaxError','palmCentroidMaxError','knifeMaterials']}),flush=True)
