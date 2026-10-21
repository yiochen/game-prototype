"""Independent judge reopen/pose audit; only writes under reviews/."""
import bpy,sys,pathlib,json,hashlib,importlib.util,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parent.parent;P=B.parents[2]/'production';C=B/'candidates/round-01';R=B/'reviews';H=P/'source/blender'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
native=module('judge_native_round01',H/'native_actions.py')

def data(project,rig):
 bpy.ops.wm.open_mainfile(filepath=str(project));root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in bpy.data.collections if root in list(c.objects))
 sc=bpy.data.scenes.new('Judge isolated Omar');sc.collection.children.link(coll);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];coll.hide_render=False;coll.hide_viewport=False;sc.view_layers[0].update();arm=next(o for o in coll.all_objects if o.type=='ARMATURE');asset={'root':root,'collection':coll}
 actions={}
 for clip in rig['clips'].values():
  for t in clip['actions']:
   a=bpy.data.actions[t['action']];actions[a.name]=hashlib.sha256(json.dumps([(c.data_path,c.array_index,[(list(k.co),k.interpolation) for k in c.keyframe_points]) for c in native._fcurves(a)],sort_keys=True).encode()).hexdigest()
 rest={b.name:[list(r) for r in b.matrix_local] for b in arm.data.bones}
 frames=[];topo={};bad=[]
 for clip in rig['clips']:
  for direction in ['N','E','S','W']:
   for i in range(12):
    native.apply_clip(asset,rig,clip,i+1,direction,sc)
    props=[o for o in coll.all_objects if '__held_' in o.name or '__knife_' in o.name or '__utensil' in o.name];vis={o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in props}
    for o in props:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
    sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get()
    ae=arm.evaluated_get(dg);bones={b.name:[list(r) for r in ae.matrix_world@b.matrix] for b in ae.pose.bones}
    palms={}
    for side in ['L','R']:
     obj=next(o for o in coll.all_objects if '__palm_'+side in o.name);ev=obj.evaluated_get(dg);palms[side]=list(sum((ev.matrix_world@v.co for v in ev.data.vertices),Vector())/len(ev.data.vertices))
    propsig={o.name:{'matrix':[list(r) for r in o.evaluated_get(dg).matrix_world],'visibility':vis[o.name]} for o in props}
    for o in coll.all_objects:
     if o.type=='MESH' and '__image_plane' not in o.name:
      e=o.evaluated_get(dg);m=e.to_mesh();counts=[len(m.vertices),len(m.edges),len(m.polygons)];e.to_mesh_clear()
      if o.name not in topo:topo[o.name]=counts
      elif topo[o.name]!=counts:bad.append([clip,direction,i,o.name,counts])
    feet={}
    for side in ['L','R']:
     obj=next(o for o in coll.all_objects if '__minimal_foot_'+side in o.name);ev=obj.evaluated_get(dg);vs=[ev.matrix_world@Vector(v) for v in ev.bound_box];feet[side]=[[min(v[j] for v in vs),max(v[j] for v in vs)] for j in range(3)]
    frames.append({'clip':clip,'direction':direction,'index':i,'bones':bones,'palms':palms,'props':propsig,'feet':feet,'rootMatrix':[list(r) for r in root.matrix_world],'rootRotationDegrees':math.degrees(root.rotation_euler.z)})
    for o in props:o.hide_render,o.hide_viewport,_=vis[o.name];o.hide_set(vis[o.name][2])
 plane=next(o for o in coll.all_objects if '__image_plane' in o.name);image=next(n.image for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
 food={'vertices':[list(v.co) for v in plane.data.vertices],'faces':[list(p.vertices) for p in plane.data.polygons],'uv':[list(v.uv) for v in plane.data.uv_layers.active.data],'packedSHA256':hashlib.sha256(image.packed_file.data).hexdigest() if image.packed_file else None}
 return {'source':str(project),'sha256':sha(project),'rest':rest,'actions':actions,'frames':frames,'topologyChanges':bad,'topologies':topo,'food':food,'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.type!='RENDER_RESULT'],'libraries':[l.filepath for l in bpy.data.libraries]}

def maxdiff(a,b):
 if isinstance(a,dict):return max(maxdiff(a[k],b[k]) for k in a)
 if isinstance(a,list):return max(maxdiff(x,y) for x,y in zip(a,b))
 return abs(a-b)
origRig=json.loads((B/'inputs/source-rig.json').read_text());variantRigPath=P/'source/variants/chef-cucumber/export/source/chef-omar/rig.json';variantRig=json.loads(variantRigPath.read_text());variantManifest=json.loads((B/'inputs/runtime-variants/original-runtime-manifest.json').read_text());expected=variantManifest['sourceFiles']['assets/production/source/variants/chef-cucumber/export/source/chef-omar/rig.json'];assert sha(variantRigPath)==expected
cases=[('catalog',B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',origRig,B/'source/round-01.blend',json.loads((C/'native-records/rig.json').read_text())),('runtimeVariants',B/'inputs/runtime-variants/chef-cucumber.blend',variantRig,B/'source/runtime-round-01.blend',json.loads((C/'runtimeVariants/native-records/rig.json').read_text()))]
results={}
for name,original,origrig,candidate,candrig in cases:
 a=data(original.resolve(),origrig);b=data(candidate.resolve(),candrig)
 rows=[]
 for orig,cand in zip(a['frames'],b['frames']):
  assert [orig[k] for k in ['clip','direction','index']]==[cand[k] for k in ['clip','direction','index']]
  rows.append({'clip':cand['clip'],'direction':cand['direction'],'index':cand['index'],'boneMatrixDifference':maxdiff(orig['bones'],cand['bones']),'palmCentroidDifference':maxdiff(orig['palms'],cand['palms']),'footBBoxDifference':maxdiff(orig['feet'],cand['feet']),'propsMatrixDifference':max(maxdiff(orig['props'][k]['matrix'],cand['props'][k]['matrix']) for k in orig['props']),'propsVisibilityEqual':all(orig['props'][k]['visibility']==cand['props'][k]['visibility'] for k in orig['props']),'rootMatrixDifference':maxdiff(orig['rootMatrix'],cand['rootMatrix']),'rotationDegrees':cand['rootRotationDegrees']})
 result={'originalProject':a['source'],'originalSHA256':a['sha256'],'candidateProject':b['source'],'candidateSHA256':b['sha256'],'restMatrixDifference':maxdiff(a['rest'],b['rest']),'actionsEqual':a['actions']==b['actions'],'actionCount':len(b['actions']),'foodGeometryUVPackedBytesEqual':a['food']==b['food'],'images':b['images'],'linkedLibraries':b['libraries'],'topologyChanges':b['topologyChanges'],'samples':rows,'sampleCount':len(rows)}
 results[name]=result
 (R/'round-01-native-reopen-audit.json').write_text(json.dumps(results,indent=2)+'\n')
 print('JUDGE_NATIVE',name,json.dumps({k:v for k,v in result.items() if k not in ['samples','images']}),flush=True)
