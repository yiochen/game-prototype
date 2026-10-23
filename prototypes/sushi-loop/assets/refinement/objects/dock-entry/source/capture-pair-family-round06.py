"""Read frozen standalone sources, append companion + b176 source family IN MEMORY.
No blend is saved. Reproduce: blender -b -t 6 --python source/capture-pair-family.py
"""
import bpy,json,math,hashlib,re
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];OUT=B/'candidates/round-06';FAM=OUT/'native-context';FAM.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
entryfile=B/'source/round-06.blend';floorfile=B/'source/resources/paired-native-v3/dock-floor-round-04.blend';original=B/'source/resources/original-library.blend'
initial_hashes={str(p):sha(p) for p in [entryfile,floorfile,original]}
bpy.ops.wm.open_mainfile(filepath=str(entryfile));sc=bpy.context.scene;cam=sc.camera;ec=bpy.data.collections['S33_PROP_dock-entry'];er=bpy.data.objects['dock-entry__root']
with bpy.data.libraries.load(str(floorfile),link=False) as (a,b):b.collections=['WarmSoft_dock-floor']
fc=bpy.data.collections['WarmSoft_dock-floor'];sc.collection.children.link(fc);fr=bpy.data.objects['dock-floor__root']
source_names=['S33_PROP_dock-entry.001','S33_PROP_dock-floor.001','S33_PROP_workshop-hut.001','S33_PROP_submarine_base.001','S33_PROP_dock-cover.001','S33_CHARACTER_customer_rosa.001']
with bpy.data.libraries.load(str(original),link=False) as (a,b):
 b.collections=list(source_names);b.actions=[n for n in a.actions if any(t in n for t in ['dock-cover','submarine-yellow','customer-rosa'])]
cols={}
for name in source_names:
 c=bpy.data.collections[name];sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
 cols[name]=c
se=cols[source_names[0]];sf=cols[source_names[1]];hut=cols[source_names[2]];sub=cols[source_names[3]];cover=cols[source_names[4]];human=cols[source_names[5]]
def root(c):return next(o for o in c.objects if o.type=='EMPTY' and o.parent is None)
sr,fsr,hr,sbr,cr,rr=[root(c) for c in [se,sf,hut,sub,cover,human]]
resolved=[]
def lookup(data,name):
 return data.get(name) or data.get(name+'.001') or next((o for o in data if re.sub(r'\.\d+$','',o.name)==re.sub(r'\.\d+$','',name)),None)
def cohort(c,asset,clip,frame=1):
 r=json.loads((B/'source/resources/frozen-neighbors'/f'{asset}-rig.json').read_text())
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
for direction,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 transform_all(a)
 capture(f'pair-{direction}',direction,[ec,fc],kind='native-pair')
 capture(f'source-pair-{direction}',direction,[se,sf],kind='native-original-pair-common-rig')
 capture(f'family-{direction}',direction,[ec,fc,hut,sub,cover],kind='native-family-current')
 capture(f'source-family-{direction}',direction,[se,sf,hut,sub,cover],kind='native-family-original-common-rig')
 # Full-family registered ground/steps/landing path; every position fixed in the same model basis.
 R=Matrix.Rotation(a,4,'Z')
 for index,(y,z) in enumerate([(-.57,0),(-.43,.0733333333),(-.25,.1466666667),(-.08,.22),(.14,.22)]):
  rr.location=R@Vector((0,y-1.5,z));rr.rotation_euler.z=a;bpy.context.view_layer.update();capture(f'walk-{direction}-{index}',direction,[ec,fc,hut,sub,cover,human],kind='native-registered-human-path')
 # Covered state context uses exact native covered action at first frame, same fixed roots.
 cohort(cover,'dock-cover','covered',1);transform_all(a);capture(f'family-covered-{direction}',direction,[ec,fc,hut,sub,cover],kind='native-family-covered');cohort(cover,'dock-cover','uncover',12)
manifest['renders']=records;manifest['sourceHashesAfterCaptures']={str(p):sha(p) for p in [entryfile,floorfile,original]};manifest['sourceBytesUnchanged']=initial_hashes==manifest['sourceHashesAfterCaptures'];(OUT/'paired-native-validation.json').write_text(json.dumps(manifest,indent=2))
print('PAIR_FAMILY_READY',len(records),manifest['sourceBytesUnchanged'])
