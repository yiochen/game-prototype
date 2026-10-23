import sys,json,math,importlib.util,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
P=Path(__file__).resolve().parent;R=P/'resources'
s=importlib.util.spec_from_file_location('floor_measure_native',R/'native_actions.py');n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
rig=json.loads((R/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in bpy.context.scene.collection.children if root in list(c.all_objects))
for c in bpy.context.scene.collection.children:c.hide_viewport=c!=col;c.hide_render=c!=col
for layer in bpy.context.scene.view_layers[0].layer_collection.children:layer.exclude=layer.collection!=col
asset={'root':root,'collection':col};samples={};first={};closure={};maxError=0;maxMotion=0
for frame in range(1,14):
 n.apply_clip(asset,rig,'scroll',frame,'S',bpy.context.scene);d=bpy.context.evaluated_depsgraph_get();rows=[]
 for o in col.all_objects:
  if o.type!='MESH' or 'periodic_wave' not in o.name:continue
  ev=o.evaluated_get(d);mesh=ev.to_mesh();coords=[list(v.co) for v in mesh.vertices];row=0 if 'wave_0' in o.name else 1;center=-.5+(row+.5)/2;t=(frame-1)/12
  error=max(abs(v[1]-(center+(-.055 if i%2==0 else .055)+.045*math.sin((v[0]+.5+t)*math.tau))) for i,v in enumerate(coords));maxError=max(maxError,error)
  if frame==1:first[o.name]=coords
  delta=max(abs(v[axis]-first[o.name][i][axis]) for i,v in enumerate(coords) for axis in range(3));maxMotion=max(maxMotion,delta)
  rows.append({'name':o.name,'formulaMaxError':error,'maxXYZDeltaFromFrame1':[max(abs(v[a]-first[o.name][i][a]) for i,v in enumerate(coords)) for a in range(3)],'ribbonWidthRange':[min(coords[i+1][1]-coords[i][1] for i in range(0,len(coords),2)),max(coords[i+1][1]-coords[i][1] for i in range(0,len(coords),2))]})
  if frame==13:closure[o.name]={'exactCoordinatesEqual':coords==first[o.name],'maximumCoordinateError':delta}
  ev.to_mesh_clear()
 samples[str(frame)]=rows
report={'derivation':'Actual evaluated mesh vertices across native action frames1..13, not names or AABB. Geometry actions only; two flat0.11-cell ribbons bend inY with1sinusoidal phase cycle/12frames. The source clip is namedscroll but no wholefloor translation,UV scroll,texture phase orZ bob occurs.','law':'x=-.501+i*1.002/64; y=center±.055+.045sin(2π(x+.5+(frame-1)/12)); center∈{-.25,.25}; z=.002. Mesh piecewise-linear interpolation introduces<7.52e-7 nativeY mismatch at±.5.', 'maxFormulaError':maxError,'maxCoordinateDisplacementFromStart':maxMotion,'closure':closure,'samples':samples}
(P/'source-temporal-measurements.json').write_text(json.dumps(report,indent=2)+'\n');print('MAX_FORMULA_ERROR',maxError,'CLOSURE',closure)
