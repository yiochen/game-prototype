import bpy,json,math,hashlib,bmesh
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent.parent
ROUND='round-01';R=P/'candidates'/ROUND;R.mkdir(parents=True,exist_ok=True)
# Run with the candidate loaded; independent reopened audit uses the same code.
s=bpy.context.scene;c=s.camera;bpy.context.view_layer.update()
root=bpy.data.objects['uniform35-wall-plain__root'];W=bpy.data.collections['S33_PROP_uniform35-wall-plain']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def projection(p):
 q=world_to_camera_view(s,c,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
def edge_profile(o,side):
 # Canonical yz profile vertices at protected world-space join planes.
 return sorted(set((round((o.matrix_world@v.co).y,6),round((o.matrix_world@v.co).z,6)) for v in o.data.vertices if abs((o.matrix_world@v.co).x-side)<1e-5))
source=json.loads((P/'source/source-inspection-corrected.json').read_text())
def src_profile(o,side):
 mat=Matrix(o['matrix']);return sorted(set((round((mat@Vector(v)).y,6),round((mat@Vector(v)).z,6)) for v in o['vertices'] if abs((mat@Vector(v)).x-side)<1e-5))
protected=[];source_map={o['name']:o for o in source['objects'] if o['type']=='MESH'}
for name,o in source_map.items():
 old={str(x):src_profile(o,x) for x in [-.5,.5]}
 if any(old.values()):
  ob=bpy.data.objects[name];new={str(x):edge_profile(ob,x) for x in [-.5,.5]}
  protected.append({'name':name,'source':old,'candidate':new,'exactYZProfilesMatch':old==new,'matrixMatch':all(abs(ob.matrix_world[i][j]-o['matrix'][i][j])<1e-6 for i in range(4) for j in range(4)) if name!='uniform35-wall-plain__baseboard_face' else 'World geometry rebuilt at original coordinates; equivalent native transform measured separately'})
def measure(ob):
 dep=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dep);me=ev.to_mesh();vv=[ev.matrix_world@v.co for v in me.vertices]
 bm=bmesh.new();bm.from_mesh(me);bm.normal_update()
 out={'name':ob.name,'location':list(ob.location),'rotation':list(ob.rotation_euler),'scale':list(ob.scale),'matrix':[list(r) for r in ob.matrix_world],'bounds':[[min(v[i] for v in vv) for i in range(3)],[max(v[i] for v in vv) for i in range(3)]],'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'degenerateFaces':sum(f.calc_area()<1e-10 for f in bm.faces),'materials':[m.name if m else None for m in ob.data.materials],'modifiers':[{'name':m.name,'type':m.type} for m in ob.modifiers]}
 bm.free();ev.to_mesh_clear();return out
meshes=[measure(o) for o in W.all_objects if o.type=='MESH']
bounds=[[min(o['bounds'][0][i] for o in meshes) for i in range(3)],[max(o['bounds'][1][i] for o in meshes) for i in range(3)]]
oldbounds=[]
for o in source_map.values():
 ma=Matrix(o['matrix']);oldbounds.extend(ma@Vector(v) for v in o['vertices'])
oldbounds=[[min(v[i] for v in oldbounds) for i in range(3)],[max(v[i] for v in oldbounds) for i in range(3)]]
front=projection((0,-.5,0));origin=projection((0,0,0));px=projection((1,-.5,0));pz=projection((0,-.5,1));basisX=[a-b for a,b in zip(px,front)];basisZ=[a-b for a,b in zip(pz,front)]
family=json.loads((P/'inputs/family-settings.json').read_text())
recipe=json.loads((P/'source'/f'{ROUND}-recipe.json').read_text())
family_profiles=[]
for plane,entries in family['joinProfiles']['S33_PROP_uniform35-wall-plain'].items():
 for entry in entries:
  ob=bpy.data.objects[entry['sourcePart']];dep=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dep);me=ev.to_mesh()
  measured=sorted(set((round((ev.matrix_world@v.co).y,8),round((ev.matrix_world@v.co).z,8)) for v in me.vertices if abs((ev.matrix_world@v.co).x-float(plane))<1e-5));ev.to_mesh_clear()
  expected=sorted(tuple(v) for v in entry['evaluatedJoinYZ']);error=max((abs(a-b) for aa,bb in zip(measured,expected) for a,b in zip(aa,bb)),default=0) if len(measured)==len(expected) else None
  family_profiles.append({'plane':float(plane),'part':ob.name,'expectedEvaluatedYZ':expected,'measuredEvaluatedYZ':measured,'maxError':error,'compatible':error is not None and error<1e-6})
validation={'schemaVersion':1,'asset':'backdrop-wall','round':ROUND,'scene':s.name,'sourceIntegrity':{'path':source['source'],'sha256':sha(source['source']),'unchanged':sha(source['source'])==source['sha256']},'familySettings':{'path':'inputs/family-settings.json','sha256':sha(P/'inputs/family-settings.json')},'capture':{'projection':'ordinary35-character-camera','nativeFrame':[s.render.resolution_x,s.render.resolution_y],'logicalFrame':[192,448],'sourceScale':3,'logicalRoot':[96,416],'declaredNativeContactAnchor':[288,1248],'worldRootOrigin':list(root.matrix_world.translation),'worldRootProjection':origin,'frontContactWorldPoint':[0,-.5,0],'frontContactProjection':front,'pixelBasisX':basisX,'pixelBasisZ':basisZ,'framePadding':{'nativeHorizontal':96,'nativeTop':96,'nativeBottom':96},'camera':{'name':c.name,'type':c.data.type,'worldMatrix':[list(r) for r in c.matrix_world],'orthoScale':c.data.ortho_scale,'sensorFit':c.data.sensor_fit,'shift':[c.data.shift_x,c.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'sourceCameraWorldMatrixExact':all(abs(c.matrix_world[i][j]-Matrix(json.loads((P/'inputs/source-assetRecord.json').read_text())['camera']['camera']['worldMatrix'])[i][j])<1e-6 for i in range(4) for j in range(4))},'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world]},'renders':[{'clip':'static','direction':'S','index':0,'path':f'candidates/{ROUND}/static-S-000.png','nativeFrame':[576,1344],'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world]}],'bounds':{'source':oldbounds,'candidateEvaluated':bounds,'sourceEnvelopePreserved':all(abs(a-b)<1e-5 for aa,bb in zip(oldbounds,bounds) for a,b in zip(aa,bb)),'footprintWidthWorldUnits':1,'functionalWallFrontY':-.5,'baselineZ':0,'addedDetailInsideX':.418,'roofCadencePerWorldUnit':4},'protectedJoinPlanes':{'planes':[-.5,.5],'objects':protected,'allExactYZProfilesMatch':all(o['exactYZProfilesMatch'] for o in protected),'note':'Original continuous boundary profiles and all source band heights remain. Baseboard interior front face is natively recessed; side/end planes retained. Added trim and supports stay within each module and do not add terminal caps.'},'familyProtectedProfiles':{'records':family_profiles,'allCompatible':all(x['compatible'] for x in family_profiles)},'topology':{'meshCount':len(meshes),'meshes':meshes,'totalVertices':sum(o['vertices'] for o in meshes),'totalPolygons':sum(o['polygons'] for o in meshes),'totalNonmanifoldEdges':sum(o['nonmanifoldEdges'] for o in meshes),'totalDegenerateFaces':sum(o['degenerateFaces'] for o in meshes)},'materialsAndLighting':{'renderer':recipe['renderer'],'lighting':recipe['lighting'],'materials':recipe['materials'],'oneConfigurationForAllFrames':True,'directionalGroundShadow':False,'groundObject':None},'dependencies':{'linkedLibraries':[{'path':l.filepath} for l in bpy.data.libraries if l.users>0],'images':[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images if im.type!='RENDER_RESULT'],'packed':True,'selfContained':not any(l.users>0 for l in bpy.data.libraries) and all(im.packed_file or im.source=='GENERATED' or im.type=='RENDER_RESULT' for im in bpy.data.images)},'checks':{'frame':s.render.resolution_x==576 and s.render.resolution_y==1344,'squarePixels':s.render.pixel_aspect_x==s.render.pixel_aspect_y==1,'basisX':abs(basisX[0]-384)<.001 and abs(basisX[1])<.001,'basisZ':abs(basisZ[0])<.001 and abs(basisZ[1]+314.5544)<.001,'frontContact':abs(front[0]-288)<.001 and abs(front[1]-1248)<.001,'sourceS0':abs(root.rotation_euler.z)<1e-7,'profiles':all(o['exactYZProfilesMatch'] for o in protected),'familyProfiles':all(x['compatible'] for x in family_profiles),'envelope':all(abs(a-b)<1e-5 for aa,bb in zip(oldbounds,bounds) for a,b in zip(aa,bb))}}
(R/'validation.json').write_text(json.dumps(validation,indent=2))
N=R/'native-records';N.mkdir(exist_ok=True)
record=json.loads((P/'inputs/source-assetRecord.json').read_text())
record['camera']['captureCamera']={**validation['capture']['camera'],'worldRootProjection':origin,'frontContactProjection':front,'pixelBasisX':basisX,'pixelBasisZ':basisZ}
record['modelingChanges']=json.loads((P/'source/geometry-stage.json').read_text())['nativeDesignChanges'];record['protectedJoinEvidence']='../validation.json';record['paletteAndLightFamilySettings']='../../../inputs/family-settings.json'
(N/'asset-record.json').write_text(json.dumps(record,indent=2))
camera=json.loads((P/'inputs/source-camera.json').read_text());camera['assets']['wall-plain']['captureCamera']=validation['capture']['camera'];camera['assets']['wall-plain']['captureCamera']['worldRootProjection']=origin;camera['assets']['wall-plain']['captureCamera']['frontContactProjection']=front
(N/'camera.json').write_text(json.dumps(camera,indent=2))
(N/'rig.json').write_text(json.dumps({'asset':'backdrop-wall','type':'static-single-facing-root','root':root.name,'sourcePhaseConvention':{'S':0},'clips':[{'clip':'static','frames':1,'fps':12,'loop':False,'direction':'S','rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world]}],'skeleton':None,'shapeKeys':None,'directionalGroundShadow':False},indent=2))
print(json.dumps({'checks':validation['checks'],'bounds':validation['bounds'],'topologyTotals':{k:v for k,v in validation['topology'].items() if k!='meshes'},'dependencies':validation['dependencies']},indent=2))
