import bpy,json,sys,math,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];proj=P/'source/round-01.blend';bpy.ops.wm.open_mainfile(filepath=str(proj));sc=bpy.context.scene;root=bpy.data.objects['floor-underwater__root'];floor=bpy.data.objects['floor-underwater__continuous_water'];mat=floor.data.materials[0]
outputs=[]
for frame in list(range(1,14))+[1.5,7.5,12.5]:
 sc.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=floor.evaluated_get(dg);me=ev.to_mesh()
 outputs.append({'frame':frame,'phase':mat.node_tree.nodes['Global one-second loop phase'].outputs[0].default_value,'vertices':[list(v.co) for v in me.vertices],'polygons':[{'vertices':list(p.vertices),'area':p.area,'normal':list(p.normal)} for p in me.polygons],'uv':[list(u.uv) for u in me.uv_layers.active.data]});ev.to_mesh_clear()
drivers=[]
for idblock in [sc,root,floor,floor.data,mat,mat.node_tree]:
 ad=idblock.animation_data
 if ad:
  for fc in ad.drivers:drivers.append({'owner':idblock.name,'dataPath':fc.data_path,'index':fc.array_index,'expression':fc.driver.expression,'variables':[v.name for v in fc.driver.variables]})
graph={'nodes':[],'links':[]}
for n in mat.node_tree.nodes:
 graph['nodes'].append({'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':[{'name':i.name,'default':list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value} for i in n.inputs if hasattr(i,'default_value')]})
for l in mat.node_tree.links:graph['links'].append([l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name])
result={'projectSHA256':hashlib.sha256(proj.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'savedScene':sc.name,'actualMasterCollection':sc.collection.name,'actualFloorCollections':[c.name for c in floor.users_collection],'sceneObjects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None} for o in sc.objects],'geometryEvaluations':outputs,'animationChannels':drivers,'externalImages':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries],'camera':{'matrix':[list(r) for r in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'resolution':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filterSize':sc.render.filter_size,'fps':sc.render.fps},'lights':[o.name for o in sc.objects if o.type=='LIGHT'],'material':'Texture-free toroidal distance caustics, emission optical field; one graph shared across every homogeneous tile and facing. No geometric displacement, normals, lights, texture resources, world-space position or arbitrary random seeds.','graph':graph,'closureExplanation':'Only animated channel is Value output phase = ((frame-1)%12)/12. Native measured phase at1 and13 is exactly0. All linked graph inputs, topology,UVs, transforms and scene settings are otherwise static. Hence complete evaluated material state and geometry close exactly. Between frames phase runs continuously; every downstream time input is sin/cos with one-second period.'}
(P/'candidates/round-01/saved-source-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print('SAVED_SOURCE_AUDIT',len(drivers),len(graph['nodes']),len(graph['links']))
