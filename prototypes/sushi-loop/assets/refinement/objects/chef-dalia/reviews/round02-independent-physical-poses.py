import bpy,json,pathlib,hashlib,importlib.util,struct
from mathutils import Vector
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-dalia');r=b/'reviews'
record=json.loads((b/'inputs/source-rig.json').read_text());spec=importlib.util.spec_from_file_location('dalia_judge_physical',b/'source/native_actions_round01.py');na=importlib.util.module_from_spec(spec);spec.loader.exec_module(na)
sources={'source':b/'source/round-02-food/dependencies/approved-body.blend','candidate':b/'source/round-02.blend'};result={}
for kind,path in sources.items():
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;root=bpy.data.objects[record['groundRootObject']];col=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects));arm=bpy.data.objects[record['armatures'][0]['object']]
 def en(l):
  if l.collection==col:l.exclude=False;l.hide_viewport=False
  for ch in l.children:en(ch)
 en(bpy.context.view_layer.layer_collection);col.hide_viewport=False
 for ob in col.all_objects:ob.hide_viewport=False;ob.hide_set(False)
 obs=sorted([ob for ob in col.all_objects if ob.type=='MESH' and '__held_dish-salmon__image_plane' not in ob.name],key=lambda ob:ob.name);assert len(obs)==95;frames=[]
 for clip in ['idle','work','hold','load']:
  for di in ['N','E','S','W']:
   for fi in range(12):
    na.apply_clip({'root':root,'collection':col,'armature':arm},record,clip,fi+1,di,sc);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();h=hashlib.sha256();bounds=[[float('inf'),-float('inf')] for k in range(3)];vertexCount=0;shoeMin=[]
    for ob in obs:
     eo=ob.evaluated_get(dg);me=eo.to_mesh();h.update(ob.name.encode());h.update(struct.pack('<I',len(me.vertices)));vertexCount+=len(me.vertices)
     for v in me.vertices:
      w=eo.matrix_world@v.co;h.update(struct.pack('<3d',*w))
      for k in range(3):bounds[k][0]=min(bounds[k][0],w[k]);bounds[k][1]=max(bounds[k][1],w[k])
      if 'shoe' in ob.name.lower():shoeMin.append(w.z)
     eo.to_mesh_clear()
    frames.append({'clip':clip,'direction':di,'index':fi,'evaluatedPhysicalWorldVertexSHA256':h.hexdigest(),'vertexCount':vertexCount,'physicalBoundsWorld':bounds,'minimumShoeZ':min(shoeMin) if shoeMin else None})
 result[kind]={'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'meshCount':len(obs),'frames':frames}
 print(kind,'physical audit complete',len(frames),flush=True)
result['all192PoseHashesEqual']=all(a['evaluatedPhysicalWorldVertexSHA256']==c['evaluatedPhysicalWorldVertexSHA256'] for a,c in zip(result['source']['frames'],result['candidate']['frames']));result['all192BoundsEqual']=all(a['physicalBoundsWorld']==c['physicalBoundsWorld'] for a,c in zip(result['source']['frames'],result['candidate']['frames']));result['method']='Independent fresh-process evaluation using original native action module,95 physical body/knife meshes, evaluated world vertex float64 hashes excluding honest food quad; no native saves.'
(r/'round02-independent-physical-poses.json').write_text(json.dumps(result,indent=2)+'\n');print('ALL192 PHYSICAL EQUAL',result['all192PoseHashesEqual'])
