import bpy,sys,importlib.util,math,json
from pathlib import Path
BASE=Path(__file__).resolve().parents[3]/'assets/production/source/blender'
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,BASE/file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
C=module('size_c','character_builders.py');H=module('size_h','character_composition.py');F=module('size_f','food_belt_builders.py');R=module('size_r','capture_runtime.py');S=module('size_s','catalog_style.py')
scene=bpy.data.scenes.new('Held plate size comparison');bpy.context.window.scene=scene;R.SCENE_NAME=scene.name
out=Path('/private/tmp/s33-held-size-comparison');out.mkdir(exist_ok=True)
for width in [.4,.35]:
 for collection in list(scene.collection.children):collection.hide_render=True
 H.SPRITE_WIDTH_CELLS=width;a=C.create_character('chef_lena');H.add_held_props(a,F,'dish-salmon');S.apply(a,'chef-lena')
 for clip,phase in [('hold',0.),('load',.5)]:
  a['pose'](clip,phase);a['root'].rotation_euler.z=0
  R.configure_camera('character-orthographic',(192,320),(96,248),2)
  scene.render.filepath=str(out/(clip+'-'+str(width)+'.png'));bpy.ops.render.render(write_still=True,scene=scene.name)
