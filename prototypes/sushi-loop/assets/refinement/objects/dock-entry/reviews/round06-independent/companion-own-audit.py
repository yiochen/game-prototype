import bpy,json,math,hashlib,importlib.util,re
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_ray_tri
O=Path(__file__).resolve().parent;B=O/'resources/repo/prototypes/sushi-loop/assets/refinement/objects/dock-entry';R=B/'source/resources/approved-human-v3';A=R/'customer-rosa-approved.blend';L=B/'source/resources/original-library.blend';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):H(p) for p in [A,L]};bpy.ops.wm.open_mainfile(filepath=str(A));rig=json.loads((R/'customer-rosa-approved-rig.json').read_text());hr=bpy.data.objects[rig['groundRootObject']];hc=next(c for c in bpy.data.collections if hr in list(c.all_objects));sc=bpy.context.scene;hc.hide_viewport=False;hc.hide_render=False
for o in hc.all_objects:o.hide_viewport=False;o.hide_set(False)
sp=importlib.util.spec_from_file_location('retained_native_actions_companion',R/'independent-floor-audit/native_actions.py');mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
with bpy.data.libraries.load(str(L),link=False) as(a,b):b.collections=['S33_PROP_workshop-hut.001','S33_PROP_submarine_base.001'];b.actions=[n for n in a.actions if 'submarine-yellow' in n]
hut=bpy.data.collections['S33_PROP_workshop-hut.001'];sub=bpy.data.collections['S33_PROP_submarine_base.001']
for c in [hut,sub]:
 sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
def root(c):return next(o for o in c.objects if o.type=='EMPTY' and o.parent is None)
root(hut).location=(.78,.35,.23);root(hut).rotation_euler=(0,0,0);root(sub).location=(-.7,-.42,.23);root(sub).rotation_euler=(0,0,0)
def lookup(data,name):return data.get(name) or data.get(name+'.001') or next((o for o in data if re.sub(r'\.\d+$','',o.name)==re.sub(r'\.\d+$','',name)),None)
sr=json.loads((B/'source/resources/frozen-neighbors/submarine-yellow-rig.json').read_text())
for o in sub.all_objects:
 if o.animation_data:
  o.animation_data.action=None
  for t in o.animation_data.nla_tracks:t.mute=True
for t in sr['clips']['dock-ready']['actions']:
 owner=lookup(bpy.data.objects,t['ownerName']) if t['ownerType']=='Object' else lookup(bpy.data.shape_keys,t['ownerName']) if t['ownerType']=='Key' else lookup(bpy.data.materials,t['materialOwnerName']).node_tree
 act=lookup(bpy.data.actions,t['action']);owner.animation_data_create();owner.animation_data.action=act;slots=list(act.slots);slot=next((s for s in slots if s.identifier==t.get('slotIdentifier')),slots[0] if len(slots)==1 else None)
 if slot:owner.animation_data.action_slot=slot
sc.frame_set(12);bpy.context.view_layer.update()
for o in sub.all_objects:
 if o.animation_data:o.animation_data.action=None

def geom(c):
 vs=[];fs=[];owners=[];objects=[]
 for o in c.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[ev.matrix_world@p.co for p in me.vertices];me.calc_loop_triangles();f=[list(t.vertices) for t in me.loop_triangles];off=len(vs);vs+=v;fs += [[off+i for i in tri] for tri in f];owners += [o.name]*len(f);objects.append({'name':o.name,'matrixWorld':[list(r) for r in ev.matrix_world],'verticesWorld':[list(p) for p in v],'triangles':f});ev.to_mesh_clear()
 return vs,fs,owners,objects,BVHTree.FromPolygons(vs,fs,all_triangles=True)
ng={name:geom(c) for name,c in [('workshop-hut',hut),('submarine-yellow',sub)]}
def segment_triangle(p,q,tri):
 vec=q-p
 if vec.length<1e-10:return None
 hit=intersect_ray_tri(tri[0],tri[1],tri[2],vec,p,True)
 if hit is None:return None
 t=(hit-p).dot(vec)/vec.length_squared
 return list(hit) if -1e-7<=t<=1+1e-7 else None
path=[(0,-2.1,0),(0,-1.9,.0733333333),(0,-1.75,.1466666667),(0,-1.55,.22),(0,-1.5,.22),(0,-1.3,.22),(.15,-.65,.22),(0,.12,.22),(.78,-.18,.22)];records=[]
for idx,pos in enumerate(path):
 mod.apply_clip({'root':hr,'collection':hc},rig,'walk',idx+1,'S',sc);hr.location=pos;hr.rotation_euler=(0,0,0);bpy.context.view_layer.update();vs,fs,owners,objs,tree=geom(hc);matches=[]
 for name,(nv,nf,no,nobjs,nt) in ng.items():
  candidates=tree.overlap(nt);hits=[];pairs=set();byobj={}
  for ai,bi in candidates:
   tri=[vs[v] for v in fs[ai]];other=[nv[v] for v in nf[bi]];points=[]
   for v,tar in [(tri,other),(other,tri)]:
    for p,q in zip(v,v[1:]+v[:1]):
     h=segment_triangle(p,q,tar)
     if h is not None:points.append(h)
   if points:
    pairs.add((ai,bi));byobj[no[bi]]=byobj.get(no[bi],0)+1
    if len(hits)<30:hits.append({'actorObject':owners[ai],'actorTriangle':ai,'neighborObject':no[bi],'neighborTriangle':bi,'pointsWorld':points})
  matches.append({'neighbor':name,'bvhTriangleCandidates':len(candidates),'confirmedCrossingTrianglePairs':len(pairs),'neighborObjectsCrossed':byobj,'exampleIntersections':hits})
 records.append({'pathIndex':idx,'sourceFrame':idx+1,'rootPosition':pos,'rootMatrix':[list(r) for r in hr.matrix_world],'rootScale':list(hr.scale),'neighborIntersections':matches})
r={'candidatePacketSHA256':'1e1eddc38ea103f5be030b49b870b0f48d8dcd22d304af083f51b243efdf65fc','sourceHashes':before,'nativeSourcesUnchanged':before=={str(p):H(p) for p in [A,L]},'method':'Exact current approved authored-scale1.25 actor walk meshes, all visible body triangles, exact b176 frozen hut and dock-ready submarine at unchanged authored roots. BVH candidate triangle pairs then independently confirmed by both triangle-edge/triangle intersection tests with segment bounds. No AABB-only collision assertion. CanonicalS physical audit is invariant under the required common rigid N/E/W assembly rotation. Source companion support/canopy defects remain separately scoped. This checks CURRENT presentation route and does not propose an actor or building geometry change.','neighborGeometry':{name:g[3] for name,g in ng.items()},'records':records};(O/'own-companion-route-audit.json').write_text(json.dumps(r,indent=2)+'\n');print('OWN_ROUTE',[(x['pathIndex'],[(n['neighbor'],n['confirmedCrossingTrianglePairs']) for n in x['neighborIntersections']]) for x in records])
