import bpy,json,os,hashlib
from mathutils import Vector
base=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
scene=bpy.context.scene
cols=[c for c in bpy.data.collections if 'wreck' in c.name.lower()]
c=[c for c in cols if 'end' in c.name.lower()]
if len(c)!=1: raise RuntimeError('Ambiguous own collections '+str([c.name for c in c]))
col=c[0]
def enabled(lc):
 lc.exclude=False;lc.hide_viewport=False
 for ch in lc.children:enabled(ch)
enabled(bpy.context.view_layer.layer_collection)
for cc in bpy.data.collections:
 cc.hide_viewport=False
for ob in col.all_objects:
 ob.hide_viewport=False;ob.hide_render=False;ob.hide_set(False)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
def v(x):return [float(z) for z in x]
def mat(m):return [v(row) for row in m]
res={'stage':'independent original-native inspection before canonical technical authority','blender':bpy.app.version_string,'file':bpy.data.filepath,'collection':col.name,'otherCollectionNamesOnly':[c.name for c in cols],'scene':scene.name,'frame':scene.frame_current,'objects':[],'sceneCaptureObservationNotAuthority':{'camera':scene.camera.name if scene.camera else None,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'percentage':scene.render.resolution_percentage,'engine':scene.render.engine}}
allp=[]
for ob in sorted(col.all_objects,key=lambda o:o.name):
 eo=ob.evaluated_get(dg)
 d={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'location':v(ob.location),'rotationEuler':v(ob.rotation_euler),'scale':v(ob.scale),'matrixWorld':mat(eo.matrix_world),'custom':{k:ob[k] for k in ob.keys()},'modifiers':[(m.name,m.type) for m in ob.modifiers],'materials':[m.name if m else None for m in getattr(ob.data,'materials',[])]}
 if ob.type=='MESH':
  me=eo.to_mesh();p=[eo.matrix_world@x.co for x in me.vertices];allp+=p
  d.update(vertices=len(me.vertices),polygons=len(me.polygons),worldBounds={'min':[min(t[i] for t in p) for i in range(3)],'max':[max(t[i] for t in p) for i in range(3)]},verticesWorld=[v(x) for x in p],polygonIndices=[list(f.vertices) for f in me.polygons]);eo.to_mesh_clear()
 res['objects'].append(d)
res['worldBounds']={'min':[min(t[i] for t in allp) for i in range(3)],'max':[max(t[i] for t in allp) for i in range(3)]}
res['collectionProperties']={k:col[k] for k in col.keys()}
if scene.camera:res['sceneCaptureObservationNotAuthority'].update(cameraMatrix=mat(scene.camera.matrix_world),cameraData={'type':scene.camera.data.type,'orthoScale':scene.camera.data.ortho_scale,'angle':scene.camera.data.angle})
res['materials']={m.name:{'diffuse':v(m.diffuse_color),'useNodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and s.type not in {'SHADER','CUSTOM'}} for n in m.node_tree.nodes] if m.use_nodes else []} for m in set(m for ob in col.all_objects if ob.type=='MESH' for m in ob.data.materials if m)}
with open(os.path.join(base,'initial-native.json'),'w') as f:json.dump(res,f,indent=2,default=str)
print('INITIAL_NATIVE',col.name,res['worldBounds'],[(o['name'],o.get('worldBounds')) for o in res['objects']])
