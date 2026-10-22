import bpy,json,hashlib,pathlib,math,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BASE=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');OBJ=BASE/'prototypes/sushi-loop/assets/refinement/objects/dock-cover';OUT=OBJ/'reviews/preparation-v1';MOD=OUT/'capture-code';RECORDS=OUT/'source-records'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,str(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
actions=load('family_actions',MOD/'native_actions.py');runtime=load('family_runtime',MOD/'capture_runtime.py');sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
assets={};rigs={}
for aid in ['dock-cover','dock-floor','dock-entry','workshop-hut','submarine-yellow']:
 r=json.loads((RECORDS/aid/'rig.json').read_text());a=json.loads((RECORDS/aid/'asset.json').read_text());root=bpy.data.objects[r['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));a.update(root=root,collection=col);assets[aid]=a;rigs[aid]=r
selected={a['collection'] for a in assets.values()}
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection not in selected
for c in sc.collection.children:c.hide_render=c not in selected;c.hide_viewport=c not in selected
runtime.scene=lambda:sc;runtime.SCENE_NAME=sc.name
camera=runtime.configure_camera('top-down-oblique-square-grid',(736,704),(368,480),2)
sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.image_settings.compression=15;sc.render.use_persistent_data=True
roots={'dock-cover':(0,0,.23),'dock-floor':(0,0,0),'dock-entry':(0,-1.5,0),'workshop-hut':(.78,.35,.23),'submarine-yellow':(-.7,-.42,.23)}
def pose(clip,index,d,subclip='dock-ready',subframe=None):
 ang={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
 for aid,a in assets.items():
  c=clip if aid=='dock-cover' else subclip if aid=='submarine-yellow' else 'static';f=index+1 if aid in ['dock-cover','submarine-yellow'] else 1
  actions.apply_clip(a,rigs[aid],c,f,d,sc)
  x,y,z=roots[aid];a['root'].location=(math.cos(ang)*x-math.sin(ang)*y,math.sin(ang)*x+math.cos(ang)*y,z)
 if subframe is not None:sc.frame_set(math.floor(subframe),subframe=subframe%1)
 sc.view_layers[0].update()
def tree(aid):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];tris=[];names=[];bounds={}
 for o in assets[aid]['collection'].all_objects:
  if o.type!='MESH' or o.hide_render or not o.visible_camera:continue
  eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();p=[eo.matrix_world@v.co for v in me.vertices];k=len(vs);vs+=p
  bounds[o.name]=[[min(q[i] for q in p) for i in range(3)],[max(q[i] for q in p) for i in range(3)]]
  for t in me.loop_triangles:tris.append(tuple(k+i for i in t.vertices));names.append(o.name)
  eo.to_mesh_clear()
 return {'bvh':BVHTree.FromPolygons(vs,tris,all_triangles=True),'names':names,'bounds':bounds,'boundsAll':[[min(p[i] for p in vs) for i in range(3)],[max(p[i] for p in vs) for i in range(3)]],'triangleCount':len(tris)}
audit={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'context':'Source-only diagnostic, no candidate or family approval','worldRootsSourceFacingS':roots,'camera':camera,'phases':[],'inbetweens':[],'support':{},'nativeContexts':[]}
for clip in ['covered','uncover']:
 for d in ['N','E','S','W']:
  for i in range(12):
   pose(clip,i,d);ts={a:tree(a) for a in assets};c=ts['dock-cover'];rec={'clip':clip,'direction':d,'index':i,'worldBounds':{a:t['boundsAll'] for a,t in ts.items()},'visibleMeshCounts':{a:len(t['bounds']) for a,t in ts.items()},'intersections':{}}
   for other in ['workshop-hut','submarine-yellow','dock-floor','dock-entry']:
    pairs=c['bvh'].overlap(ts[other]['bvh']);partpairs=sorted(set((c['names'][x],ts[other]['names'][y]) for x,y in pairs));rec['intersections'][other]={'trianglePairs':len(pairs),'objectPairs':partpairs}
   audit['phases'].append(rec)
   if i in [0,5,11]:
    p=OUT/'native-family'/f'{clip}-{d}-{i:02d}.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=sc.name);audit['nativeContexts'].append({'clip':clip,'direction':d,'index':i,'path':str(p.relative_to(OBJ/'reviews')),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  if d=='S':
   for f in [1.5,3.5,6.5,9.5,11.5,12.5,13]:
    pose(clip,0,d,subframe=f);ts={a:tree(a) for a in assets};c=ts['dock-cover'];rec={'clip':clip,'frame':f,'direction':d,'intersections':{}}
    for other in ['workshop-hut','submarine-yellow']:
     pairs=c['bvh'].overlap(ts[other]['bvh']);rec['intersections'][other]={'trianglePairs':len(pairs),'objectPairs':sorted(set((c['names'][x],ts[other]['names'][y]) for x,y in pairs))}
    audit['inbetweens'].append(rec)
pose('covered',0,'S');ts={a:tree(a) for a in assets};deck=ts['dock-floor']['bvh'];cover=ts['dock-cover']['bvh']
for n,b in ts['dock-cover']['bounds'].items():
 if 'corner_tie_rope' not in n:continue
 xy=[sum([b[0][i],b[1][i]])/2 for i in [0,1]];hit=deck.ray_cast(Vector((xy[0],xy[1],2)),Vector((0,0,-1)))
 audit['support'][n]={'bounds':b,'sampleXY':xy,'deckRayHit':list(hit[0]) if hit[0] else None,'verticalGap':b[0][2]-hit[0].z if hit[0] else None}
audit['roofRays']=[]
for xy in [(1.03,.54),(1.03,.44),(1.03,.64),(.78,.35)]:
 row={'xy':xy}
 for aid in ['dock-cover','workshop-hut','submarine-yellow']:
  h=ts[aid]['bvh'].ray_cast(Vector((*xy,4)),Vector((0,0,-1)));row[aid]=list(h[0]) if h[0] else None
 audit['roofRays'].append(row)
# Native static root/geometry captures above are correct evaluated matrices, unlike hidden stale raw matrices.
audit['visibleObjectBoundsS']= {a:t['bounds'] for a,t in ts.items()}
(OUT/'family-phase-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('DONE FAMILY PHASE AUDIT')
