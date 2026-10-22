"""Read-only joint native ray calibration on both exact approved actor sources."""
import bpy,sys,json,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from food_common_round02 import *
OUT=P.parent/'candidates/round-02'
depths=[.6,.5,.4,.3,.2,.1,0.]
records=[];sources=[]
for runtime in [False,True]:
 c=config(runtime);assert sha(P/c['basis'])==c['basisSHA256'];bpy.ops.wm.open_mainfile(filepath=str(P/c['basis']))
 sc,coll,root,arm,rig,asset,plane=setup(c);coefficient,z,d0=coeffs(plane,root);rr=ray(sc)
 im=bpy.data.images.load(str(P/c['canonical']),check_existing=False);w,h=im.size;pixels=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4)
 yy,xx=np.mgrid[0:h:8,0:w:8];mask=pixels[yy,xx,3]>=.5;xx=xx[mask];yy=yy[mask]
 width=float(plane.data.vertices[1].co.x-plane.data.vertices[0].co.x);height=width*h/w
 local=[Vector(((float(x)+.5)/w*width-width*.5,(float(y)+.5)/h*height,0)) for x,y in zip(xx,yy)]
 source={'food':c['variant'],'sourceSHA256':sha(P/c['basis']),'localXYCoefficient':coefficient,'localZ':z,'rootUniformScale':root.scale.x,'actualD0World':d0,'cameraRay':list(rr),'canonicalSize':[w,h],'canonicalSHA256':sha(P/c['canonical']),'sampleStride':8,'opaqueSamples':len(local),'shader':{'interpolation':image_node(plane).interpolation,'extension':image_node(plane).extension,'colorspace':image_node(plane).image.colorspace_settings.name,'alphaMode':image_node(plane).image.alpha_mode},'drivers':[{'path':f.data_path,'axis':f.array_index,'expression':f.driver.expression,'mapping':{'keyframes':len(f.keyframe_points),'modifiers':[m.type for m in f.modifiers]}} for f in plane.animation_data.drivers]};sources.append(source)
 for clip in rig['clips']:
  if 'hold' not in clip and 'load' not in clip:continue
  for idx in range(12):
   native.apply_clip(asset,rig,clip,idx+1,'N',sc);dg=bpy.context.evaluated_depsgraph_get();e=plane.evaluated_get(dg)
   vertices=[];faces=[]
   for o in coll.all_objects:
    if o.type!='MESH' or o==plane or o.hide_render:continue
    ev=o.evaluated_get(dg);me=ev.to_mesh();start=len(vertices);vertices.extend([ev.matrix_world@v.co for v in me.vertices]);faces.extend([tuple(start+i for i in p.vertices) for p in me.polygons]);ev.to_mesh_clear()
   bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=False)
   points=[e.matrix_world@p for p in local]
   values=[]
   for dmin in depths:
    if dmin>d0+1e-6:continue
    shift=rr*(dmin-d0);visible=0
    for p in points:
     q=p+shift;hit=bvh.ray_cast(q+rr*3,-rr,3-1e-5)
     if hit[0] is None:visible+=1
    values.append({'dMinWorld':dmin,'visibleOpaqueSamples':visible})
   records.append({'food':c['variant'],'clip':clip,'direction':'N','index':idx,'sampleCount':len(points),'depths':values})
   print('CALIBRATION',c['variant'],clip,idx,values,flush=True)
safe=[d for d in depths if all(next((v['visibleOpaqueSamples'] for v in r['depths'] if abs(v['dMinWorld']-d)<1e-8),10**9)==0 for r in records)]
assert safe,'No fully hidden rear solution within the authorized depth interval'
largest=max(safe);selected=max(0,round(largest-.1,8))
assert selected in safe
result={'method':'One joint ray calibration across both exact approved sources/all48 N hold/load frames. Full canonical aspect/fullUV at existing width, alpha>=.5 sampled every8 source pixels; native evaluated opaque body BVH, camera ray from actual saved camera. Select one shared depth0.1world behind largest tested zero-visible rear value as an occlusion margin. Native renders remain final visible evidence.','sources':sources,'testedDepthsWorld':depths,'largestTestedJointZeroVisibleDepthWorld':largest,'selectedSharedDMinWorld':selected,'safeTestedDepthsWorld':safe,'records':records}
write(OUT/'joint-depth-calibration.json',result)
for runtime in [False,True]:
 name='runtime-config-round02.json' if runtime else 'config-round02.json';c=config(runtime);c['dMinWorld']=selected;write(P/name,c)
print('SELECTED SHARED DMIN',selected,flush=True)
