import bpy,sys,json,math,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True;P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('contact_native',P/'resources/native/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py' and s.get('issue')==33);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
rig=json.loads((P/'resources/inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in sc.collection.children if root in list(c.all_objects));asset={'root':root,'collection':col}
def walk(l):
 yield l
 for c in l.children:yield from walk(c)
for l in walk(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
for c in [col,*list(col.children_recursive)]:c.hide_render=False;c.hide_viewport=False
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=col
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
def hull(points):
 pts=sorted(set((round(v[0],8),round(v[1],8)) for v in points))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lo=[]
 for p in pts:
  while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 hi=[]
 for p in reversed(pts):
  while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def plane(o,evaled=False):
 eo=o.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaled else o;m=eo.to_mesh() if evaled else o.data;v=[eo.matrix_world@p.co for p in m.vertices];pts=[]
 for edge in m.edges:
  a,b=[v[i] for i in edge.vertices]
  if abs(a.z)<1e-7:pts.append(list(a[:2]))
  if a.z*b.z<0:pts.append(list((a+(b-a)*(-a.z/(b.z-a.z)))[:2]))
 h=hull(pts)
 if evaled:eo.to_mesh_clear()
 return {'convexHullXY':h,'area':abs(sum(h[i][0]*h[(i+1)%len(h)][1]-h[(i+1)%len(h)][0]*h[i][1] for i in range(len(h)))/2) if h else 0}
out={}
for d in ['N','E','S','W']:
 native.apply_clip(asset,rig,'idle',frame=1,direction=d,scene=sc);sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
 out[d]={o.name:{'raw':plane(o),'evaluated':plane(o,True)} for o in col.all_objects if o.type=='MESH' and 'base_rock' in o.name}
(P/'ground-contact-measurements.json').write_text(json.dumps({'planeZ':0,'interpretation':'Finite cross sections at nominal ground; not full occupied-cell opacity. Rocks penetrate nominal ground to z=-0.06. No floor flattening law inferred.','contacts':out},indent=2)+'\n')
print('PORTAL_CONTACTS_DONE')
