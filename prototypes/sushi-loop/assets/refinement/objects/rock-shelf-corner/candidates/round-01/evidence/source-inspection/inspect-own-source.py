import bpy,json,os
from mathutils import Vector
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=base+'/reviews/preparation-v1/resources/source/source.blend')
scene=bpy.context.scene
rows=[]
for o in scene.objects:
 row={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)}
 if o.type=='MESH':
  coords=[o.matrix_world@v.co for v in o.data.vertices]
  row.update(vertices=len(coords),polygons=len(o.data.polygons),bounds=[[min(v[i] for v in coords) for i in range(3)],[max(v[i] for v in coords) for i in range(3)]],materials=[m.name if m else None for m in o.data.materials])
 if o.type=='LIGHT':row['light']={'energy':o.data.energy,'shape':o.data.shape if hasattr(o.data,'shape') else None,'size':getattr(o.data,'size',None)}
 rows.append(row)
materials=[]
for m in bpy.data.materials:
 materials.append({'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type} for n in m.node_tree.nodes] if m.use_nodes else []})
result={'source':bpy.data.filepath,'objects':rows,'materials':materials,'camera':scene.camera.name if scene.camera else None,'render':{'engine':scene.render.engine,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'aspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'transparent':scene.render.film_transparent}}
open(base+'/source/own-source-inspection.json','w').write(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
