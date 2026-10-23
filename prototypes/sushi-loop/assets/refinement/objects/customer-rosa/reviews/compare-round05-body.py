import sys
sys.dont_write_bytecode=True
import bpy,pathlib,json,hashlib
O=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-rosa');R=O/'reviews';records={}
for kind,filename,prefix in [('main','round-05.blend',''),('runtime','round-05-runtime.blend','S10 meal ')]:
 bpy.ops.wm.open_mainfile(filepath=str(O/'source'/filename));root=bpy.data.objects[prefix+'customer_rosa__ground_root.001'];col=root.users_collection[0];rows=[]
 for o in col.all_objects:
  if o.type!='MESH' or o.name.endswith('__image_plane') or '__knife_' in o.name:continue
  shape={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons],'vertexGroups':[[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in o.data.vertices],'objectMatrix':[list(r) for r in o.matrix_local]}
  rows.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'sha256':hashlib.sha256(json.dumps(shape,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
 records[kind]=rows
records['geometryTransformsWeightsIdentical']=sorted(r['sha256'] for r in records['main'])==sorted(r['sha256'] for r in records['runtime']);(R/'round05-independent-main-runtime-body.json').write_text(json.dumps(records,indent=2)+'\n');print('Independent current main/runtime body geometry+transforms+weights identical',records['geometryTransformsWeightsIdentical'],'meshes',len(records['main']),len(records['runtime']))
