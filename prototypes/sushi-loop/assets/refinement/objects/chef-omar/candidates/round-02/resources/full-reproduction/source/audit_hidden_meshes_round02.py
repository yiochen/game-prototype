"""Fresh-process numeric parity for every viewport-culled non-food mesh."""
import bpy,sys,json,subprocess
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
from semantic_food_round02 import evaluated,compact_geometry,rigid_geometry_from_evaluated_parent
if '--mode' not in sys.argv:
 for runtime in [False,True]:
  c=config(runtime)
  for mode,project in [('source',c['basis']),('candidate',c['candidate'])]:
   args=[bpy.app.binary_path,'-b',str(P/project),'-t','2','--python',str(Path(__file__).resolve()),'--','--mode',mode]
   if runtime:args.append('--runtime')
   subprocess.run(args,check=True)
 sys.exit(0)
runtime='--runtime' in sys.argv;c=config(runtime);mode=sys.argv[sys.argv.index('--mode')+1];out=(P/c['candidateFolder']).resolve();sc,coll,root,arm,rig,asset,plane=setup(c);records=[];arrays={};visible_checks=[];tmp=out/'hidden-mesh-temporary-baseline.npz'
reference=np.load(tmp) if mode=='candidate' else None
for clip in rig['clips']:
 for direction in ['N','E','S','W']:
  for index in range(12):
   native.apply_clip(asset,rig,clip,index+1,direction,sc);gs={}
   for obj in coll.all_objects:
    if obj.type!='MESH' or '__knife_' not in obj.name:continue
    flags=(obj.hide_render,obj.hide_viewport,obj.hide_get())
    actual,matrix=rigid_geometry_from_evaluated_parent(obj,bpy.context.evaluated_depsgraph_get());gs[obj.name]=actual
    if not (obj.hide_viewport or obj.hide_get()):
     rr,mm=compact_geometry({obj.name:actual},{obj.name:evaluated(obj,bpy.context.evaluated_depsgraph_get())})
     visible_checks.append({'clip':clip,'direction':direction,'index':index,'mesh':obj.name,'maxima':mm})
    assert (obj.hide_render,obj.hide_viewport,obj.hide_get())==flags
   key=f'{clip}|{direction}|{index}|'
   if mode=='source':
    for name,aa in gs.items():
     for j,a in enumerate(aa):arrays[key+name+'|'+str(j)]=a
   else:
    baseline={name:tuple(reference[key+name+'|'+str(j)] for j in range(3)) for name in gs};rows,maxima=compact_geometry(gs,baseline);records.append({'clip':clip,'direction':direction,'index':index,'meshes':rows,'maxima':maxima,'nativeRenderVisibilityPreserved':True,'viewportFlagsUnchanged':True,'method':'rigid local mesh and native basis under actual evaluated utensil parent; no culled evaluated mesh identity matrices used'})
if mode=='source':
 np.savez_compressed(tmp,**arrays);print('HIDDEN BASELINE',c['variant'],len(arrays),flush=True)
else:
 ok=all(all(v==0 for v in r['maxima']) for r in records) and all(max(r['maxima'])<1e-6 for r in visible_checks);write(out/'hidden-mesh-evaluation-validation.json',{'ok':ok,'sourceSHA256':sha(P/c['basis']),'candidateSHA256':sha(P/c['candidate']),'method':'Two isolated fresh Blender processes. Fixed rigid knife meshes have no modifiers, constraints or shape keys. Their world vertices/normals are reconstructed using the actual evaluated non-culled utensil parent, native parent inverse and local basis; this is explicitly not a claim that viewport-culled evaluated_get returned actual geometry. Reconstruction is cross-checked against actual evaluated visible knife geometry on all work poses. No visibility/controller/project/render mutation. Temporary binary comparison arrays are deleted after comparison.','visibleKnifeReconstructionCrosschecks':visible_checks,'frames':records})
 current=json.loads((out/'native-frames.json').read_text());bykey={(r['clip'],r['direction'],r['index']):r for r in records}
 for r in current:
  r['meshParity'].update(bykey[(r['clip'],r['direction'],r['index'])]['meshes']);r['rigidKnifeGeometryMethod']='actual evaluated utensil parent × unchanged native parentInverse × native localBasis; no visibility change'
 write(out/'native-frames.json',current);v=json.loads((out/'validation.json').read_text());v['hiddenMeshNumericAudit']='hidden-mesh-evaluation-validation.json';v['ok']=v['ok'] and ok;write(out/'validation.json',v);reference.close();tmp.unlink();print('HIDDEN MESH PARITY',c['variant'],ok,sum(len(r['meshes']) for r in records),flush=True)
