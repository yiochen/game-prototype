import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(bpy.data.filepath).resolve().parent.parent;OUT=BASE/'candidates/round-01'
sc=bpy.context.scene;root=bpy.data.objects[sc['sourceRootObject']];col=bpy.data.collections[sc['assetCollection']]
bpy.context.view_layer.update();cap=json.loads((OUT/'native-capture.json').read_text());src=json.loads((BASE/'inputs/source-camera.json').read_text())
rows=lambda m:[list(r) for r in m]
cam=sc.camera;dep=bpy.context.evaluated_depsgraph_get()
cap['camera'].update({'worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dep,x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'elevationDegrees':math.degrees(math.asin(cam.matrix_world[2][2])),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]})
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
r=px((0,0,0));cap['calibration']={'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)}
cap['reopenedSourceCameraMeasured']=True
allvs=[];meshes=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];allvs+=vs
 bm=bmesh.new();bm.from_mesh(me)
 meshes.append({'name':o.name,'vertices':len(me.vertices),'faces':len(me.polygons),'bounds':{'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]},'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces),'materials':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]})
 bm.free();ev.to_mesh_clear()
bounds={'min':[min(v[i] for v in allvs) for i in range(3)],'max':[max(v[i] for v in allvs) for i in range(3)],'radialMax':max(math.hypot(v.x,v.y) for v in allvs)}
images=[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images]
lights=[{'name':o.name,'type':o.data.type,'location':list(o.location),'energy':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT']
nodeTypes=sorted(set(n.bl_idname for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes));mats=[{'name':m.name,'nodes':sorted(set(n.type for n in m.node_tree.nodes)),'principled':{k:list(v.default_value) if hasattr(v.default_value,'__len__') and not isinstance(v.default_value,str) else v.default_value for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED' for k,v in n.inputs.items() if k in ['Base Color','Roughness','Specular IOR Level','Coat Weight','Coat Roughness']}} for m in bpy.data.materials if m.use_nodes]
maxdiff=lambda a,b:max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
diffs={k:maxdiff(cap['camera'][k+'Matrix'],src['camera'][k+'Matrix']) for k in ['world','projection']}
cal={k:max(abs(x-y) for x,y in zip(v,src['calibration'][k])) for k,v in cap['calibration'].items()}
checks={'physicalXYWithinHalfCell':min(bounds['min'][:2])>=-.50001 and max(bounds['max'][:2])<=.50001,'heightWithinEnvelope':bounds['min'][2]>=0 and bounds['max'][2]<=.20001,'occupiedRadiusPreserved':abs(bounds['radialMax']-.38)<.00001,'sourceCameraPreserved':max(diffs.values())<1e-6,'sourceCalibrationPreserved':max(cal.values())<.001,'native4ResolutionAndAspect':sc.render.resolution_x==768 and sc.render.resolution_y==1408 and abs(sc.render.pixel_aspect_x-src['camera']['pixelAspect'][0])<1e-6,'noRasterSubstitute':not images and not any('TexImage' in t for t in nodeTypes),'closedNativeResources':not images and not bpy.data.libraries,'fourNativeFacings':set(cap['views'])==set('NESW'),'noArmatureOrAnimation':not bpy.data.actions and not any(o.type=='ARMATURE' for o in col.all_objects),'closedTopology':not any(o['nonManifoldEdges'] or o['zeroAreaFaces'] for o in meshes)}
record={'schemaVersion':1,'asset':'decor-starfish','round':1,'project':'source/round-01.blend','projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'collection':col.name,'rootObject':root.name,'rootMatrix':rows(root.matrix_world),'physicalBounds':bounds,'nominalFunctionalHeight':.2,'originalPhysicalZ':[.07,.17],'authorizedPhysicalEnvelope':[0,.2],'footprint':[1,1],'rootCell':[.5,.5],'blocking':False,'meshes':meshes,'meshObjectCount':len(meshes),'camera':cap,'sourceCameraDifference':diffs,'sourceCalibrationDifferencePixels':cal,'renderViews':{f'static-{d}':v for d,v in cap['views'].items()},'lighting':{'horizontalSymmetry':4,'lights':lights,'worldStrength':sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value,'groundPlane':False,'directionalCastShadow':False},'materials':mats,'shaderNodeTypes':nodeTypes,'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'images':images,'externalFiles':[]},'topology':{'nonManifoldEdges':sum(o['nonManifoldEdges'] for o in meshes),'zeroAreaFaces':sum(o['zeroAreaFaces'] for o in meshes)},'checks':checks}
(OUT/'source-audit.json').write_text(json.dumps(record,indent=2)+'\n');(BASE/'source/round-01-native-camera.json').write_text(json.dumps(cap,indent=2)+'\n')
pub=json.loads(json.dumps(cap));pub['captureScale']=2;pub['sourceScale']=2;pub['nativeResolution']=[768,1408];pub['publishedResolution']=[384,704];pub['publicationSampling']={'method':'Pillow LANCZOS','wholeCanvasScale':.5,'fitOccupiedAlpha':False}
pub['render']['resolution']=[384,704]
for k,v in pub['calibration'].items():pub['calibration'][k]=[n*.5 for n in v]
(BASE/'source/round-01-published-camera.json').write_text(json.dumps(pub,indent=2)+'\n')
asset={'id':'decor-starfish','projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,248],'scale':2,'sourceScale':2,'nativeCaptureScale':4,'footprint':[1,1],'height':.2,'measuredPhysicalBounds':bounds,'sockets':{},'ports':{},'blocking':False,'rootCell':[.5,.5],'clips':{'idle':{'frames':1,'fps':12,'static':True,'loop':False}},'directions':list('NESW'),'artStyle':{'direction':'warm softly lit cartoon','nativeProceduralMaterial':True,'horizontalLightingSymmetry':4}}
(BASE/'source/round-01-published-assetRecord.json').write_text(json.dumps(asset,indent=2)+'\n');asset['scale']=4;(BASE/'source/round-01-native-assetRecord.json').write_text(json.dumps(asset,indent=2)+'\n')
rig={'assetId':'decor-starfish','source':'round-01-recipe.py','fps':12,'static':True,'groundRootObject':root.name,'footprint':[1,1],'sockets':{},'ports':{},'armatures':[],'actionCount':0,'clips':{'idle':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'actions':[],'controlsByFrame':[{}],'geometryOwners':[],'shaderChannels':[]}},'views':{d:{'rootMatrix':v['rootMatrix'],'frame':1} for d,v in cap['views'].items()}}
(BASE/'source/round-01-rig.json').write_text(json.dumps(rig,indent=2)+'\n');print(json.dumps({'bounds':bounds,'cameraDifference':diffs,'checks':checks,'topology':record['topology']},indent=2))
