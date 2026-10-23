import bpy,sys,json,hashlib,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('water_recipe',P/'source/reproduce.py');recipe=importlib.util.module_from_spec(spec);spec.loader.exec_module(recipe)
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'));sc=bpy.context.scene;root=bpy.data.objects['floor-underwater__root'];floor=bpy.data.objects['floor-underwater__continuous_water'];root.rotation_euler.z=0;camera=recipe.configure(sc);rows=[]
for frame in [1.5,7.5,12.5]:
 sc.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update();p=P/'candidates/round-01/inbetweens'/('frame-%04.1f.png'%frame);p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);r=recipe.measured(sc,root,floor,'S',frame-1,camera);r.update(path=p.relative_to(P).as_posix(),sha256=recipe.sha(p));rows.append(r)
recipe.write(P/'candidates/round-01/inbetweens-records.json',{'projectSHA256':recipe.sha(P/'source/round-01.blend'),'views':rows})
