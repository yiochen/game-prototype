import bpy,sys,json,pathlib,math,hashlib,gzip,importlib.util,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=pathlib.Path(__file__).resolve().parent;OBJ=HERE.parent;RT='--runtime' in sys.argv;FULL='--full' in sys.argv
OUT=OBJ/'candidates/round-03';OUT=OUT/'runtimeVariants' if RT else OUT;OUT.mkdir(parents=True,exist_ok=True)
rigpath=OBJ/('inputs/runtime-variants/export/source/customer-rosa/rig.json' if RT else 'inputs/source-rig.json');rig=json.loads(rigpath.read_text());baseline=json.loads((OBJ/('reviews/source-contract-runtime.json' if RT else 'reviews/source-contract-main.json')).read_text());old=json.load(gzip.open(OBJ/('reviews/source-samples-runtime.json.gz' if RT else 'reviews/source-samples-main.json.gz')))
brief=json.loads((OBJ/'brief.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=root.users_collection[0];arm=next(o for o in col.all_objects if o.type=='ARMATURE');sc=bpy.context.scene;cam=sc.camera;plane=next(o for o in col.all_objects if '__held_' in o.name and o.type=='MESH');food=plane.parent
spec=importlib.util.spec_from_file_location('rosa_native',HERE/'resources/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native);asset={'root':root,'collection':col,'armature':arm}
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
col.hide_viewport=False;col.hide_render=False;arm.hide_viewport=False;arm.hide_set(False);sc.view_layers[0].update()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def vec(v):return [round(float(x),8) for x in v]
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def actionhash(a):return digest([(fc.data_path,fc.array_index,[(vec(k.co),k.interpolation) for k in fc.keyframe_points]) for fc in native._fcurves(a)])
def px(v):p=world_to_camera_view(sc,cam,Vector(v));return [p.x*384,(1-p.y)*640]
def bounds(o,dep):
 e=o.evaluated_get(dep);m=e.to_mesh();a=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',a);a=a.reshape(-1,3);mx=np.array(e.matrix_world);a=a@mx[:3,:3].T+mx[:3,3];e.to_mesh_clear();return [a.min(axis=0).tolist(),a.max(axis=0).tolist()]
foodid='dish-salmon' if RT else 'dish-cucumber';fm=next(m for m in json.loads((OBJ/'reviews/semantic-food-mapping.json').read_text()) if m['food']==foodid);mp=next(m for m in fm['thresholds'] if m['alphaThreshold']==128)
records=[];contacterr=0;fooderr=0;cornererr=0;visibility=True;clipbounds={};loopchecks=[];actions=[]
for clip,c in rig['clips'].items():
 cid=clip.replace('_','-');oldframes={(f['facing'],f['frame']):f for f in old[clip]};cb=[[1e9]*3,[-1e9]*3]
 for t in c['actions']:
  ah=actionhash(bpy.data.actions[t['action']]);expected=next(a['sha256'] for a in baseline['clips'][clip]['actions'] if a['action']==t['action']);actions.append({'clip':cid,'owner':t['ownerName'],'action':t['action'],'sha256':ah,'sourceEqual':ah==expected})
 for direction in ['N','E','S','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,clip,f,direction,sc);dep=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dep);bf=oldframes[direction,f]
   bones={n:vec(ae.matrix_world@ae.pose.bones[n].head) for n in bf['bones']}
   contacts={'ground':vec(root.matrix_world.translation),'seat':vec(ae.matrix_world@ae.pose.bones['pelvis'].head-root.matrix_world.to_3x3()@Vector((0,0,float(root.get('seat_pelvis_offset',.08))))),'mouth':vec(ae.matrix_world@ae.pose.bones['head'].matrix@ae.pose.bones['head'].bone.matrix_local.inverted()@Vector((0,-.255,.543)))}
   ce=max([abs(a-b) for typ,val in [('bones',bones),('contacts',contacts)] for k in val for a,b in zip(val[k],bf[typ][k])]);contacterr=max(contacterr,ce);fr=vec(food.matrix_world.translation);fe=max(abs(a-b) for a,b in zip(fr,bf['foodRoot']));fooderr=max(fooderr,fe)
   corners=[px(plane.matrix_world@v.co) for v in plane.data.vertices];oldp=bf['projectedCorners'];xc=(oldp[0][0]+oldp[1][0])/2+mp['proposedFullUVCenterOffsetXWorld']*256;bot=oldp[0][1]-mp['proposedFullUVBottomOffsetWorld']*256;w,h=mp['proposedFullUVQuadWorld'];expected=[[xc-w*128,bot],[xc+w*128,bot],[xc+w*128,bot-h*256],[xc-w*128,bot-h*256]];pe=max(abs(a-b) for co,ex in zip(corners,expected) for a,b in zip(co,ex));cornererr=max(cornererr,pe)
   visibility=visibility and (not plane.hide_render)==bf['foodVisible'];bs=[bounds(o,dep) for o in col.all_objects if o.type=='MESH' and not o.hide_render and o!=plane and '__knife_' not in o.name];env=[[min(v[0][i] for v in bs) for i in range(3)],[max(v[1][i] for v in bs) for i in range(3)]]
   for i in range(3):cb[0][i]=min(cb[0][i],env[0][i]);cb[1][i]=max(cb[1][i],env[1][i])
   records.append({'clip':cid,'direction':direction,'frame':f-1,'bones':bones,'contacts':contacts,'bounds':env,'sourceContactError':ce,'foodRoot':fr,'sourceFoodRootError':fe,'foodVisible':not plane.hide_render,'projectedFoodCorners':corners,'semanticProjectionErrorPx':pe})
 clipbounds[cid]=cb
 # Check every original full matrix at loop closure and retain nonloop endpoints.
 def pose():return [float(v) for b in arm.evaluated_get(bpy.context.evaluated_depsgraph_get()).pose.bones for row in b.matrix for v in row]
 native.apply_clip(asset,rig,clip,1,'S',sc);a=pose();endpoint=13 if c['loop'] else 12;native.apply_clip(asset,rig,clip,endpoint,'S',sc);z=pose();loopchecks.append({'clip':cid,'loop':c['loop'],'endpoint':endpoint,'maximumMatrixDifference':max(abs(x-y) for x,y in zip(a,z))})
rest=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':vec(b.head_local),'tail':vec(b.tail_local),'deform':b.use_deform} for b in arm.data.bones]
imgs=[i for i in bpy.data.images if i.source in ['FILE','TILED']];texture=[{'name':i.name,'size':list(i.size),'packed':bool(i.packed_file),'sha256':hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else None} for i in imgs];uv=[list(x.uv) for x in plane.data.uv_layers.active.data]
envlimits=brief['constraints']['functionalGeometryEnvelope'];envelope=[]
for clip,b in clipbounds.items():
 z=envlimits['perClipBodyZWorld'][clip];envelope.append({'clip':clip,'bounds':b,'xyPassed':max(abs(b[j][i]) for j in [0,1] for i in [0,1])<=.50001,'zPassed':b[0][2]>=z[0]-1e-5 and b[1][2]<=z[1]+1e-5,'sourceZEnvelope':z})
checks={'contactTrajectory':contacterr<1e-6,'foodRootTrajectory':fooderr<1e-6,'semanticQuadProjection':cornererr<.001,'visibility':visibility,'restSkeleton':rest==baseline['restBones'],'actions':all(x['sourceEqual'] for x in actions),'loopClosure':all(x['maximumMatrixDifference']<1e-5 for x in loopchecks if x['loop']),'bodyEnvelope':all(x['xyPassed'] and x['zPassed'] for x in envelope),'foodBytes':len(texture)==1 and texture[0]['sha256']==brief['foodDependencies'][foodid]['sha256'],'fullUV':sorted(uv)==sorted([[0,0],[1,0],[1,1],[0,1]]),'rootScale':list(root.scale)==[1.25]*3,'registeredCamera':max(abs(a-b) for a,b in zip(px((0,0,0)),[192,496]))<.001 and cam.data.ortho_scale==1.5,'frameSize':[sc.render.resolution_x,sc.render.resolution_y]==[384,640]}
(OUT/'measurements.json.gz').write_bytes(gzip.compress(json.dumps(records,separators=(',',':')).encode(),mtime=0))
audit={'savedReopenedSource':str(pathlib.Path(bpy.data.filepath).relative_to(OBJ)),'projectSHA256':sha(bpy.data.filepath),'blender':bpy.app.version_string,'frozenBriefSHA256':sha(OBJ/'brief.json'),'sampleCount':len(records),'checks':checks,'allChecksPassed':all(checks.values()),'maximumErrors':{'contactWorld':contacterr,'foodRootWorld':fooderr,'semanticFoodProjectionPx':cornererr},'camera':{'matrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'rootPx':px((0,0,0)),'nativeFrame':[384,640],'fps':12,'cardinals':{'S':0,'E':90,'N':180,'W':-90}},'rig':{'root':root.name,'armature':arm.name,'scale':list(root.scale),'rest':rest,'actions':actions,'loopClosure':loopchecks},'envelope':envelope,'food':{'id':foodid,'textures':texture,'uv':uv,'singleFixedMapping':mp,'depthWorld':float(plane.get('camera_ray_depth_bias_world_cells')),'depthChanged':False,'representation':'Canonical 2D raster bound to original animated food root, full UV; native body is 3D'},'measurements':{'path':str((OUT/'measurements.json.gz').relative_to(OBJ)),'sha256':sha(OUT/'measurements.json.gz')},'physicalBoundsPolicy':'Visible native body excludes canonical camera-ray food display card and hidden utensils; body coordinates/topology freely refined inside functional envelope.'}
(OUT/'validation.json').write_text(json.dumps(audit,indent=2)+'\n');print('AUDIT',json.dumps({'checks':checks,'maximumErrors':audit['maximumErrors'],'envelope':envelope}),flush=True)
if not all(checks.values()):raise RuntimeError('Fix failed native contract before captures')
for r in records:
 if not FULL and not (r['frame'] in [0,6] and r['clip'] in ['walk','seated-wait','eat','happy','eat-salmon','seated-wait-empty']):continue
 clip=next(c for c in rig['clips'] if c.replace('_','-')==r['clip']);native.apply_clip(asset,rig,clip,r['frame']+1,r['direction'],sc);path=OUT/('frames' if FULL else 'preflight')/(r['clip']+'-'+r['direction'])/(f"{r['frame']:03d}.png");path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 print('CAPTURE',r['clip'],r['direction'],r['frame'],flush=True)
(OUT/'capture-status.json').write_text(json.dumps({'state':'complete','full':FULL,'count':len(records) if FULL else 'preflight','sourceSHA256':sha(bpy.data.filepath)},indent=2)+'\n')
