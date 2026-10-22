import bpy,pathlib,json
out=pathlib.Path(__file__).parent
c=bpy.data.collections['S33_FB_belt-straight-n.001']
s=bpy.data.scenes.new('Judge read-only family inspection');s.collection.children.link(c);bpy.context.window.scene=s;c.hide_viewport=False;c.hide_render=False
for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
d={'blend':bpy.data.filepath,'collection':c.name,'objects':[],'cameras':[],'resources':[]}
for o in c.all_objects:
 rec={'name':o.name,'rotationZ':o.rotation_euler.z,'parent':o.parent.name if o.parent else None}
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices];rec['bounds']=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]];rec['materials']=[m.name for m in o.data.materials if m]
 d['objects'].append(rec)
for sc in bpy.data.scenes:
 if sc.camera:
  cam=sc.camera;d['cameras'].append({'scene':sc.name,'name':cam.name,'worldMatrix':[[float(v) for v in row] for row in cam.matrix_world],'ortho':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]})
for o in c.all_objects:
 if o.type!='MESH':continue
 for m in o.data.materials:
  if m and m.use_nodes:
   for n in m.node_tree.nodes:
    if n.type=='TEX_IMAGE':d['resources'].append({'material':m.name,'image':n.image.name if n.image else None})
(out/'native-family-inspection.json').write_text(json.dumps(d,indent=2))
print(json.dumps({'cameras':d['cameras'],'rootOrient':[(o['name'],o['rotationZ']) for o in d['objects'] if o['name'].endswith(('root.001','orientation.001'))],'resources':d['resources']}))
