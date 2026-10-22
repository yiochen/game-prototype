import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib,pathlib,gzip
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
ROOT=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
OBJ=ROOT/'prototypes/sushi-loop/assets/refinement/objects/customer-rosa'
OUT=OBJ/'reviews'
def h(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def clean(x):
 if hasattr(x,'to_list'):return x.to_list()
 return str(x)
def vec(x):return [round(float(v),8) for v in x]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def curves(a):
 if hasattr(a,'fcurves'):return list(a.fcurves)
 return [fc for la in a.layers for st in la.strips for sl in a.slots for bag in [st.channelbag(sl)] if bag for fc in bag.fcurves]
def actionhash(a):return digest([(fc.data_path,fc.array_index,[(vec(k.co),k.interpolation) for k in fc.keyframe_points]) for fc in curves(a)])
def assign(target):
 o=bpy.data.objects[target['ownerName']];a=bpy.data.actions[target['action']];o.animation_data_create();o.animation_data.action=a
 slot=next((s for s in a.slots if s.identifier==target.get('slotIdentifier')),None)
 if slot:o.animation_data.action_slot=slot
 return o

def inspect(project,rigpath,label):
 bpy.ops.wm.open_mainfile(filepath=str(project))
 r=json.loads(rigpath.read_text());root=bpy.data.objects[r['groundRootObject']];col=next(c for c in root.users_collection if root.name in c.all_objects)
 sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
 def visible(l):
  l.exclude=False;l.hide_viewport=False;l.collection.hide_viewport=False;l.collection.hide_render=False
  for child in l.children:visible(child)
 visible(bpy.context.view_layer.layer_collection)
 for c in sc.collection.children:c.hide_render=c!=col
 cam=sc.camera
 saved={'scene':sc.name,'camera':cam.name,'matrix':[[float(x) for x in row] for row in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y]}
 # Reproduce Rosa's registered camera from her own source-camera record, not the library's active world camera.
 cam.matrix_world=Matrix(json.loads((OBJ/'inputs/source-camera.json').read_text())['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.2749992311000824
 sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.fps=12;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*640]
 # Resolve shift directly against ground root to avoid stale numerical shifts.
 cam.data.shift_y=0;bpy.context.view_layer.update();base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cam.data.shift_y=(496-base[1])/dy;bpy.context.view_layer.update()
 arm=next(o for o in col.all_objects if o.type=='ARMATURE');plane=next(o for o in col.all_objects if o.get('representation')=='2D ImageGen sprite, not modeled sushi');food=plane.parent
 tex=next(n for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');im=tex.image
 packed=bytes(im.packed_file.data) if im.packed_file else None
 if packed:(OUT/('source-packed-food-'+label+'.png')).write_bytes(packed)
 drivers=[{'path':fc.data_path,'index':fc.array_index,'expression':fc.driver.expression,'variables':[{'name':v.name,'id':t.id.name if t.id else None,'path':t.data_path} for v in fc.driver.variables for t in v.targets]} for fc in plane.animation_data.drivers]
 info={'project':str(project.relative_to(ROOT)),'projectSHA256':h(project),'rigSHA256':h(rigpath),'collection':col.name,'objectCount':len(col.all_objects),'root':root.name,'rootLocation':vec(root.location),'rootScale':vec(root.scale),'rootProperties':{k:root[k] for k in ('uniform_native_scale','anatomy_height','seat_environment_z','seat_character_plane','seat_pelvis_offset','food_composition','held_food_source') if k in root},'armature':arm.name,'restBones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':vec(b.head_local),'tail':vec(b.tail_local),'deform':b.use_deform} for b in arm.data.bones], 'savedActiveCamera':saved,'registeredCamera':{'name':cam.name,'worldMatrix':[[float(x) for x in row] for row in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'resolution':[384,640],'pixelAspect':[1,1],'groundRootPx':px((0,0,0)),'unitXPx':px((1,0,0)),'unitDepthPx':px((0,-1,0)),'unitHeightPx':px((0,0,1))},'food':{'root':food.name,'plane':plane.name,'localVertices':[vec(v.co) for v in plane.data.vertices],'uv':[vec(u.uv) for u in plane.data.uv_layers.active.data],'imageName':im.name,'imageSize':list(im.size),'packedSHA256':hashlib.sha256(packed).hexdigest() if packed else None,'props':dict(plane.items()),'drivers':drivers},'clips':{},'sampleCount':0}
 for ob in col.all_objects:
  if ob.animation_data:
   ob.animation_data.action=None
   for t in ob.animation_data.nla_tracks:t.mute=True
 archives={}
 for clip,c in r['clips'].items():
  allsamples=[];bmin=[1e9]*3;bmax=[-1e9]*3;visiblefood=0;contactranges={};owners=[]
  for target in c['actions']:
   ob=assign(target);owners.append({'owner':ob.name,'action':target['action'],'sha256':actionhash(bpy.data.actions[target['action']])})
  for facing,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
   root.rotation_euler.z=angle
   for frame in range(1,c['lastUniqueFrame']+1):
    sc.frame_set(frame);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dep)
    bones={n:vec(ae.matrix_world@ae.pose.bones[n].head) for n in ['pelvis','head','foot_L','foot_R','hand_L','hand_R','foot_goal_L','foot_goal_R','hand_goal_L','hand_goal_R']}
    contacts={'ground':vec(root.matrix_world.translation),'seat':vec(ae.matrix_world@ae.pose.bones['pelvis'].head-root.matrix_world.to_3x3()@Vector((0,0,float(root.get('seat_pelvis_offset',.08))))),'mouth':vec(ae.matrix_world@ae.pose.bones['head'].matrix@ae.pose.bones['head'].bone.matrix_local.inverted()@Vector((0,-.255,.543)))}
    corners=[vec(plane.matrix_world@v.co) for v in plane.data.vertices];pcoords=[px(v) for v in corners]
    for o in col.all_objects:
     if o.type!='MESH' or o==plane or o.hide_render:continue
     e=o.evaluated_get(dep);mesh=e.to_mesh()
     for v in mesh.vertices:
      co=e.matrix_world@v.co
      for k in range(3):bmin[k]=min(bmin[k],co[k]);bmax[k]=max(bmax[k],co[k])
     e.to_mesh_clear()
    visiblefood+=not plane.hide_render
    for n,v in {**bones,**contacts}.items():
     mm=contactranges.setdefault(n,[[1e9]*3,[-1e9]*3])
     for k in range(3):mm[0][k]=min(mm[0][k],v[k]);mm[1][k]=max(mm[1][k],v[k])
    allsamples.append({'facing':facing,'frame':frame,'bones':bones,'contacts':contacts,'foodRoot':vec(food.matrix_world.translation),'corners':corners,'projectedCorners':pcoords,'foodVisible':not plane.hide_render})
  archives[clip]=allsamples
  info['clips'][clip]={'frames':c['frames'],'fps':c['fps'],'loop':c['loop'],'firstFrame':c['firstFrame'],'lastUniqueFrame':c['lastUniqueFrame'],'closingKeyFrame':c.get('closingKeyFrame'),'actions':owners,'samples':len(allsamples),'samplesSHA256':digest(allsamples),'physicalGeometryBounds':[vec(bmin),vec(bmax)],'contactRanges':contactranges,'foodVisibleSamples':visiblefood,'sampleFirst':allsamples[0],'sampleLast':allsamples[-1]};info['sampleCount']+=len(allsamples)
 archive=gzip.compress(json.dumps(archives,separators=(',',':')).encode(),mtime=0);archivepath=OUT/('source-samples-'+label+'.json.gz');archivepath.write_bytes(archive);info['sampleArchive']={'path':archivepath.name,'sha256':h(archivepath),'format':'gzip JSON, all576 source samples across main+runtime, recomputable from inspect-source.py'}
 (OUT/('source-contract-'+label+'.json')).write_text(json.dumps(info,indent=2,default=clean)+'\n')
 print('JUDGE_RESULT',label,info['sampleCount'],col.name,info['registeredCamera'],flush=True)
 return info
main=inspect(ROOT/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',OBJ/'inputs/source-rig.json','main')
variant=inspect(OBJ/'inputs/runtime-variants/starter-meals-project.blend',OBJ/'inputs/runtime-variants/export/source/customer-rosa/rig.json','runtime')
