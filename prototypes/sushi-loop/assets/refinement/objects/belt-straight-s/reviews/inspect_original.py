import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector, Matrix
base=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/belt-straight-s')
col=bpy.data.collections['S33_FB_belt-straight-s.001']
original=bpy.context.scene
scene=bpy.data.scenes.new('S independent source inspection')
scene.collection.children.link(col)
bpy.context.window.scene=scene
for c in [col]+list(col.children_recursive):
 c.hide_viewport=False;c.hide_render=False
for o in col.all_objects:
 o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
source_camera=json.loads((base/'inputs/source-camera.json').read_text())
raw_library_camera={'name':original.camera.name,'worldMatrix':matraw if False else [list(r) for r in original.camera.matrix_world],'note':'The library active camera belongs to another asset and is not the registered belt capture. It is not used for this inspection.'}
cam=bpy.data.objects.new('Independent registered S capture camera',original.camera.data.copy())
scene.collection.objects.link(cam);scene.camera=cam
cam.matrix_world=Matrix(source_camera['camera']['worldMatrix'])
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=0
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=source_camera['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=source_camera['camera']['pixelAspect'][1]
from bpy_extras.object_utils import world_to_camera_view
bpy.context.view_layer.update()
basey=(1-world_to_camera_view(scene,cam,Vector((0,0,0))).y)*704
cam.data.shift_y=1;bpy.context.view_layer.update()
dy=(1-world_to_camera_view(scene,cam,Vector((0,0,0))).y)*704-basey
cam.data.shift_y=(496-basey)/dy;bpy.context.view_layer.update()
scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['belt-straight-s__root.001'];orient=bpy.data.objects['belt-straight-s__orientation.001']
def mat(m):return [list(r) for r in m]
def obj_info(o):
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':mat(o.matrix_world)}
 if o.type=='MESH':
  vv=[o.matrix_world@v.co for v in o.data.vertices];d['bounds']=[[min(v[i] for v in vv) for i in range(3)],[max(v[i] for v in vv) for i in range(3)]];d['verticesWorld']=[list(v) for v in vv];d['uvs']=[list(x.uv) for x in o.data.uv_layers.active.data] if o.data.uv_layers.active else [];d['materials']=[m.name for m in o.data.materials if m]
 return d
objects=[obj_info(o) for o in col.all_objects]
matr=bpy.data.materials['S33_belt-straight-s_moving_deck.001'];nt=matr.node_tree
anim=nt.animation_data;action=anim.action
curves=[]
for l in action.layers:
 for s in l.strips:
  for cb in s.channelbags:
   for fc in cb.fcurves:curves.append({'dataPath':fc.data_path,'arrayIndex':fc.array_index,'keys':[{'frame':kp.co.x,'value':kp.co.y,'interpolation':kp.interpolation} for kp in fc.keyframe_points]})
phases=[]
for f in range(1,26):
 scene.frame_set(f);bpy.context.view_layer.update();phases.append({'frame':f,'phase':nt.nodes['Value'].outputs[0].default_value})
scene.frame_set(1);bpy.context.view_layer.update()
facings={}
from bpy_extras.object_utils import world_to_camera_view
for facing,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update()
 deck=bpy.data.objects['belt-straight-s__connected_straight_deck.001']
 uv=deck.data.uv_layers.active.data
 # original deck quad: group world corners by native UV.x incoming/outgoing ends
 ports={}
 for end,uvx in [('incoming',0),('outgoing',1)]:
  vs=[deck.matrix_world@deck.data.vertices[loop.vertex_index].co for loop in deck.data.loops if abs(uv[loop.index].uv.x-uvx)<1e-6]
  p=sum(vs,Vector())/len(vs);q=world_to_camera_view(scene,scene.camera,p);r=world_to_camera_view(scene,scene.camera,Vector((0,0,0)))
  ports[end]={'world':list(p),'rootRelativeLogical':[(q.x-r.x)*192,-(q.y-r.y)*352]}
 facings[facing]={'publisherRootAngleDegrees':angle,'deckMatrixWorld':mat(deck.matrix_world),'ports':ports,'bounds':[[min((o.matrix_world@v.co)[i] for o in col.all_objects if o.type=='MESH' for v in o.data.vertices) for i in range(3)],[max((o.matrix_world@v.co)[i] for o in col.all_objects if o.type=='MESH' for v in o.data.vertices) for i in range(3)]]}
root.rotation_euler.z=0;bpy.context.view_layer.update()
cam=scene.camera
out={'source':'production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend','isolation':'Source collection linked into new active inspection scene; collection/object hide_viewport/hide_render/hide_set all false; view_layer.update after frame and root changes. No blend saved.','unusedRawLibraryCamera':raw_library_camera,'registeredCameraBasis':'inputs/source-camera.json plus capture_runtime.py configure_camera convention. Camera matrix, projection, calibration independently compared below.','originalScene':original.name,'collection':col.name,'root':root.name,'orientation':{'name':orient.name,'parent':orient.parent.name if orient.parent else None,'rotationEuler':list(orient.rotation_euler),'matrixWorld':mat(orient.matrix_world)},'camera':{'projectionMatrix':mat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=scene.render.pixel_aspect_x,scale_y=scene.render.pixel_aspect_y)),'calibration':{k:list(v) for k,v in [(k,Vector((world_to_camera_view(scene,cam,Vector(p)).x*384,(1-world_to_camera_view(scene,cam,Vector(p)).y)*704))) for k,p in [('root',(0,0,0)),('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]]},'name':cam.name,'matrixWorld':mat(cam.matrix_world),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'originalResolution':[original.render.resolution_x,original.render.resolution_y,original.render.resolution_percentage]},'objects':objects,'animation':{'materialOwner':matr.name,'nodeTreeOwner':nt.name,'action':action.name,'slot':anim.action_slot.identifier if anim.action_slot else None,'curves':curves,'phaseEvaluations':phases,'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':[{ 'name':s.name,'value':list(s.default_value) if hasattr(s,'default_value') and hasattr(s.default_value,'__len__') else s.default_value if hasattr(s,'default_value') else None} for s in n.inputs]} for n in nt.nodes],'links':[{'from':l.from_node.name+':'+l.from_socket.name,'to':l.to_node.name+':'+l.to_socket.name} for l in nt.links]},'facings':facings}
(base/'reviews/native-source-inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'orientation':out['orientation'],'camera':out['camera'],'objects':[{k:v for k,v in x.items() if k not in ['verticesWorld']} for x in objects],'animation':{k:v for k,v in out['animation'].items() if k not in ['nodes','links']},'facings':facings},indent=2))
