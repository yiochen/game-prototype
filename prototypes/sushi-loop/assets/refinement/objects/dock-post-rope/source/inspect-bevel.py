import bpy
p='/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=p)
o=bpy.data.objects['dock-post-rope__thick_sag_rope_0']
for m in o.modifiers:
 print([(k,getattr(m,k)) for k in ['name','type','width','segments','affect','limit_method','angle_limit','harden_normals','miter_outer','miter_inner','profile']])
