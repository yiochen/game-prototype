"""Replay the saved candidate into a NEW output folder; never rewrite sealed evidence.

Run with the supplied host Python: reproduce.py --output /absolute/NEW_DIRECTORY
Optional --smoke exports two known native poses, without creating partial atlases.
"""
import sys,json,hashlib,argparse,math,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
worker='--blender-worker' in sys.argv
argv=sys.argv[sys.argv.index('--')+1:]if worker else sys.argv[1:]
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--smoke',action='store_true');p.add_argument('--blender-worker',action='store_true');a=p.parse_args(argv)
out=Path(a.output).resolve();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if worker:
 import bpy
 assert out.is_dir()
 bpy.ops.wm.open_mainfile(filepath=str(H/'cover.blend'));sc=bpy.context.scene
 root=bpy.data.objects['dock-cover__root'];keys=bpy.data.objects['dock-cover__attached_canvas_hems_and_stitches'].data.shape_keys
 rig=json.loads((H/'rig.json').read_text());samples=[('covered','S',0),('uncover','E',11)]if a.smoke else [(c,d,i)for c in ('covered','uncover')for d in 'NESW'for i in range(12)]
 records=[]
 for clip,d,index in samples:
  keys.animation_data.action=None
  for key in keys.key_blocks:key.value=0
  action=bpy.data.actions[rig['clips'][clip]['action']];keys.animation_data.action=action
  if action.slots:keys.animation_data.action_slot=action.slots[0]
  root.rotation_euler.z={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d]
  sc.frame_set(index+1);bpy.context.view_layer.update();f=out/'frames'/f'{clip}-{d}'/f'{index:03d}.png';f.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(f);bpy.ops.render.render(write_still=True)
  records.append({'clip':clip,'direction':d,'index':index,'path':str(f.relative_to(out)),'sha256':sha(f)})
 (out/'native-replay.json').write_text(json.dumps({'sourceProjectSHA256':sha(H/'cover.blend'),'blender':bpy.app.version_string,'smokeOnly':a.smoke,'records':records},indent=2)+'\n')
else:
 assert not out.exists(),'Choose a new directory; immutable capture output is never overwritten'
 out.mkdir(parents=True)
 cmd=['/opt/homebrew/bin/blender','-b','-t','2','--python',str(H/'reproduce.py'),'--','--blender-worker','--output',str(out)]
 if a.smoke:cmd.append('--smoke')
 subprocess.run(cmd,check=True)
 from PIL import Image
 r=json.loads((out/'native-replay.json').read_text());r['atlases']=[]
 for rec in r['records']:
  im=Image.open(out/rec['path']).convert('RGBA');rec['decodedRGBASHA256']=hashlib.sha256(im.tobytes()).hexdigest();assert im.size==(1472,1408)
 if not a.smoke:
  for c in ('covered','uncover'):
   for d in 'NESW':
    im=Image.new('RGBA',(7360,4224))
    for i in range(12):im.paste(Image.open(out/'frames'/f'{c}-{d}'/f'{i:03d}.png').convert('RGBA'),((i%5)*1472,(i//5)*1408))
    f=out/'atlases'/f'{c}-{d}.png';f.parent.mkdir(exist_ok=True);im.save(f,optimize=True);r['atlases'].append({'clip':c,'direction':d,'path':str(f.relative_to(out)),'sha256':sha(f),'columns':5,'rows':3,'size':[7360,4224],'rects':[[i%5*1472,i//5*1408,1472,1408]for i in range(12)],'fps':12,'loop':c=='covered','frameOrder':list(range(12))})
 (out/'reproduction-manifest.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({'output':str(out),'sourceProjectSHA256':r['sourceProjectSHA256'],'rawFrames':len(r['records']),'atlases':len(r['atlases']),'smokeOnly':a.smoke}))
