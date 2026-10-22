"""Reopen exact hut; append exact floor04/entry06 and original source family in memory.
No source is saved. Cohorts are bound from immutable original native rig metadata.
"""
import bpy,json,math,hashlib,shutil,re
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];S=B/'source';O=B/'candidates/round-01';R=S/'resources';C=O/'contexts';C.mkdir(exist_ok=True);BR=R/'browser';BR.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Exact resource closure is local to own source/resources.
orig=B.parents[1]/'backups/b1765262bfa897ad-sushi-loop-world-library.blend'
for source,dest in [(orig,R/'original-library.blend'),(B/'inputs/paired-native/dock-entry-round-06.blend',R/'paired-entry-round-06.blend')]:
 if not dest.exists():shutil.copyfile(source,dest)
for asset in ['submarine-yellow','dock-cover']:
 dest=R/'family-rigs'/f'{asset}.json';dest.parent.mkdir(exist_ok=True)
 if not dest.exists():shutil.copyfile(B.parent/'dock-floor/source/resources/family-rigs'/f'{asset}.json',dest)
approved=R/'customer-rosa-approved.blend'
if not approved.exists():shutil.copyfile(B/'inputs/paired-native/customer-rosa-approved.blend',approved)
sources={'approvedRosa':approved,'hut':S/'round-01.blend','floor':R/'paired-floor-round-04.blend','entry':R/'paired-entry-round-06.blend','original':R/'original-library.blend'};before={k:sha(p) for k,p in sources.items()}
assert before['floor']=='94b509984dc442547602f32feada987c5119e3b9031eb1bd65a6a07769880418' and before['entry']=='22bd2b05201567c22d9dabcf767a3daf0639342e5522c43900ff4b777f5f3b37'
bpy.ops.wm.open_mainfile(filepath=str(sources['hut']));sc=bpy.context.scene;cam=sc.camera;hut=bpy.data.collections['WarmSoft_workshop-hut'];hr=bpy.data.objects['workshop-hut__root']
for file,name in [(sources['floor'],'WarmSoft_dock-floor'),(sources['entry'],'S33_PROP_dock-entry')]:
 with bpy.data.libraries.load(str(file),link=False) as (a,b):b.collections=[name]
 sc.collection.children.link(bpy.data.collections[name])
floor=bpy.data.collections['WarmSoft_dock-floor'];entry=bpy.data.collections['S33_PROP_dock-entry']
names=['S33_PROP_submarine_base.001','S33_PROP_dock-cover.001']
with bpy.data.libraries.load(str(sources['original']),link=False) as (a,b):b.collections=list(names);b.actions=[n for n in a.actions if any(t in n for t in ['submarine-yellow','dock-cover'])]
for n in names:
 c=bpy.data.collections[n];sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
sub,cover=[bpy.data.collections[n] for n in names]
with bpy.data.libraries.load(str(approved),link=False) as (a,b):b.collections=['S33_CHARACTER_customer_rosa.001'];b.actions=[n for n in a.actions if 'customer-rosa' in n]
human=bpy.data.collections['S33_CHARACTER_customer_rosa.001'];sc.collection.children.link(human);human.hide_viewport=False;human.hide_render=False
for o in human.all_objects:o.hide_viewport=False;o.hide_set(False)
def getroot(c):return next(o for o in c.objects if o.type=='EMPTY' and o.parent is None)
fr,er,sr,cr,rr=[getroot(c) for c in [floor,entry,sub,cover,human]]
collections=[hut,floor,entry,sub,cover,human]
def lookup(data,name):return data.get(name) or data.get(name+'.001') or next((o for o in data if re.sub(r'\.\d+$','',o.name)==re.sub(r'\.\d+$','',name)),None)
resolved=[]
def cohort(c,asset,clip,frame):
 rig=json.load(open(R/'family-rigs'/f'{asset}.json'))
 for o in c.all_objects:
  if o.animation_data:
   o.animation_data.action=None
   for t in o.animation_data.nla_tracks:t.mute=True
 for rec in rig['clips'][clip]['actions']:
  typ=rec['ownerType']
  if typ=='Object':owner=lookup(bpy.data.objects,rec['ownerName'])
  elif typ=='Key':owner=lookup(bpy.data.shape_keys,rec['ownerName'])
  elif 'materialOwnerName' in rec:
   m=lookup(bpy.data.materials,rec['materialOwnerName']);owner=m.node_tree if m else None
  else:owner=None
  act=lookup(bpy.data.actions,rec['action'])
  if owner is None or act is None:raise RuntimeError(f'Missing native action {rec}')
  owner.animation_data_create();owner.animation_data.action=act;slots=list(act.slots);slot=next((s for s in slots if s.identifier==rec.get('slotIdentifier')),slots[0] if len(slots)==1 else None)
  if slot:owner.animation_data.action_slot=slot
  resolved.append({'asset':asset,'clip':clip,'owner':owner.name,'action':act.name,'slot':slot.identifier if slot else None})
 sc.frame_set(frame);bpy.context.view_layer.update()
cohort(sub,'submarine-yellow','dock-ready',1);cohort(human,'customer-rosa','stand',1);cohort(cover,'dock-cover','uncover',12)

def visible(cs):
 for c in collections:c.hide_render=c not in cs

def setup(frame=(768,768),anchor=(384,440)):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*frame[0],(1-p.y)*frame[1]))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]-base.y)/dy;bpy.context.view_layer.update();p=px((0,0,0))
 return {'frame':frame,'anchor':list(p),'captureScale':2,'root':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p),'matrix':[list(x) for x in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]}
def transform(a,humanY=-1.02):
 m=Matrix.Rotation(a,4,'Z')
 for r,p in [(hr,(.78,.35,.23)),(fr,(0,0,0)),(er,(0,-1.5,0)),(sr,(-.7,-.42,.23)),(cr,(0,0,.23)),(rr,(.66,.35+humanY,.22))]:r.location=m@Vector(p);r.rotation_euler.z=a;r.scale=(1.25,1.25,1.25) if r==rr else (1,1,1)
 rr.rotation_euler.z=a+math.pi
 bpy.context.view_layer.update()

def geometry(c,visibleonly=True):
 dg=bpy.context.evaluated_depsgraph_get();vs=[];fs=[];objects=[]
 for o in c.all_objects:
  if o.type!='MESH' or (visibleonly and o.hide_render):continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();p=[ev.matrix_world@v.co for v in me.vertices];faces=[list(f.vertices) for f in me.polygons];off=len(vs);vs+=p;fs += [[i+off for i in f] for f in faces]
  objects.append({'name':o.name,'bounds':{'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)]},'vertexCount':len(p),'matrix':[list(x) for x in ev.matrix_world]});ev.to_mesh_clear()
 return objects,BVHTree.FromPolygons(vs,fs,all_triangles=False),{'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]}
records=[]
def capture(name,d,cs,frame=(768,768),anchor=(384,440),folder=C,kind='native-family'):
 visible(cs);cal=setup(frame,anchor);p=folder/(name+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 record={'path':str(p.relative_to(B)),'sha256':sha(p),'direction':d,'kind':kind,'camera':cal,'filterSize':sc.render.filter_size,'rootRotationZ':hr.rotation_euler.z,'rootMatrix':[list(x) for x in hr.matrix_world],'roots':{r.name:{'location':list(r.location),'rotation':list(r.rotation_euler),'scale':list(r.scale),'matrix':[list(x) for x in r.matrix_world]} for r in [hr,fr,er,sr,cr,rr]},'frame':sc.frame_current};records.append(record);return record

humanEvidence=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 for i,y in enumerate([-1.25,-1.02]):
  cohort(human,'customer-rosa','stand',1);transform(a,y);hg,ht,hb=geometry(human);ug,ut,ub=geometry(hut);sg,st,sb=geometry(sub)
  overlapsH=ht.overlap(ut);overlapsS=ht.overlap(st)
  record=capture(f'approved-human-{d}-{i}',d,[hut,floor,entry,sub,human],kind='native-approved-human-approach')
  # Actual visible evaluated sole vertices and paired deck surface, no fitted bounds.
  dg=bpy.context.evaluated_depsgraph_get();soles=[]
  _,ft,fb=geometry(floor)
  for o in human.all_objects:
   if o.type!='MESH' or o.hide_render or not any(t in o.name.lower() for t in ['foot','shoe','sole']):continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices];minz=min(p.z for p in ps);low=[p for p in ps if p.z<=minz+1e-5];rays=[]
   for v in low:
    q,n,idx,dist=ft.ray_cast(v+Vector((0,0,.02)),Vector((0,0,-1)),.1);rays.append({'sole':list(v),'deck':list(q) if q else None,'deltaWorld':v.z-q.z if q else None})
   soles.append({'name':o.name,'minWorldZ':minz,'lowestVertices':rays});ev.to_mesh_clear()
  solePatches=[]
  for footX in [.55,.82]:
   samples=[]
   for ix in range(7):
    for iy in range(7):
     p=Matrix.Rotation(a,4,'Z')@Vector((footX-.015+ix*.005,.35+y+.012+iy*.005,.18))
     h,hn,hi,hd=ht.ray_cast(p,Vector((0,0,1)),.1);f,fn,fi,fd=ft.ray_cast(p+Vector((0,0,.10)),Vector((0,0,-1)),.2)
     samples.append({'xy':list(p)[:2],'sole':list(h) if h else None,'deck':list(f) if f else None,'deltaWorld':h.z-f.z if h and f else None})
   solePatches.append({'unrotatedX':footX,'area':.03*.03,'samples':samples,'maxAbsoluteDifferenceWorld':max(abs(v['deltaWorld']) for v in samples if v['deltaWorld'] is not None),'allSurfaceSamplesPresent':all(v['deltaWorld'] is not None for v in samples)})
  humanEvidence.append({'direction':d,'soleSupportFiniteAreas':solePatches,'actorFacesFacadeRelativeRadians':math.pi,'approachIndex':i,'localHutRelativePosition':[-.12,y,-.01],'unrotatedWorld':[.66,.35+y,.22],'actualRoot':list(rr.location),'actualScale':list(rr.scale),'bounds':hb,'nativeObjects':hg,'soles':soles,'hutOverlapTrianglePairs':len(overlapsH),'submarineOverlapTrianglePairs':len(overlapsS),'path':record['path']})
 # Explicit optional derived environment projection reference, never actual consumer substitute.
 transform(a);rr.location=(0,0,0);bpy.context.view_layer.update();capture(f'controlled-approved-rosa-stand-{d}',d,[human],(192,320),(96,248),BR,kind='controlled-human-environment-projection')
manifest={'sources':{k:{'path':str(p.relative_to(B)),'sha256':before[k]} for k,p in sources.items()},'sourceUnchanged':{k:sha(p)==before[k] for k,p in sources.items()},'pairedImportNeverSaved':True,'frozenBriefSHA256':sha(B/'brief.json'),'humanEvidence':humanEvidence,'captures':records,'actor':'Exact approved Rosa standalone, preserved authored root scale1.25, source stand action, faces facade at relativepi. Rows retained in outward-facing draft are superseded. This supersedes old b176 human diagnostics only.','consumerDifference':'Actual consumer must retain exact published35degree Rosa sprite; native physical context uses approved native geometry at common environment projection. Body pixels are not claimed identical; source scale, position, sole contact and clearances are measured natively.','nativeActionResolutions':resolved}
(O/'approved-human-audit.json').write_text(json.dumps(manifest,indent=2));print('APPROVED_HUMAN_READY',[(x['direction'],x['approachIndex'],x['bounds'],[(s['name'],s['minWorldZ']) for s in x['soles']]) for x in humanEvidence],flush=True)
