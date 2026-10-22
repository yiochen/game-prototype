"""Portable fresh native replay and frozen-renderer canonical-v2 diagnostics."""
import bpy,sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[args.index('--output')+1]).resolve() if '--output' in args else P.parent/'candidates/round-02/replay'
out.mkdir(parents=True,exist_ok=True);rows=[];output_settings={}
for runtime in [False,True]:
 c=config(runtime);rec=json.loads((P/('runtime-recipe-round02.json' if runtime else 'recipe-round02.json')).read_text())
 hold='hold-cucumber' if runtime else 'hold';load='load-cucumber' if runtime else 'load'
 for mode,project in [('candidate',c['candidate']),('canonical-v2',c['canonicalBaseline']),('approved-old-food',c['basis'])]:
  bpy.ops.wm.open_mainfile(filepath=str(P/project));sc,coll,root,arm,rig,asset,plane=setup(c);enable_saved_device(sc)
  image=image_node(plane).image
  output_settings[c['variant']+'-'+mode]={k:getattr(sc.render.image_settings,k) for k in ['file_format','color_mode','color_depth','compression']}
  assert image.packed_file,'Portable sources must contain packed food pixels'
  if mode=='candidate':assert sha(P/project)==rec['candidateSHA256']
  samples=[(cl,d,i) for cl in [hold,load] for d in ['N','E','S','W'] for i in [0,11]]
  if mode=='candidate' and not runtime:samples += [('work','S',5),('idle','S',0)]
  for clip,d,idx in samples:
   native.apply_clip(asset,rig,clip,idx+1,d,sc);q=quad_state(sc,plane)
   path=out/mode/c['variant']/(f'{clip}-{d}-{idx:03d}.png');path.parent.mkdir(parents=True,exist_ok=True)
   if mode!='approved-old-food':sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   rows.append({'mode':mode,'food':c['variant'],'clip':clip,'direction':d,'index':idx,'path':str(path.relative_to(out)) if mode!='approved-old-food' else None,'sha256':sha(path) if mode!='approved-old-food' else None,'projectSHA256':sha(P/project),'quadNativePixels':q['projected'].tolist(),'bottomNativePixel':q['bottomPixel'].tolist(),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'scene':sc.name,'camera':sc.camera.name,'imagePackedSHA256':hashlib.sha256(image.packed_file.data).hexdigest(),'libraries':[l.filepath for l in bpy.data.libraries]})
   write(out/'replay-manifest.json',rows)
  if mode=='candidate':
   for a in [-135,-90.1,90.1,135]:
    native.apply_clip(asset,rig,hold,6,'S',sc);root.rotation_euler.z=math.radians(a);root.update_tag();bpy.context.view_layer.update()
    path=out/'candidate'/c['variant']/(f'turn-{a:+07.2f}.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    rows.append({'mode':'candidate-intermediate','food':c['variant'],'clip':hold,'index':5,'angleDegrees':a,'path':str(path.relative_to(out)),'sha256':sha(path),'projectSHA256':sha(P/project),'resolution':[sc.render.resolution_x,sc.render.resolution_y],'scene':sc.name,'camera':sc.camera.name})
    write(out/'replay-manifest.json',rows)
outputs_equal=all(output_settings[f+'-candidate']==output_settings[f+'-canonical-v2']==output_settings[f+'-approved-old-food'] for f in ['salmon','cucumber'])
write(out/'closure.json',{'ok':all(not r.get('libraries') for r in rows) and outputs_equal,'sourceDirectoryName':P.name,'candidateProjects':{n:sha(P/n) for n in ['round-02.blend','runtime-round-02.blend']},'canonicalInputs':{n:sha(P/'round-02-resources'/n) for n in ['dish-salmon.png','dish-cucumber.png']},'freshCandidateRenders':sum(r['mode'].startswith('candidate') for r in rows),'canonicalV2Renders':sum(r['mode']=='canonical-v2' for r in rows),'bodyAndRendererEdits':False,'outputSettingsExactlyEqual':outputs_equal,'outputSettings':output_settings,'portableSourceFiles':{p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in str(p)},'reconstruction':'Run build_food_round02.py in this source directory; both bases/canonical inputs/native action code/rig/configuration are local and hash-bound. Run replay_food_round02.py -- --output <directory> in clean background Blender.'})
print('PORTABLE REPLAY COMPLETE',len(rows),flush=True)
