import bpy,json,math
from pathlib import Path
p=Path(__file__).resolve().parents[1];sc=bpy.context.scene
root=bpy.data.objects['reef-middle__root'];root.rotation_euler.z=0;bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get();o=bpy.data.objects['reef-middle__continuous_core'];e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
def val(x):
    try:return list(x) if not isinstance(x,(str,int,float,bool)) else x
    except:return str(x)
def mat(m):return {'name':m.name,'nodes':[{'type':n.bl_idname,'name':n.name,'inputs':{s.identifier:val(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'ramp':{'interpolation':n.color_ramp.interpolation,'elements':[(x.position,list(x.color)) for x in n.color_ramp.elements]} if n.type=='VALTORGB' else None} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]}
bands={}
for side,x in [('W',-.5),('E',.5)]:
    tris=[]
    for t in me.loop_triangles:
        vs=[list(me.vertices[i].co) for i in t.vertices]
        if all(abs(v[0])>=.42-1e-6 and abs(v[0]-x)<=.080001 for v in vs) and any(abs(v[0]-x)<1e-6 for v in vs) and not all(abs(v[0]-x)<1e-6 for v in vs):
            tris.append({'vertices':vs,'cornerNormals':[list(me.corner_normals[i].vector) for i in t.loops],'normal':list(t.normal),'material':me.materials[t.material_index].name,'polygonIndex':t.polygon_index})
    bands[side]={'orderedRing':[list(v.co) for v in me.vertices if abs(v.co.x-x)<1e-6],'triangles':tris}
# Actual evaluated triangle normal field; evaluate barycentric positions without assuming normal storage identity.
samples=[]
for side,band in bands.items():
 for i,t in enumerate(band['triangles']):
  for w in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
   q=[sum(w[k]*t['vertices'][k][j] for k in range(3)) for j in range(3)];n=[sum(w[k]*t['cornerNormals'][k][j] for k in range(3)) for j in range(3)];ln=sum(x*x for x in n)**.5
   samples.append({'side':side,'triangle':i,'weights':w,'position':q,'normalizedInterpolatedNormal':[x/ln for x in n],'material':t['material']})
usedmats={m.name:m for m in me.materials}
points=[];geometry=[]
for ob in bpy.data.collections['reef-middle'].all_objects:
 if ob.type!='MESH':continue
 ev=ob.evaluated_get(dg);mm=ev.to_mesh();v=[ev.matrix_world@x.co for x in mm.vertices];points+=v
 geometry.append({'name':ob.name,'privateMeshUsers':ob.data.users,'bounds':[[min(x[j] for x in v) for j in range(3)],[max(x[j] for x in v) for j in range(3)]],'animation':bool(ob.animation_data),'shapeKeys':bool(ob.data.shape_keys)});ev.to_mesh_clear()
cam=sc.camera
out={'blender':bpy.app.version_string,'root':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'bands':bands,'renderedFieldSamples':samples,'materials':[mat(m) for m in usedmats.values()],'geometry':geometry,'bounds':[[min(v[j] for v in points) for j in range(3)],[max(v[j] for v in points) for j in range(3)]],'camera':{'matrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size},'color':{'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'samples':sc.eevee.taa_render_samples},'lights':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'type':o.data.type} for o in sc.objects if o.type=='LIGHT'],'world':{'nodes':[{'type':n.bl_idname,'name':n.name,'inputs':{s.identifier:val(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in sc.world.node_tree.nodes]},'actions':[a.name for a in bpy.data.actions],'dependencies':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[x.name for x in bpy.data.images]}}
(p/'evidence/canonical-native-audit.json').write_text(json.dumps(out,indent=2)+'\n');e.to_mesh_clear()
print('bands',[(s,len(b['triangles'])) for s,b in bands.items()]);print('bounds',out['bounds']);print('camera',out['camera'])
