"""Reopen exact round sources, render all native frames and compare evaluated contacts."""
import bpy,json,math,sys,hashlib,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent; BASE=P.parent; sys.path.insert(0,str(P))
import native_actions_round01 as native
from audit_common_round01 import contacts,geometry,food_signature
runtime='--runtime' in sys.argv
prefix='runtime-' if runtime else ''
OUT=BASE/'candidates/round-01';OUT=OUT/'runtimeVariants' if runtime else OUT;OUT.mkdir(parents=True,exist_ok=True)
recipe=json.loads((P/(prefix+'recipe-round01.json')).read_text())
rig=json.loads((P/(prefix+'rig-round01.json')).read_text())
source_path=P/('runtime-round-01.blend' if runtime else 'round-01.blend')
sc=bpy.data.scenes[recipe['scene']];bpy.context.window.scene=sc
coll=bpy.data.collections[recipe['collection']];root=bpy.data.objects[recipe['root']];arm=bpy.data.objects[recipe['armature']]
asset={'collection':coll,'root':root,'armature':arm};coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update()
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception as e:print('METAL',e)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def px(v):
 p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
reference={(r['clip'],r['direction'],r['index']):r for r in json.loads((P/(prefix+'source-contacts-round01.json')).read_text())}
rest=json.loads((P/(prefix+'source-rest-round01.json')).read_text())
rest_error=max(abs(arm.data.bones[n].matrix_local[i][j]-v['matrix'][i][j]) for n,v in rest.items() for i in range(4) for j in range(4))
food_original=json.loads((P/(prefix+'source-food-round01.json')).read_text());food_current=food_signature(coll)
food_unchanged=food_current==food_original
actions={}
for name,expected in recipe['originalActionSHA256'].items():
 a=bpy.data.actions[name]
 h=hashlib.sha256(json.dumps([(c.data_path,c.array_index,[(list(k.co),k.interpolation) for k in c.keyframe_points]) for c in native._fcurves(a)],sort_keys=True).encode()).hexdigest()
 actions[name]={'sha256':h,'sourceSHA256':expected,'unchanged':h==expected}
render_rows=[];current_contacts=[];topologies={};failures=[];max_bone=max_palm=max_foot=max_prop=max_dish=max_knife=0.;start=time.time()
for clip in rig['clips']:
 for direction in ['N','E','S','W']:
  for idx in range(12):
   native.apply_clip(asset,rig,clip,idx+1,direction,sc);dg=bpy.context.evaluated_depsgraph_get();ref=reference[(clip,direction,idx)]
   ct=contacts(coll,root,arm,dg);ct.update(clip=clip,direction=direction,index=idx)
   bone_error=max(abs(ct['bones'][n]['matrix'][i][j]-ref['bones'][n]['matrix'][i][j]) for n in ct['bones'] for i in range(4) for j in range(4));max_bone=max(max_bone,bone_error)
   palm_error=max((Vector(ct['palms'][s])-Vector(ref['palms'][s])).length for s in ['L','R']);max_palm=max(max_palm,palm_error)
   foot_error=max(abs(ct['feet'][s]['bounds'][i][j]-ref['feet'][s]['bounds'][i][j]) for s in ['L','R'] for i in range(3) for j in range(2));max_foot=max(max_foot,foot_error)
   prop_error=max(abs(ct['props'][n]['matrix'][i][j]-ref['props'][n]['matrix'][i][j]) for n in ct['props'] for i in range(4) for j in range(4));max_prop=max(max_prop,prop_error)
   dish_error=(Vector(ct['dishToPalmMidpointVector'])-Vector(ref['dishToPalmMidpointVector'])).length;max_dish=max(max_dish,dish_error)
   if clip=='work':max_knife=max(max_knife,ct['knifeToRightPalmError'])
   visibility={n:v['hide']==ref['props'][n]['hide'] for n,v in ct['props'].items()}
   ct['sourceComparison']={'boneMatrixError':bone_error,'palmCentroidError':palm_error,'footBoundsError':foot_error,'propMatrixError':prop_error,'dishPalmVectorError':dish_error,'visibilityEqual':all(visibility.values())};current_contacts.append(ct)
   gs={o.name:geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name}
   actor={n:g for n,g in gs.items() if '__knife_' not in n}
   bounds=[[min(v['bounds'][i][0] for v in actor.values()),max(v['bounds'][i][1] for v in actor.values())] for i in range(3)]
   for name,g in gs.items():
    topo=(g['vertices'],g['edges'],g['polygons']);prior=topologies.setdefault(name,topo)
    if topo!=prior:failures.append({'topologyChanged':name,'clip':clip,'direction':direction,'index':idx})
    if g['nonfiniteVertices'] or g['nonfiniteNormals']:failures.append({'nonfinite':name,'index':idx})
   expected_rotation={'N':180,'E':90,'S':0,'W':-90}[direction]
   if abs(math.degrees(root.rotation_euler.z)-expected_rotation)>.0001:failures.append({'facingError':[clip,direction,idx]})
   if not all(visibility.values()):failures.append({'visibilityChanged':[clip,direction,idx]})
   frame=OUT/'frames'/(clip+'-'+direction)/(f'{idx:03d}.png');frame.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(frame)
   bpy.ops.render.render(write_still=True)
   row={'clip':clip,'direction':direction,'index':idx,'path':str(frame.relative_to(BASE)),'sha256':sha(frame),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'rootPixel':px((0,0,0)),'cameraMatrix':[list(r) for r in sc.camera.matrix_world],'cameraProjectionMatrix':[list(r) for r in sc.camera.calc_matrix_camera(dg,x=384,y=640,scale_x=1,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'actorBounds':bounds,'geometry':gs,'contactComparison':ct['sourceComparison']};render_rows.append(row)
   (OUT/'progress.json').write_text(json.dumps({'done':len(render_rows),'total':96 if runtime else 192,'current':[clip,direction,idx],'seconds':time.time()-start}));print('FRAME',len(render_rows),clip,direction,idx,flush=True)
(OUT/'native-frames.json').write_text(json.dumps(render_rows,separators=(',',':')))
(OUT/'evaluated-contacts.json').write_text(json.dumps(current_contacts,separators=(',',':')))
loops={}
for clip,record in rig['clips'].items():
 rows=[]
 for f in ([1,13] if record.get('loop') else [1,12]):
  native.apply_clip(asset,rig,clip,f,'S',sc);rows.append(contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get()))
 err=max(abs(rows[0]['bones'][n]['matrix'][i][j]-rows[1]['bones'][n]['matrix'][i][j]) for n in rows[0]['bones'] for i in range(4) for j in range(4))
 loops[clip]={'loop':record.get('loop'),'closingFrame':13 if record.get('loop') else None,'boneEndpointDifference':err,'frameOrder':list(range(12)),'fps':12,'sourceActionOwners':record['actions']}
images=[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.type!='RENDER_RESULT']
weights={}
for o in coll.all_objects:
 if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers):
  weights[o.name]={'vertices':len(o.data.vertices),'unweighted':sum(not v.groups for v in o.data.vertices),'nonUnitWeights':sum(abs(sum(g.weight for g in v.groups)-1)>1e-4 for v in o.data.vertices)}
camera_source=json.loads((BASE/'inputs/source-camera.json').read_text())['camera']
camera_world_error=max(abs(sc.camera.matrix_world[i][j]-camera_source['worldMatrix'][i][j]) for i in range(4) for j in range(4))
projection=sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=1,scale_y=1)
camera_projection_error=max(abs(projection[i][j]-camera_source['projectionMatrix'][i][j]) for i in range(4) for j in range(4))
ok=not failures and rest_error<1e-7 and max_bone<1e-6 and max_palm<.0001 and max_foot<.002 and max_prop<1e-6 and food_unchanged and all(a['unchanged'] for a in actions.values()) and camera_world_error<1e-6 and camera_projection_error<1e-6 and not bpy.data.libraries and all(im['packed'] for im in images) and all(v['unweighted']==0 and v['nonUnitWeights']==0 for v in weights.values())
validation={'asset':'chef-omar','round':1,'runtimeVariant':runtime,'status':'Native technical audit; independent visual verdict pending','ok':ok,'blenderVersion':bpy.app.version_string,'source':str(source_path.relative_to(BASE)),'sourceSHA256':sha(source_path),'renderCount':len(render_rows),'renderManifest':str((OUT/'native-frames.json').relative_to(BASE)),'clipFacingCount':len(rig['clips'])*4,'fps':12,'nativeStateFrames':12,'camera':recipe['camera'],'cameraWorldMaxDifferenceToOriginal':camera_world_error,'cameraProjectionMaxDifferenceToOriginal':camera_projection_error,'restMatrixMaxDifference':rest_error,'boneMatrixMaxDifferenceToOriginal':max_bone,'palmCentroidMaxDifferenceToOriginalWorld':max_palm,'footBoundsMaxDifferenceToOriginalWorld':max_foot,'attachmentMatrixMaxDifferenceToOriginal':max_prop,'dishPalmRelativeVectorMaxDifferenceToOriginal':max_dish,'workKnifeToActualPalmMaxWorldError':max_knife if not runtime else None,'contactToleranceWorld':.002,'contactManifest':str((OUT/'evaluated-contacts.json').relative_to(BASE)),'topologyInvariantPerObject':topologies,'topologyFailures':failures,'weights':weights,'actions':actions,'foodGeometryUVDriversAndPackedBytesUnchanged':food_unchanged,'food':food_current,'loops':loops,'images':images,'linkedLibraries':[l.filepath for l in bpy.data.libraries],'renderSettings':recipe['renderer'],'representation':{'chef':'native3D','knife':'native3D','heldDish':'separate packed exact original2D with original action and cancellation/depth drivers'},'limits':['All contacts are compared to actual evaluated source frames; source camera-facing dish behavior remains','Visual review of occlusion, garment finish and temporal quality is reserved to independent judge']}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2))
print('COMPLETE',json.dumps({k:validation[k] for k in ['ok','renderCount','cameraWorldMaxDifferenceToOriginal','cameraProjectionMaxDifferenceToOriginal','restMatrixMaxDifference','boneMatrixMaxDifferenceToOriginal','palmCentroidMaxDifferenceToOriginalWorld','footBoundsMaxDifferenceToOriginalWorld','attachmentMatrixMaxDifferenceToOriginal']}),flush=True)
