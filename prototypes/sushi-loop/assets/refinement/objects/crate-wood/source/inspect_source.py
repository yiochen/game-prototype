import bpy,json,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent
root=bpy.data.objects['crate-wood__root']
for s in bpy.data.scenes:
 if root.name in s.objects:
  bpy.context.window.scene=s
  def show(l):
   l.exclude=False;l.hide_viewport=False
   l.collection.hide_viewport=False
   for child in l.children:show(child)
  show(s.view_layers[0].layer_collection)
  s.view_layers[0].update()
  break
cols=[c for c in bpy.data.collections if root.name in c.all_objects]
objects=[o for o in cols[0].all_objects]
out={'blender':bpy.app.version_string,'root':{'name':root.name,'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale),'properties':dict(root.items())},'collections':[c.name for c in cols],'objects':[],'scenes':[]}
for o in objects:
 rec={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world],'properties':dict(o.items())}
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices]
  rec.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),bounds=[[min(pt[i] for pt in pts) for i in range(3)],[max(pt[i] for pt in pts) for i in range(3)]],modifiers=[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],materials=[])
  for m in o.data.materials:
   rec['materials'].append({'name':m.name,'nodes':[{'type':n.type,'label':n.label,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and not isinstance(i.default_value,str)}} for n in m.node_tree.nodes]})
 out['objects'].append(rec)
for s in bpy.data.scenes:
 out['scenes'].append({'name':s.name,'properties':dict(s.items()),'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'camera':s.camera.name if s.camera else None,'rootScene':root.name in s.objects,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'location':list(o.location)} for o in s.objects if o.type=='LIGHT']})
(p/'source-inspection.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
print(json.dumps({'root':out['root'],'collections':out['collections'],'objects':[{k:o[k] for k in ('name','type','dimensions','location','rotation','parent','bounds','modifiers') if k in o} for o in out['objects']],'scenes':out['scenes']},indent=2,default=str))
