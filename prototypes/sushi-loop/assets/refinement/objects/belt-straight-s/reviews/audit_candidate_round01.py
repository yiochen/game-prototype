import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
base=Path(__file__).resolve().parent.parent;out=base/'reviews/round-01-native';out.mkdir(exist_ok=True)
family=json.loads((base/'inputs/family-settings.json').read_text());source=json.loads((base/'reviews/native-source-inspection.json').read_text())
sc=bpy.context.scene;col=bpy.data.collections['S33_FB_belt-straight-s.001'];root=bpy.data.objects['belt-straight-s__root.001'];orient=bpy.data.objects['belt-straight-s__orientation.001']
for c in [col]+list(col.children_recursive):c.hide_viewport=False;c.hide_render=False
for o in col.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
root.rotation_euler.z=0;sc.frame_set(1);bpy.context.view_layer.update()
def rows(m):return [list(r) for r in m]
def val(x):
 try:return list(x)
 except:return x
errors=[]
def check(path,actual,expected,tol=0):
 if isinstance(expected,(list,tuple)):
  if len(actual)!=len(expected):errors.append({'path':path,'actual':val(actual),'expected':expected});return
  for i,(a,b) in enumerate(zip(actual,expected)):check(path+'/'+str(i),a,b,tol)
 elif isinstance(expected,(int,float)) and not isinstance(expected,bool):
  if abs(actual-expected)>tol:errors.append({'path':path,'actual':actual,'expected':expected})
 elif actual!=expected:errors.append({'path':path,'actual':actual,'expected':expected})
def graph(nt,expected,path):
 check(path+'/nodeCount',len(nt.nodes),len(expected['nodes']));check(path+'/linkCount',len(nt.links),len(expected['links']))
 for en in expected['nodes']:
  n=nt.nodes.get(en['name'])
  if not n:errors.append({'path':path,'missingNode':en['name']});continue
  check(path+'/'+n.name+'/type',n.bl_idname,en['type'])
  for k,v in en['properties'].items():check(path+'/'+n.name+'/'+k,getattr(n,k),v)
  for sockfield in ['inputs','outputs']:
   sockets=getattr(n,sockfield);check(path+'/'+n.name+'/'+sockfield+'Count',len(sockets),len(en[sockfield]))
   for s in en[sockfield]:
    actual=sockets[s['index']];check(path+'/'+n.name+'/'+sockfield+'/'+str(s['index'])+'/identifier',actual.identifier,s['identifier'])
    if 'defaultValue' in s:check(path+'/'+n.name+'/'+sockfield+'/'+str(s['index'])+'/defaultValue',val(actual.default_value),s['defaultValue'])
  if 'colorRamp' in en:
   r=n.color_ramp;e=en['colorRamp'];check(path+'/'+n.name+'/rampInterpolation',r.interpolation,e['interpolation']);check(path+'/'+n.name+'/rampMode',r.color_mode,e['colorMode']);check(path+'/'+n.name+'/rampHue',r.hue_interpolation,e['hueInterpolation']);check(path+'/'+n.name+'/rampElementCount',len(r.elements),len(e['elements']))
   for i,el in enumerate(e['elements']):check(path+'/'+n.name+'/ramp/'+str(i)+'/position',r.elements[i].position,el['position']);check(path+'/'+n.name+'/ramp/'+str(i)+'/color',list(r.elements[i].color),el['color'])
 actual_links=[{'fromNode':l.from_node.name,'fromSocketIndex':list(l.from_node.outputs).index(l.from_socket),'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocketIndex':list(l.to_node.inputs).index(l.to_socket),'toSocket':l.to_socket.name} for l in nt.links]
 check(path+'/links',sorted([json.dumps(l,sort_keys=True) for l in actual_links]),sorted([json.dumps(l,sort_keys=True) for l in expected['links']]))
material_checks=[]
for fn,expected in family['materials'].items():
 actual_name='S33_belt-straight-s_moving_deck_native' if fn.startswith('S33_belt-straight-n_moving_deck') else fn
 m=bpy.data.materials[actual_name];before=len(errors);graph(m.node_tree,expected['nodeTree'],'materials/'+actual_name);check('materials/'+actual_name+'/surfaceRenderMethod',m.surface_render_method,expected['surfaceRenderMethod']);material_checks.append({'actual':actual_name,'family':fn,'exactGraphAndRampInputs':len(errors)==before})
graph(sc.world.node_tree,family['world']['nodes'],'world')
light_values=[]
for ex in family['lights']:
 o=bpy.data.objects[ex['name']];light_values.append({'name':o.name,'energy':o.data.energy,'matrixWorld':rows(o.matrix_world)})
 for k,a,e in [('type',o.data.type,ex['type']),('energy',o.data.energy,ex['energy']),('color',list(o.data.color),ex['color']),('shape',o.data.shape,ex['shape']),('size',o.data.size,ex['size']),('matrixWorld',rows(o.matrix_world),ex['matrixWorld'])]:check('lights/'+o.name+'/'+k,a,e)
cam=sc.camera;pr=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)
camera={'worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(pr),'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
for k in camera:check('camera/'+k,camera[k],family['capture'][k])
def pixel(p):
 q=world_to_camera_view(sc,cam,Vector(p));return Vector((q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y))
r=pixel((0,0,0));camera['calibration']={'root':list(r),'unitX':list(pixel((1,0,0))-r),'unitDepth':list(pixel((0,-1,0))-r),'unitHeight':list(pixel((0,0,1))-r)}
for k,e in family['capture']['calibration'].items():check('camera/calibration/'+k,camera['calibration'][k],e,0.0001)
check('intrinsicOrientation',orient.rotation_euler.z,0)
source_objects={o['name']:o for o in source['objects']}
profiles=[]
for name in ['belt-straight-s__connected_straight_deck.001','belt-straight-s__stationary_rail_-0.001','belt-straight-s__stationary_rail_0.001']:
 o=bpy.data.objects[name];vv=[o.matrix_world@v.co for v in o.data.vertices];sv=source_objects[name]['verticesWorld']
 for end in [-.5,.5]:
  aa=[list(v) for v in vv if abs(v.y-end)<1e-6];bb=[v for v in sv if abs(v[1]-end)<1e-6];md=max(min((Vector(a)-Vector(b)).length for a in aa) for b in bb);profiles.append({'object':name,'planeY':end,'candidateVertices':aa,'sourceVertices':bb,'maxNearestDistance':md});check('profiles/'+name+'/'+str(end),md,0,1e-6)
deck=bpy.data.objects['belt-straight-s__connected_straight_deck.001'];uvs=[list(u.uv) for u in deck.data.uv_layers.active.data];check('sourceDeckUV',uvs,source_objects[deck.name]['uvs'])
nt=deck.data.materials[0].node_tree;an=nt.animation_data;act=an.action
curves=[]
for l in act.layers:
 for strip in l.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:curves.append({'dataPath':fc.data_path,'arrayIndex':fc.array_index,'keys':[{'frame':k.co.x,'value':k.co.y,'interpolation':k.interpolation} for k in fc.keyframe_points]})
check('originalActionName',act.name,source['animation']['action']);check('originalActionSlot',an.action_slot.identifier,source['animation']['slot']);check('originalCurveExact',curves,source['animation']['curves'])
phase_values=[]
for f in range(1,26):
 sc.frame_set(f);bpy.context.view_layer.update();v=nt.nodes['Value'].outputs[0].default_value;phase_values.append(v);check('phase/'+str(f),v,source['animation']['phaseEvaluations'][f-1]['phase'])
facings={}
for facing,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(degrees);sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();verts=[]
 for o in col.all_objects:
  if o.type=='MESH':
   eo=o.evaluated_get(dg);me=eo.to_mesh();verts += [eo.matrix_world@v.co for v in me.vertices];eo.to_mesh_clear()
 bounds=[[min(v[i] for v in verts) for i in range(3)],[max(v[i] for v in verts) for i in range(3)]];ports={}
 for port,ux in [('incoming',0),('outgoing',1)]:
  pv=[deck.matrix_world@deck.data.vertices[l.vertex_index].co for l in deck.data.loops if abs(uvs[l.index][0]-ux)<1e-6];p=sum(pv,Vector())/len(pv);ports[port]={'world':list(p),'logicalRootRelative':list((pixel(p)-r)/2)}
 facings[facing]={'rootMatrix':rows(root.matrix_world),'orientationMatrix':rows(orient.matrix_world),'bounds':bounds,'ports':ports}
 for port in ports:check('ports/'+facing+'/'+port,ports[port]['world'],source['facings'][facing]['ports'][port]['world'],1e-6)
 for ix in [0,7,23,24]:
  sc.frame_set(ix+1);bpy.context.view_layer.update();sc.render.filepath=str(out/f'rerender-{facing}-{ix:02}.png');bpy.ops.render.render(write_still=True)
linked=[x.name for collection_name in ['objects','meshes','materials','node_groups','worlds','actions','images'] for x in getattr(bpy.data,collection_name) if x.library]
external={'libraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'path':x.filepath,'source':x.source} for x in bpy.data.images],'linkedIDs':linked}
geometry_animated=[o.name for o in col.all_objects if o.animation_data and o.animation_data.action];check('noGeometryAnimationOwners',geometry_animated,[])
coords=[{'material':m.name,'node':n.name,'object':n.object.name if n.object else None} for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_COORD']
result={'packetSHA256':'612d71d45c15be7141e7e75e9e342c5eeff3a7190432799fc4c16cab011d3a14','actualSavedScene':sc.name,'activeCamera':cam.name,'intrinsicOrientation':orient.rotation_euler.z,'sourceAction':{'material':deck.data.materials[0].name,'nodeTree':nt.name,'action':act.name,'slot':an.action_slot.identifier,'curves':curves,'all25PhaseValues':phase_values},'camera':camera,'profiles':profiles,'uvs':uvs,'materialChecks':material_checks,'lights':light_values,'externalDependencies':external,'coordinateOwners':coords,'facings':facings,'actualRender':{'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'samplingPattern':sc.cycles.sampling_pattern,'scrambling':sc.cycles.scrambling_distance,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'denoising':sc.cycles.use_denoising,'dither':sc.render.dither_intensity,'viewTransform':sc.view_settings.view_transform,'exposure':sc.view_settings.exposure},'errors':errors,'rerenderedSamples':16,'sourceSaved':False}
(base/'reviews/round-01-independent-native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('INDEPENDENT_AUDIT',json.dumps({'errors':errors,'samples':16,'dependency':external,'materialChecks':material_checks}))
