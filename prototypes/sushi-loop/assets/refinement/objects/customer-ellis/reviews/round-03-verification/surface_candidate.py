import bpy,json,sys,importlib.util,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;OBJ=P.parents[1];MODE=sys.argv[sys.argv.index('--')+1];record=json.loads((OBJ/('inputs/source-rig.json' if MODE=='main' else 'inputs/runtime-variants/export/source/customer-ellis/rig.json')).read_text());root=bpy.data.objects[record['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];collection=next(c for c in sc.collection.children if root.name in c.all_objects)
for c in sc.collection.children:c.hide_viewport=c!=collection;c.hide_render=c!=collection
collection.hide_viewport=False;collection.hide_render=False
def show(layer):
 layer.exclude=False;layer.hide_viewport=False
 for c in layer.children:show(c)
show(sc.view_layers[0].layer_collection)
spec=importlib.util.spec_from_file_location('judge_surface_native',OBJ.parents[2]/'production/source/blender/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);asset={'root':root,'collection':collection}
source=json.loads((P.parent/(MODE+'-audit.json')).read_text());lookup={(s['clip'],s['direction'],s['frame']):s for s in source['samples']};rest={b['name']:Matrix(b['matrix']) for b in source['armature']['rest']};witnesses=json.loads((P/'original-surface-witnesses.json').read_text());out={'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'method':'Independently derived original rest-mesh extreme face centers, transported with original saved native pose matrices. Distance to actual evaluated remodeled mesh BVH in every pose. Includes pelvis underside, palms/thumbs top, soles bottom, mouth skin carrier. AABB-bottom-center shortcut was rejected for tilted shoes.','witnesses':witnesses,'samples':[],'maxError':0,'failures':[],'groups':{}}
for w in witnesses:
 o=bpy.data.objects[('S10 meal ' if MODE=='runtime' else '')+w['suffix']];groups={g.name:[] for g in o.vertex_groups}
 for v in o.data.vertices:
  for g in v.groups:groups[o.vertex_groups[g.group].name].append(g.weight)
 out['groups'][o.name]={g:{'weightedVertices':len(v),'minWeight':min(v),'maxWeight':max(v)} for g,v in groups.items() if v}
for clip,c in record['clips'].items():
 for direction in ['S','E','N','W']:
  for frame in range(1,c['frames']+1):
   native.apply_clip(asset,record,clip,frame=frame,direction=direction,scene=sc);dg=bpy.context.evaluated_depsgraph_get();s=lookup[(clip,direction,frame)];rows=[]
   for w in witnesses:
    o=bpy.data.objects[('S10 meal ' if MODE=='runtime' else '')+w['suffix']];expected=Matrix(s['contacts'][w['bone']]['matrix'])@rest[w['bone']].inverted()@Vector(w['point']);e=o.evaluated_get(dg);mesh=e.to_mesh();tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in mesh.vertices],[list(f.vertices) for f in mesh.polygons]);hit=tree.find_nearest(expected);e.to_mesh_clear();row={'object':o.name,'kind':w['kind'],'sourceExpected':list(expected),'nearest':list(hit[0]),'distance':hit[3]};rows.append(row);out['maxError']=max(out['maxError'],hit[3])
    if hit[3]>.005:out['failures'].append({'clip':clip,'direction':direction,'frame':frame,**row})
   out['samples'].append({'clip':clip,'direction':direction,'frame':frame,'surfaces':rows})
(P/(MODE+'-surface-verification.json')).write_text(json.dumps(out,indent=2)+'\n');print(MODE,len(out['samples']),out['maxError'],len(out['failures']))
