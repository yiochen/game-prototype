import bpy,json,pathlib,importlib.util,hashlib,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir');R=P/'reviews/round-01-evidence';ROOT=P.parents[2]/'production/source/blender'
spec=importlib.util.spec_from_file_location('samir_judge_native',ROOT/'native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
inputs={'main-source':P/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','main-candidate':P/'source/round-01/samir-main.blend','runtime-source':P/'inputs/runtime-variants/starter-meals-project.blend','runtime-candidate':P/'source/round-01/samir-runtime.blend'}
probes={'left-foot':('minimal_foot_L','foot_L',(-.115,-.02,0)),'right-foot':('minimal_foot_R','foot_R',(.115,-.02,0)),'seat':('pelvis','pelvis',(0,.006,.070000008)),'left-palm':('palm_L','hand_L',(-.267,-.025,.216999993)),'right-palm':('palm_R','hand_R',(.267,-.025,.216999993)),'left-thumb':('thumb_L','hand_L',(-.229,-.081,.183)),'right-thumb':('thumb_R','hand_R',(.229,-.081,.183)),'mouth':('smile','head',(0,-.256999999,.537799984))}
results={}
def val(v):
 if isinstance(v,(str,bool,int,float)):return v
 try:return [val(x) for x in v]
 except:return str(v)
def sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def graph(t):
 if not t:return None
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[(s.identifier,val(s.default_value)) for s in n.inputs if hasattr(s,'default_value')],'outputs':[(s.identifier,val(s.default_value)) for s in n.outputs if hasattr(s,'default_value')],'operation':getattr(n,'operation',None),'blend':getattr(n,'blend_type',None),'space':getattr(n,'space',None),'nested':graph(n.node_tree) if n.type=='GROUP' else None} for n in t.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in t.links]}
for tag,file in inputs.items():
 bpy.ops.wm.open_mainfile(filepath=str(file.resolve()));mode=tag.split('-')[0];rig=json.loads((P/('inputs/source-rig.json' if mode=='main' else 'inputs/runtime-variants/export/source/customer-samir/rig.json')).read_text());root=bpy.data.objects[rig['groundRootObject']];collection=next(c for c in bpy.data.collections if root in list(c.all_objects));scene=next(s for s in bpy.data.scenes if root in list(s.objects));bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
 for c in scene.collection.children:c.hide_viewport=c!=collection;c.hide_render=c!=collection
 def visit(l):
  l.exclude=False;l.hide_viewport=False
  for q in l.children:visit(q)
 for layer in scene.view_layers:visit(layer.layer_collection)
 collection.hide_viewport=False;arm=next(o for o in collection.all_objects if o.type=='ARMATURE');asset={'root':root,'collection':collection}
 parts={o.name.split('customer_samir__')[1].split('.')[0]:o for o in collection.all_objects if o.type=='MESH' and 'customer_samir__' in o.name};body=[o for o in collection.all_objects if o.type=='MESH' and o.get('weighted_character_geometry')]
 materials={m.name.replace('S10 meal ',''):graph(m.node_tree) for o in body for m in o.data.materials if m}
 lights=[{'type':o.data.type,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':getattr(o.data,'size',None),'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT' and not o.hide_render]
 samples=[]
 for clip in rig['clips']:
  for dr in ['S','E','N','W']:
   for frame in range(1,13):
    native.apply_clip(asset,rig,clip,frame,dr,scene);dg=bpy.context.evaluated_depsgraph_get();points={}
    for label,(part,bone,point) in probes.items():
     target=arm.matrix_world@arm.pose.bones[bone].matrix@arm.data.bones[bone].matrix_local.inverted()@Vector(point)
     e=parts[part].evaluated_get(dg);mesh=e.to_mesh();verts=[e.matrix_world@v.co for v in mesh.vertices];faces=[tuple(p.vertices) for p in mesh.polygons];hit=BVHTree.FromPolygons(verts,faces).find_nearest(target);e.to_mesh_clear();points[label]={'target':list(target),'nearestActualSurface':list(hit[0]),'distance':hit[3]}
    samples.append({'clip':clip,'direction':dr,'frame':frame,'points':points})
 result={'projectSHA256':hashlib.sha256(file.read_bytes()).hexdigest(),'samples':samples,'materialGraphSHA256':sha(materials),'materialGraphs':materials,'lights':lights,'scope':'Eight declared source functional surface probes queried against actual modifier-evaluated native corresponding anatomical meshes, not merely bone locations. Full body geometry shape remains free.'};results[tag]=result;(R/(tag+'-surfaces-materials.json')).write_text(json.dumps(result,indent=2)+'\n');print('AUDIT',tag,len(samples),'material',result['materialGraphSHA256'],flush=True)
summary={}
for mode in ['main','runtime']:
 a,b=results[mode+'-source'],results[mode+'-candidate'];errs={k:0 for k in probes}
 for x,y in zip(a['samples'],b['samples']):
  for k in probes:errs[k]=max(errs[k],(Vector(x['points'][k]['nearestActualSurface'])-Vector(y['points'][k]['nearestActualSurface'])).length)
 summary[mode]={'maxSourceToCandidateActualSurfacePointDeviationWorldCells':errs,'samples':len(a['samples']),'toleranceWorldCells':.005}
summary['matchingNativeMainRuntimeMaterialGraphs']=results['main-candidate']['materialGraphSHA256']==results['runtime-candidate']['materialGraphSHA256']
(R/'surfaces-materials-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('SUMMARY',summary,flush=True)
