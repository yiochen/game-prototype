"""In-memory cohort-ID diagnostic: exact geometry/actions/camera; never saved into source."""
import sys
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent
exec(compile((H/'context_setup.py').read_text(),str(H/'context_setup.py'),'exec'))
D=OUT/'depth-identity';D.mkdir(exist_ok=True);actor=actorSnapshots['exterior-stop']
for c in actorSnapshots.values():c.hide_render=True
actor.hide_render=False
palette={'cover':(1,0,1),'floor':(1,1,0),'entry':(0,1,1),'hut':(0,1,0),'sub':(0,0,1),'human':(1,0,0)}
for aid,c in [('cover',cover),('floor',fc),('entry',ec),('hut',hc),('sub',subc),('human',actor)]:
 m=bpy.data.materials.new('DIAGNOSTIC cohort '+aid);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*palette[aid],1);e.inputs['Strength'].default_value=1;o=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],o.inputs['Surface'])
 for ob in c.all_objects:
  if ob.type=='MESH':
   for i in range(len(ob.data.materials)):ob.data.materials[i]=m
sc.view_settings.exposure=0;sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0
records=[]
for case in plan['cases']:
 for c in actorSnapshots.values():c.hide_render=True
 actor=actorSnapshots[case['id']];actor.hide_render=False
 humanMat=bpy.data.materials['DIAGNOSTIC cohort human']
 for ob in actor.all_objects:
  if ob.type=='MESH':
   for i in range(len(ob.data.materials)):ob.data.materials[i]=humanMat
 for d in ['N','E','S','W']:
  R=Matrix.Rotation(dirs[d],4,'Z')
  for ob in actor.objects:
   a=ob['original_world_matrix'];ob.matrix_world=R@Matrix([a[i:i+4]for i in range(0,16,4)])
  for clip,i in [('covered',0),('uncover',5),('uncover',11)]:
   subpose('upgraded-dock-ready');coverpose(clip,i+1,d);p=D/'human'/f'{case["id"]}-{clip}-{d}-{i:02d}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'case':case['id'],'clip':clip,'direction':d,'index':i,'path':str(p.relative_to(O)),'sha256':sha(p)})
(D/'human-records.json').write_text(json.dumps(records,indent=2)+'\n');print('COMPLETE HUMAN DEPTH STUDY',len(records))
