import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]
brief=json.loads((BASE/'brief.json').read_text())
results=[]
for source in [brief['source'],brief['supplementalSources'][0]]:
 path=source['project'];bpy.ops.wm.open_mainfile(filepath=path)
 scene=bpy.context.scene;dep=bpy.context.evaluated_depsgraph_get()
 rec={'project':path,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'version':bpy.app.version_string,'scene':scene.name,'properties':dict(scene.items()),'render':{'engine':scene.render.engine,'samples':scene.cycles.samples,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'gamma':scene.view_settings.gamma},'objects':[],'materials':[]}
 for o in scene.objects:
  r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':[list(x) for x in o.matrix_world]}
  if o.type=='MESH':
   e=o.evaluated_get(dep);m=e.to_mesh();pts=[e.matrix_world@v.co for v in m.vertices]
   r.update({'vertices':len(m.vertices),'faces':len(m.polygons),'materialSlots':[x.name if x else None for x in o.data.materials],'bounds':{'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}});e.to_mesh_clear()
  elif o.type=='LIGHT':r.update({'energy':o.data.energy,'color':list(o.data.color),'size':getattr(o.data,'size',None)})
  elif o.type=='CAMERA':r.update({'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]})
  rec['objects'].append(r)
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  ns=[]
  for n in m.node_tree.nodes:
   d={'name':n.name,'type':n.type,'inputs':{}}
   for s in n.inputs:
    if not hasattr(s,'default_value'):continue
    v=s.default_value
    try:v=list(v)
    except TypeError:pass
    if isinstance(v,(float,int,str,bool,list)):d['inputs'][s.name]=v
   if n.type=='VALTORGB':d['ramp']=[(x.position,list(x.color)) for x in n.color_ramp.elements]
   ns.append(d)
  rec['materials'].append({'name':m.name,'nodes':ns,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]})
 results.append(rec)
(BASE/'source/inspection.json').write_text(json.dumps(results,indent=2)+'\n')
print('INSPECTED',[(x['scene'],len(x['objects'])) for x in results])
