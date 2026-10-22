import bpy, json, os, sys, math
from pathlib import Path
from mathutils import Matrix, Vector, Euler, Quaternion, Color
sys.dont_write_bytecode = True
OUT = Path(__file__).parent
def val(v):
    if isinstance(v,(Matrix,Vector,Euler,Quaternion,Color)): return [val(x) for x in v]
    if hasattr(v, '__iter__') and not isinstance(v,str): return [val(x) for x in v]
    return v
def props(x): return {k:val(x[k]) for k in x.keys() if k!='_RNA_UI'}
cs=[c for c in bpy.data.collections if 'floor-underwater' in c.name]
result={'blender':bpy.app.version_string,'filepath':bpy.data.filepath,'collections':[],'scenes':[], 'cameras':[]}
for s in bpy.data.scenes:
 result['scenes'].append({'name':s.name,'camera':s.camera.name if s.camera else None,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'engine':s.render.engine,'filmTransparent':s.render.film_transparent,'frame':[s.frame_start,s.frame_end,s.frame_current], 'fps':s.render.fps,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'world':s.world.name if s.world else None})
for c in cs:
 objects=[]
 for o in c.all_objects:
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':val(o.matrix_world),'location':val(o.location),'rotation':val(o.rotation_euler),'scale':val(o.scale),'properties':props(o),'hideRender':o.hide_render,'materials':[x.name for x in o.data.materials] if o.type=='MESH' else []}
  if o.type=='MESH':
   d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),edges=len(o.data.edges),uvLayers=[x.name for x in o.data.uv_layers],vertexNormals=[list(o.data.vertices[i].normal) for i in range(min(4,len(o.data.vertices)))],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers],shapeKeys=[{'name':k.name,'value':k.value,'min':k.slider_min,'max':k.slider_max} for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [])
  objects.append(d)
 result['collections'].append({'name':c.name,'hideRender':c.hide_render,'properties':props(c),'objects':objects})
for o in bpy.data.objects:
 if o.type=='CAMERA': result['cameras'].append({'name':o.name,'type':o.data.type,'matrix':val(o.matrix_world),'orthoScale':o.data.ortho_scale,'properties':props(o)})
(OUT/'source-collection-first-inspection.json').write_text(json.dumps(result,indent=2))
print('AUDIT',[(c['name'],len(c['objects'])) for c in result['collections']])
