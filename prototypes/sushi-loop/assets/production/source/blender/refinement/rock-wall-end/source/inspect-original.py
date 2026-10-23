import bpy,json,hashlib
from mathutils import Vector
p='/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=p)
print('COLLECTIONS',[(c.name,len(c.objects)) for c in bpy.data.collections if 'rock' in c.name.lower()])
for c in bpy.data.collections:
 if 'rock' in c.name.lower() and 'end' in c.name.lower():
  out={'source':p,'collection':c.name,'objects':[]}
  for o in c.all_objects:
   rec={'name':o.name,'type':o.type,'loc':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)}
   if o.type=='MESH':
    vs=[o.matrix_world@v.co for v in o.data.vertices]
    rec.update(vertices=len(vs),faces=len(o.data.polygons),bounds=[[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)],materials=[m.name for m in o.data.materials])
   out['objects'].append(rec)
  path='/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/rock-wall-end/source/independent-native-inspection.json'
  open(path,'w').write(json.dumps(out,indent=2))
  print(json.dumps(out))
