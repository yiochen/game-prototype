import bpy,pathlib,json,hashlib,importlib.util,math
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
b=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-dalia');r=b/'reviews';source=json.loads((r/'source-evaluated-audit.json').read_text());sr={(f['clip'],f['direction'],f['index']):f for f in source['frames']};record=json.loads((b/'inputs/source-rig.json').read_text())
origScene=bpy.context.scene;cam=origScene.camera;root=bpy.data.objects[record['groundRootObject']];col=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects));arm=bpy.data.objects[record['armatures'][0]['object']]
lightRecords=[{'name':o.name,'type':o.data.type,'location':list(o.matrix_world.translation),'energy':o.data.energy,'size':o.data.size if hasattr(o.data,'size') else None,'color':list(o.data.color)} for o in origScene.objects if o.type=='LIGHT']
sc=bpy.data.scenes.new('Dalia independent candidate audit');sc.collection.children.link(col);bpy.context.window.scene=sc;col.hide_viewport=False;col.hide_render=False
if cam.name not in sc.objects:sc.collection.objects.link(cam)
sc.camera=cam;sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1
for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
helper=b/'source/native_actions_round01.py';spec=importlib.util.spec_from_file_location('dalia_review_original_native',helper);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
asset={'root':root,'collection':col,'armature':arm};meshes=[o for o in col.all_objects if o.type=='MESH'];top={};changes=[];ext=[];frames=[]
def mbounds(o,dg):
 eo=o.evaluated_get(dg);pts=[eo.matrix_world@Vector(v) for v in eo.bound_box];return [[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]
def center(o,dg):
 eo=o.evaluated_get(dg);vs=eo.data.vertices;return list(sum((eo.matrix_world@v.co for v in vs),Vector())/len(vs))
def delta(a,b):
 if isinstance(a,list):return max([delta(x,y) for x,y in zip(a,b)] or [0])
 return abs(a-b)
maxPalm=0.;maxFeet=0.;maxDish=0.;maxKnife=0.;maxMovingTop=-999.;footprint=True;finite=True
for clip in ['idle','work','hold','load']:
 for di in ['N','E','S','W']:
  for fi in range(12):
   native.apply_clip(asset,record,clip,fi+1,di,sc);dg=bpy.context.evaluated_depsgraph_get();f0=sr[(clip,di,fi)];body=[]
   for o in meshes:
    eo=o.evaluated_get(dg);me=eo.data;signature=[len(me.vertices),len(me.edges),len(me.polygons)];prev=top.setdefault(o.name,signature)
    if signature!=prev:changes.append({'clip':clip,'direction':di,'index':fi,'object':o.name,'counts':signature})
    if not o.hide_render and '__held_dish' not in o.name:
     body += [eo.matrix_world@Vector(v) for v in eo.bound_box]
    if not all(math.isfinite(v) for row in eo.matrix_world for v in row):finite=False
   for s in ['L','R']:
    palm=bpy.data.objects['chef_dalia__palm_'+s+'.001'];orig=f0['parts'][palm.name];maxPalm=max(maxPalm,delta(center(palm,dg),orig['center']))
    foot=bpy.data.objects['chef_dalia__minimal_foot_'+s];ob=f0['parts'][foot.name]['bounds'];maxFeet=max(maxFeet,delta(mbounds(foot,dg),[[ob['min'][i],ob['max'][i]] for i in range(3)]))
   dish=bpy.data.objects[record['groundRootObject']+'__held_dish-salmon'];maxDish=max(maxDish,delta([list(z) for z in dish.matrix_world],f0['dishRootMatrix']))
   if clip=='work':maxKnife=max(maxKnife,delta(center(bpy.data.objects[record['groundRootObject']+'__knife_handle'],dg),center(bpy.data.objects['chef_dalia__palm_R.001'],dg)))
   bounds=[[min(v[i] for v in body),max(v[i] for v in body)] for i in range(3)];maxMovingTop=max(maxMovingTop,bounds[2][1]-f0['bodyBounds']['max'][2]);footprint=footprint and max(abs(bounds[i][j]) for i in [0,1] for j in [0,1])<=0.50001
   frames.append({'clip':clip,'direction':di,'index':fi,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'bodyBounds':bounds})
for o in meshes:
 for m in o.data.materials:
  if m and m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
     im=n.image;ext.append({'object':o.name,'image':im.name,'path':im.filepath,'packed':bool(im.packed_file),'packedSHA256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None})
camRecord=json.loads((b/'inputs/source-camera.json').read_text())['camera'];dg=bpy.context.evaluated_depsgraph_get();proj=cam.calc_matrix_camera(dg,x=384,y=640,scale_x=1,scale_y=1)
pixel=world_to_camera_view(sc,cam,Vector((0,0,0)));result={'candidateProjectSHA256':hashlib.sha256((b/'source/round-01.blend').read_bytes()).hexdigest(),'originalProjectSHA256':source['sourceProjectSHA256'] if 'sourceProjectSHA256' in source else 'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','blenderVersion':bpy.app.version_string,'method':'Reopened sealed candidate; isolated intended asset; applied recorded original action helper, sampled all192 frames. No project or render saved.','frameCount':len(frames),'meshCount':len(meshes),'cameraWorldMaxDifferenceToInput':delta([list(z) for z in cam.matrix_world],camRecord['worldMatrix']),'cameraProjectionMaxDifferenceToInput':delta([list(z) for z in proj],camRecord['projectionMatrix']),'projectedRootNative':[pixel.x*384,(1-pixel.y)*640],'rootScale':list(root.scale),'palmCentroidMaxComponentDifferenceToIndependentOriginal':maxPalm,'footBoundsMaxComponentDifferenceToIndependentOriginal':maxFeet,'dishRootMatrixMaxComponentDifferenceToIndependentOriginal':maxDish,'workKnifePalmCenterMaxComponentDifference':maxKnife,'maxMovingTopDeltaToIndependentOriginal':maxMovingTop,'allBodyFramesInsideOneCell':footprint,'topologyChanges':changes,'stableEvaluatedCounts':top,'finiteMatrices':finite,'materialsImages':ext,'linkedLibraries':[z.filepath for z in bpy.data.libraries],'originalSceneLightRecords':lightRecords,'originalSceneRender':{'engine':origScene.render.engine,'resolution':[origScene.render.resolution_x,origScene.render.resolution_y],'transparentFilm':origScene.render.film_transparent,'viewTransform':origScene.view_settings.view_transform,'exposure':origScene.view_settings.exposure},'frames':frames}
(r/'round01-independent-native-checks.json').write_text(json.dumps(result,indent=2)+'\n');print('RESULT',json.dumps({k:v for k,v in result.items() if k not in ['frames','stableEvaluatedCounts']},indent=2))
