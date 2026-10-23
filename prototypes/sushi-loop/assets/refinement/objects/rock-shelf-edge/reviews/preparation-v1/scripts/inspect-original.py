import bpy, json, math, hashlib, os
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parent.parent
scenes=[]
for sc in bpy.data.scenes:
 scenes.append({'name':sc.name,'objects':len(sc.objects),'camera':sc.camera.name if sc.camera else None,'render':{'engine':sc.render.engine,'x':sc.render.resolution_x,'y':sc.render.resolution_y,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'eevee':{p.identifier:getattr(sc.eevee,p.identifier) for p in sc.eevee.bl_rna.properties if p.identifier in ['taa_render_samples','use_gtao','use_soft_shadows']}})
collections=[c for c in bpy.data.collections if c.name=='rock-shelf-edge']
if not collections: collections=[c for c in bpy.data.collections if 'rock-shelf-edge' in c.name]
report={'blender':bpy.app.version_string,'scenes':scenes,'collections':[]}
for c in collections:
 cd={'name':c.name,'hide_render':c.hide_render,'objects':[]}
 for o in c.all_objects:
  od={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix_world':[list(r) for r in o.matrix_world],'hide_render':o.hide_render,'props':{k:o[k] for k in o.keys()}}
  if o.type=='MESH':
   od['vertices']=[list(v.co) for v in o.data.vertices];od['polygons']=[{'vertices':list(p.vertices),'normal':list(p.normal),'material':p.material_index,'smooth':p.use_smooth} for p in o.data.polygons]
   od['modifiers']=[{'name':m.name,'type':m.type,**{p.identifier:getattr(m,p.identifier) for p in m.bl_rna.properties if p.identifier in ['width','segments','limit_method','angle_limit','keep_sharp','weight','mode','thickness','offset']}} for m in o.modifiers]
   od['materials']=[]
   for mat in o.data.materials:
    md={'name':mat.name,'diffuse':list(mat.diffuse_color),'use_nodes':mat.use_nodes,'nodes':[],'links':[]}
    if mat.use_nodes:
     for n in mat.node_tree.nodes:
      nd={'name':n.name,'type':n.type,'operation':getattr(n,'operation',None),'inputs':{}}
      for inp in n.inputs:
       try: val=inp.default_value;nd['inputs'][inp.name]=list(val) if hasattr(val,'__len__') else val
       except: pass
      if n.type=='VALTORGB':nd['color_ramp']=[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
      md['nodes'].append(nd)
     md['links']=[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in mat.node_tree.links]
    od['materials'].append(md)
  cd['objects'].append(od)
 report['collections'].append(cd)
(BASE/'source-inspection.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print(json.dumps({'scenes':scenes,'collections':[{'name':c['name'],'objects':[{'name':o['name'],'type':o['type'],'vertices':len(o.get('vertices',[])),'materials':[m['name'] for m in o.get('materials',[])]} for o in c['objects']]} for c in report['collections']]}))
