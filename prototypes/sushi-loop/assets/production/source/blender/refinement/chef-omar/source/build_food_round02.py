"""Reproduce only the frozen canonical image/UV/aspect and v3 XYZ driver whitelist."""
import bpy,sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
for runtime in [False,True]:
 c=config(runtime);assert sha(P/c['basis'])==c['basisSHA256'];assert c['dMinWorld'] is not None
 bpy.ops.wm.open_mainfile(filepath=str(P/c['basis']));sc,coll,root,arm,rig,asset,plane=setup(c)
 coefficient,z,d0=coeffs(plane,root);assert 0<=c['dMinWorld']<=d0
 yaw_before=next(f for f in plane.animation_data.drivers if f.data_path=='rotation_euler' and f.array_index==2)
 yaw_expr=yaw_before.driver.expression
 width,height,im=canonicalize(c,plane)
 # The canonical-v2 source-law baseline is a separate saved diagnostic project.
 im.filepath='//'+Path(c['canonical']).name;save_library(P/c['canonicalBaseline'],sc,rig)
 im.filepath='//round-02-resources/'+Path(c['canonical']).name
 expressions=install_law(plane,root,c['dMinWorld'],coefficient,z,d0)
 assert yaw_before.driver.expression==yaw_expr
 native.apply_clip(asset,rig,next(iter(rig['clips'])),1,'S',sc)
 save_library(P/c['candidate'],sc,rig)
 c['candidateSHA256']=sha(P/c['candidate']);c['canonicalBaselineSHA256']=sha(P/c['canonicalBaseline']);c['measuredD0World']=d0;c['localXYCoefficient']=coefficient;c['originalLocalZ']=z;c['canonicalLocalWidth']=width;c['canonicalLocalHeight']=height;c['driverExpressionsXYZ']=expressions;c['preservedYawExpression']=yaw_expr
 write(P/('runtime-recipe-round02.json' if runtime else 'recipe-round02.json'),c)
 print('BUILT',c['candidate'],c['candidateSHA256'],c['variant'],'dMin',c['dMinWorld'],flush=True)
