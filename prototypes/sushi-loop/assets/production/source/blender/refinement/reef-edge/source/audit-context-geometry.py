import sys
sys.dont_write_bytecode=True
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Matrix
B=Path(__file__).resolve().parent;O=B.parent;E=O/'candidates/round-01/evidence'
assets={}
for key,file,col in [('edge',B/'round-01.blend','reef-edge'),('middle',B/'resources/canonical-middle02.blend','reef-middle'),('corner',B/'resources/original-context.blend','S33_PROP_reef-corner.001'),('end',B/'resources/original-context.blend','S33_PROP_reef-end.001')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));c=bpy.data.collections[col];sc=next(s for s in bpy.data.scenes if c.name in s.collection.children);bpy.context.window.scene=sc
 def enable(l):
  l.exclude=False;l.hide_viewport=False
  for ch in l.children:enable(ch)
 enable(bpy.context.view_layer.layer_collection)
 for ob in c.all_objects:ob.hide_set(False);ob.hide_viewport=False
 sc.frame_set(1);bpy.context.view_layer.update();root=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None);root.rotation_euler.z=0;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ob=next(o for o in c.all_objects if 'continuous_core' in o.name);ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();m=root.matrix_world.inverted()@ev.matrix_world;vs=[m@v.co for v in me.vertices];rings={}
 for side,axis,p in [('W',0,-.5),('E',0,.5),('N',1,.5)]:rings[side]=[list(v) for v in vs if abs(v[axis]-p)<1e-6]
 assets[key]={'vertices':[list(v) for v in vs],'triangles':[list(t.vertices) for t in me.loop_triangles],'rings':rings,'source':str(file.relative_to(O)),'root':root.name,'collection':c.name};ev.to_mesh_clear()
def transformed(key,side,x,y,a):return [[x+v[0]*math.cos(a)-v[1]*math.sin(a),y+v[0]*math.sin(a)+v[1]*math.cos(a),v[2]] for v in assets[key]['rings'][side]]
contacts=[('middle','E',-1,0,0,'edge','W',0,0,0),('edge','E',0,0,0,'middle','W',1,0,0),('edge','E',0,0,0,'corner','W',1,0,0),('corner','N',1,0,0,'middle','W',1,1,math.pi/2),('middle','E',1,1,math.pi/2,'end','W',1,2,math.pi/2)]
rows=[]
for a,sa,x,y,r,b,sb,xx,yy,rr in contacts:
 va=transformed(a,sa,x,y,r);vb=transformed(b,sb,xx,yy,rr);delta=max([min(math.dist(v,w) for w in vb) for v in va]+[min(math.dist(v,w) for w in va) for v in vb]);rows.append({'a':[a,sa,x,y,r],'b':[b,sb,xx,yy,rr],'aRing':va,'bRing':vb,'maxSymmetricPointDistance':delta})
(E/'context-geometry.json').write_text(json.dumps({'assets':assets,'contacts':rows,'provisionalContext':'Original corner/end material and interior art remain unapproved scaffolds; primary middle-edge-middle is hard field/visual gate. All raw rings measured in actual native root coordinates before global rotation.'},indent=2)+'\n');print(json.dumps([r['maxSymmetricPointDistance'] for r in rows]))
