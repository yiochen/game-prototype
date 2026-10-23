import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.dont_write_bytecode=True
from common import *
rec,root,col,arm,foodroot,plane=context();sc=bpy.context.scene
rows=[]
def en(l):
 rows.append({'collection':l.collection.name,'exclude':l.exclude,'hideViewport':l.hide_viewport,'isVisible':l.is_visible})
 if l.collection==col:l.exclude=False;l.hide_viewport=False
 for c in l.children:en(c)
en(bpy.context.view_layer.layer_collection)
print('LAYERS',rows,'COLL',col.name,col.hide_viewport,col.hide_render)
col.hide_viewport=False
for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();r=phase('idle','N',0);compact(OUT/'mapping-diagnostic-unexcluded.json',r);print('UNEXCLUDED',r['planeMatrix'],r['planeLocalLocation'])
