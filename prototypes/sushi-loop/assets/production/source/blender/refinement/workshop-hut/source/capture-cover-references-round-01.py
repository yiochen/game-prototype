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
for asset in ['submarine-yellow','dock-cover','customer-rosa']:
 dest=R/'family-rigs'/f'{asset}.json';dest.parent.mkdir(exist_ok=True)
 if not dest.exists():shutil.copyfile(B.parent/'dock-floor/source/resources/family-rigs'/f'{asset}.json',dest)
sources={'hut':S/'round-01.blend','floor':R/'paired-floor-round-04.blend','entry':R/'paired-entry-round-06.blend','original':R/'original-library.blend'};before={k:sha(p) for k,p in sources.items()}
assert before['floor']=='94b509984dc442547602f32feada987c5119e3b9031eb1bd65a6a07769880418' and before['entry']=='22bd2b05201567c22d9dabcf767a3daf0639342e5522c43900ff4b777f5f3b37'
bpy.ops.wm.open_mainfile(filepath=str(sources['hut']));sc=bpy.context.scene;cam=sc.camera;hut=bpy.data.collections['WarmSoft_workshop-hut'];hr=bpy.data.objects['workshop-hut__root']
for file,name in [(sources['floor'],'WarmSoft_dock-floor'),(sources['entry'],'S33_PROP_dock-entry')]:
 with bpy.data.libraries.load(str(file),link=False) as (a,b):b.collections=[name]
 sc.collection.children.link(bpy.data.collections[name])
floor=bpy.data.collections['WarmSoft_dock-floor'];entry=bpy.data.collections['S33_PROP_dock-entry']
names=['S33_PROP_submarine_base.001','S33_PROP_dock-cover.001','S33_CHARACTER_customer_rosa.001']
with bpy.data.libraries.load(str(sources['original']),link=False) as (a,b):b.collections=list(names);b.actions=[n for n in a.actions if any(t in n for t in ['submarine-yellow','dock-cover','customer-rosa'])]
for n in names:
 c=bpy.data.collections[n];sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
sub,cover,human=[bpy.data.collections[n] for n in names]
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
 for r,p in [(hr,(.78,.35,.23)),(fr,(0,0,0)),(er,(0,-1.5,0)),(sr,(-.7,-.42,.23)),(cr,(0,0,.23)),(rr,(.66,.35+humanY,.22))]:r.location=m@Vector(p);r.rotation_euler.z=a;r.scale=(1,1,1)
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

for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 for clip in ['covered','uncover']:
  for idx in [0,5,11]:
   cohort(cover,'dock-cover',clip,idx+1);transform(a);cr.location=(0,0,0);bpy.context.view_layer.update();capture(f'dock-cover-{clip}-{d}-{idx:02}',d,[cover],(736,704),(368,480),BR,kind='native-old-cover-reference-registered')
(O/'old-cover-reference-audit.json').write_text(json.dumps({'sources':{k:{'path':str(p.relative_to(B)),'sha256':before[k]} for k,p in sources.items()},'captures':records,'reason':'Source cover original logical frame736x704/root368x480 retained, recaptures replace cropped draft references only; no source/model changed.'},indent=2))
