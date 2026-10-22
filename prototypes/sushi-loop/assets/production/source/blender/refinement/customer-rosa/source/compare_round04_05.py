import bpy,json,pathlib,hashlib,bmesh
H=pathlib.Path(__file__).resolve().parent;O=H.parent

def fingerprint(o):
 m=o.data
 return {'vertices':[list(v.co) for v in m.vertices],'faces':[(list(p.vertices),p.material_index,p.use_smooth) for p in m.polygons],'weights':[[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in m.vertices],'materials':[{'name':ma.name,'nodes':[(n.type,[(i.name,str(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in ma.node_tree.nodes],'links':[(l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name) for l in ma.node_tree.links]} for ma in m.materials],'modifiers':[(md.type,md.name) for md in o.modifiers],'matrixParentInverse':[list(r) for r in o.matrix_parent_inverse],'localTransform':[list(o.location),list(o.rotation_euler),list(o.scale)]}
def inspect(file):
 bpy.ops.wm.open_mainfile(filepath=str(H/file));sc=bpy.context.scene;root=next(o for o in sc.objects if o.name.endswith('customer_rosa__ground_root.001'));c=root.users_collection[0];nonhair={};hair=[]
 for ob in c.all_objects:
  if ob.type!='MESH':continue
  ishair=any(k in ob.name for k in ['continuous rounded bob','front swept lock','rounded fringe','connected sculpted bob'])
  if ishair:
   bm=bmesh.new();bm.from_mesh(ob.data);hair.append({'object':ob.name,'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'headWeightOnly':all(len(v.groups)==1 and ob.vertex_groups[v.groups[0].group].name=='head' and v.groups[0].weight==1 for v in ob.data.vertices)});bm.free()
  else:
   key=ob.name.replace('S10 meal ','').replace('Rosa refined runtime ','Rosa refined ');data=fingerprint(ob);data['materials']=[{**m,'name':m['name'].replace(' runtime ',' ')} for m in data['materials']];nonhair[key]=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
 lights=[{'name':ob.name,'matrix':[list(r) for r in ob.matrix_world],'energy':ob.data.energy,'color':list(ob.data.color),'type':ob.data.type,'size':ob.data.size} for ob in sc.objects if ob.type=='LIGHT'];world=[(n.type,[(i.name,str(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in sc.world.node_tree.nodes]
 return {'project':file,'sha256':hashlib.sha256((H/file).read_bytes()).hexdigest(),'nonHairMeshes':nonhair,'hair':hair,'lights':lights,'world':world,'camera':{'matrix':[list(r) for r in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]}}
old=inspect('round-04.blend');new=inspect('round-05.blend');rt=inspect('round-05-runtime.blend');unchanged=old['nonHairMeshes']==new['nonHairMeshes'];assert unchanged;assert old['lights']==new['lights'] and old['world']==new['world'] and old['camera']==new['camera'];assert len(new['hair'])==1 and new['hair'][0]['nonManifoldEdges']==0
out={'mainRound04':old,'mainRound05':new,'runtimeRound05':rt,'nonHairMeshDataAndMaterialsExactRound04':unchanged,'lightsWorldCameraExactRound04':True,'newHairOneClosedManifoldMesh':True,'sourceChangePolicy':'Only hair geometry/construction changes. Prior credited body, face, garments, shoes, materials, lights, world, camera, food and source action cohorts are retained. Full new native captures account for hair light interaction.'};(O/'candidates/round-05/round04-preservation.json').write_text(json.dumps(out,indent=2)+'\n');print('PRESERVATION',unchanged,new['hair'])
