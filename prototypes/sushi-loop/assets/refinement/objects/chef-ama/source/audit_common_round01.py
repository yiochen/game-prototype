import bpy,math,json
import hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

def centroid(o,dg):
 e=o.evaluated_get(dg);return sum((e.matrix_world@v.co for v in e.data.vertices),Vector())/len(e.data.vertices)
def geometry(o,dg):
 e=o.evaluated_get(dg);me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices]
 data={'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'bounds':[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)],'nonfiniteVertices':sum(not all(math.isfinite(n) for n in v) for v in points),'nonfiniteNormals':sum(not all(math.isfinite(n) for n in p.normal) for p in me.polygons),'zeroAreaPolygons':sum(p.area<1e-12 for p in me.polygons)}
 e.to_mesh_clear();return data

def surface(o,dg):
 e=o.evaluated_get(dg);me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];faces=[list(p.vertices) for p in me.polygons];e.to_mesh_clear()
 return points,faces

def near_surface(a,b,dg):
 ap,af=surface(a,dg);bp,bf=surface(b,dg);tree=BVHTree.FromPolygons(bp,bf,all_triangles=False)
 pairs=[(tree.find_nearest(p),p) for p in ap];(q,n,face,distance),p=min(pairs,key=lambda x:x[0][3])
 return {'distanceWorld':distance,'pointA':list(p),'nearestPointB':list(q),'objects':[a.name,b.name],'method':'evaluated world mesh vertex to triangulated mesh surface nearest point; intersecting surfaces require visual occlusion review'}

def actual_surfaces(coll,dg,palms):
 def obj(token):return next(o for o in coll.all_objects if token in o.name)
 feet={};hands={}
 for side in ['L','R']:
  foot=obj('__minimal_foot_'+side);pts,faces=surface(foot,dg)
  feet[side]={'minimumActualVertexZ':min(v.z for v in pts),'groundVertexCount':sum(abs(v.z)<1e-6 for v in pts),'bounds':[[min(v[i] for v in pts),max(v[i] for v in pts)] for i in range(3)]}
  palm=obj('__palm_'+side);thumb=obj('__thumb_'+side)
  sleeve=next(o for o in coll.all_objects if '__arm_'+side in o.name or '__R01_rounded_arm_'+side in o.name)
  hands[side]={'sleeveToPalm':near_surface(sleeve,palm,dg),'thumbToPalm':near_surface(thumb,palm,dg)}
 handle=obj('__knife_handle');blade=obj('__knife_blade');plane=obj('__image_plane');pp,pf=surface(plane,dg)
 # Source image quad bottom edge: local y0, source alpha rectangle bottom is plate contact.
 pe=plane.evaluated_get(dg);local=list(pe.data.vertices);ymin=min(v.co.y for v in local);bottom=[pe.matrix_world@v.co for v in local if abs(v.co.y-ymin)<1e-6];bottompoint=sum(bottom,Vector())/len(bottom)
 midpoint=(palms['L']+palms['R'])*.5
 return {'feet':feet,'hands':hands,'knifeGrip':{'handleToRightPalmSurface':near_surface(handle,obj('__palm_R'),dg),'handleToRightThumbSurface':near_surface(handle,obj('__thumb_R'),dg),'bladeToHandleSurface':near_surface(blade,handle,dg)},'dish2DInsert':{'nativePlaneCorners':[list(v) for v in pp],'alphaRectangleBottomWorldMidpoint':list(bottompoint),'planeBottomToPalmMidpointVector':list(bottompoint-midpoint),'sourceDepthBiasHonored':True,'representation':'original packed2D image plane, not rebuilt native3D plate','method':'evaluated source native plane bottom edge using preserved alpha rectangle registration'}}

def contacts(coll,root,arm,dg):
 ae=arm.evaluated_get(dg);palms={side:centroid(next(o for o in coll.all_objects if '__palm_'+side in o.name),dg) for side in ['L','R']}
 # Hidden objects may be omitted from the depsgraph after reopening a saved library.
 # Expose only for attachment evaluation, record original visibility and restore before render.
 prop_objects=[o for o in coll.all_objects if '__held_' in o.name or '__knife_' in o.name or '__utensil' in o.name]
 visibility={o.name:(o.hide_render,o.hide_viewport,o.hide_get()) for o in prop_objects}
 for o in prop_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();exposed=bpy.context.evaluated_depsgraph_get()
 measurements=actual_surfaces(coll,exposed,palms)
 props={o.name:{'matrix':[list(r) for r in o.evaluated_get(exposed).matrix_world],'hide':visibility[o.name][0],'hideViewport':visibility[o.name][1],'sampling':'temporarily exposed exact native owner, original visibility restored'} for o in prop_objects}
 for o in prop_objects:
  r,v,h=visibility[o.name];o.hide_render=r;o.hide_viewport=v;o.hide_set(h)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dg)
 feet={side:geometry(next(o for o in coll.all_objects if '__minimal_foot_'+side in o.name),dg) for side in ['L','R']}
 dish=next(o for o in coll.all_objects if o.type=='EMPTY' and '__held_' in o.name);knife=next(o for o in coll.all_objects if '__utensil' in o.name)
 midpoint=(palms['L']+palms['R'])*.5
 return {'actualSurfaceContacts':measurements,'bones':{b.name:{'head':list(ae.matrix_world@b.head),'tail':list(ae.matrix_world@b.tail),'matrix':[list(r) for r in ae.matrix_world@b.matrix]} for b in ae.pose.bones},'palms':{s:list(v) for s,v in palms.items()},'feet':feet,'props':props,'rootMatrix':[list(r) for r in root.matrix_world],'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'dishToPalmMidpointVector':list(dish.evaluated_get(dg).matrix_world.translation-midpoint),'knifeToRightPalmError':(knife.evaluated_get(dg).matrix_world.translation-palms['R']).length}

def food_signature(coll):
 o=next(o for o in coll.all_objects if '__image_plane' in o.name)
 im=next(n.image for n in o.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
 drivers=[]
 for obj in [o,o.parent]:
  for fc in (obj.animation_data.drivers if obj.animation_data else []):
   drivers.append({'owner':obj.name,'path':fc.data_path,'index':fc.array_index,'expression':fc.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path,'bone':t.bone_target,'transformType':t.transform_type,'transformSpace':t.transform_space} for t in v.targets]} for v in fc.driver.variables]})
 return {'object':o.name,'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'uv':[list(v.uv) for v in o.data.uv_layers.active.data],'packedImageSHA256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None,'drivers':drivers}
