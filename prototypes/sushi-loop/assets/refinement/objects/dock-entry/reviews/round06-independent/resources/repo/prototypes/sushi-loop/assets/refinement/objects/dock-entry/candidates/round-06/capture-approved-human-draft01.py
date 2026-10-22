"""Read frozen standalone sources, append companion + b176 source family IN MEMORY.
No blend is saved. Reproduce: blender -b -t 6 --python source/capture-pair-family.py
"""
import bpy,json,math,hashlib,re
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];OUT=B/'candidates/round-06';FAM=OUT/'native-approved-human';FAM.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
entryfile=B/'source/round-06.blend';floorfile=B/'source/resources/paired-native-v3/dock-floor-round-04.blend';original=B/'source/resources/original-library.blend'
initial_hashes={str(p):sha(p) for p in [entryfile,floorfile,original]}
bpy.ops.wm.open_mainfile(filepath=str(entryfile));sc=bpy.context.scene;cam=sc.camera;ec=bpy.data.collections['S33_PROP_dock-entry'];er=bpy.data.objects['dock-entry__root']
with bpy.data.libraries.load(str(floorfile),link=False) as (a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc);fr=bpy.data.objects['dock-floor__root']
source_names=['S33_PROP_dock-entry.001','S33_PROP_dock-floor.001','S33_PROP_workshop-hut.001','S33_PROP_submarine_base.001','S33_PROP_dock-cover.001']
with bpy.data.libraries.load(str(original),link=False) as (a,b):
 b.collections=list(source_names);b.actions=[n for n in a.actions if any(t in n for t in ['dock-cover','submarine-yellow'])]
cols={}
for name in source_names:
 c=bpy.data.collections[name];sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
 cols[name]=c
approved=B/'source/resources/approved-human-v3/customer-rosa-approved.blend'
with bpy.data.libraries.load(str(approved),link=False) as (a,b):b.collections=['S33_CHARACTER_customer_rosa.001'];b.actions=[n for n in a.actions if 'customer-rosa' in n]
human=bpy.data.collections['S33_CHARACTER_customer_rosa.001'];sc.collection.children.link(human);human.hide_viewport=False;human.hide_render=False
for o in human.all_objects:o.hide_viewport=False;o.hide_set(False)
se=cols[source_names[0]];sf=cols[source_names[1]];hut=cols[source_names[2]];sub=cols[source_names[3]];cover=cols[source_names[4]]
def root(c):return next(o for o in c.objects if o.type=='EMPTY' and o.parent is None)
sr,fsr,hr,sbr,cr,rr=[root(c) for c in [se,sf,hut,sub,cover,human]]
resolved=[]
def lookup(data,name):
 return data.get(name) or data.get(name+'.001') or next((o for o in data if re.sub(r'\.\d+$','',o.name)==re.sub(r'\.\d+$','',name)),None)
def cohort(c,asset,clip,frame=1):
 r=json.loads(((B/'source/resources/approved-human-v3/customer-rosa-approved-rig.json') if asset=='customer-rosa' else (B/'source/resources/frozen-neighbors'/f'{asset}-rig.json')).read_text())
 for o in c.all_objects:
  if o.animation_data:
   o.animation_data.action=None
   for t in o.animation_data.nla_tracks:t.mute=True
 for t in r['clips'][clip]['actions']:
  typ=t['ownerType']
  if typ=='Object':owner=lookup(bpy.data.objects,t['ownerName'])
  elif typ=='Key':owner=lookup(bpy.data.shape_keys,t['ownerName'])
  elif 'materialOwnerName' in t:
   m=lookup(bpy.data.materials,t['materialOwnerName']);owner=m.node_tree if m else None
  else:owner=None
  act=lookup(bpy.data.actions,t['action'])
  if owner is None or act is None:raise RuntimeError(f'Missing native cohort owner/action: {t}')
  owner.animation_data_create();owner.animation_data.action=act
  slots=list(act.slots);slot=next((s for s in slots if s.identifier==t.get('slotIdentifier')),slots[0] if len(slots)==1 else None)
  if slot:owner.animation_data.action_slot=slot
  resolved.append({'asset':asset,'clip':clip,'requestedOwner':t['ownerName'],'actualOwner':owner.name,'action':act.name,'slot':slot.identifier if slot else None})
 sc.frame_set(frame);bpy.context.view_layer.update()
cohort(sub,'submarine-yellow','dock-ready',1);cohort(cover,'dock-cover','uncover',12);cohort(human,'customer-rosa','stand',1);sc.frame_set(12);bpy.context.view_layer.update()
for c in [sub,cover]:
 for o in c.all_objects:
  if o.animation_data:o.animation_data.action=None
# Pure render visibility is selected by collection, retaining native child hide actions.
def visibility(active):
 for c in [ec,fc,se,sf,hut,sub,cover,human]:c.hide_render=c not in active

def setup(frame=(640,640),anchor=(320,320)):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*frame[0],(1-p.y)*frame[1]))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]-base.y)/dy;bpy.context.view_layer.update();p=px((0,0,0))
 return {'logicalFrame':frame,'logicalAnchor':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p),'cameraMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]}
records=[]
def capture(name,direction,active,frame=(640,640),anchor=(320,320),kind='native'):

 if 'family' in kind or 'human' in kind:frame=(768,768);anchor=(384,440)
 visibility(active);cal=setup(frame,anchor);p=FAM/(name+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'kind':kind,'direction':direction,'path':str(p.relative_to(B)),'sha256':sha(p),'calibration':cal,'entryRoot':list(er.location),'rootRotationZ':er.rotation_euler.z,'rootMatrix':[list(r) for r in er.matrix_world],'familyRoots':{o.name:{'location':list(o.location),'rotationZ':o.rotation_euler.z,'matrixWorld':[list(r) for r in o.matrix_world]} for o in [fr,hr,sbr,cr,rr]},'frame':sc.frame_current})
def transform_all(a):
 R=Matrix.Rotation(a,4,'Z')
 for o,co in [(fr,(0,0,0)),(er,(0,-1.5,0)),(sr,(0,-1.5,0)),(fsr,(0,0,0)),(hr,(.78,.35,.23)),(sbr,(-.7,-.42,.23)),(cr,(0,0,.23)),(rr,(0,-2.05,0))]:o.rotation_euler.z=a;o.location=R@Vector(co)
 bpy.context.view_layer.update()
# Evaluated native geometry includes exact vertices, normals, topology and boundary rays.
def geom(c):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];polys=[];objects=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  e=o.evaluated_get(dg);m=e.to_mesh();verts=[e.matrix_world@v.co for v in m.vertices];faces=[list(p.vertices) for p in m.polygons];off=len(vs);vs+=verts;polys +=[[i+off for i in p] for p in faces]
  incidence={tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))):0 for p in m.polygons for i in range(len(p.vertices))}
  for p in m.polygons:
   for i in range(len(p.vertices)):incidence[tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)])))]+=1
  objects.append({'name':o.name,'hideRender':o.hide_render,'visibleRenderMesh':not o.hide_render,'matrixWorld':[list(r) for r in e.matrix_world],'verticesWorld':[list(v) for v in verts],'polygons':faces,'polygonNormalsWorld':[list((e.matrix_world.to_3x3()@p.normal).normalized()) for p in m.polygons],'nonmanifoldEdges':sum(n!=2 for n in incidence.values()),'zeroAreaFaces':sum(p.area<1e-12 for p in m.polygons),'looseVertices':len(m.vertices)-len(set(i for p in m.polygons for i in p.vertices)),'bounds':[[min(v[i] for v in verts) for i in range(3)],[max(v[i] for v in verts) for i in range(3)]],'materials':[m.name for m in o.data.materials]});e.to_mesh_clear()
 return objects,BVHTree.FromPolygons(vs,polys,all_triangles=False)
transform_all(0);eg,et=geom(ec);fg,ft=geom(fc);hg,ht=geom(human)
def ray(t,p,d=(0,0,-1),length=4):
 q,n,idx,dist=t.ray_cast(Vector(p),Vector(d),length);return {'point':list(q) if q else None,'normal':list(n) if n else None,'distance':dist}
sections=[]
for i in range(193):
 x=-.48+i*.005
 sections.append({'x':x,'entryNearBoundary':ray(et,(x,-1.5-1e-6,1)),'floorNearBoundary':ray(ft,(x,-1.5+1e-6,1)),'entryEndFace':ray(et,(x,-1.5+.01,.20),(0,-1,0),.1),'floorEndFace':ray(ft,(x,-1.5-.01,.20),(0,1,0),.1)})
walk=[]
for x in [-.38,-.25,0,.25,.38]:
 for localy in [-.49,-.45,-.375,-.333,-.30,-.25,-.167,-.16,-.1,-.05,-.001]:walk.append({'x':x,'entryLocalY':localy,'surface':ray(et,(x,localy-1.5,1))})
manifest={'asset':'dock-entry','pairedSources':json.loads((B/'source/paired-source-binding-v3.json').read_text()),'originalSHA256':sha(original),'noBlendResaved':True,'renderer':sc.render.engine,'actualFilterSize':sc.render.filter_size,'actualTaaRenderSamples':sc.eevee.taa_render_samples,'frozenBriefSHA256':sha(B/'brief-v3-native-sampling.json'),'entryNativeObjects':eg,'floorNativeObjects':fg,'nativeHumanObjects':hg,'sharedSections':sections,'walkingFlightSections':walk,'semanticMarkers':{'entry':[0,-.5,0],'dock':[0,.5,.23]},'neighborOriginalRoots':{'workshop-hut':[.78,.35,.23],'submarine-yellow':[-.7,-.42,.23],'dock-cover':[0,0,.23]},'nativeActionResolutions':resolved,'neighborKnownSupportGaps':{'workshop-hut':.035,'submarine-yellow':.055},'humanContactNote':'Source Rosa stand cohort, exact root follows measured support heights. Fixed original world scale, no fitting. On source stairs the same references expose old submerged geometry. Native context is visual path evidence, not new gameplay.','renders':records}

# Approved body is the same exact native geometry as real published consumer,
# but these derived images intentionally use55degree environment camera, not35degree authoring camera.
path=[(0,-2.1,0),(0,-1.9,.0733333333),(0,-1.75,.1466666667),(0,-1.55,.22),(0,-1.5,.22),(0,-1.3,.22),(.15,-.65,.22),(0,.12,.22),(.78,-.18,.22)]
measurements=[]
def body_measure(a,index,position):
 dg=bpy.context.evaluated_depsgraph_get();visible=[];feet=[];inv=Matrix.Rotation(-a,4,'Z')
 for o in human.all_objects:
  if o.type!='MESH' or o.hide_render:continue
  e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@x.co for x in m.vertices];bounds=[[min(x[i] for x in v) for i in range(3)],[max(x[i] for x in v) for i in range(3)]];item={'name':o.name,'boundsWorld':bounds,'visibleRenderMesh':True,'vertexCount':len(v)};visible.append(item)
  if 'minimal_foot' in o.name:
   vv=[inv@x for x in v];feet.append({**item,'verticesWorld':[list(x) for x in v],'verticesUnrotatedFloorWorld':[list(x) for x in vv],'minRelativeRootZ':min(x.z for x in v)-rr.location.z,'footXYEnvelopeUnrotated':[[min(x[i] for x in vv) for i in range(2)],[max(x[i] for x in vv) for i in range(2)]]})
  e.to_mesh_clear()
 return {'direction':{0:'S'}.get(a,''),'phaseIndex':index,'clip':'walk','frame':index+1,'pathPositionFloorWorld':position,'actualRootMatrix':[list(r) for r in rr.matrix_world],'actualRootScale':list(rr.scale),'visibleFeet':feet,'visibleBodyBoundsWorld':[[min(o['boundsWorld'][0][i] for o in visible) for i in range(3)],[max(o['boundsWorld'][1][i] for o in visible) for i in range(3)]],'lowestVisibleSoleRelativeRootZ':min(f['minRelativeRootZ'] for f in feet),'visibleMeshes':visible}
for direction,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 transform_all(a);R=Matrix.Rotation(a,4,'Z')
 for index,position in enumerate(path):
  cohort(human,'customer-rosa','walk',index+1);rr.location=R@Vector(position);rr.rotation_euler.z=a;bpy.context.view_layer.update();capture(f'approved-walk-{direction}-{index}',direction,[ec,fc,hut,sub,cover,human],kind='native-registered-human-path');rec=body_measure(a,index,position);rec['direction']=direction;measurements.append(rec)
manifest['renders']=records;manifest['humanApprovedSource']={'path':str(approved.relative_to(B)),'sha256':sha(approved),'metadataHeight':rr.get('anatomy_height'),'canonicalUniformNativeScaleMetadata':rr.get('uniform_native_scale'),'actualRootScale':list(rr.scale),'authoredCameraRecord':'source/resources/approved-human-v3/customer-rosa-approved-camera.json','authoredProjectionDegrees':35,'derivedContextProjectionDegrees':55.00797980144134,'noPixelParityClaim':'Actual browser primary uses real published35degree atlas; these derived55degree frames assert native physical body/foot/clearance only. No actor scaling/fitting/warp/per-facing nudges.'};manifest['humanPath']=path;manifest['humanPoseMeasurements']=measurements;manifest['sourceHashesAfterCaptures']={str(p):sha(p) for p in [entryfile,floorfile,original]};manifest['sourceBytesUnchanged']=initial_hashes==manifest['sourceHashesAfterCaptures'];manifest['approvedHumanSourceUnchanged']=sha(approved)=='a6fe68fa07f3930c3d8e88ae6df992fefe447a9ef18935e322daf6f4bbc28253';manifest['oldB176HumanEvidenceScope']='Earlier native-context/walk-* uses older1.5125 b176 Rosa and remains diagnostic only; it does not establish approved body parity.';(OUT/'approved-human-native-validation.json').write_text(json.dumps(manifest,indent=2));print('APPROVED_HUMAN_NATIVE_READY',len(records),manifest['sourceBytesUnchanged'],manifest['approvedHumanSourceUnchanged'])
