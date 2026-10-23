import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib,importlib.util,math
from pathlib import Path
from mathutils import Vector
B=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets');O=B/'refinement/objects/garbage-shelving';out=O/'reviews/source-audit';src=Path(__file__).resolve().parent/'resources'
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=mod('gs_contacts_actions',src/'native_actions.py');root=bpy.data.objects['garbage-shelving__root'];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];col=next(c for c in sc.collection.children if root in list(c.all_objects))
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=lc.collection!=col
for c in sc.collection.children:c.hide_viewport=c!=col;c.hide_render=c!=col
r=json.loads((O/'inputs/source-rig.json').read_text());a={'collection':col,'root':root}
n.apply_clip(a,r,'idle',1,'S',sc);d=bpy.context.evaluated_depsgraph_get();contacts=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(d);m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices];zmin=min(v.z for v in vs);low=[list(v) for v in vs if v.z<=zmin+.005];ground=[list(v) for v in vs if v.z<=.04]
 contacts.append({'object':o.name,'minimumZ':zmin,'lowestVerticesWithin005':low,'verticesBelow004':ground,'objectOrigin':list(o.location),'roleInference':'four main support foot' if 'upright' in o.name else 'fallen detached board' if 'fallen_board' in o.name else 'loose ground debris' if 'debris' in o.name else 'shelf content' if 'stored_box' in o.name else 'above-ground structural member'})
 e.to_mesh_clear()
materials={s.material for o in col.all_objects if o.type=='MESH' for s in o.material_slots if s.material};materialstates=[]
for clip,config in r['clips'].items():
 for i in range(config['frames']):
  n.apply_clip(a,r,clip,i+1,'S',sc);ms=[]
  for m in sorted(materials,key=lambda m:m.name):
   nodes=[]
   for node in m.node_tree.nodes:
    vals=[]
    for kind in ['inputs','outputs']:
     for j,s in enumerate(getattr(node,kind)):
      if not hasattr(s,'default_value'):continue
      v=s.default_value
      if isinstance(v,(str,float,int,bool)):pass
      else:
       try:v=list(v)
       except:continue
      vals.append([kind,j,s.name,v])
    nodes.append({'name':node.name,'type':node.type,'values':vals})
   ms.append({'name':m.name,'nodes':nodes,'materialAction':m.animation_data.action.name if m.animation_data and m.animation_data.action else None,'nodeAction':m.node_tree.animation_data.action.name if m.node_tree.animation_data and m.node_tree.animation_data.action else None,'nodeDrivers':len(m.node_tree.animation_data.drivers) if m.node_tree.animation_data else 0})
  txt=json.dumps(ms,sort_keys=True);materialstates.append({'clip':clip,'frame0':i,'shaderNumericSHA256':hashlib.sha256(txt.encode()).hexdigest(),'materials':ms if i==0 else None})
external=[]
for o in col.all_objects:
 if o.parent and o.parent not in list(col.all_objects):external.append(['parent',o.name,o.parent.name])
 for m in o.modifiers:
  t=getattr(m,'object',None)
  if t and t not in list(col.all_objects):external.append(['modifier',o.name,t.name])
 for c in o.constraints:
  t=getattr(c,'target',None)
  if t and t not in list(col.all_objects):external.append(['constraint',o.name,t.name])
paths=['native_actions.py','capture_runtime.py','catalog_style.py','catalog_faceted.py','catalog_art_revision.py','prop_builders.py']
result={'groundRoot':{'name':root.name,'parent':root.parent.name if root.parent else None,'location':list(root.location),'scale':list(root.scale),'rotationIdleS':[0,0,0]},'physicalContactSamplesIdleS':contacts,'declaredSupportMask':[[0,0],[1,0],[0,1],[1,1]],'coordinateMapping':'Catalog rootCell[1,1]; occupied/support cell union x[-1,1],y[-1,1], x is X, depth is -Y. Semantic support is mask; native positive-Z contact gap recorded rather than silently changing root.','materialStates':materialstates,'shaderNumericUniqueHashes':len(set(x['shaderNumericSHA256'] for x in materialstates)),'foreignObjectDependencies':external,'moduleHashes':{p:hashlib.sha256((src/p).read_bytes()).hexdigest() for p in paths},'hasArmature':any(o.type=='ARMATURE' for o in col.all_objects),'notes':['Contact vertices use evaluated modifier mesh, never inferred from alpha silhouette.','Material values hashed over25Sphase evaluations; no material or node-tree actions or drivers. Other directions reuse the same materials.','Source has no declared ports/sockets, no armature and no UV/image dependency. Shape/mesh counts are descriptive evidence only.']}
(out/'contacts-shaders-resources.json').write_text(json.dumps(result,indent=2)+'\n')
print('CONTACT_AUDIT_DONE',len(contacts),result['shaderNumericUniqueHashes'])
