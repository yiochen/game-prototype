import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
out=Path(__file__).resolve().parents[1]
asset='creature-fish'
colls=[c for c in bpy.data.collections if c.name==asset or c.name.startswith(asset+'__')]
owned=[o for o in bpy.data.objects if o.name.startswith(asset+'__')]
# Enable every collection ancestor by recursive traversal, then owned object visibility.
def enable_lc(lc):
 found=lc.collection in colls
 for child in lc.children: found=enable_lc(child) or found
 if found: lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_render=False;lc.collection.hide_viewport=False
 return found
enable_lc(bpy.context.view_layer.layer_collection)
for o in owned:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get();dg.update()
def matrix(m):return [list(r) for r in m]
def bounds(pts):return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]} if pts else None
objs=[]
for o in owned:
 raw=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
 ev=[]
 if o.type=='MESH':
  e=o.evaluated_get(dg); m=e.to_mesh();ev=[e.matrix_world@v.co for v in m.vertices];e.to_mesh_clear()
 objs.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':matrix(o.matrix_world),'rawBounds':bounds(raw),'evaluatedBounds':bounds(ev),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if hasattr(o.data,'materials') else [],'modifiers':[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers],'vertexGroups':[v.name for v in o.vertex_groups] if o.type=='MESH' else [],'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else [],'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform} for b in o.data.bones] if o.type=='ARMATURE' else []})
materials={}
for o in owned:
 if hasattr(o.data,'materials'):
  for m in o.data.materials:
   if m and m.name not in materials:
    materials[m.name]={'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(int,float,str,list,tuple,Vector))}} for n in m.node_tree.nodes] if m.use_nodes else []}
s=bpy.context.scene
result={'blend':bpy.data.filepath,'blender':bpy.app.version_string,'sceneFrame':s.frame_current,'collections':[c.name for c in colls],'ownedCount':len(owned),'objects':objs,'materials':materials,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None),'matrix':matrix(o.matrix_world)} for o in s.objects if o.type=='LIGHT'],'activeCamera':{'name':s.camera.name,'type':s.camera.data.type,'matrix':matrix(s.camera.matrix_world),'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y]} if s.camera else None,'sceneRender':{'engine':s.render.engine,'size':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'transparent':s.render.film_transparent},'actions':[{'name':a.name,'range':list(a.frame_range)} for a in bpy.data.actions if asset in a.name],'external':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE']}}
(out/'actual-source-inspection.json').write_text(json.dumps(result,indent=2))
print('INSPECTED',len(owned),'objects')
