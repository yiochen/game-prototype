import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.dont_write_bytecode=True
from common import *
r=phase('idle','N',0);keys=['rootMatrix','cameraMatrix','foodRootMatrix','planeMatrix','planeLocalLocation','planeLocalRotation','foodVerticesWorld','foodCornersNative','semanticSupportLocal','semanticSupportNative','widthWorld','heightWorld','visibility'];print(json.dumps({k:r[k] for k in keys if k!='visibility'},indent=2));print('planevis',{k:v for k,v in r['visibility'].items() if 'image_plane' in k or 'held_dish' in k});compact(OUT/'mapping-diagnostic-final-reassert.json',r)
