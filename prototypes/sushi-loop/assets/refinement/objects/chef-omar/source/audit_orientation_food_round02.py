"""Verify expression input against actual semantic forward/camera horizontal vectors."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
for runtime in [False,True]:
 c=config(runtime);rec=json.loads((P/('runtime-recipe-round02.json' if runtime else 'recipe-round02.json')).read_text());bpy.ops.wm.open_mainfile(filepath=str(P/c['candidate']));sc,coll,root,arm,rig,asset,plane=setup(c)
 out=(P/c['candidateFolder']).resolve();rows=[]
 def sample(phase):
  forward=root.matrix_world.to_3x3()@Vector((0,-1,0));forward.z=0;forward.normalize();horizontal=ray(sc);horizontal.z=0;horizontal.normalize();f=forward.dot(horizontal);expression=math.cos(root.rotation_euler.z)
  rows.append({**phase,'rootDegrees':math.degrees(root.rotation_euler.z),'actualForward':list(forward),'actualCameraHorizontal':list(horizontal),'actualDot':f,'expressionCosYaw':expression,'difference':abs(f-expression),'rootHasParent':root.parent is not None,'rootScale':list(root.scale)})
 for clip in rig['clips']:
  for d in ['N','E','S','W']:
   for i in range(12):native.apply_clip(asset,rig,clip,i+1,d,sc);sample({'clip':clip,'direction':d,'index':i})
 angles=[-180,-135,-45,0,45,135,180]+[s*(90+d) for s in [-1,1] for d in [-.1,-.02,-.015,-.0146,-.0145,-.014,-.01,-.001,0,.001,.01,.014,.0145,.0146,.015,.02,.1]]
 for angle in angles:
  native.apply_clip(asset,rig,'hold-cucumber' if runtime else 'hold',6,'S',sc);root.rotation_euler.z=math.radians(angle);root.update_tag();bpy.context.view_layer.update();sample({'angleDegrees':angle})
 maximum=max(r['difference'] for r in rows);write(out/'semantic-orientation-validation.json',{'ok':maximum<1e-6 and not any(r['rootHasParent'] for r in rows),'candidateSHA256':sha(P/c['candidate']),'maxDotVsExpressionDifference':maximum,'samples':rows,'lawSharedDMinWorld':c['dMinWorld'],'definition':'Actual normalized semantic ground-forward(0,-1,0) transformed by root, dotted with actual saved camera ground-horizontal direction. Expression cos(rootYaw) agrees at native float precision; no discrete facing/action/head tilt input.'})
 print('ORIENTATION',c['variant'],maximum,flush=True)
