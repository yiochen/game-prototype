import bpy,json,hashlib,sys,math
sys.dont_write_bytecode=True
from pathlib import Path
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-car');O=P/'reviews/round-01-independent';sc=bpy.context.scene;baseline=json.loads((O/'native-candidate-audit.json').read_text());sourceLights=baseline['lights'];rows=[];groups=[];errors=[]
roots=[bpy.data.objects[n] for n in ['garbage-car__root','garbage-car__root.001','garbage-car__root.002']]
def err(a,b):return max(abs(x-y) for x,y in zip(np.array(a).ravel(),np.array(b).ravel()))
for root,expected in zip(roots,[[1.5,-1,0],[5.5,-1,0],[1.5,-4,0]]):
 if err(list(root.location),expected)>1e-6:errors.append('root placement '+root.name)
 coll=root.users_collection[0];lights=[x for x in sc.objects if x.type=='LIGHT' and x.light_linking.receiver_collection==coll]
 if len(lights)!=5:errors.append('expected five receiving lights '+root.name)
 meshrows=[]
 for obj in coll.all_objects:
  if obj.type=='MESH':
   meshrows.append({'role':obj.name,'localMatrix': [list(r) for r in root.matrix_world.inverted()@obj.matrix_world],'meshSHA256':hashlib.sha256(np.array([list(v.co) for v in obj.data.vertices],dtype=np.float64).tobytes()).hexdigest(),'materials':[m.name for m in obj.data.materials]})
 group=[]
 for obj in lights:
  relative=root.matrix_world.inverted()@obj.matrix_world
  row={'root':root.name,'receiver':coll.name,'name':obj.name,'type':obj.data.type,'energy':obj.data.energy,'color':list(obj.data.color),'size':obj.data.size,'shape':obj.data.shape,'shadow':obj.data.use_shadow,'relativeMatrix':[list(r) for r in relative],'locationRelativeToRoot':[relative[i][3] for i in range(3)],'receiverMembers':sorted(x.name for x in coll.all_objects)}
  matches=[x for x in sourceLights if err([x['matrix'][i][3] for i in range(3)],row['locationRelativeToRoot'])<1e-6]
  if len(matches)!=1:errors.append('source local light position mismatch '+obj.name)
  else:
   source=matches[0];row['sourceLight']=source['name'];row['sourceMatrixMaxError']=err(source['matrix'],row['relativeMatrix'])
   if row['sourceMatrixMaxError']>1e-6:errors.append('relative matrix '+obj.name)
   for key in ['type','energy','color','size','shape','shadow']:
    if source[key]!=row[key]:errors.append('light setting '+key+' '+obj.name)
  # Read receiver link states where exposed; defaults must include entire own collection.
  row['directCollectionMembers']=sorted(x.name for x in coll.objects)
  rows.append(row);group.append(obj)
 groups.append({'root':root.name,'meshRows':sorted(meshrows,key=lambda x:x['role']),'lights':[x.name for x in group]})
for obj in sc.objects:
 if obj.type=='LIGHT' and obj.light_linking.receiver_collection not in [r.users_collection[0] for r in roots]:errors.append('unlinked or foreign additive light '+obj.name)
for group in groups[1:]:
 if len(group['meshRows'])!=len(groups[0]['meshRows']):errors.append('instance meshcount')
 # Blender copy renames numeric suffixes in authored coordinates (e.g.0.45)
 # rather than preserving a parseable basename. Match actual mesh bytes,
 # material identity and root-relative transform one-to-one instead.
 remaining=list(groups[0]['meshRows'])
 for b in group['meshRows']:
  matches=[(err(a['localMatrix'],b['localMatrix']),a) for a in remaining if a['meshSHA256']==b['meshSHA256'] and a['materials']==b['materials']]
  if not matches:errors.append('nonidentical instance geometry '+b['role']);continue
  delta,a=min(matches,key=lambda x:x[0]);b['matchedOriginal']=a['role'];b['matrixError']=delta
  if delta>1e-6:errors.append('nonidentical instance transform '+b['role'])
  remaining.remove(a)
def px(v):
 p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
record={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'isolatedProjectSHA256':baseline['projectSHA256'],'errors':errors,'roots':[{'name':r.name,'matrix':[list(x) for x in r.matrix_world],'projectedRoot':px(r.location)} for r in roots],'lights':rows,'groups':groups,'camera':{'frame':[sc.render.resolution_x,sc.render.resolution_y],'matrix':[list(x) for x in sc.camera.matrix_world],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'lightingInterpretation':'Three translated copies of identical asset-local five-light rig, receiver-linked to each independent car. Initial unlinked distance-falloff diagnostic is retained separately; this is not one global position-independent light field.'}
(O/'native-context-independent-audit.json').write_text(json.dumps(record,indent=2)+'\n');print('CONTEXT AUDIT',len(rows),'errors',errors,flush=True)
if '--audit-only' in sys.argv:sys.exit(0)
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
for d in prefs.devices:d.use=d.type=='METAL'
sc.render.filepath=str(O/'independent-native-repeated.png');bpy.ops.render.render(write_still=True)
for obj in sc.objects:
 if obj.type=='LIGHT' and obj.light_linking.receiver_collection!=roots[0].users_collection[0]:obj.hide_render=True
sc.render.filepath=str(O/'independent-native-only-first-rig.png');bpy.ops.render.render(write_still=True)
print('CONTEXT RENDERS COMPLETE',flush=True)
