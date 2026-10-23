import sys
sys.dont_write_bytecode=True
import bpy,json,importlib.util
from pathlib import Path
P=Path(__file__).resolve().parent
exec(compile((P/'inspect-source.py').read_text(),str(P/'inspect-source.py'),'exec'))
arm=bpy.data.objects['creature-eel__armature.003'];body=bpy.data.objects['creature-eel__continuous_body.003'];rig=json.loads((P/'resources/inputs/source-rig.json').read_text())
spec=importlib.util.spec_from_file_location('probe_native',str(P/'resources/blender/native_actions.py'));N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
a={'collection':col,'root':root};out={'posePosition':arm.data.pose_position,'poseRotationModes':{b.name:b.rotation_mode for b in arm.pose.bones},'constraints':{b.name:[c.type for c in b.constraints] for b in arm.pose.bones},'bodyModifier':{x:getattr(body.modifiers[0],x) for x in ['use_vertex_groups','use_bone_envelopes','use_deform_preserve_volume','show_render','show_viewport']},'samples':[]}
for pose_position in ['REST','POSE']:
 arm.data.pose_position=pose_position
 for fr in [1,4,7]:
  N.apply_clip(a,rig,'swim',fr,'S',sc);dg=bpy.context.evaluated_depsgraph_get();e=body.evaluated_get(dg);me=e.to_mesh();pp=[e.matrix_world@v.co for v in me.vertices];out['samples'].append({'mode':pose_position,'frame':fr,'bounds':[[min(v[k] for v in pp) for k in range(3)],[max(v[k] for v in pp) for k in range(3)]],'boneEuler':list(arm.pose.bones['spine_6'].rotation_euler),'evalBoneMatrix':[list(r) for r in arm.evaluated_get(dg).pose.bones['spine_6'].matrix],'boneMatrix':[list(r) for r in arm.pose.bones['spine_6'].matrix]});e.to_mesh_clear()
(P/'deformation-probe.json').write_text(json.dumps(out,indent=2)+'\n');print(out)
