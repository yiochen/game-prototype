import bpy,json,pathlib
OUT=pathlib.Path(__file__).parent
s=bpy.context.scene
matches=[c for c in bpy.data.collections if 'shelf' in c.name.lower()]
def mat(m):
    return {'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(int,float,bool,str)) or hasattr(i,'default_value') and hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str)}} for n in m.node_tree.nodes] if m.use_nodes else []}
def obj(o):
    x={'name':o.name,'type':o.type,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix_world':[list(r) for r in o.matrix_world],'parent':o.parent.name if o.parent else None,'hide_render':o.hide_render,'animation':bool(o.animation_data)}
    if o.type=='MESH':
        x.update(vertices=[list(v.co) for v in o.data.vertices], polygons=[{'vertices':list(p.vertices),'normal':list(p.normal),'material_index':p.material_index,'smooth':p.use_smooth} for p in o.data.polygons], materials=[mat(m) for m in o.data.materials if m],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers])
    return x
r={'blend':bpy.data.filepath,'version':bpy.app.version_string,'allCollections':[c.name for c in bpy.data.collections],'shelfCollections':{c.name:[obj(o) for o in c.all_objects] for c in matches}}
(OUT/'original-native.json').write_text(json.dumps(r,indent=2))
print(json.dumps({'shelfCollections':{c.name:[o.name for o in c.all_objects] for c in matches}}))
