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
for clip in ['covered','uncover']:
 for d in ['N','E','S','W']:
  R=Matrix.Rotation(dirs[d],4,'Z')
  for ob in actor.objects:
   a=ob['original_world_matrix'];ob.matrix_world=R@Matrix([a[i:i+4]for i in range(0,16,4)])
  for i in range(12):
   coverpose(clip,i+1,d)
   for q in fixtures.values():q['collection'].hide_render=True
   actor.hide_render=True;p=D/'cover-alone'/f'{clip}-{d}-{i:02d}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
   records.append({'kind':'isolated-cover-ID','clip':clip,'direction':d,'index':i,'path':str(p.relative_to(O)),'sha256':sha(p),'actualRootMatrix':[list(r)for r in cr.matrix_world]})
   for q in fixtures.values():q['collection'].hide_render=False
   actor.hide_render=False
   for mode in ['dock-ready','dock-charging','upgraded-dock-ready','upgraded-dock-charging']:
    subpose(mode);coverpose(clip,i+1,d);p=D/'joint'/f'{mode}-{clip}-{d}-{i:02d}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'kind':'joint-native-ID','clip':clip,'direction':d,'index':i,'mode':mode,'path':str(p.relative_to(O)),'sha256':sha(p),'actualRootMatrix':[list(r)for r in cr.matrix_world],'visibleMainMeshes':sorted(o.name for o in subc.all_objects if o.type=='MESH'and not o.hide_render)})
  (D/'progress.json').write_text(json.dumps({'records':len(records)})+'\n')
(D/'records.json').write_text(json.dumps({'projectSHA256':sha(H/'cover.blend'),'mainSHA256':sourceHashes['sub'],'method':'Exact evaluated geometry/material visibility actions and unchanged camera. Diagnostic memory-only cohort emission substitutions and exposure0 identify depth. Standalone/candidate source materials unchanged. Compare opaque isolated-cover pixels to joint native front cohort, not mixed-projection consumer RGB.','palette':palette,'records':records},indent=2)+'\n');print('COMPLETE DEPTH IDENTITIES',len(records))
