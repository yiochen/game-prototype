import bpy,json,importlib.util
from pathlib import Path
D=Path(__file__).resolve().parent;OUT=D.parent.parent/'candidates/round-01/light-trials';OUT.mkdir(exist_ok=True)
s=bpy.context.scene
for look in ['AgX - Medium High Contrast','AgX - Medium Low Contrast','AgX - None']:
 try:
  s.view_settings.view_transform='AgX';s.view_settings.look=look
 except Exception:continue
 s.render.filepath=str(OUT/(look+'.png'));bpy.ops.render.render(write_still=True)
s.view_settings.view_transform='Standard';s.view_settings.look='None'
for o in s.objects:
 if o.type=='LIGHT':o.data.energy*=.6
s.render.filepath=str(OUT/'standard-light60.png');bpy.ops.render.render(write_still=True)
