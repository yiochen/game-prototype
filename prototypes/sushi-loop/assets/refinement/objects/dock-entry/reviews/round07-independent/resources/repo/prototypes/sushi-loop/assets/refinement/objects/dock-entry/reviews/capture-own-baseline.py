import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree
ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');OUT=ROOT/'prototypes/sushi-loop/assets/refinement/objects/dock-entry/reviews';sc=bpy.context.scene
for vl in sc.view_layers:
 def enable(lc):
  lc.exclude=False;lc.hide_viewport=False
  for child in lc.children:enable(child)
 enable(vl.layer_collection)
for c in bpy.data.collections:c.hide_viewport=False;c.hide_render=False
entry=bpy.data.collections['S33_PROP_dock-entry.001'];floor=bpy.data.collections['S33_PROP_dock-floor.001'];er=bpy.data.objects['dock-entry__root.001'];fr=bpy.data.objects['dock-floor__root.001']
allowed=set(entry.all_objects)|set(floor.all_objects)
for o in sc.objects:
 o.hide_set(False);o.hide_viewport=False;o.hide_render= o not in allowed and o.type not in ['CAMERA','LIGHT']
bpy.context.view_layer.update()
raw={'library':bpy.data.filepath,'sourceSHA256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','objects':[],'profiles':[],'captures':[]}
bvhs={}
for c in [entry,floor]:
 vs=[];fs=[]
 for o in c.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[ev.matrix_world@x.co for x in me.vertices];polys=[list(p.vertices) for p in me.polygons];raw['objects'].append({'name':o.name,'verticesWorld':[list(x) for x in v],'polygons':polys,'matrixWorld':[list(row) for row in ev.matrix_world]});off=len(vs);vs+=v;fs += [[i+off for i in f] for f in polys];ev.to_mesh_clear()
 bvhs[c.name]=BVHTree.FromPolygons(vs,fs,all_triangles=False)
def hit(tree,x,y):
 p,n,idx,d=tree.ray_cast(Vector((x,y,2)),Vector((0,0,-1)),4)
 return None if p is None else [*p]
for x in [0,.006,.02,.07,.10,.12,.24,.375,.38,.43,.479]:
 for y in [-.500,-.495,-.483,-.375,-.267,-.255,-.250,-.245,-.233,-.125,-.017,-.005,0,.005,.013,.017,.125,.233,.245,.25,.255,.267,.375,.483,.495,.5]:
  raw['profiles'].append({'x':x,'entryLocalY':y,'entryTop':hit(bvhs[entry.name],x,y),'floorTopAtJoinedXY':hit(bvhs[floor.name],x,y-1.5)})
cam=sc.camera;rec=json.loads((OUT.parent/'inputs/source-camera.json').read_text());cam.matrix_world=Matrix(rec['camera']['worldMatrix']);cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';sc.render.engine='BLENDER_EEVEE';sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=rec['camera']['pixelAspect'][0];sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
# All changes stay in this background process; no project is written.
def setup(frame,root):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*frame[0],(1-p.y)*frame[1]))
 b=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(root[1]-b.y)/dy;bpy.context.view_layer.update();p=px((0,0,0));return {'frameLogical':frame,'rootLogical':list(p),'unitX':list(px((1,0,0))-p),'unitDepth':list(px((0,-1,0))-p),'unitHeight':list(px((0,0,1))-p),'cameraWorld':[list(row) for row in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]}
for f,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 er.rotation_euler.z=a;fr.rotation_euler.z=a;er.location=(0,0,0);fr.location=(0,0,0)
 floor.hide_render=True
 for o in floor.all_objects:o.hide_render=True
 cal=setup((192,352),(96,248));p=OUT/f'own-native-entry-{f}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);raw['captures'].append({'kind':'standalone-entry','facing':f,'path':p.name,'calibration':cal})
 floor.hide_render=False
 for o in floor.all_objects:o.hide_render=False
 er.location=Matrix.Rotation(a,4,'Z')@Vector((0,-1.5,0));cal=setup((640,640),(320,320));p=OUT/f'own-native-joined-{f}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);raw['captures'].append({'kind':'floor-entry-depth-tested','facing':f,'path':p.name,'entryRootWorld':list(er.location),'calibration':cal})
(OUT/'own-native-geometry-and-captures.json').write_text(json.dumps(raw,indent=2)+'\n')
