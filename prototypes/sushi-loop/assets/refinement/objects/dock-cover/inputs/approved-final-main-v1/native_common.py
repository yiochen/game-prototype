"""Read-only final-source playback. Canonical equipment receives visibility only."""
import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
H=Path(__file__).resolve().parent;B=H.parents[1];R=H/'resources';O=B/'candidates/round-01'
DIRS={'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [val(x) for x in v]
 except:return str(v)
def hd(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def save(p,d):Path(p).write_text(json.dumps(d,indent=2,default=str)+'\n')
def bounds(p):return [[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
def open_source():
 bpy.ops.wm.open_mainfile(filepath=str(H/'project.blend'))
 return bpy.context.scene,bpy.data.objects['submarine-yellow__root'],bpy.data.collections['WarmSoft_submarine-yellow_stage1']
def apply(clip,frame=1,direction='S',location=(0,0,0)):
 s=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];c=bpy.data.collections['WarmSoft_submarine-yellow_stage1'];removed=json.loads(c['removedProvisionalOwners'])
 for owner,an in json.loads(root['nativeActions'])[clip].items():
  if owner not in bpy.data.objects:
   assert owner in removed and owner.startswith('PROVISIONAL__');continue
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a
  if a.slots:o.animation_data.action_slot=a.slots[0]
 for owner,an in json.loads(c['canonicalVisibilityActions'])[clip].items():
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
 root.location=location;root.rotation_euler.z=DIRS[direction]
 s.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
def geometry(objs,include_hidden=False):
 dg=bpy.context.evaluated_depsgraph_get();pts=[];faces=[];per={}
 for o in objs:
  if o.type!='MESH' or (o.hide_render and not include_hidden):continue
  e=o.evaluated_get(dg);m=e.to_mesh();p=[e.matrix_world@v.co for v in m.vertices];start=len(pts);pts+=p;faces += [[start+i for i in f.vertices] for f in m.polygons];per[o.name]={'bounds':bounds(p),'vertices':len(p)};e.to_mesh_clear()
 return pts,faces,per
def capture_record(clip,d,f,p,kind='runtime'):
 s=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];c=bpy.data.collections['WarmSoft_submarine-yellow_stage1']
 return {'clip':clip,'direction':d,'index':int(f)-1 if kind=='runtime' else None,'frame':f,'kind':kind,'path':str(p.relative_to(B)),'sha256':sha(p),'size':[s.render.resolution_x,s.render.resolution_y],'rootRotationZ':root.rotation_euler.z,'rootMatrix':val(root.matrix_world),'cameraMatrix':val(s.camera.matrix_world),'cameraOrthoScale':s.camera.data.ortho_scale,'cameraShift':[s.camera.data.shift_x,s.camera.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filterSize':s.render.filter_size,'visibleMeshNames':sorted(o.name for o in c.all_objects if o.type=='MESH' and not o.hide_render)}
