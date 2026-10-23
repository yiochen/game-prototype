import bpy,json,pathlib,importlib.util,hashlib,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
repo=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
base=repo/'prototypes/sushi-loop/assets/refinement/objects/belt-straight-e'
rounddir=base/'candidates/round-01';out=base/'reviews/round-01-inspection'
spec=importlib.util.spec_from_file_location('original_native_actions',repo/'prototypes/sushi-loop/assets/production/source/blender/revisions/4fa9e22e555f8aad/native_actions.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
record=json.loads((rounddir/'rig.json').read_text());scene=bpy.context.scene
coll=bpy.data.collections['S33_FB_belt-straight-e.001'];root=bpy.data.objects[record['groundRootObject']];orient=bpy.data.objects['belt-straight-e__orientation.001'];deck=bpy.data.objects['belt-straight-e__connected_straight_deck.001']
asset={'collection':coll,'root':root};mat=bpy.data.materials[record['clips']['running']['actions'][0]['materialOwnerName']];phase=mat.node_tree.nodes['Value'].outputs[0];cam=scene.camera
def xy(v):
 p=world_to_camera_view(scene,cam,Vector(v));return [p.x*scene.render.resolution_x,(1-p.y)*scene.render.resolution_y]
report={'project':bpy.data.filepath,'projectSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':scene.name,'savedCamera':{'name':cam.name,'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'root':xy((0,0,0)),'unitX':xy((1,0,0)),'unitDepth':xy((0,-1,0)),'unitHeight':xy((0,0,1))},'orientation':list(orient.rotation_euler),'savedVisibility':{'collectionHiddenViewport':coll.hide_viewport,'collectionHiddenRender':coll.hide_render},'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath} for i in bpy.data.images],'materials':[],'lights':[],'render':{'engine':scene.render.engine,'samples':scene.cycles.samples,'device':scene.cycles.device,'filter':scene.cycles.pixel_filter_type,'filterWidth':scene.cycles.filter_width,'denoise':scene.cycles.use_denoising,'dither':scene.render.dither_intensity,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure},'samples':{},'judgeRenders':[]}
for light in scene.objects:
 if light.type=='LIGHT':report['lights'].append({'name':light.name,'energy':light.data.energy,'location':list(light.location),'rotation':list(light.rotation_euler),'type':light.data.type,'size':light.data.size})
for m in bpy.data.materials:
 if not m.use_nodes:continue
 report['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'image':n.image.name if n.bl_idname=='ShaderNodeTexImage' and n.image else None} for n in m.node_tree.nodes],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links]})
for d in 'NESW':
 samples=[]
 for i in range(25):
  native.apply_clip(asset,record,'running',i+1,d,scene);dg=bpy.context.evaluated_depsgraph_get();parts=[];allpts=[]
  for obj in coll.all_objects:
   if obj.type!='MESH':continue
   ev=obj.evaluated_get(dg);mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];allpts+=pts
   boundary={str(end):[list(p) for p in pts if abs(p[0 if d in 'NS' else 1]-end)<1e-6] for end in [-.5,.5]}
   parts.append({'name':obj.name,'vertices':len(mesh.vertices),'edges':len(mesh.edges),'polygons':len(mesh.polygons),'bounds':[[min(v[k] for v in pts) for k in range(3)],[max(v[k] for v in pts) for k in range(3)]],'portBoundary':boundary,'faceCornerIndices':[list(p.vertices) for p in mesh.polygons] if 'stationary_rail' in obj.name else None});ev.to_mesh_clear()
  uv=[]
  for loop in deck.data.loops:
   p=deck.matrix_world@deck.data.vertices[loop.vertex_index].co;uv.append({'world':list(p),'uv':list(deck.data.uv_layers.active.data[loop.index].uv)})
  samples.append({'index':i,'frame':i+1,'closure':i==24,'phase':phase.default_value,'rootRotation':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'bounds':[[min(v[k] for v in allpts) for k in range(3)],[max(v[k] for v in allpts) for k in range(3)]],'deckUV':uv,'parts':parts})
 report['samples'][d]=samples
 # Independently render a real saved-scene frame without altering materials/lights/camera/settings.
 for i in ([0,23] if d=='E' else [0]):
  native.apply_clip(asset,record,'running',i+1,d,scene);scene.render.filepath=str(out/f'judge-native-{d}-{i:02}.png');bpy.ops.render.render(write_still=True);report['judgeRenders'].append({'direction':d,'index':i,'path':scene.render.filepath})
(out/'native-candidate-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'camera':report['savedCamera'],'orientation':report['orientation'],'libraries':report['libraries'],'images':report['images'],'render':report['render'],'samples':{d:{'bounds':s[0]['bounds'],'phaseExact':all(abs(v['phase']+7*v['index']/24)<1e-6 for v in s),'deckUV':s[0]['deckUV'],'topologyStable':all([(p['name'],p['vertices'],p['edges'],p['polygons']) for p in v['parts']]==[(p['name'],p['vertices'],p['edges'],p['polygons']) for p in s[0]['parts']] for v in s)} for d,s in report['samples'].items()}},indent=2))
