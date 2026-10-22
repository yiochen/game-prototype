import bpy,sys,json,hashlib,numpy as np
from pathlib import Path
b=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-noor');sys.path.insert(0,str(b/'source'));import native_actions_round01 as NA
rig=json.loads((b/'source/rig-round01.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=root.users_collection[0];arm=bpy.data.objects[rig['clips']['idle']['actions'][0]['ownerName']];asset={'root':root,'collection':coll,'armature':arm};scene=bpy.context.scene
source=json.loads((b/'candidates/round-02/source-phases.json').read_text());lookup={(x['clip'],x['direction'],x['index']):x for x in source};report={'sourceProjectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'phaseCount':0,'physicalMeshComparisons':0,'mismatches':[],'method':'Fresh actual approved source evaluated coordinate/normal arrays independently compared to bound source phase records; all non-food physical meshes, food quad excluded.'}
def arr(xs,k,w):
 a=np.empty(len(xs)*w,dtype=np.float32);xs.foreach_get(k,a);return a.reshape(-1,w)
def h(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   NA.apply_clip(asset,rig,clip,i+1,d,scene);dg=bpy.context.evaluated_depsgraph_get();ref=lookup[(clip,d,i)];report['phaseCount']+=1
   for name,old in ref['physicalMeshes'].items():
    obj=bpy.data.objects[name];ev=obj.evaluated_get(dg);me=ev.to_mesh();co=arr(me.vertices,'co',3);vn=arr(me.vertices,'normal',3);cn=arr(me.corner_normals,'vector',3);pn=arr(me.polygons,'normal',3);matrix=np.array(ev.matrix_world,dtype=np.float64);world=co@matrix[:3,:3].T+matrix[:3,3];nm=np.linalg.inv(matrix[:3,:3]).T;wn=vn@nm.T;wn=wn/np.maximum(np.linalg.norm(wn,axis=1)[:,None],1e-30)
    actual={'localCoordinates':h(co),'worldCoordinates':h(world),'vertexNormals':h(vn),'worldVertexNormals':h(wn),'cornerNormals':h(cn),'polygonNormals':h(pn)};report['physicalMeshComparisons']+=1
    bad=[k for k in actual if actual[k]!=old[k]]
    if bad:report['mismatches'].append({'clip':clip,'direction':d,'index':i,'object':name,'fields':bad})
    ev.to_mesh_clear()
(b/'reviews/round02-independent-approved-source-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('PHASES',report['phaseCount'],'PHYSICAL_COMPARE',report['physicalMeshComparisons'],'MISMATCHES',len(report['mismatches']))
