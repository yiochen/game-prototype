import bpy,json,math,sys,hashlib,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).parent;BASE=P.parent;OUT=BASE/'candidates/round-02';sys.path.insert(0,str(P));import native_actions_round02 as native
from audit_common_round02 import contacts,geometry
rig=json.loads((P/'rig-round02.json').read_text());sc=bpy.data.scenes['Ellis warm soft round02'];bpy.context.window.scene=sc;coll=bpy.data.collections['S33_CHARACTER_chef_ellis.001'];root=bpy.data.objects['chef_ellis__ground_root.001'];arm=bpy.data.objects['chef_ellis__armature.001'];asset={'collection':coll,'root':root,'armature':arm}
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception as e:print('METAL',e)
original=json.loads((P/'source-contacts-round02.json').read_text());reference={(r['clip'],r['direction'],r['index']):r for r in original}
rest=json.loads((P/'source-rest-round02.json').read_text());rest_error=max(abs(arm.data.bones[n].matrix_local[i][j]-v['matrix'][i][j]) for n,v in rest.items() for i in range(4) for j in range(4))
render_rows=[];current_contacts=[];topologies={};failures=[];max_delta=0.;max_palm=0.;max_foot=0.;max_dish=0.;max_knife=0.;start=time.time()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def px(v):p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
for clip in ['idle','work','hold','load']:
 for direction in ['N','E','S','W']:
  for idx in range(12):
   native.apply_clip(asset,rig,clip,idx+1,direction,sc);dg=bpy.context.evaluated_depsgraph_get();ref=reference[(clip,direction,idx)];ct=contacts(coll,root,arm,dg);ct.update(clip=clip,direction=direction,index=idx)
   pose_error=max(abs(ct['bones'][n]['matrix'][i][j]-ref['bones'][n]['matrix'][i][j]) for n in ct['bones'] for i in range(4) for j in range(4));max_delta=max(max_delta,pose_error)
   palm_error=max((Vector(ct['palms'][s])-Vector(ref['palms'][s])).length for s in ['L','R']);max_palm=max(max_palm,palm_error)
   foot_error=max(abs(ct['feet'][s]['bounds'][i][j]-ref['feet'][s]['bounds'][i][j]) for s in ['L','R'] for i in range(3) for j in range(2));max_foot=max(max_foot,foot_error)
   prop_error=max(abs(ct['props'][n]['matrix'][i][j]-ref['props'][n]['matrix'][i][j]) for n in ct['props'] for i in range(4) for j in range(4));max_dish=max(max_dish,prop_error)
   if clip=='work':max_knife=max(max_knife,ct['knifeToRightPalmError'])
   ct['sourceComparison']={'boneMatrixError':pose_error,'palmCentroidError':palm_error,'footBoundsError':foot_error,'propMatrixError':prop_error};current_contacts.append(ct)
   gs={o.name:geometry(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name};world_bounds=[[min(v['bounds'][i][0] for n,v in gs.items() if '__knife_' not in n),max(v['bounds'][i][1] for n,v in gs.items() if '__knife_' not in n)] for i in range(3)]
   for name,g in gs.items():
    topo=(g['vertices'],g['edges'],g['polygons']);prior=topologies.setdefault(name,topo)
    if topo!=prior:failures.append({'topologyChanged':name,'clip':clip,'direction':direction,'index':idx})
    if g['nonfiniteVertices'] or g['nonfiniteNormals']:failures.append({'nonfinite':name,'index':idx})
   frame=OUT/'frames'/(clip+'-'+direction)/(f'{idx:03d}.png');frame.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(frame)
   if '--audit-only' not in sys.argv:bpy.ops.render.render(write_still=True)
   row={'clip':clip,'direction':direction,'index':idx,'path':str(frame.relative_to(BASE)),'sha256':sha(frame),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'rootPixel':px((0,0,0)),'cameraMatrix':[list(r) for r in sc.camera.matrix_world],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'nativeBounds':world_bounds,'geometry':gs,'contactComparison':ct['sourceComparison'],'sourceBodyBounds':ref['bodyBounds'],'physicalBodyExcludes':'display-only packed2D salmon and knife separately audited','dishVisibility':{n:v['hide'] for n,v in ct['props'].items() if '__held_' in n},'knifeVisibility':{n:v['hide'] for n,v in ct['props'].items() if '__knife_' in n}};render_rows.append(row)
   (OUT/'progress.json').write_text(json.dumps({'done':len(render_rows),'total':192,'current':[clip,direction,idx],'seconds':time.time()-start}));print('FRAME',len(render_rows),clip,direction,idx,flush=True)
(OUT/'native-frames.json').write_text(json.dumps(render_rows,separators=(',',':')));(OUT/'evaluated-contacts.json').write_text(json.dumps(current_contacts,separators=(',',':')))
# Loop behavior from exact native key1/key13 evaluated matrices; load retains native nonloop endpoint.
loops={}
for clip in rig['clips']:
 rows=[]
 for f in ([1,13] if rig['clips'][clip].get('loop') else [1,12]):
  native.apply_clip(asset,rig,clip,f,'S',sc);rows.append(contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get()))
 err=max(abs(rows[0]['bones'][n]['matrix'][i][j]-rows[1]['bones'][n]['matrix'][i][j]) for n in rows[0]['bones'] for i in range(4) for j in range(4));loops[clip]={'loop':rig['clips'][clip].get('loop'),'closingFrame':13 if rig['clips'][clip].get('loop') else None,'boneEndpointDifference':err,'preservedSourceActionOwners':rig['clips'][clip]['actions']}
images=[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'packedSHA256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images if im.type!='RENDER_RESULT']
validation={'asset':'chef-ellis','round':2,'status':'technical audit complete; independent visual verdict pending','ok':not failures and rest_error<1e-7 and max_delta<1e-6 and max_palm<.0001 and max_foot<.001 and max_dish<1e-6,'blenderVersion':bpy.app.version_string,'source':str(P/'round-02.blend'),'sourceSHA256':sha(P/'round-02.blend'),'renderCount':len(render_rows),'renderManifest':'native-frames.json','clipCount':16,'fps':12,'nativeStateFrames':12,'camera':json.loads((P/'recipe-round02.json').read_text())['camera'],'restMatrixMaxDifference':rest_error,'boneMatrixMaxDifferenceToOriginal':max_delta,'palmCentroidMaxDifferenceToOriginalWorld':max_palm,'footBoundsMaxDifferenceToOriginalWorld':max_foot,'attachmentMatrixMaxDifferenceToOriginal':max_dish,'workKnifeToActualPalmMaxWorldError':max_knife,'contactToleranceWorld':.001,'contactManifest':'evaluated-contacts.json','topologyInvariantPerObject':topologies,'topologyFailures':failures,'loops':loops,'images':images,'facingConvention':{'S':0,'E':90,'N':180,'W':-90},'linkedLibraries':[l.filepath for l in bpy.data.libraries],'renderSettings':json.loads((P/'recipe-round02.json').read_text())['renderer'],'representation':{'chef':'native3D','knife':'native3D','heldDish':'separate packed original2D with original action and cancellation/depth drivers'},'limits':['Natural source-consistent north body occlusion is retained; evaluated attachment matrices checked directly','No gameplay serving behavior authored or altered; exact original baked load action retained']}
(OUT/'validation.json').write_text(json.dumps(validation,indent=2));print('COMPLETE',json.dumps({k:validation[k] for k in ['ok','renderCount','restMatrixMaxDifference','boneMatrixMaxDifferenceToOriginal','palmCentroidMaxDifferenceToOriginalWorld','footBoundsMaxDifferenceToOriginalWorld','attachmentMatrixMaxDifferenceToOriginal','workKnifeToActualPalmMaxWorldError']}),flush=True)
