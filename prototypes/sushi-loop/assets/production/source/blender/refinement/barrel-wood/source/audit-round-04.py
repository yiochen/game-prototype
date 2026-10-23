import bpy,json,hashlib,bmesh
from pathlib import Path
base=Path(__file__).resolve().parent.parent;out=base/'candidates/round-04'
v=json.loads((out/'validation.json').read_text());sc=bpy.context.scene
v['dependencies']={'libraries':[{'path':l.filepath,'name':l.name} for l in bpy.data.libraries],'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images if i.source=='FILE'],'packed':all(i.packed_file for i in bpy.data.images if i.source=='FILE')}
v['projectReopenAudit']={'scene':sc.name,'camera':sc.camera.name,'objectCount':len(sc.objects),'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'renderEngine':sc.render.engine,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'],'actions':[a.name for a in bpy.data.actions if a.users>0],'sourceProjectSHA256':hashlib.sha256((base/'source/round-04.blend').read_bytes()).hexdigest(),'externalDependencyCount':len(bpy.data.libraries)+sum(i.source=='FILE' and not i.packed_file for i in bpy.data.images)}
v['nativeShaderEvidence']=[]
for m in bpy.data.materials:
 if not m.use_nodes:continue
 graph=[]
 for n in m.node_tree.nodes:
  inputs={}
  for s in n.inputs:
   if not hasattr(s,'default_value'):continue
   value=s.default_value
   try:value=list(value)
   except TypeError:pass
   if isinstance(value,(int,float,str,list,bool)):inputs[s.name]={'value':value,'linked':s.is_linked}
  graph.append({'type':n.type,'name':n.name,'operation':getattr(n,'operation',None),'inputs':inputs})
 v['nativeShaderEvidence'].append({'material':m.name,'nodes':graph,'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]})
v['visibleVolumeMethods']={'lid':'Same five planks; closed top grids gently crown by 0.011 world across width plus 0.005 at length ends, maximum source height unchanged. Broad root-local Y-squared warm variation; no noise or image texture.','hoops':'Original 14-gon perimeters retained with subdivided side segments and 12-point rounded ring cross-sections. Restrained shader tint uses world-normal Z only, with dark navy body and softer upward edge.','lighting':'Exactly the round03 centered broad light, four equal fills and neutral ambient; no preferred horizontal direction.'}
v['materials']['navyHex']='native normal-Z mix: 102B58 to 2D5289'
(out/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
print('AUDIT',json.dumps(v['dependencies']),len(v['projectReopenAudit']['actions']),'actions')
