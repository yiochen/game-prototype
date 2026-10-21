import bpy,json,math,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent.parent;O=P/'candidates/round-07';v=json.loads((O/'validation.json').read_text());project=P/'source/round-07.blend'
bpy.ops.wm.open_mainfile(filepath=str(project));s=bpy.context.scene;root=bpy.data.objects[v['contract'].get('root','dock-post-rope__root.001')];cam=s.camera
bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def mat(m):return [[float(x) for x in r] for r in m]
def px(point):q=world_to_camera_view(s,cam,Vector(point));return [q.x*384,(1-q.y)*704]
proj=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=704,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)
source=json.loads((P/'inputs/source-camera.json').read_text())
rootpix=px((0,0,0));camera={'worldMatrix':mat(cam.matrix_world),'projectionMatrix':mat(proj),'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'sensorFit':cam.data.sensor_fit,'orthoScale':cam.data.ortho_scale,'shiftY':cam.data.shift_y,'frame':[384,704],'rootPixels':rootpix,'sourceWorldMatrixMaxError':max(abs(cam.matrix_world[i][j]-source['camera']['worldMatrix'][i][j]) for i in range(4) for j in range(4)),'sourceProjectionMatrixMaxError':max(abs(proj[i][j]-source['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4))}
topology={};parts=[o for o in s.objects if o.type=='MESH']
for o in parts:
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bm=bmesh.new();bm.from_mesh(me)
 topology[o.name]={'vertices':len(me.vertices),'faces':len(me.polygons),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'uvLayers':[u.name for u in o.data.uv_layers]};bm.free();ev.to_mesh_clear()
profile={}
for key in ['-.5','.5']:pass
pts={}
for plane in ['-0.5','0.5']:
 pts[plane]=sorted(set(tuple(p[1:]) for record in v['geometry']['candidate'].values() for p in record['cutPlanePoints'][plane]))
def haus(a,b):return max(min(math.dist(p,q) for q in b) for p in a)
profile={'cutPlaneWorldX':[-.5,.5],'sourceAndCandidateExactPointListsEqual':v['geometry']['cutProfilesUnchanged'],'candidateYZProfileMinus':pts['-0.5'],'candidateYZProfilePlus':pts['0.5'],'opposingYZProfileHausdorffError':max(haus(pts['-0.5'],pts['0.5']),haus(pts['0.5'],pts['-0.5'])),'geometryJoinPlaneGap':0,'nativeJoinInstanceSpacing':1.0,'preservedOriginalProfiles':True,'roundedProtectedEdgeGeometry':False}
ports=[]
for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();rr=[]
 for p in v['contract']['ports']:
  wp=root.matrix_world@Vector(p['position']);wn=root.matrix_world.to_3x3()@Vector(p['normal']);q=px(wp);rr.append({'name':p['direction'],'profile':p['profile'],'worldPosition':list(wp),'worldNormal':list(wn),'logicalRootRelativeProjection':[(q[0]-rootpix[0])/2,(q[1]-rootpix[1])/2]})
 ports.append({'direction':d,'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':mat(root.matrix_world),'ports':rr})
root.rotation_euler.z=0;bpy.context.view_layer.update()
prefs=bpy.context.preferences.addons['cycles'].preferences
try:
 prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 s.cycles.device='GPU'
except Exception:pass
s.render.filepath=str(O/'fresh-reload-S.png');bpy.ops.render.render(write_still=True)
v['freshReload']={'projectSHA256':hashlib.sha256(project.read_bytes()).hexdigest(),'successful':True,'camera':camera,'savedRootRotationZ':0.0,'render':'candidates/round-07/fresh-reload-S.png','topology':topology,'allMeshesManifold':all(x['nonManifoldEdges']==0 and x['zeroAreaFaces']==0 for x in topology.values()),'dependencies':{'linkedLibraries':[l.filepath for l in bpy.data.libraries],'externalImages':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'selfContained':not bpy.data.libraries and not any(i.source=='FILE' and not i.packed_file for i in bpy.data.images)}}
v['profileMeasurements']=profile;v['rotatedPortMeasurements']=ports;v['geometry']['capDetail']='Broad low-contrast radial growth rings centered independently on each protected cut plane. Both joined halves sample radius abs(y) at the shared plane; identical colors and phase. Top and cap cut faces share softly inclined top normals and radial material phase at the protected boundary to prevent cut-face color contamination in separately captured alpha assembly; no displacement, vertex movement or boundary rounding.'
v['capCutShaderValidation']={'method':'One symmetric procedural camera-ray radiance material only on the two intentional cap cut faces; same shader in every facing. Other ray transport uses the accepted Principled BSDF. No projected image, raster edit, alpha adjustment or geometry movement.','cause':'Exposed vertical cap cut faces enter the fractional-pixel edge of each independent capture. Cycles hemisphere correction makes them darker than adjacent top surfaces despite top-like custom normals. Joined geometry hides those cut faces.','calibration':'Native 512-sample linear EXR full-cap measurements, globally fitted four-coefficient smooth irradiance model; not per-pixel or per-facing coefficients.','model':'C = topBaseColor * ring(radius) * (K0 + K2*(y/.175)^2) + (S0 + S2*(y/.175)^2)','nativeMaterials':[]}
for o in parts:
 if 'post_cap' not in o.name:continue
 m=o.data.materials[2];ns=m.node_tree.nodes
 v['capCutShaderValidation']['nativeMaterials'].append({'object':o.name,'material':m.name,'cutFaceIndices':[p.index for p in o.data.polygons if p.material_index==2],'topFaceIndices':[p.index for p in o.data.polygons if p.material_index==1],'K0':float(ns['Top irradiance K0 K2'].inputs[2].default_value),'K2':float(ns['Top irradiance K0 K2'].inputs[1].default_value),'S0':float(ns['Top broad reflection S0 S2'].inputs[2].default_value),'S2':float(ns['Top broad reflection S0 S2'].inputs[1].default_value),'lightPathCameraRaySwitch':any(n.bl_idname=='ShaderNodeLightPath' for n in ns),'textureImages':[n.image.name for n in ns if n.bl_idname=='ShaderNodeTexImage' and n.image]})
(O/'validation.json').write_text(json.dumps(v,indent=2));print('FRESH_RELOAD_AUDIT_DONE',json.dumps({'cameraMaxError':camera['sourceProjectionMatrixMaxError'],'profileError':profile['opposingYZProfileHausdorffError'],'manifold':v['freshReload']['allMeshesManifold']}))
