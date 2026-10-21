import bpy, json, pathlib, importlib.util, math, hashlib
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

repo=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
base=repo/'prototypes/sushi-loop/assets/refinement/objects/belt-straight-e'
out=base/'reviews/source-inspection'
spec=importlib.util.spec_from_file_location('native_actions', repo/'prototypes/sushi-loop/assets/production/source/blender/revisions/4fa9e22e555f8aad/native_actions.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
record=json.loads((base/'inputs/source-rig.json').read_text())
camera_record=json.loads((base/'inputs/source-camera.json').read_text())
coll=bpy.data.collections['S33_FB_belt-straight-e.001']
root=bpy.data.objects[record['groundRootObject']]
deck=next(o for o in coll.objects if '__connected_straight_deck' in o.name)
orient=next(o for o in coll.objects if '__orientation' in o.name)
saved_scene=bpy.context.scene
report={'sourceFile':bpy.data.filepath,'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'savedSceneCamera':{'name':saved_scene.camera.name,'worldMatrix':[list(r) for r in saved_scene.camera.matrix_world]},'collection':coll.name,'orientationLocalRadians':list(orient.rotation_euler),'rootSavedRotation':list(root.rotation_euler),'objects':[]}
report['libraryCollectionHidden']={'viewport':coll.hide_viewport,'render':coll.hide_render}
scene=bpy.data.scenes.new('Judge E source inspection');scene.collection.children.link(coll);bpy.context.window.scene=scene
coll.hide_viewport=False;coll.hide_render=False
for o in coll.objects:
 report['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'localLocation':list(o.location),'localRotation':list(o.rotation_euler),'localScale':list(o.scale),'hiddenRender':o.hide_render,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'meshVertices':[list(v.co) for v in o.data.vertices] if o.type=='MESH' else [],'polygons':[list(p.vertices) for p in o.data.polygons] if o.type=='MESH' else [],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]})
 o.hide_render=False;o.hide_viewport=False
camdata=bpy.data.cameras.new('Judge registered camera');cam=bpy.data.objects.new('Judge registered camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
cam.matrix_world=Matrix(camera_record['camera']['worldMatrix']);camdata.type='ORTHO';camdata.ortho_scale=2.252887725830078;camdata.shift_x=0;camdata.shift_y=.20454464852809906
scene.render.resolution_x=384;scene.render.resolution_y=704;scene.render.resolution_percentage=100;scene.render.pixel_aspect_x=camera_record['camera']['pixelAspect'][0];scene.render.pixel_aspect_y=1
asset={'collection':coll,'root':root}
phase=bpy.data.materials[record['clips']['running']['actions'][0]['materialOwnerName']].node_tree.nodes['Value'].outputs[0]
def point(v):
 q=world_to_camera_view(scene,cam,Vector(v));return [q.x*384,(1-q.y)*704]
report['camera']={'worldMatrix':[list(r) for r in cam.matrix_world],'elevationDegrees':math.degrees(math.atan2(cam.location.z,abs(cam.location.y))),'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'frame':[384,704],'root':point((0,0,0)),'unitX':point((1,0,0)),'unitDepth':point((0,-1,0)),'unitHeight':point((0,0,1))}
report['facingSamples']={}
for direction in ['N','E','S','W']:
 samples=[]
 for frame in range(1,26):
  native.apply_clip(asset,record,'running',frame,direction,scene)
  dg=bpy.context.evaluated_depsgraph_get();pts=[];topology=[]
  for o in coll.objects:
   if o.type!='MESH':continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();pts.extend(ev.matrix_world@v.co for v in me.vertices);topology.append([o.name,len(me.vertices),len(me.edges),len(me.polygons)]);ev.to_mesh_clear()
  uvpoints=[]
  for loop in deck.data.loops:
   v=deck.matrix_world@deck.data.vertices[loop.vertex_index].co
   uvpoints.append({'vertex':loop.vertex_index,'uv':list(deck.data.uv_layers.active.data[loop.index].uv),'world':list(v)})
  incoming=[Vector(x['world']) for x in uvpoints if abs(x['uv'][0])<1e-5];outgoing=[Vector(x['world']) for x in uvpoints if abs(x['uv'][0]-1)<1e-5]
  ports={k:sum(vs,Vector())/len(vs) for k,vs in [('incoming',incoming),('outgoing',outgoing)]}
  ports['deck']=root.matrix_world@Vector((0,0,.64))
  samples.append({'frame':frame,'runtimeIndex':frame-1 if frame<25 else None,'closure':frame==25,'phase':phase.default_value,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'bounds':[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]],'ports':{k:{'world':list(v),'pixel':point(v)} for k,v in ports.items()},'deckVerticesUV':uvpoints,'topology':topology})
 report['facingSamples'][direction]=samples
report['closureCheck']={d:{'phaseFirst':s[0]['phase'],'phaseClosing':s[-1]['phase'],'phaseDifference':s[-1]['phase']-s[0]['phase'],'allPhaseErrorsUnder1e-6':all(abs(v['phase']+7*(v['frame']-1)/24)<1e-6 for v in s),'staticEvaluatedTopology':all(v['topology']==s[0]['topology'] for v in s)} for d,s in report['facingSamples'].items()}
(out/'native-source-inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'orientationLocalRadians':report['orientationLocalRadians'],'camera':report['camera'],'facings':{d:{'bounds':s[0]['bounds'],'ports':s[0]['ports'],'rootRotationDegrees':s[0]['rootRotationDegrees']} for d,s in report['facingSamples'].items()},'closureCheck':report['closureCheck']},indent=2))
