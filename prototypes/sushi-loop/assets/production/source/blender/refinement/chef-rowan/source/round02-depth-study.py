"""Depth-only representative study; reads immutable round01 baseline, never saves it."""
import bpy,math,json,importlib.util
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=HERE/'round02-depth-study';OUT.mkdir(exist_ok=True)
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());scene=bpy.context.scene
root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001']
col.hide_viewport=False;col.hide_render=False
for o in col.objects:o.hide_set(False)
def unhide(lc):
 lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
 for c in lc.children:unhide(c)
unhide(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update()
food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[food.name+'__image_plane']
spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
asset=dict(root=root,collection=col)
def depth(d):
 k=d/root.scale.x*math.cos(math.radians(35));plane.location.z=d/root.scale.x*math.sin(math.radians(35))
 for f in plane.animation_data.drivers:
  if f.data_path=='location':f.driver.expression=f'-{"sin" if f.array_index==0 else "cos"}(facing)*{k!r}'
 plane['camera_ray_depth_bias_world_cells']=d;bpy.context.view_layer.update()
records=[]
for d in [0,.15,.3,.45]:
 depth(d)
 for clip,frame in [('hold',1),('load',6)]:
  for direction in ['N','E','S','W']:
   native.apply_clip(asset,rig,clip,frame,direction,scene);bpy.context.view_layer.update()
   path=OUT/f'd{round(d*100):02}-{clip}-{direction}-{frame:02}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   records.append(dict(d=d,clip=clip,frame=frame,direction=direction,path=path.name))
(OUT/'records.json').write_text(json.dumps(records,indent=2)+'\n')
