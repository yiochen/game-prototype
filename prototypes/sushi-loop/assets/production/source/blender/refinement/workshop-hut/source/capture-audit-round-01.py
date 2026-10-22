"""Reopen standalone bytes, audit actual state, native wholeframes, then pair in memory only."""
import bpy,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];S=B/'source';O=B/'candidates/round-01';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=S/'round-01.blend';original_sha=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['workshop-hut__root'];col=bpy.data.collections['WarmSoft_workshop-hut'];sc.frame_set(1);bpy.context.view_layer.update()
def box(ps):return {'min':[min(p[i] for p in ps) for i in range(3)],'max':[max(p[i] for p in ps) for i in range(3)]}
def geom(c):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[];records=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices];faces=[list(f.vertices) for f in me.polygons];off=len(vs);vs+=p;fs += [[i+off for i in f] for f in faces]
  inc={}
  for face in faces:
   for i in range(len(face)):
    edge=tuple(sorted((face[i],face[(i+1)%len(face)])));inc[edge]=inc.get(edge,0)+1
  records.append({'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in ev.matrix_world],'bounds':box(p),'vertices':[list(v) for v in p],'faces':faces,'vertexCount':len(p),'polygonCount':len(faces),'nonmanifoldEdges':sum(n!=2 for n in inc.values()),'zeroAreaFaces':sum(f.area<1e-12 for f in me.polygons),'materials':[m.name for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]});ev.to_mesh_clear()
 return records,BVHTree.FromPolygons(vs,fs,all_triangles=False),box(vs)
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [plain(x) for x in v]
 except:return str(v)
def camera():
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 p=px((0,0,0))
 return {'projection':'top-down-oblique-square-grid','frame':[sc.render.resolution_x//2,sc.render.resolution_y//2],'anchor':[96,352],'captureScale':2,'fps':sc.render.fps,'camera':{'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'calibration':{'root':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p)}}
objects,tree,bounds=geom(col);geometry_hash=hashlib.sha256(json.dumps(objects,sort_keys=True).encode()).hexdigest()
audit={'asset':'workshop-hut','source':'source/round-01.blend','sourceSHA256':original_sha,'frozenBriefSHA256':sha(B/'brief.json'),'blenderVersion':bpy.app.version_string,'savedStateReopened':True,'standaloneBeforePairing':True,'root':{'name':root.name,'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale),'matrix':[list(x) for x in root.matrix_world]},'boundsRootLocal':bounds,'geometrySHA256':geometry_hash,'objects':objects,'camera':camera(),'settings':{'engine':sc.render.engine,'filterSize':sc.render.filter_size,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'fps':sc.render.fps,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'eeveeTAASamples':sc.eevee.taa_render_samples if hasattr(sc.eevee,'taa_render_samples') else None,'useNodes':sc.use_nodes},'lights':[{'name':o.name,'matrix':[list(x) for x in o.matrix_world],'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'shape':o.data.shape} for o in bpy.data.objects if o.type=='LIGHT'],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'source':i.source,'size':list(i.size)} for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries],'drivers':[{'id':o.name,'paths':[d.data_path for d in o.animation_data.drivers]} for o in bpy.data.objects if o.animation_data and o.animation_data.drivers],'rigs':[o.name for o in bpy.data.objects if o.type=='ARMATURE'],'materials':[],'nativeCaptures':[]}
for m in bpy.data.materials:
 audit['materials'].append({'name':m.name,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes],'links':[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in m.node_tree.links]})
(O/'native-records/camera.json').write_text(json.dumps(camera(),indent=2))
asset=json.load(open(S/'resources/source-assetRecord.json'));asset['scale']=2;asset['groundRootObject']=root.name;asset['nativeProject']='source/round-01.blend';asset['artStyle']={'lighting':'centered overhead + four equal cardinal broad fills','nativeModel':'crafted thick pitched roof, coherent walls, closed facade and connected support'};(O/'native-records/asset.json').write_text(json.dumps(asset,indent=2))
rig=json.load(open(S/'resources/source-rig.json'));rig['groundRootObject']=root.name;rig['status']='static-native-reconstructed';(O/'native-records/rig.json').write_text(json.dumps(rig,indent=2))
# First wholeframes from saved/reopened standalone, exact untrimmed 384x896 regions.
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=a;bpy.context.view_layer.update();p=O/'frames'/('static-'+d)/'000.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);at=O/'atlases'/('static-'+d+'.png');shutil.copyfile(p,at)
 audit['nativeCaptures'].append({'clip':'static','direction':d,'index':0,'path':str(p.relative_to(B)),'sha256':sha(p),'atlas':str(at.relative_to(B)),'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(x) for x in root.matrix_world],'doorSocketWorld':list(bpy.data.objects['workshop-hut__door_socket'].matrix_world.translation),'camera':camera(),'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'renderFilterSize':sc.render.filter_size})
# Full evaluated local geometry envelope handed to cover editor, explicitly no approval.
(O/'native-envelope.json').write_text(json.dumps({'asset':'workshop-hut','sourceSHA256':original_sha,'geometrySHA256':geometry_hash,'boundsRootLocal':bounds,'compositionRoot':[.78,.35,.23],'roofAndChimney':[r for r in objects if any(t in r['name'] for t in ['roof','ridge','chimney'])],'approval':'pending independent judge'},indent=2))
# Pair only in memory after own standalone captures. No source resave.
root.rotation_euler.z=0;root.location=(.78,.35,.23)
floor=S/'resources/paired-floor-round-04.blend'
with bpy.data.libraries.load(str(floor),link=False) as (a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc);bpy.context.view_layer.update();fgeom,ft,fb=geom(fc);_,ht,hb=geom(col)
def ray(tree,x,y,z,dz=-1):
 p,n,i,dist=tree.ray_cast(Vector((x,y,z)),Vector((0,0,dz)),5);return {'point':list(p) if p else None,'normal':list(n) if n else None,'triangle':i,'distance':dist}
areas=[{'id':'front-left','localBox':[[-.21,-.15],[-.32,-.24]]},{'id':'rear-left','localBox':[[-.21,-.15],[.23,.31]]},{'id':'rear-right','localBox':[[.29,.35],[.23,.31]]}]
contacts=[]
for ar in areas:
 diffs=[];samples=[]
 for i in range(9):
  for j in range(9):
   x=.78+ar['localBox'][0][0]+(ar['localBox'][0][1]-ar['localBox'][0][0])*i/8;y=.35+ar['localBox'][1][0]+(ar['localBox'][1][1]-ar['localBox'][1][0])*j/8
   f=ray(ft,x,y,.5);h=ray(ht,x,y,.18,1)
   delta=h['point'][2]-f['point'][2] if f['point'] and h['point'] else None
   diffs.append(delta);samples.append({'xy':[x,y],'deck':f,'hutUnderside':h,'differenceWorld':delta})
 contacts.append({**ar,'area':(ar['localBox'][0][1]-ar['localBox'][0][0])*(ar['localBox'][1][1]-ar['localBox'][1][0]),'samples':samples,'maxAbsoluteDifferenceWorld':max(abs(x) for x in diffs if x is not None),'noMissingSurfaces':all(x is not None for x in diffs)})
audit['pairedSupport']={'hutSHA256':original_sha,'floorSHA256':sha(floor),'pairedOnlyInMemory':True,'contacts':contacts,'contactToleranceWorld':1e-5,'selectedStructuralSurface':'Broad bottom face of connected native foundation sill; each sampled finite-area patch lies on actual flat floor board plateau and actual sill underside. Three noncollinear patches.','patchCenterDistances':{'frontRear':.55,'leftRight':.5},'thresholdSections':[{'localX':x,'floor':ray(ft,.78+x,.35-.52,.5),'hutBottom':ray(ht,.78+x,.35-.52,.18,1)} for x in [-.25,-.20,-.15,-.10,-.05,0]],'fullFamilyClaim':False}
assert sc.render.filter_size==.5
assert bounds['min'][0]>=-.583-1e-5 and bounds['max'][0]<=.583+1e-5
assert bounds['min'][1]>=-.6099854-1e-5 and bounds['max'][1]<=.6099854+1e-5
assert bounds['min'][2]>=-.012-1e-5 and bounds['max'][2]<=1.81+1e-5
for c in contacts:assert c['noMissingSurfaces'] and c['maxAbsoluteDifferenceWorld']<=1e-5
assert sha(source)==original_sha
audit['sourceUnchangedAfterPairing']=sha(source)==original_sha
(O/'native-audit.json').write_text(json.dumps(audit,indent=2));(O/'support-contact.json').write_text(json.dumps(audit['pairedSupport'],indent=2))
print('NATIVE_AUDIT_READY',original_sha,bounds,geometry_hash,[c['maxAbsoluteDifferenceWorld'] for c in contacts],flush=True)
