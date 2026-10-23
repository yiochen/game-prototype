import bpy, json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
SOURCE=(BASE/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.data.scenes.new('slate-rock independent source inspection')
bpy.context.window.scene=scene
col=bpy.data.collections['S33_PROP_slate-rock.001']
scene.collection.children.link(col)
col.hide_render=col.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
parts=[]
for o in col.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in o.matrix_world]}
 if o.type=='MESH':
  e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();pts=[e.matrix_world@v.co for v in m.vertices]
  r.update({'baseVertices':[list(v.co) for v in o.data.vertices],'baseFaces':[list(p.vertices) for p in o.data.polygons],'smooth':[p.use_smooth for p in o.data.polygons],'bounds':{'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]},'evaluatedVertices':len(m.vertices),'evaluatedFaces':len(m.polygons),'modifiers':[{'name':mod.name,'type':mod.type,'width':getattr(mod,'width',None),'segments':getattr(mod,'segments',None),'affect':getattr(mod,'affect',None),'angleLimit':getattr(mod,'angle_limit',None)} for mod in o.modifiers],'materials':[]})
  e.to_mesh_clear()
  for mat in o.data.materials:
   mr={'name':mat.name,'diffuse':list(mat.diffuse_color),'nodes':[],'links':[]}
   if mat.use_nodes:
    for n in mat.node_tree.nodes:
     nr={'name':n.name,'type':n.bl_idname,'inputs':{}}
     for inp in n.inputs:
      if hasattr(inp,'default_value'):
       v=inp.default_value
       try:v=list(v)
       except TypeError:pass
       if isinstance(v,(str,int,float,list,bool)):nr['inputs'][inp.name]=v
     mr['nodes'].append(nr)
    mr['links']=[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in mat.node_tree.links]
   r['materials'].append(mr)
 parts.append(r)
(BASE/'source/source-inspection.json').write_text(json.dumps({'source':str(SOURCE),'isolatedCollection':col.name,'parts':parts},indent=2)+'\n')
print(json.dumps({'parts':parts},indent=2))
