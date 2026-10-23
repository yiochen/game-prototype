import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
rootdir=Path.cwd();base=rootdir/'prototypes/sushi-loop/assets';out=base/'refinement/objects/chef-ellis/reviews/source-inspection';inp=out.parent.parent/'inputs'
sys.path.insert(0,str(base/'production/source/blender'))
import native_actions
record=json.loads((inp/'source-rig.json').read_text());collection=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];arm=bpy.data.objects['chef_ellis__armature.001']
collection.hide_viewport=False;collection.hide_render=False
scene=bpy.data.scenes.new('JUDGE_CHEF_ELLIS_SOURCE_INSPECTION');scene.collection.children.link(collection);bpy.context.window.scene=scene
objects=list(collection.all_objects);scene.view_layers[0].update();asset={'root':root,'collection':collection,'armature':arm}
def vec(v):return [float(x) for x in v]
def matrix(v):return [vec(r) for r in v]
def custom(o):
 d={}
 for k in o.keys():
  v=o[k]
  try:d[k]=v.to_list()
  except:
   try:json.dumps(v);d[k]=v
   except:d[k]=str(v)
 return d
report={'sourceProject':str(base/'production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'),'blenderVersion':bpy.app.version_string,'nativeActionsSHA256':hashlib.sha256(Path(native_actions.__file__).read_bytes()).hexdigest(),'collection':collection.name,'isolation':'source collection had global hide_viewport=True and hide_render=True; unhidden in memory and linked to new active scene before dependency graph evaluation; source not saved','rootName':root.name,'rootCustom':custom(root),'rootInitialMatrix':matrix(root.matrix_world),'armature':{'name':arm.name,'matrix':matrix(arm.matrix_world),'custom':custom(arm),'restBones':[{ 'name':b.name,'head':vec(b.head_local),'tail':vec(b.tail_local),'parent':b.parent.name if b.parent else None,'matrix':matrix(b.matrix_local)} for b in arm.data.bones]},'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixLocal':matrix(o.matrix_local),'modifiers':[{'name':m.name,'type':m.type,'object':getattr(m,'object',None).name if getattr(m,'object',None) else None} for m in o.modifiers],'custom':custom(o),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None} for o in objects],'samples':[],'sourceAttachmentDrivers':{o.name:[{'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in o.animation_data.drivers] for o in objects if o.animation_data and o.animation_data.drivers}}
watch=[o for o in objects if any(s in o.name for s in ['palm_','thumb_','minimal_foot_','held_dish','utensil','knife_','cap_crown','head.'])]
for clip in ['idle','work','hold','load']:
 for direction in ['S','E','N','W']:
  for index in range(12):
   native_actions.apply_clip(asset,record,clip,index+1,direction,scene);dg=bpy.context.evaluated_depsgraph_get();ea=arm.evaluated_get(dg);meshstats={};bounds=[]
   for o in objects:
    eo=o.evaluated_get(dg)
    if o.type=='MESH':
     mesh=eo.to_mesh();verts=[eo.matrix_world@v.co for v in mesh.vertices];meshstats[o.name]={'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'hidden':bool(o.hide_render),'min':[min(v[i] for v in verts) for i in range(3)],'max':[max(v[i] for v in verts) for i in range(3)],'centroid':[sum(v[i] for v in verts)/len(verts) for i in range(3)]}
     if not o.hide_render:bounds.extend(verts)
     eo.to_mesh_clear()
   body=[(name,v) for name,v in meshstats.items() if not v['hidden'] and 'image_plane' not in name]
   sample={'physicalBodyBounds':{'min':[min(v['min'][j] for name,v in body) for j in range(3)],'max':[max(v['max'][j] for name,v in body) for j in range(3)]},'clip':clip,'direction':direction,'index':index,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':matrix(root.matrix_world),'visibleBounds':{'min':[min(v[i] for v in bounds) for i in range(3)],'max':[max(v[i] for v in bounds) for i in range(3)]},'bonePose':{b.name:{'headWorld':vec(ea.matrix_world@b.head),'tailWorld':vec(ea.matrix_world@b.tail),'matrix':matrix(b.matrix),'location':vec(b.location),'rotation':vec(b.rotation_euler)} for b in ea.pose.bones},'attachmentTransforms':{o.name:{'location':vec(o.location),'matrixWorld':matrix(o.matrix_world),'rotationEuler':vec(o.rotation_euler),'scale':vec(o.scale),'hideRender':bool(o.hide_render),'hideViewport':bool(o.hide_viewport)} for o in watch},'meshStats':meshstats}
   report['samples'].append(sample)
# Preserve exact loop closure action evaluation in canonical S, with export still only1..12.
report['closureSamples']={}
for clip in ['idle','work','hold']:
 native_actions.apply_clip(asset,record,clip,13,'S',scene);ea=arm.evaluated_get(bpy.context.evaluated_depsgraph_get())
 report['closureSamples'][clip]={'bones':{b.name:{'headWorld':vec(arm.matrix_world@b.head),'tailWorld':vec(arm.matrix_world@b.tail),'matrix':matrix(b.matrix)} for b in ea.pose.bones},'attachmentTransforms':{o.name:{'location':vec(o.location),'matrixWorld':matrix(o.matrix_world),'scale':vec(o.scale),'hideRender':bool(o.hide_render)} for o in watch}}
report['finalEvaluatedArmatureMatrix']=matrix(arm.matrix_world)
camRecord=json.loads((inp/'source-camera.json').read_text());data=bpy.data.cameras.new('JUDGE_registered_camera');data.type='ORTHO';data.ortho_scale=2.5;data.shift_y=.275;camera=bpy.data.objects.new('JUDGE_registered_camera',data);scene.collection.objects.link(camera);camera.matrix_world=Matrix(camRecord['camera']['worldMatrix']);scene.camera=camera;scene.render.resolution_x=384;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
bpy.context.view_layer.update()
from bpy_extras.object_utils import world_to_camera_view
def project(v):
 p=world_to_camera_view(scene,camera,Vector(v));return [p.x*384,(1-p.y)*640]
origin=project((0,0,0));unit={name:[project(v)[j]-origin[j] for j in range(2)] for name,v in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}
report['registeredCameraReconstruction']={'source':'source-camera.json matrix and projection parameters; no pixel fit','matrix':matrix(camera.matrix_world),'type':data.type,'orthoScale':data.ortho_scale,'shiftY':data.shift_y,'frame':[384,640],'logicalFrame':[192,320],'projectedRoot':origin,'basis':unit,'projectionMatrix':matrix(camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1))}

report['images']=[{'name':i.name,'filepath':i.filepath,'packed':i.packed_file is not None,'size':list(i.size)} for i in bpy.data.images if any(i==n.image for o in objects if hasattr(o.data,'materials') for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE')]
(out/'native-source-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('JUDGEAUDIT',len(report['samples']),'native samples; object count',len(objects),'bone names',[b.name for b in arm.pose.bones]);print('IMAGES',report['images']);print('ROOT',report['rootCustom'])
