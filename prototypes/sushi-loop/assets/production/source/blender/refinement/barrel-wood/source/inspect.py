import bpy,json
from pathlib import Path
out={"version":bpy.app.version_string,"scenes":[]}
for sc in bpy.data.scenes:
 d={"name":sc.name,"camera":sc.camera.name if sc.camera else None,"collections":[]}
 for c in sc.collection.children:
  if 'barrel' in c.name.lower():
   d['collections'].append({'name':c.name,'hide_render':c.hide_render,'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dim':list(o.dimensions),'mesh':{'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'smooth':sum(p.use_smooth for p in o.data.polygons)} if o.type=='MESH' else None,'materials':[{'name':m.name,'nodes':[{'type':n.type,'name':n.name,'inputs':{i.name:str(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes]} for m in o.data.materials if m and m.use_nodes] if o.type=='MESH' else [],'custom':dict(o.items())} for o in c.all_objects]})
 out['scenes'].append(d)
Path(__file__).with_name('inspection.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
