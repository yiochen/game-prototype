import bpy,json,sys,math
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent
out=BASE/'evidence';out.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'resources/source/original.blend'))
sc=next(s for s in bpy.data.scenes if any(o.name.startswith('reef-middle__root') for o in s.objects));bpy.context.window.scene=sc
report={'blender':bpy.app.version_string,'savedScene':sc.name,'savedCamera':None,'collections':[],'family':{},'externalImages':[]}
if sc.camera:report['savedCamera']={'name':sc.camera.name,'matrix':[list(r) for r in sc.camera.matrix_world],'ortho':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(bpy.context.view_layer.layer_collection):l.exclude=False;l.hide_viewport=False
for c in bpy.data.collections:
 if 'reef-' in c.name:report['collections'].append({'name':c.name,'hide_render':c.hide_render,'hide_viewport':c.hide_viewport,'objects':[o.name for o in c.all_objects]})
for aid in ['reef-middle','reef-edge','reef-corner','reef-end']:
 cols=[c for c in bpy.data.collections if c.name=='S33 '+aid or c.name=='S33 '+aid+'.001' or c.name==aid or c.name.startswith(aid+'__')]
 if not cols:cols=[c for c in bpy.data.collections if any(o.get('assetId')==aid or o.name.startswith(aid+'__root') for o in c.objects)]
 c=cols[0]
 for cc in bpy.data.collections:cc.hide_render=cc!=c;cc.hide_viewport=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 root=next(o for o in c.all_objects if o.name.startswith(aid+'__root'))
 rec={'collection':c.name,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'rootProperties':dict(root.items()),'objects':[]}
 for o in c.all_objects:
  z={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world],'properties':dict(o.items()),'animation':bool(o.animation_data),'modifiers':[m.type for m in o.modifiers]}
  if o.type=='MESH':
   ev=o.evaluated_get(dg);me=ev.to_mesh();pts=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices]
   z.update(vertices=[list(v) for v in pts],faces=[{'vertices':list(p.vertices),'normal':list(p.normal),'material':p.material_index,'smooth':p.use_smooth} for p in me.polygons],bounds=[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)],uvLayers=list(me.uv_layers.keys()),shapeKeys=bool(o.data.shape_keys),materials=[])
   for m in me.materials:
    z['materials'].append({'name':m.name,'props':dict(m.items()),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:(list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value) for i in n.inputs if hasattr(i,'default_value') and i.type in ['VALUE','RGBA','VECTOR','INT','BOOLEAN']}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]})
   ev.to_mesh_clear()
  rec['objects'].append(z)
 report['family'][aid]=rec
for i in bpy.data.images:
 if i.source=='FILE':report['externalImages'].append({'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file)})
(out/'native-inspection.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print('INSPECTED',[(aid,len(v['objects'])) for aid,v in report['family'].items()])
