import bpy,pathlib,json,hashlib,importlib.util
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-dalia');out=b/'reviews/round02-food-evidence';rec=json.loads((b/'inputs/source-rig.json').read_text());root=bpy.data.objects[rec['groundRootObject']];col=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects));arm=bpy.data.objects[rec['armatures'][0]['object']]
def en(l):
 if l.collection==col:l.exclude=False;l.hide_viewport=False
 for c in l.children:en(c)
en(bpy.context.view_layer.layer_collection);col.hide_viewport=False
for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
spec=importlib.util.spec_from_file_location('dalia_control_original_native',b/'source/native_actions_round01.py');na=importlib.util.module_from_spec(spec);spec.loader.exec_module(na);sc=bpy.context.scene;na.apply_clip({'root':root,'collection':col,'armature':arm},rec,'hold',1,'S',sc)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices();devices=[]
for d in prefs.devices:
 d.use=d.type=='METAL';devices.append({'name':d.name,'type':d.type,'use':d.use})
assert any(d['type']=='METAL' and d['use'] for d in devices)
sc.cycles.device='GPU'
result={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'clip':'hold','direction':'S','index':0,'purpose':'Independent fresh-process actual round02 packed dependency render, no source modifications or save.','devices':devices,'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'useAnimatedSeed':sc.cycles.use_animated_seed,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'denoise':sc.cycles.use_denoising,'renderFiles':[]}
result['images']=[{'name':im.name,'filepath':im.filepath,'resolvedPath':bpy.path.abspath(im.filepath),'resolvedPathExists':pathlib.Path(bpy.path.abspath(im.filepath)).is_file(),'size':list(im.size),'packed':bool(im.packed_file),'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.name not in ['Render Result','Viewer Node']]
for i in range(1):
 p=out/f'fresh-process-candidate-hold-S-000-{i+1}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);result['renderFiles'].append({'path':str(p.relative_to(b)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(b/'reviews/round02-independent-reopen-control-record.json').write_text(json.dumps(result,indent=2)+'\n');print('FRESH CANDIDATE PACKED CONTROL COMPLETE')
