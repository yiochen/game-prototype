"""Exact native stationary-structure depth against all nine unchanged authored human stances."""
import sys
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
text=(H/'depth_identity.py').read_text();exec(compile(text[:text.index('records=[]')],str(H/'depth_identity.py'),'exec'))
D=OUT/'support-depth';D.mkdir(exist_ok=True);cloth.hide_render=True
for q in fixtures.values():q['collection'].hide_render=True
for c in actorSnapshots.values():c.hide_render=True
records=[]
for d in ['N','E','S','W']:
 coverpose('covered',1,d);p=D/f'structure-alone-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'kind':'structure-alone','direction':d,'path':str(p.relative_to(O)),'sha256':sha(p),'actualRootMatrix':[list(r)for r in cr.matrix_world]})
for case in plan['cases']:
 for c in actorSnapshots.values():c.hide_render=True
 actor=actorSnapshots[case['id']];actor.hide_render=False;humanMat=bpy.data.materials['DIAGNOSTIC cohort human']
 for ob in actor.all_objects:
  if ob.type=='MESH':
   for i in range(len(ob.data.materials)):ob.data.materials[i]=humanMat
 for d in ['N','E','S','W']:
  R=Matrix.Rotation(dirs[d],4,'Z')
  for ob in actor.objects:
   a=ob['original_world_matrix'];ob.matrix_world=R@Matrix([a[i:i+4]for i in range(0,16,4)])
  coverpose('covered',1,d);gg=g.geometry(actor);p=D/f'{case["id"]}-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'kind':'structure-and-human','case':case['id'],'direction':d,'path':str(p.relative_to(O)),'sha256':sha(p),'actualRootMatrix':[list(r)for r in cr.matrix_world],'actualActorMaximumWorldZ':max(v.z for row in gg for v in row['vertices'])})
(D/'records.json').write_text(json.dumps({'coverSourceSHA256':sha(H/'cover.blend'),'method':'Memory-only native cohort-ID emission. Moving cloth hidden only for this strict stationary-structure study. All supports/frame/braces remain native unchanged. Exact approved Rosa poses/scale/material visibility and root locations are preserved; no source saved.','records':records},indent=2)+'\n');print('COMPLETE STATIONARY STRUCTURE STUDY',len(records))
