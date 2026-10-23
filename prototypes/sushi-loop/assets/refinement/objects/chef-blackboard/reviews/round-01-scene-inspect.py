import bpy,json
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;c=bpy.data.collections['S33_PROP_chef-blackboard'];root=bpy.data.objects['chef-blackboard__root'];face=bpy.data.objects['chef-blackboard__blank_dynamic_face']
lights=[{'name':o.name,'type':o.data.type,'location':list(o.location),'energy':o.data.energy,'size':getattr(o.data,'size',None)} for o in s.objects if o.type=='LIGHT']
meshes=[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]} for o in c.all_objects if o.type=='MESH']
front=[]
ev=face.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];miny=min(p.y for p in pts)
for poly in mesh.polygons:
 world=[ev.matrix_world@mesh.vertices[i].co for i in poly.vertices]
 if max(abs(p.y-miny) for p in world)<1e-6:
  front.append({'worldY':miny,'xRange':[min(p.x for p in world),max(p.x for p in world)],'zRange':[min(p.z for p in world),max(p.z for p in world)],'evaluatedLocalNormal':list(poly.normal)})
ev.to_mesh_clear()
d={'project':bpy.data.filepath,'collections':list(bpy.data.collections.keys()),'objectsByType':{t:len([o for o in s.objects if o.type==t]) for t in set(o.type for o in s.objects)},'meshes':meshes,'faceFrontPlanes':front,'sockets':{n:{'local':list(bpy.data.objects[n].location),'world':list(bpy.data.objects[n].matrix_world.translation),'parent':bpy.data.objects[n].parent.name} for n in ['CB01_socket_recipe_face','CB01_socket_display_face']},'lights':lights,'worldNodes':[x.bl_idname for x in s.world.node_tree.nodes] if s.world.use_nodes else [],'materials':[{'name':m.name,'nodes':[n.bl_idname for n in m.node_tree.nodes] if m.use_nodes else []} for m in bpy.data.materials],'libraries':[l.filepath for l in bpy.data.libraries],'images':[i.filepath for i in bpy.data.images],'fonts':[f.filepath for f in bpy.data.fonts]}
Path(__file__).with_suffix('.json').write_text(json.dumps(d,indent=2)+'\n')
print('JUDGE_SCENE_INSPECTION',len(meshes),'meshes',len(lights),'lights',len(bpy.data.images),'images')
