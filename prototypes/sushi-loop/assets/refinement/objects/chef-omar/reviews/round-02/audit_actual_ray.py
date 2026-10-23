import sys
sys.dont_write_bytecode=True
import bpy,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parent;S=R.parents[1]/'candidates/round-02/portable-replay/source';sys.path.insert(0,str(S));from food_common_round02 import *
result={}
for runtime in [False,True]:
 c=config(runtime);sets=[]
 for cand in [False,True]:
  bpy.ops.wm.open_mainfile(filepath=str(S/c['candidate' if cand else 'basis']));sc,coll,root,arm,rig,asset,plane=setup(c);rv=ray(sc);rr=[]
  for cl in rig['clips']:
   for d in ['N','E','S','W']:
    for i in range(12):
     native.apply_clip(asset,rig,cl,i+1,d,sc);flags=(plane.hide_viewport,plane.hide_get());plane.hide_viewport=False;plane.hide_set(False);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();e=plane.evaluated_get(dg);m=e.matrix_world;par=plane.parent.evaluated_get(dg).matrix_world@plane.matrix_parent_inverse;off=m.translation-par.translation
     rr.append({'origin':list(m.translation),'ray':list(rv),'depth':off.dot(rv),'offPerp':(off-rv*off.dot(rv)).length,'f':math.cos(root.rotation_euler.z)});plane.hide_viewport=flags[0];plane.hide_set(flags[1]);bpy.context.view_layer.update()
  sets.append(rr)
 mx=0
 for a,b in zip(*sets):
  delta=Vector(b['origin'])-Vector(a['origin']);rv=Vector(b['ray']);mx=max(mx,(delta-rv*delta.dot(rv)).length)
 result[c['variant']]={'frames':len(sets[1]),'actualSavedCameraRay':sets[1][0]['ray'],'maxSourceCandidateDisplacementPerpendicularWorld':mx,'maxCandidateOffsetPerpendicularWorld':max(r['offPerp'] for r in sets[1]),'sourceDepthRange':[min(r['depth'] for r in sets[0]),max(r['depth'] for r in sets[0])],'candidateDepthRange':[min(r['depth'] for r in sets[1]),max(r['depth'] for r in sets[1])]}
 write(R/'actual-ray-audit.json',result)
print(json.dumps(result),flush=True)
