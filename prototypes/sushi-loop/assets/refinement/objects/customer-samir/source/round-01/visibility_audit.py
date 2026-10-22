import bpy,json,sys,hashlib,importlib.util
from pathlib import Path
D=Path(__file__).resolve().parent;P=D.parent.parent;MODE=next(x for x in sys.argv if x in ['main','runtime']);TAG='candidate' if '--candidate' in sys.argv else 'source'
rig=json.loads((D/'resources'/('source-'+MODE+'-rig.json')).read_text());root=bpy.data.objects[rig['groundRootObject']];c=next(c for c in bpy.data.collections if root in list(c.all_objects));s=next(s for s in bpy.data.scenes if root in list(s.objects));bpy.context.window.scene=s;bpy.context.window.view_layer=s.view_layers[0]
for x in s.collection.children:x.hide_viewport=x!=c;x.hide_render=x!=c
c.hide_viewport=False;c.hide_render=False
for layer in s.view_layers:
 def expose(x):
  x.exclude=False;x.hide_viewport=False
  for y in x.children:expose(y)
 expose(layer.layer_collection)
spec=importlib.util.spec_from_file_location('samir_native',D/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
owners={}
for info in rig['clips'].values():
 for t in info['actions']:
  if t['ownerType']=='Object' and any(f.data_path in ['hide_render','hide_viewport'] for f in native._fcurves(bpy.data.actions[t['action']])):owners[t['ownerName']]=bpy.data.objects[t['ownerName']]
def key(o):return o.name.split('customer_samir__',1)[-1]
weights={}
for o in c.all_objects:
 if o.type=='MESH' and o.get('weighted_character_geometry'):
  part=key(o).split('.')[0];sums=[sum(g.weight for g in v.groups) for v in o.data.vertices];used=sorted({o.vertex_groups[g.group].name for v in o.data.vertices for g in v.groups if g.weight>0})
  weights[part]={'vertexCount':len(o.data.vertices),'usedDeformationGroups':used,'minimumWeightSum':min(sums),'maximumWeightSum':max(sums),'unweightedVertices':sum(x==0 for x in sums),'weightDigest':hashlib.sha256(json.dumps([[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in o.data.vertices]).encode()).hexdigest()}
  if part.startswith(('palm_','thumb_','minimal_foot_')):assert 'head' not in used,(part,used)
rows=[]
for clip in rig['clips']:
 for direction in ['S','E','N','W']:
  for frame in range(1,13):
   native.apply_clip({'root':root,'collection':c},rig,clip,frame,direction,s);rows.append({'clip':clip,'direction':direction,'frame':frame,'visibility':{key(o):{'hideRender':bool(o.hide_render),'hideViewport':bool(o.hide_viewport)} for o in owners.values()}})
out={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'mode':MODE,'tag':TAG,'ownerCount':len(owners),'samples':rows,'actualNativeDeformationWeights':weights}
(P/'candidates/round-01'/('visibility-'+MODE+'-'+TAG+'.json')).write_text(json.dumps(out,indent=2)+'\n');print(MODE,TAG,len(rows),len(owners))
