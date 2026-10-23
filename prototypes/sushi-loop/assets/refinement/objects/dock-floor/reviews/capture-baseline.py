import bpy,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent
BASE=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production')
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
assets={}
for aid in ['dock-floor','dock-entry','workshop-hut','submarine-yellow']:
 r=json.loads((BASE/f'source/records/{aid}/rig.json').read_text());root=bpy.data.objects[r['groundRootObject']];c=next(c for c in sc.collection.children if root in list(c.all_objects));assets[aid]={'root':root,'collection':c,'rig':r};root.rotation_euler=(0,0,0);root.location=(0,0,0)
spec=importlib.util.spec_from_file_location('judge_native_actions',BASE/'source/blender/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def show(aids):
 for l in sc.view_layers[0].layer_collection.children:l.exclude=False
 for c in sc.collection.children:c.hide_render=c.name not in [assets[a]['collection'].name for a in aids];c.hide_viewport=c.hide_render
 for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection.hide_render
 sc.view_layers[0].update()
def config(frame,root):
 scale=2;sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
 cam=sc.camera;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 cm=json.loads((BASE/'source/records/dock-floor/camera.json').read_text());cam.matrix_world=Matrix(cm['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=0;sc.view_layers[0].update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;sc.view_layers[0].update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(root[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-root[0])/frame[0];sc.view_layers[0].update()
 sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15;sc.render.threads_mode='FIXED';sc.render.threads=6
 return {'frame':frame,'logicalRoot':root,'scale':scale,'cameraName':cam.name,'matrixWorld':[list(x) for x in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'calibration':{n:list(px(v)-px((0,0,0))) for n,v in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]},'rootProjection':list(px((0,0,0))),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'savedCompositor':sc.compositing_node_group.name}
record={'method':'Read immutable b176 native library; isolate exact authored collection; reconstruct camera from dock-floor source record at uniform2x; source materials/lights/compositor retained. In-memory transforms only, no blend saved.','captures':[]}
for mode in ['floor','entry-join','full-context']:
 if mode=='full-context':dirs=['S']
 else:dirs=['N','E','S','W']
 ids={'floor':['dock-floor'],'entry-join':['dock-floor','dock-entry'],'full-context':list(assets)}[mode];show(ids)
 if mode=='full-context':native.apply_clip(assets['submarine-yellow'],assets['submarine-yellow']['rig'],'dock-ready',1,'S',sc)
 for d in dirs:
  angle={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];R=Matrix.Rotation(angle,3,'Z')
  for aid,a in assets.items():
   p={'dock-floor':(0,0,0),'dock-entry':(0,-1.5,0),'workshop-hut':(.78,.35,.23),'submarine-yellow':(-.70,-.42,.23)}[aid];a['root'].location=R@Vector(p);a['root'].rotation_euler.z=angle
  sc.view_layers[0].update();cam=config((448,480),(224,256)) if mode=='floor' else config((576,640),(288,352));path=OUT/f'native-{mode}-{d}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=sc.name)
  record['captures'].append({'mode':mode,'facing':d,'path':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera':cam,'rootTransforms':{aid:[list(x) for x in a['root'].matrix_world] for aid,a in assets.items() if aid in ids}})
  print('JUDGE_CAPTURE',mode,d,flush=True)
 if mode=='full-context':
  meshes=[]
  for o in assets['submarine-yellow']['collection'].all_objects:
   if o.type=='MESH' and not o.hide_render:
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();vs=[e.matrix_world@v.co for v in me.vertices];meshes.append({'name':o.name,'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]});e.to_mesh_clear()
  record['submarineDockReadyVisibleBounds']=meshes
(OUT/'native-capture-evidence.json').write_text(json.dumps(record,indent=2)+'\n')
