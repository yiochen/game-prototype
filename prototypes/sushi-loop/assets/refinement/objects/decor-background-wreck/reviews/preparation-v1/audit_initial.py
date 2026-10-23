import bpy,json
from pathlib import Path
out=Path(__file__).resolve().parent
names=[c.name for c in bpy.data.collections if 'decor-background-wreck' in c.name]
cols=[bpy.data.collections[n] for n in names]
objs=list(dict.fromkeys(o for c in cols for o in c.all_objects))
for c in cols: c.hide_render=False;c.hide_viewport=False
for o in objs:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
def enable(lc):
    if any(o in objs for o in lc.collection.all_objects):lc.exclude=False;lc.hide_viewport=False
    for x in lc.children:enable(x)
for vl in bpy.context.scene.view_layers:enable(vl.layer_collection)
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def mat(m):return [list(r) for r in m]
def anim(x):
    ad=getattr(x,'animation_data',None)
    if not ad:return None
    return {'action':ad.action.name if ad.action else None,'drivers': [{'data_path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for f in ad.drivers],'nlaTracks':[{'name':t.name,'strips':[{'action':s.action.name if s.action else None,'frame_start':s.frame_start,'frame_end':s.frame_end} for s in t.strips]} for t in ad.nla_tracks]}
def bounds(vs):
    return [[min(v[i] for v in vs),max(v[i] for v in vs)] for i in range(3)] if vs else None
rows=[]
dg=bpy.context.evaluated_depsgraph_get()
for o in objs:
    ev=o.evaluated_get(dg)
    raw=[o.matrix_world@v.co for v in o.data.vertices] if o.type=='MESH' else []
    eva=[]
    if o.type=='MESH':
        me=ev.to_mesh();eva=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
    rows.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':mat(o.matrix_world),'matrixLocal':mat(o.matrix_local),'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'rawBounds':bounds(raw),'evaluatedBounds':bounds(eva),'rawVertices':[list(v) for v in raw],'rawFaces':[list(p.vertices) for p in o.data.polygons] if o.type=='MESH' else None,'vertexCount':len(raw),'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None),'showRender':m.show_render} for m in o.modifiers],'constraints':[{'name':c.name,'type':c.type,'target':getattr(getattr(c,'target',None),'name',None)} for c in o.constraints],'uvLayers':[u.name for u in o.data.uv_layers] if o.type=='MESH' else [],'shapeKeys': [k.name for k in o.data.shape_keys.key_blocks] if o.type=='MESH' and o.data.shape_keys else [],'animation':anim(o),'dataAnimation':anim(o.data),'materials':[s.material.name if s.material else None for s in o.material_slots],'customProperties':{k:str(v) for k,v in o.items()}})
mats=list(dict.fromkeys(s.material for o in objs for s in o.material_slots if s.material))
materials=[]
for m in mats:
    materials.append({'name':m.name,'diffuseColor':list(m.diffuse_color),'users':m.users,'library':m.library.filepath if m.library else None,'animation':anim(m),'nodesAnimation':anim(m.node_tree) if m.node_tree else None,'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') and not isinstance(i.default_value,str) else i.default_value for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes] if m.node_tree else []})
s=bpy.context.scene
r={'sourceFile':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'collections':[{'name':c.name,'objects':[o.name for o in c.objects],'library':c.library.filepath if c.library else None} for c in cols],'ownedObjects':rows,'materials':materials,'scene':{'name':s.name,'camera':s.camera.name if s.camera else None,'frame':s.frame_current,'frameStart':s.frame_start,'frameEnd':s.frame_end,'fps':s.render.fps,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'transparent':s.render.film_transparent,'animation':anim(s)},'cameras':[{'name':o.name,'matrixWorld':mat(o.matrix_world),'type':o.data.type,'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]} for o in s.objects if o.type=='CAMERA'],'lights':[{'name':o.name,'matrixWorld':mat(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'hideRender':o.hide_render} for o in s.objects if o.type=='LIGHT'],'libraries':[{'name':x.name,'filepath':x.filepath} for x in bpy.data.libraries],'images':[{'name':x.name,'filepath':x.filepath,'packed':bool(x.packed_file),'source':x.source,'users':x.users} for x in bpy.data.images],'actions':[{'name':a.name,'frameRange':list(a.frame_range),'users':a.users} for a in bpy.data.actions if any(a==getattr(getattr(o,'animation_data',None),'action',None) for o in objs)]}
(out/'native-initial-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'collections':names,'objects':[{'name':x['name'],'raw':x['rawBounds'],'evaluated':x['evaluatedBounds']} for x in rows],'camera':r['scene']['camera']}))
