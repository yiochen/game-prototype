import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(bpy.data.filepath).resolve().parent.parent;OUT=BASE/'candidates/round-03'
sc=bpy.context.scene;root=bpy.data.objects[sc['sourceRootObject']];col=bpy.data.collections[sc['assetCollection']];cap=json.loads((OUT/'native-capture.json').read_text());source=json.loads((BASE/'inputs/source-camera.json').read_text())
def rows(m):return [list(r) for r in m]
def px(p):
 v=world_to_camera_view(sc,sc.camera,Vector(p));return Vector((v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y))
origin=px((0,0,0));cap['calibration']={'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)}
cap['axes']={'x':'X','depth':'-Y','height':'Z'}
allvs=[];meshes=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep);me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];allvs+=vs
 bm=bmesh.new();bm.from_mesh(me)
 meshes.append({'name':o.name,'vertices':len(me.vertices),'faces':len(me.polygons),'bounds':{'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]},'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces),'materials':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]})
 bm.free();ev.to_mesh_clear()
bounds={'min':[min(v[i] for v in allvs) for i in range(3)],'max':[max(v[i] for v in allvs) for i in range(3)]};bounds['dimensions']=[bounds['max'][i]-bounds['min'][i] for i in range(3)]
images=[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images]
lights=[{'name':o.name,'type':o.data.type,'location':list(o.location),'energy':o.data.energy,'size':o.data.size} for o in sc.objects if o.type=='LIGHT']
nodeTypes=sorted(set(n.bl_idname for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes));mats=[{'name':m.name,'nodes':sorted(set(n.type for n in m.node_tree.nodes))} for m in bpy.data.materials if m.use_nodes]
maxdiff=lambda a,b:max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
record={'schemaVersion':1,'asset':'column-broken','round':3,'project':'source/round-03.blend','projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':sc.name,'rootObject':root.name,'rootMatrix':rows(root.matrix_world),'physicalBounds':bounds,'meshes':meshes,'meshObjectCount':len(meshes),'camera':cap,'cameraMatrixDifference':{'world':maxdiff(cap['camera']['worldMatrix'],source['camera']['worldMatrix']),'projection':maxdiff(cap['camera']['projectionMatrix'],source['camera']['projectionMatrix'])},'renderViews':{f'static-{d}':v for d,v in cap['views'].items()},'lighting':{'horizontalSymmetry':4,'lights':lights,'worldStrength':sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value,'groundPlane':False},'materials':mats,'shaderNodeTypes':nodeTypes,'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'images':images,'externalFiles':[]},'topology':{'nonManifoldEdges':sum(o['nonManifoldEdges'] for o in meshes),'zeroAreaFaces':sum(o['zeroAreaFaces'] for o in meshes)},'checks':{'physicalXYWithinHalfCell':min(bounds['min'][:2])>=-.50001 and max(bounds['max'][:2])<=.50001,'heightWithinFunctionalMaximum':bounds['max'][2]<=1.88001,'groundZ0':abs(bounds['min'][2])<.00001,'sourceCameraPreserved':maxdiff(cap['camera']['worldMatrix'],source['camera']['worldMatrix'])<1e-6 and maxdiff(cap['camera']['projectionMatrix'],source['camera']['projectionMatrix'])<1e-6,'native4SquarePixels':sc.render.resolution_x==768 and sc.render.resolution_y==1280 and sc.render.pixel_aspect_x==sc.render.pixel_aspect_y==1,'noRasterSubstitute':not images and not any('TexImage' in t for t in nodeTypes),'closedNativeResources':not images and not bpy.data.libraries,'fourNativeFacings':set(cap['views'])==set('NESW'),'noArmatureOrAnimation':not bpy.data.actions and not any(o.type=='ARMATURE' for o in col.all_objects)}}
(OUT/'source-audit.json').write_text(json.dumps(record,indent=2)+'\n')
(BASE/'source/round-03-camera.json').write_text(json.dumps(cap,indent=2)+'\n')
asset={'id':'column-broken','projection':'height-dependent-35-square-footing','frame':[192,320],'anchor':[96,248],'scale':4,'publishedSourceScale':2,'footprint':[1,1],'height':bounds['max'][2],'functionalMaximumHeight':1.88,'physicalBounds':bounds,'sockets':{},'ports':{},'squareFooting':True,'footingTransition':.42,'camera_elevation_degrees':35,'clips':{'static':{'frames':1,'fps':12,'static':True,'loop':False}},'directions':['N','E','S','W'],'artStyle':{'direction':'warm softly lit cartoon','nativeProceduralMaterial':True,'horizontalLightingSymmetry':4}}
(BASE/'source/round-03-assetRecord.json').write_text(json.dumps(asset,indent=2)+'\n')
rig={'assetId':'column-broken','source':'round-03-recipe.py','fps':12,'static':True,'groundRootObject':root.name,'footprint':[1,1],'sockets':{},'ports':{},'armatures':[],'actionCount':0,'clips':{'static':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'actions':[],'controlsByFrame':[{}],'geometryOwners':[],'shaderChannels':[]}},'views':{d:{'rootMatrix':v['rootMatrix'],'frame':1} for d,v in cap['views'].items()}}
(BASE/'source/round-03-rig.json').write_text(json.dumps(rig,indent=2)+'\n')
print(json.dumps({'bounds':bounds,'checks':record['checks'],'topology':record['topology']},indent=2))
