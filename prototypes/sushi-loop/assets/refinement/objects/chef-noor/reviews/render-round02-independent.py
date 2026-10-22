import bpy,json,sys,hashlib
from pathlib import Path
b=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-noor')
sys.path.insert(0,str(b/'source'));import native_actions_round02 as NA
rig=json.loads((b/'source/rig-round02.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=root.users_collection[0];arm=bpy.data.objects[rig['clips']['idle']['actions'][0]['ownerName']];asset={'root':root,'collection':coll,'armature':arm};s=bpy.context.scene
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='METAL';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='METAL'
except Exception:pass
report={'sourceProjectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'engine':s.render.engine,'device':s.cycles.device,'samples':s.cycles.samples,'seed':s.cycles.seed,'denoising':s.cycles.use_denoising,'renders':[],'noProjectSave':True}
for clip,d,i in [('hold','N',0),('load','E',5)]:
 NA.apply_clip(asset,rig,clip,i+1,d,s);p=b/'reviews'/f'round02-fresh-independent-{clip}-{d}-{i:03d}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);report['renders'].append({'clip':clip,'direction':d,'index':i,'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(b/'reviews/round02-fresh-independent-render.json').write_text(json.dumps(report,indent=2)+'\n')
