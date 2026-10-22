import bpy,json,math,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent;OBJ=HERE.parents[1];OUT=OBJ/'candidates/stage1-v6';RES=HERE/'resources'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vv(x):return [round(float(v),9) for v in x]
bpy.ops.wm.open_mainfile(filepath=str(HERE/'submarine-stage1.blend'))
sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['submarine-yellow__root'];col=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];actions=json.loads(root['nativeActions'])
def apply(clip,frame=1):
 for owner,name in actions[clip].items():
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[name];o.animation_data.action=a
  if a.slots:o.animation_data.action_slot=a.slots[0]
 sc.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
records=[];dirs={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
for clip in ['dock-ready','upgraded-dock-ready']:
 for d,a in dirs.items():
  if '--quick' in sys.argv and (clip!='dock-ready' or d!='S'):continue
  root.location=(0,0,0);root.rotation_euler.z=a;apply(clip);p=OUT/(clip+'-'+d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  records.append({'kind':'actual saved native action source representative','clip':clip,'frame':1,'direction':d,'path':str(p.relative_to(OBJ)),'sha256':sha(p),'rootMatrix':[vv(r) for r in root.matrix_world],'cameraMatrix':[vv(r) for r in cam.matrix_world],'nativeFrame':[640,768],'equipment':'PROVISIONAL' if clip.startswith('upgraded') else 'none'})
if '--quick' not in sys.argv:
 companions={}
 for key,file,colname,loc in [('floor','dock-floor-round-04.blend','WarmSoft_dock-floor',(0,0,0)),('entry','dock-entry-round-06.blend','S33_PROP_dock-entry',(0,-1.5,0)),('hut','workshop-hut-round-01.blend','WarmSoft_workshop-hut',(.78,.35,.23))]:
  with bpy.data.libraries.load(str(RES/file),link=False) as(src,dst):
   if colname not in src.collections:colname=next(n for n in src.collections if ('hut' in n.lower() if key=='hut' else key in n.lower()))
   dst.collections=[colname]
  c=dst.collections[0];sc.collection.children.link(c);c.hide_render=False;c.hide_viewport=False;r=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);companions[key]=(c,r,loc)
 sc.render.resolution_x=1280;sc.render.resolution_y=1536;cam.data.ortho_scale=6;cam.data.shift_y=.10
 for d,a in dirs.items():
  R=Matrix.Rotation(a,3,'Z');root.location=R@Vector((-.70,-.42,.23));root.rotation_euler.z=a
  for key,(c,r,loc) in companions.items():r.location=R@Vector(loc);r.rotation_euler.z=a
  apply('upgraded-dock-ready');p=OUT/('family-PROVISIONAL-'+d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
  records.append({'kind':'native physical family context; PROVISIONAL equipment','clip':'upgraded-dock-ready','frame':1,'direction':d,'path':str(p.relative_to(OBJ)),'sha256':sha(p),'rootMatrix':[vv(r) for r in root.matrix_world],'nativeFrame':[1280,1536],'cameraMatrix':[vv(r) for r in cam.matrix_world],'orthoScale':6,'shiftY':.10,'nativeBasis':'256pixels/Xworld as native body; larger canvas only, geometry scale unchanged.','companionRoots':{k:{'matrix':[vv(v) for v in r.matrix_world]} for k,(c,r,loc) in companions.items()},'projectionDisclosure':'Single physical main65degree native scene. Companions retain their own standalone55degree contracts; no sprite pixelidentity implied. No cover approval claimed.'})
 (OUT/'representative-captures.json').write_text(json.dumps({'sourceSHA256':sha(HERE/'submarine-stage1.blend'),'captures':records},indent=2)+'\n')
