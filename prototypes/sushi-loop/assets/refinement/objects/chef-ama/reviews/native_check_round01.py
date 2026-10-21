import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');C=P/'candidates/round-01'
sys.path.insert(0,str(P.parents[2]/'production/source/blender'))
import native_actions as NA
rig=json.loads((P/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in bpy.data.collections if root in list(c.all_objects));sc=next(s for s in bpy.data.scenes if root.name in s.objects)
bpy.context.window.scene=sc
coll.hide_render=False;coll.hide_viewport=False
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False
bpy.context.view_layer.update();arm=next(o for o in coll.all_objects if o.type=='ARMATURE')
manifest=json.loads((C/'native-frames.json').read_text());reference={(r['clip'],r['direction'],r['index']):r for r in manifest}
original=json.loads((P/'reviews/source-inspection.json').read_text())
asset={'id':'chef-ama','root':root,'collection':coll};errors=[];maxroot=0;maxbounds=0;maxcontact=0;counts={};weighted=0;badweights=0
for o in coll.all_objects:
 if o.type!='MESH':continue
 if any(m.type=='ARMATURE' for m in o.modifiers):
  for v in o.data.vertices:
   weighted+=1; total=sum(g.weight for g in v.groups)
   if abs(total-1)>1e-5:badweights+=1
for clip in ['idle','work','hold','load']:
 for direction,ang in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
  for index in range(12):
   NA.apply_clip(asset,rig,clip,index+1,direction,sc);dg=bpy.context.evaluated_depsgraph_get();ref=reference[(clip,direction,index)];maxroot=max(maxroot,abs(root.rotation_euler.z-ang))
   for o in coll.all_objects:
    if o.type!='MESH':continue
    ev=o.evaluated_get(dg);n=(len(ev.data.vertices),len(ev.data.edges),len(ev.data.polygons))
    if o.name in counts and counts[o.name]!=n:errors.append({'object':o.name,'phase':[clip,direction,index],'topologyChanged':n})
    counts[o.name]=n
    if o.name in ref['geometry']:
     bounds=[[min((ev.matrix_world@Vector(c))[i] for c in ev.bound_box),max((ev.matrix_world@Vector(c))[i] for c in ev.bound_box)] for i in range(3)]
     # Evaluated bounding boxes can conservatively differ from actual vertex bounds; recorded only, not used as equality proof.
   if direction=='S':
    ar=arm.evaluated_get(dg)
    poses={b.name:list((ar.matrix_world@b.matrix).translation) for b in ar.pose.bones if any(v in b.name for v in ['foot','hand','ground','head'])}
    src=original['clips'][clip]['frames'][index]['poseContactsWorld']
    maxcontact=max(maxcontact,max(abs(poses[n][j]-src[n][j]) for n in src for j in range(3)))
rootpix=world_to_camera_view(sc,sc.camera,Vector((0,0,0)));rootpix=[rootpix.x*sc.render.resolution_x,(1-rootpix.y)*sc.render.resolution_y]
images=[{'name':im.name,'packed':bool(im.packed_file),'hash':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None,'source':im.filepath} for im in bpy.data.images if im.type=='IMAGE']
out={'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'nativeScene':sc.name,'collection':coll.name,'rootScale':list(root.scale),'actualCamera':{'type':sc.camera.data.type,'orthoScale':sc.camera.data.ortho_scale,'worldMatrix':[list(r) for r in sc.camera.matrix_world],'rootPixel':rootpix,'frame':[sc.render.resolution_x,sc.render.resolution_y]},'evaluatedPhases':192,'maxFacingRotationErrorRadians':maxroot,'allEvaluatedTopologyCountsStable':not errors,'topologyErrors':errors,'meshObjectCount':len(counts),'weightedVertices':weighted,'nonUnitWeights':badweights,'S48PhaseContactBoneOriginMaxDifferenceToMyOriginalSourceInspection':maxcontact,'images':images,'linkedLibraries':[l.filepath for l in bpy.data.libraries],'notes':['Read-only saved candidate reopen; no .blend save or render performed.','All192 evaluated mesh counts and native facing rotations independently sampled. Source48 S bone contact origins compared to my own initial original-source inspection. Exact surface/action/rest/height evidence additionally read in hash-bound validation and root audit.','Evaluated bbox is not substituted for actual vertex bounds; parent full192 actual native audit and sealed actual-vertex records remain surface/envelope evidence.']}
(P/'reviews/round01-independent-native-check.json').write_text(json.dumps(out,indent=2)+'\n')
print('AMA_NATIVE_CHECK',json.dumps({k:v for k,v in out.items() if k not in ['actualCamera','images','notes']},indent=2))
