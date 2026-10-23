import bpy,json,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1])
def mat(m): return [list(r) for r in m]
def anim(id):
 a=getattr(id,'animation_data',None)
 return None if not a else {'action':a.action.name if a.action else None,'drivers':len(a.drivers),'nla':len(a.nla_tracks)}
collections=[]
for c in bpy.data.collections:
 if 'rock-half-width' in c.name:
  records=[]
  for o in c.all_objects:
   records.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':mat(o.matrix_world),'matrixLocal':mat(o.matrix_local),'dimensions':list(o.dimensions),'hideViewport':o.hide_viewport,'hideRender':o.hide_render,'hidden':o.hide_get(),'custom':dict(o.items()),'animation':anim(o),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers],'materials':[s.material.name if s.material else None for s in o.material_slots]})
  collections.append({'name':c.name,'custom':dict(c.items()),'hideViewport':c.hide_viewport,'hideRender':c.hide_render,'objects':records})
result={'blender':bpy.app.version_string,'file':bpy.data.filepath,'collections':collections,'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None,'frame':s.frame_current,'resolution':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'world':s.world.name if s.world else None,'viewlayers':[{'name':v.name,'use':v.use} for v in s.view_layers]} for s in bpy.data.scenes],'libraries':[l.filepath for l in bpy.data.libraries]}
out.write_text(json.dumps(result,indent=2,default=str)+'\n')
