"""Recapture two immutable round01 hidden-food slots to quantify renderer rounding."""
import bpy,json,importlib.util,sys
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=HERE/('round02-candidate-pixel-probe' if '--candidate' in sys.argv else 'round02-baseline-pixel-probe');OUT.mkdir(exist_ok=True)
rig=json.loads((OBJ/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];col.hide_viewport=False;col.hide_render=False
spec=importlib.util.spec_from_file_location('native',HERE/'resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
def vis(lc):
 lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
 for c in lc.children:vis(c)
vis(bpy.context.view_layer.layer_collection);bpy.data.objects[rig['armatures'][0]['object']].hide_set(False);bpy.context.view_layer.update();asset=dict(root=root,collection=col)
for clip,frame in [('idle',7),('work',6)]:
 native.apply_clip(asset,rig,clip,frame,'N',bpy.context.scene);bpy.context.view_layer.update();bpy.context.scene.render.filepath=str(OUT/f'{clip}-N-{frame-1:02}.png');bpy.ops.render.render(write_still=True)
