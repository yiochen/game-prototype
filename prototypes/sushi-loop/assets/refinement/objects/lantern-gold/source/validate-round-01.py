"""Fresh-process validation of the saved native project, plus one exact re-render."""
import bpy,json,pathlib,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=pathlib.Path(__file__).resolve().parent.parent
OUT=HERE/'candidates/round-01'
original=json.loads((OUT/'validation-native.json').read_text())
project=HERE/'source/round-01.blend'
bpy.ops.wm.open_mainfile(filepath=str(project))
sc=bpy.context.scene
root=bpy.data.objects['lantern__root.001']
meshes=[o for o in sc.objects if o.type=='MESH']
def geom(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();pts=[ev.matrix_world@v.co for v in m.vertices]
 rec={'vertices':len(m.vertices),'edges':len(m.edges),'polygons':len(m.polygons),'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'matrixWorld':[[float(v) for v in row] for row in o.matrix_world]};ev.to_mesh_clear();return rec
diffs=[];frames=[]
for d in 'NESW':
 root.rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
 for f in range(1,14):
  sc.frame_set(f);sc.view_layers[0].update();observed={o.name:geom(o) for o in meshes}
  for n,v in observed.items():
   expected=original['nativeGeometryMeasurements'][d][f-1][n]
   assert all(v[k]==expected[k] for k in ['vertices','edges','polygons'])
   diffs.extend(abs(v['bounds'][r][i]-expected['bounds'][r][i]) for r in range(2) for i in range(3))
   diffs.extend(abs(v['matrixWorld'][r][i]-expected['matrixWorld'][r][i]) for r in range(4) for i in range(4))
  frames.append({'direction':d,'frame':f,'objects':observed})
cam=sc.camera
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
cal={'root':px((0,0,0))}
for k,v in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]:cal[k]=[px(v)[i]-cal['root'][i] for i in range(2)]
images=[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE']
libs=[l.filepath for l in bpy.data.libraries]
assert not images and not libs
assert max(diffs)<1e-6
assert original['projectSha256']==hashlib.sha256(project.read_bytes()).hexdigest()
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
for dev in prefs.devices:dev.use=dev.type=='METAL'
sc.cycles.device='GPU'
result={'freshReloadPassed':True,'projectSha256':original['projectSha256'],'maxMeasurementDelta':max(diffs),'cameraCalibration':cal,'framesMeasured':len(frames),'measurements':frames,'externalImages':images,'linkedLibraries':libs,'meshObjects':len(meshes),'sceneObjects':len(sc.objects),'savedActions':[a.name for a in bpy.data.actions],'savedRigActionsAssigned':{o.name:o.animation_data.action.name for o in meshes if o.animation_data and o.animation_data.action},'renderDevice':'Apple M4 (GPU - 10 cores), METAL','rerenderPath':'candidates/round-01/reload-N-000.png'}
(OUT/'validation-reload.json').write_text(json.dumps(result,indent=2)+'\n')
root.rotation_euler.z=math.pi;sc.frame_set(1);sc.view_layers[0].update()
sc.render.filepath=str(OUT/'reload-N-000.png');bpy.ops.render.render(write_still=True,scene=sc.name)
print('FRESH_RELOAD_PASSED',flush=True)
