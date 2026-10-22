"""Measure and capture the clean saved round02 source; never save pose changes."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;B=P.parent;O=B/'candidates/round-02';O.mkdir(exist_ok=True)
s=bpy.context.scene;cam=s.camera;c=bpy.data.collections['S33_PROP_decor-background-wreck.001'];root=bpy.data.objects['decor-background-wreck__root.001'];owned=list(c.all_objects)
project=Path(bpy.data.filepath);source_sha=hashlib.sha256(project.read_bytes()).hexdigest()
def mat(m):return [list(r) for r in m]
def px(v):
 p=world_to_camera_view(s,cam,Vector(v));return [p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y]
def bounds(vs):return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)]
def sample():
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();pts=[];meshes=[]
 for o in owned:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];pts+=vs
  meshes.append({'object':o.name,'matrixWorld':mat(ev.matrix_world),'vertices':len(me.vertices),'polygons':len(me.polygons),'bounds':bounds(vs),'geometrySHA256':hashlib.sha256(json.dumps({'verts':[list(v) for v in vs],'faces':[list(f.vertices) for f in me.polygons]},sort_keys=True).encode()).hexdigest()});ev.to_mesh_clear()
 return pts,meshes
records=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(degrees);s.frame_set(1);bpy.context.view_layer.update();pts,meshes=sample();dg=bpy.context.evaluated_depsgraph_get()
 path=O/'native/static'/direction/'000.png';path.parent.mkdir(parents=True,exist_ok=True);s.render.filepath=str(path)
 r={'direction':direction,'clip':'static','index':0,'nativeFrame':1,'sourceProject':'source/round-02.blend','sourceProjectSHA256':source_sha,'rootObject':root.name,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':mat(root.matrix_world),'cameraWorldMatrix':mat(cam.matrix_world),'projectionMatrix':mat(cam.calc_matrix_camera(dg,x=768,y=1408,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)),'nativeFrameSize':[768,1408],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'rootPixels':px((0,0,0)),'unitXPixels':px((1,0,0)),'unitDepthPixels':px((0,-1,0)),'unitHeightPixels':px((0,0,1)),'evaluatedBounds':bounds(pts),'meshes':meshes,'path':str(path.relative_to(B)),'engine':s.render.engine,'filterSize':s.render.filter_size,'samples':s.cycles.samples}
 bpy.ops.render.render(write_still=True);r['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();records.append(r)

# Enumerate every effective owner used by this static isolated source.
owners=[s,cam,cam.data,root,s.world,s.world.node_tree]
for o in owned:
 owners.append(o)
 if o.data:owners.append(o.data)
 for slot in o.material_slots:
  if slot.material:owners.extend([slot.material,slot.material.node_tree])
for o in s.objects:
 if o.type=='LIGHT':owners.extend([o,o.data])
if getattr(s,'compositing_node_group',None):owners.append(s.compositing_node_group)
unique={x.as_pointer():x for x in owners if x}
channels=[]
for x in unique.values():
 a=getattr(x,'animation_data',None)
 channels.append({'name':x.name,'rna':x.bl_rna.identifier,'action':getattr(getattr(a,'action',None),'name',None),'drivers':len(a.drivers) if a else 0,'nlaTracks':len(a.nla_tracks) if a else 0,'shapeKeys':getattr(getattr(x,'shape_keys',None),'name',None)})
root.rotation_euler.z=0;holds=[]
for f in [1,2,12,25]:
 s.frame_set(f);pts,ms=sample();holds.append({'frame':f,'seconds':(f-1)/12,'rootMatrix':mat(root.matrix_world),'meshGeometrySHA256':{x['object']:x['geometrySHA256'] for x in ms},'bounds':bounds(pts),'visibleOwnObjects':sorted(o.name for o in owned if not o.hide_render)})
first=holds[0]['meshGeometrySHA256'];assert all(x['meshGeometrySHA256']==first for x in holds)
assert all(not x['action'] and not x['drivers'] and not x['nlaTracks'] and not x['shapeKeys'] for x in channels)
rest=holds[0]['bounds'];assert all(rest[i][0]>=lo-1e-6 and rest[i][1]<=hi+1e-6 for i,(lo,hi) in enumerate([(-.5,.5),(-.1,.1),(.04,.75)])),rest
report={'asset':'decor-background-wreck','round':'round-02','sourceProject':'source/round-02.blend','sourceProjectSHA256':source_sha,'blenderVersion':bpy.app.version_string,'rootObject':root.name,'captureRecords':records,'restBounds':rest,'restEnvelope':[[-.5,.5],[-.1,.1],[.04,.75]],'restEnvelopePass':True,'staticHolds':holds,'effectiveTemporalOwners':channels,'staticHoldGeometryEqual':True,'visibleOwnership':sorted(o.name for o in s.objects if not o.hide_render),'externalLibraries':list(bpy.data.libraries.keys()),'images':list(bpy.data.images.keys()),'compositor':{'enabled':bool(getattr(s,'compositing_node_group',None))},'lighting':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'],'renderRecipe':json.loads((P/'round-02-recipe.json').read_text()),'groundPlane':False,'supportContactClaim':False,'noProjectSavedDuringCapture':True}
(O/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n')
camera=json.loads((P/'round-02-resources/native/registered-camera.json').read_text());camera['captureScale']=2;camera['camera']['worldMatrix']=mat(cam.matrix_world);camera['camera']['projectionMatrix']=records[0]['projectionMatrix'];camera['camera']['orthoScale']=cam.data.ortho_scale;camera['camera']['shift']=[cam.data.shift_x,cam.data.shift_y];camera['calibration']={'root':[v/2 for v in records[0]['rootPixels']],'unitX':[(records[0]['unitXPixels'][i]-records[0]['rootPixels'][i])/2 for i in range(2)],'unitDepth':[(records[0]['unitDepthPixels'][i]-records[0]['rootPixels'][i])/2 for i in range(2)],'unitHeight':[(records[0]['unitHeightPixels'][i]-records[0]['rootPixels'][i])/2 for i in range(2)]};camera['nativeCaptureScale']=4;camera['nativeFrame']=[768,1408];camera['publishedFrame']=[384,704];camera['publication']='Uniform wholecanvas LANCZOS native4x to published2x';camera['artStyle']=report['renderRecipe']['render']
(O/'published-camera.json').write_text(json.dumps(camera,indent=2)+'\n')
asset={'id':'decor-background-wreck','collection':c.name,'rootObject':root.name,'rootLocation':[0,0,0],'rootScale':[1,1,1],'rootRestRotation':[0,0,0],'restBounds':rest,'meshCount':sum(o.type=='MESH' for o in owned),'geometry':'Native rebuilt rounded timber hull/mast/crossbar/cabin, static native rope; no textures or image cards','footprint':[1,1],'height':.75,'nonblocking':True,'layer':1,'sourceCaptureScale':4,'publishedSourceScale':2,'sourceSHA256':source_sha}
(O/'assetRecord.json').write_text(json.dumps(asset,indent=2)+'\n');(O/'rig.json').write_text(json.dumps({'asset':'decor-background-wreck','rootObject':root.name,'armatures':[],'actions':[],'drivers':[],'nla':[],'shapeKeys':[],'clips':[{'id':'static','frames':1,'fps':12,'static':True,'loop':False,'frameOrder':[0]}],'staticHolds':holds},indent=2)+'\n')
print('CAPTURE COMPLETE',rest,'sourceSHA256',source_sha)
