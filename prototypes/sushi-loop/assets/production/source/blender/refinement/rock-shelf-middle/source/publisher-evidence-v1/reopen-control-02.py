"""Read-only saved-source all4 replay with measured pose ledger; never saves a blend."""
import bpy,sys,json,math,hashlib,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[2];OUT=BASE/'candidates/round-01/publisher-evidence-v1/replay-control-02'
SOURCE=BASE/'source/round-01.blend';EXPECTED='da1b8a61f51d4dad60132e9627650ba1b2563e8f6887a6e27b0bb155926669af'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(BASE).as_posix()
assert sha(SOURCE)==EXPECTED
original=json.loads((BASE/'delivery/manifest.json').read_text());originalchecks={p:sha(BASE/p)==v['sha256'] for p,v in original['files'].items()};assert all(originalchecks.values())
# This process is invoked with -b exact saved blend. Do not execute build recipe or reconfigure the scene.
assert Path(bpy.data.filepath).resolve()==SOURCE.resolve()
s=bpy.context.scene;root=bpy.data.objects['rock-shelf-middle__root'];cam=s.camera
assert s.render.resolution_x==768 and s.render.resolution_y==1408 and s.render.filter_size==.5
assert s.render.engine=='BLENDER_EEVEE' and s.eevee.taa_render_samples==32
originalSettings={'resolution':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filterSize':s.render.filter_size,'engine':s.render.engine,'renderSamples':s.eevee.taa_render_samples,'filmTransparent':s.render.film_transparent,'fps':s.render.fps,'frameStart':s.frame_start,'frameEnd':s.frame_end,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'dither':s.render.dither_intensity,'compression':s.render.image_settings.compression}
views={}
for direction,requested in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=requested;s.frame_set(1);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();actual=root.evaluated_get(dep)
 def px(point):
  p=world_to_camera_view(s,cam,Vector(point));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
 p=px(actual.matrix_world.translation);X=px((1,0,0))-px((0,0,0));D=px((0,-1,0))-px((0,0,0));H=px((0,0,1))-px((0,0,0))
 path=OUT/f'replay-{direction}-4x.png';assert not path.exists(),'Retain existing replay; choose a new supplement for rerun'
 settings={'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(row) for row in actual.matrix_world],'rootLocalMatrix':[list(row) for row in root.matrix_local],'requestedRotationZ':requested,'clip':'static','direction':direction,'index':0,'nativeFrame':s.frame_current,'fps':s.render.fps,'frame':[192,352],'anchor':[96,248],'captureScale':4,'renderSize':[s.render.resolution_x,s.render.resolution_y],'camera':{'name':cam.name,'type':cam.data.type,'sensorFit':cam.data.sensor_fit,'orthoScale':cam.data.ortho_scale,'worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(dep,x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'elevationDegrees':math.degrees(math.atan2(cam.location.z,math.hypot(cam.location.x,cam.location.y)))},'calibration':{'root':list(p),'unitX':list(X),'unitDepth':list(D),'unitHeight':list(H)},'filterSize':s.render.filter_size,'sourceProject':rel(SOURCE),'sourceProjectSHA256':EXPECTED,'path':rel(path)}
 s.render.filepath=str(path);bpy.ops.render.render(write_still=True);settings['sha256']=sha(path)
 views[direction]=settings
 (OUT/f'pose-{direction}.json').write_text(json.dumps(settings,indent=2)+'\n')
# Actual static data/ownership from reopened source, not stale source-rig labels.
objects=[];actions=[];materials=[];lights=[];images=[]
for o in s.objects:
 action=o.animation_data.action.name if o.animation_data and o.animation_data.action else None
 objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'action':action,'shapeKeys':bool(o.data.shape_keys) if o.type=='MESH' else False})
 if action:actions.append({'object':o.name,'action':action})
 if o.type=='LIGHT':lights.append({'name':o.name,'type':o.data.type,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape})
for m in bpy.data.materials:
 materials.append({'name':m.name,'action':m.animation_data.action.name if m.animation_data and m.animation_data.action else None,'nodeAction':m.node_tree.animation_data.action.name if m.node_tree and m.node_tree.animation_data and m.node_tree.animation_data.action else None})
for i in bpy.data.images:images.append({'name':i.name,'source':i.source,'packed':bool(i.packed_file),'filepath':i.filepath})
assert not actions and not any(m['action'] or m['nodeAction'] for m in materials)
ledger={'asset':'rock-shelf-middle','round':'round-01','supplement':'publisher-evidence-v1','purpose':'Measured read-only exact-saved-source all4 native pose and render replay. No source resave or art changes.','sourceProject':rel(SOURCE),'sourceProjectSHA256':EXPECTED,'blender':bpy.app.version_string,'views':views,'captureRecords':views,'savedSettings':originalSettings,'staticChecks':{'frame':s.frame_current,'fps':s.render.fps,'frameStart':s.frame_start,'frameEnd':s.frame_end,'loop':False,'actualActions':actions,'materialActions':materials,'armatures':[o.name for o in s.objects if o.type=='ARMATURE'],'shapeKeys':[o['name'] for o in objects if o['shapeKeys']]},'objects':objects,'lights':lights,'images':images,'libraries':[l.filepath for l in bpy.data.libraries],'sourceSHAAfterReplay':sha(SOURCE),'original132UnchangedBefore':all(originalchecks.values()),'original132UnchangedAfter':all(sha(BASE/p)==v['sha256'] for p,v in original['files'].items()),'sourceResaved':False}
assert ledger['sourceSHAAfterReplay']==EXPECTED and ledger['original132UnchangedAfter']
(OUT/'pose-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
print(json.dumps({'sourceSHA256':EXPECTED,'all132Unchanged':ledger['original132UnchangedAfter'],'actualRootRotationZ':{d:r['rootRotationZ'] for d,r in views.items()}},indent=2))
