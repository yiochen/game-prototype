from pathlib import Path
import sys,bpy
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
for runtime in [False,True]:
 c=config(runtime);bpy.ops.wm.open_mainfile(filepath=str(P/c['candidate']));sc,co,root,arm,rig,asset,plane=setup(c);enable_saved_device(sc)
 for d in ['N','E','S','W']:
  native.apply_clip(asset,rig,'hold-cucumber' if runtime else 'hold',6,d,sc);out=P.parent/'candidates/round-02'/('tests-'+c['variant']+'-'+d+'.png');sc.render.filepath=str(out);bpy.ops.render.render(write_still=True)
