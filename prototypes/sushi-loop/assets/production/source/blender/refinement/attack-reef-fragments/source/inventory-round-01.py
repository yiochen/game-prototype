"""Record actual saved editable source settings without rendering or saving it."""
import bpy,json,sys,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
S=Path(__file__).resolve().parent;B=S.parent;C=B/'candidates/round-01'
def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [val(x) for x in v]
 except TypeError:return str(v)
def matrix(m):return [list(row) for row in m]
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;sc.view_layers[0].update();col=bpy.data.collections['S33_CFX_attack-reef-fragments.001']
materials=[]
for m in bpy.data.materials:
 materials.append({'name':m.name,'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'identifier':s.identifier,'name':s.name,'value':val(s.default_value),'linked':s.is_linked} for s in n.inputs if hasattr(s,'default_value')]} for n in m.node_tree.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]})
meshes=[]
for o in col.all_objects:
 if o.type!='MESH':continue
 me=o.data;edgeuses={tuple(sorted(e.vertices)):0 for e in me.edges}
 for poly in me.polygons:
  for edge in poly.edge_keys:edgeuses[tuple(sorted(edge))]+=1
 meshes.append({'name':o.name,'mesh':me.name,'vertices':len(me.vertices),'faces':len(me.polygons),'materialSlots':[m.name for m in me.materials],'faceMaterials':[p.material_index for p in me.polygons],'nonmanifoldRawEdges':sum(v!=2 for v in edgeuses.values()),'modifiers':[{'name':m.name,'type':m.type,'width':m.width if hasattr(m,'width') else None,'segments':m.segments if hasattr(m,'segments') else None,'hardenNormals':m.harden_normals if hasattr(m,'harden_normals') else None,'showRender':m.show_render,'showViewport':m.show_viewport} for m in o.modifiers]})
actions=[]
for a in bpy.data.actions:
 curves=[fc for l in a.layers for s in l.strips for bag in s.channelbags for fc in bag.fcurves]
 actions.append({'name':a.name,'fakeUser':a.use_fake_user,'slots':[s.identifier for s in a.slots],'frameRange':val(a.frame_range),'curveCount':len(curves),'keyframeCount':sum(len(fc.keyframe_points) for fc in curves),'extrapolation':sorted({fc.extrapolation for fc in curves}),'interpolations':sorted({k.interpolation for fc in curves for k in fc.keyframe_points})})
data={'sourcePath':bpy.data.filepath,'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'scene':sc.name,'collection':col.name,'meshes':meshes,'materials':materials,'actions':actions,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrix':matrix(o.matrix_world)} for o in sc.objects if o.type=='LIGHT'],'world':{'name':sc.world.name,'nodes':[{'type':n.type,'inputs':[{'name':i.name,'value':val(i.default_value)} for i in n.inputs if hasattr(i,'default_value')]} for n in sc.world.node_tree.nodes]},'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent,'samples':sc.eevee.taa_render_samples,'filterSize':sc.render.filter_size,'dither':sc.render.dither_intensity,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None},'excluded':'No ground receiver, floor, foreign asset, target billboard or other2D effect in candidate scene.'}
(C/'native-source-inventory.json').write_text(json.dumps(data,indent=2)+'\n');assert len(actions)==27;assert all(x['nonmanifoldRawEdges']==0 for x in meshes)
print('SOURCE_INVENTORY',len(meshes),'closed native meshes',len(actions),'persisted actions')
