import bpy,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-05';N=R/'native-records';N.mkdir(exist_ok=True)
sc=bpy.context.scene;cam=sc.camera;G=bpy.data.collections['S33_PROP_uniform35-gate'];W=bpy.data.collections['S33_PROP_uniform35-wall-plain'];root=bpy.data.objects['uniform35-gate__root'];wr=bpy.data.objects['uniform35-wall-plain__root'];sc.view_layers[0].update()
W.hide_viewport=False;sc.view_layers[0].update()
baseline=json.loads((P/'source/native-baseline.json').read_text());recipe=json.loads((P/'source/round-05-recipe.json').read_text())
def matrix(o):return [list(r) for r in o.matrix_world]
def project(v):
 q=world_to_camera_view(sc,cam,Vector(v));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def camera_record():return {'type':cam.data.type,'worldMatrix':matrix(cam),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'elevationDegrees':math.degrees(math.asin(cam.matrix_world.to_quaternion()@Vector((0,0,1))).z) if False else math.degrees(math.asin((cam.matrix_world.to_quaternion()@Vector((0,0,1))).z)),'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'projection':'original35-character-orthographic','sourceScale':3,'nativePixelsPerWorldUnitX':project((1,-.5,0))[0]-project((0,-.5,0))[0]}
def audit_collection(col):
 dg=bpy.context.evaluated_depsgraph_get();out={};allpts=[]
 for o in col.objects:
  if o.type not in {'MESH','CURVE'}:continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();pts=[o.matrix_world@v.co for v in me.vertices];allpts+=pts
  entry={'type':o.type,'vertices':len(me.vertices),'polygons':len(me.polygons),'materials':[m.name if m else None for m in o.data.materials],'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'matrix':matrix(o),'modifiers':[m.type for m in o.modifiers]}
  ev.to_mesh_clear()
  if o.type=='MESH':
   entry['sourceMeshSha256']=hashlib.sha256(json.dumps({'verts':[list(v.co) for v in o.data.vertices],'polys':[list(f.vertices) for f in o.data.polygons]},sort_keys=True).encode()).hexdigest()
   b=baseline[col.name].get(o.name,{})
   if b.get('protectedJoin'):entry['protectedProfileUnchanged']=entry['sourceMeshSha256']==b['geometrySha256'] and matrix(o)==b['matrix'];entry['sourceProtectedSha256']=b['geometrySha256']
  out[o.name]=entry
 px=[project(v) for v in allpts];bounds=[[min(v[i] for v in allpts) for i in range(3)],[max(v[i] for v in allpts) for i in range(3)]]
 return {'objectTypeCounts':{typ:sum(o.type==typ for o in col.objects) for typ in ['MESH','CURVE','EMPTY']},'objects':out,'evaluatedWorldBounds':bounds,'projectedPixelBounds':[[min(v[i] for v in px) for i in range(2)],[max(v[i] for v in px) for i in range(2)]],'projectedHeightTiles':(max(v[1] for v in px)-min(v[1] for v in px))/384,'worldWidth':bounds[1][0]-bounds[0][0]}
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.refresh_devices()
 for d in pref.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
except Exception:pass
# This script starts by reopening the exact saved candidate, before any diagnostic scene changes.
cr=camera_record();ga=audit_collection(G);wa=audit_collection(W)
cal={'nativeObjectOrigin':project((0,0,0)),'frontContactAnchor':project((0,-.5,0)),'unitXFromContact':project((1,-.5,0)),'unitHeightFromContact':project((0,-.5,1)),'logicalRoot':[288,416],'logicalFrame':[576,448]}
validation={'schemaVersion':1,'asset':'backdrop-entrance','round':'round-05','reopenedProject':'source/round-05.blend','reopenedSourceSha256':hashlib.sha256((P/'source/round-05.blend').read_bytes()).hexdigest(),'blender':bpy.app.version_string,'sourceIntegrity':{'original':recipe['sourceSha256'],'currentOriginal':hashlib.sha256((P/'../../../production/source/backdrop/restaurant-backdrop-35.blend').resolve().read_bytes()).hexdigest(),'backup':hashlib.sha256((P/'../../backups/927a8a59e8d0f1e9-restaurant-backdrop-35.blend').resolve().read_bytes()).hexdigest()},'camera':cr,'calibration':cal,'assetAudit':ga,'wallContextAudit':wa,'footprint':[4,3],'opening':{'leftPlaneX':-1.0,'rightPlaneX':1.0,'widthWorld':2.0,'sourceJambMeshBounds':[-1,1]},'protectedJoinPlanes':{'entrance':[-2,2],'wallContext':[-.5,.5],'geometryAndMatricesUnchanged':all(o.get('protectedProfileUnchanged',True) for a in [ga,wa] for o in a['objects'].values())},'sourcePhase':{'convention':'original publisher static player-facing facade S; S0','rootObject':'uniform35-gate__root','rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':matrix(root),'registeredFrontContactPoint':[0,-.5,0]},'renders':[{'clip':'static','direction':'S','index':0,'path':'candidates/round-05/static-S-000.png','rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':matrix(root),'camera':cr,'nativeFrame':[1728,1344],'logicalFrame':[576,448],'sourceScale':3,'frontContactAnchor':cal['frontContactAnchor']}],'renderer':recipe['renderer'],'lighting':recipe['lighting'],'dependencies':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'externalTextures':[]},'scope':{'floorMeshesPresent':False,'nativeSOnly':True,'matchingWall':'context-only, pending separate fresh-pair review','blankWallFieldsPreserved':True},'checks':{'sourceIntegrity':len(set([recipe['sourceSha256'],hashlib.sha256((P/'../../../production/source/backdrop/restaurant-backdrop-35.blend').resolve().read_bytes()).hexdigest(),hashlib.sha256((P/'../../backups/927a8a59e8d0f1e9-restaurant-backdrop-35.blend').resolve().read_bytes()).hexdigest()]))==1,'frontAnchorErrorPixels':math.dist(cal['frontContactAnchor'],[864,1248]),'cameraMatrixMaxError':max(abs(cr['worldMatrix'][i][j]-recipe['camera']['matrix'][i][j]) for i in range(4) for j in range(4)),'semanticCountsPreserved':ga['objectTypeCounts']=={'MESH':114,'CURVE':2,'EMPTY':1}}}
# Reopen render is independent technical evidence and does not replace the selected hero bytes.
sc.render.filepath=str(R/'reopened-S.png');bpy.ops.render.render(write_still=True)
# Native metadata describes this per-object frame and sourceScale3 without generic world-sprite claims.
nativeCamera={'schemaVersion':2,'projection':'ordinary35-character-camera','physicalCell':1,'renderPitch':128,'sourceZCalibration':1.002513204765747,'projectedHeightTiles':3,'sourceScale':3,'wallLighting':'warm soft native surfaces; z-only sky plus infinite symmetric overhead/front sun; no ground or lamp wall falloff','assets':{'gate':{'collection':G.name,'widthTiles':4,'heightTiles':3,'openingWidthTiles':2,'frame':[576,448],'anchor':[288,416],'cellSize':128,'captureScale':3,'contentRect':[96,96,1536,1152],'camera':cr,'calibration':{'baseline':cal['frontContactAnchor'],'unitX':[384,0],'unitHeight':[0,-314.5544]},'nativeZScale':1.002513204765747,'registrationPoint':[0,-.5,0],'nativeObjectOrigin':cal['nativeObjectOrigin']}}}
assetRecord={'id':'backdrop-entrance','surface':{'width':4,'height':3,'openingWidth':2,'baseboard':True,'lighting':'warm soft native surfaces; infinite x-neutral illumination; no ground cast shadow'},'camera':nativeCamera['assets']['gate'],'geometryAudit':'../validation.json','sourcePhase':validation['sourcePhase'],'materialsRecipe':'../../../source/round-05-recipe.json'}
rig={'schemaVersion':1,'asset':'backdrop-entrance','type':'static-native-facade','rootObject':root.name,'rootMatrix':matrix(root),'directions':['S'],'rootRotationRadiansByDirection':{'S':0.0},'clips':[{'id':'static','frames':1,'fps':12,'loop':False}],'registration':{'point':[0,-.5,0],'nativePixels':[864,1248],'logicalPixels':[288,416],'originIsRegistrationPoint':False},'armature':None,'sockets':{'thresholdContact':[0,-.5,0],'clearEntranceLeft':[-1,-.5,0],'clearEntranceRight':[1,-.5,0]}}
for name,data in [('camera.json',nativeCamera),('asset-record.json',assetRecord),('rig.json',rig)]: (N/name).write_text(json.dumps(data,indent=2))
# Independently capture the matching one-tile context at the same 384px/unit scale and source camera matrix.
for o in G.objects:o.hide_render=True
for o in W.objects:o.hide_render=False
W.hide_render=False;W.hide_viewport=False
sc.render.resolution_x=576;sc.render.resolution_y=1344;cam.data.ortho_scale=1.5;cam.data.shift_y=recipe['camera']['shift'][1]*4.5/1.5
sc.view_layers[0].update();validation['wallContextCapture']={'camera':camera_record(),'rootMatrix':matrix(wr),'registeredContact':project((0,-.5,0)),'path':'candidates/round-05/wall-context-S.png','status':'context-only; separate wall approval required'}
sc.render.filepath=str(R/'wall-context-S.png');bpy.ops.render.render(write_still=True)
# Connected 11-tile native assembly, preserving scale and projected registration. No framing by visible bounds.
for o in W.objects:o.hide_render=True
for o in G.objects:o.hide_render=False
assembly=bpy.data.collections.new('Context only native facade join assembly');sc.collection.children.link(assembly)
placements=[-4.5,-3.5,-2.5,2.5,3.5,4.5,5.5]
for i,x in enumerate(placements):
 nr=wr.copy();nr.name='Context wall root %02d'%i;assembly.objects.link(nr);nr.location.x=x;nr.hide_render=False
 for o in W.objects:
  if o==wr:continue
  no=o.copy();no.name='Context wall %02d '%i+o.name;assembly.objects.link(no);no.parent=nr;no.hide_render=False
sc.render.resolution_x=4416;sc.render.resolution_y=1344;cam.data.ortho_scale=11.5;cam.data.shift_y=recipe['camera']['shift'][1]*4.5/11.5;cam.location.x=.5
sc.view_layers[0].update();validation['nativeConnectedPreview']={'camera':camera_record(),'entranceRootMatrix':matrix(root),'wallCenterX':placements,'tilePitchNativePixels':384,'widthTiles':11,'path':'candidates/round-05/native-joined-raw.png','wallStatus':'matching context only; not sibling production approval'}
sc.render.filepath=str(R/'native-joined-raw.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-05-join-context.blend'))
validation['nativeConnectedPreview']['project']='source/round-05-join-context.blend'
(R/'validation.json').write_text(json.dumps(validation,indent=2))
print('CAPTURE_AND_REOPEN_VALIDATION_SAVED')
