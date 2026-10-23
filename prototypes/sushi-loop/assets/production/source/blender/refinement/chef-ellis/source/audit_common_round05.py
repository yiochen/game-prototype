import bpy,math,json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

def centroid(o,dg):
 e=o.evaluated_get(dg);return sum((e.matrix_world@v.co for v in e.data.vertices),Vector())/len(e.data.vertices)
def geometry(o,dg):
 e=o.evaluated_get(dg);me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices]
 data={'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'bounds':[[min(v[i] for v in points),max(v[i] for v in points)] for i in range(3)],'nonfiniteVertices':sum(not all(math.isfinite(n) for n in v) for v in points),'nonfiniteNormals':sum(not all(math.isfinite(n) for n in p.normal) for p in me.polygons),'zeroAreaPolygons':sum(p.area<1e-12 for p in me.polygons)}
 e.to_mesh_clear();return data

def contacts(coll,root,arm,dg):
 ae=arm.evaluated_get(dg);palms={side:centroid(next(o for o in coll.all_objects if '__palm_'+side in o.name),dg) for side in ['L','R']}
 # Hidden objects may be omitted from the depsgraph after reopening a saved library.
 # Expose only for attachment evaluation, record original visibility and restore before render.
 prop_objects=[o for o in coll.all_objects if '__held_' in o.name or '__knife_' in o.name or '__utensil' in o.name]
 visibility={o.name:(o.hide_render,o.hide_viewport,o.hide_get()) for o in prop_objects}
 for o in prop_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();exposed=bpy.context.evaluated_depsgraph_get()
 props={o.name:{'matrix':[list(r) for r in o.evaluated_get(exposed).matrix_world],'hide':visibility[o.name][0],'hideViewport':visibility[o.name][1],'sampling':'temporarily exposed exact native owner, original visibility restored'} for o in prop_objects}
 for o in prop_objects:
  r,v,h=visibility[o.name];o.hide_render=r;o.hide_viewport=v;o.hide_set(h)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ae=arm.evaluated_get(dg)
 feet={side:geometry(next(o for o in coll.all_objects if '__minimal_foot_'+side in o.name),dg) for side in ['L','R']}
 dish=next(o for o in coll.all_objects if o.type=='EMPTY' and '__held_' in o.name);knife=next(o for o in coll.all_objects if '__utensil' in o.name)
 midpoint=(palms['L']+palms['R'])*.5
 return {'bones':{b.name:{'head':list(ae.matrix_world@b.head),'tail':list(ae.matrix_world@b.tail),'matrix':[list(r) for r in ae.matrix_world@b.matrix]} for b in ae.pose.bones},'palms':{s:list(v) for s,v in palms.items()},'feet':feet,'props':props,'rootMatrix':[list(r) for r in root.matrix_world],'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'dishToPalmMidpointVector':list(dish.evaluated_get(dg).matrix_world.translation-midpoint),'knifeToRightPalmError':(knife.evaluated_get(dg).matrix_world.translation-palms['R']).length}
