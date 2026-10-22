import bpy,pathlib,json,hashlib,math,struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import native_actions as na
P=Path(__file__).parent;BASE=P.parent.parent;OUT=BASE/'candidates/round-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):Path(p).write_text(json.dumps(x,indent=2,default=str)+'\n')
def compact(p,x):Path(p).write_text(json.dumps(x,separators=(',',':'),default=str)+'\n')
def hashed(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def context():
 record=json.loads((P/'dependencies/rig.json').read_text());root=bpy.data.objects[record['groundRootObject']];col=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects));arm=bpy.data.objects[record['armatures'][0]['object']];foodroot=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[foodroot.name+'__image_plane'];return record,root,col,arm,foodroot,plane
def baseline():
 record,root,col,arm,foodroot,plane=context()
 def canon(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 def h(v):return hashlib.sha256(canon(v)).hexdigest()
 def val(v):
  if isinstance(v,(str,bool,int,float)) or v is None:return v
  try:return list(v)
  except:return str(v)
 def tree(t):
  return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'name':s.name,'index':i,'value':val(s.default_value)} for i,s in enumerate(n.inputs) if hasattr(s,'default_value')],'outputs':[{'name':s.name,'index':i,'value':val(s.default_value)} for i,s in enumerate(n.outputs) if hasattr(s,'default_value')],'image':n.image.name if getattr(n,'image',None) else None,'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None),'interpolation':getattr(n,'interpolation',None),'extension':getattr(n,'extension',None),'projection':getattr(n,'projection',None)} for n in t.nodes],'links':[{'fromNode':l.from_node.name,'fromIndex':list(l.from_node.outputs).index(l.from_socket),'toNode':l.to_node.name,'toIndex':list(l.to_node.inputs).index(l.to_socket)} for l in t.links]}
 meshes={};transforms={};materials={}
 for o in col.all_objects:
  transforms[o.name]={'type':o.type,'parent':o.parent.name if o.parent else None,'matrixBasis':[list(z) for z in o.matrix_basis],'matrixParentInverse':[list(z) for z in o.matrix_parent_inverse],'hideRender':o.hide_render,'modifiers':[{k:val(getattr(m,k,None)) for k in ['name','type','show_render','show_viewport','vertex_group','invert_vertex_group','use_vertex_groups','use_bone_envelopes','use_deform_preserve_volume']} | {'target':getattr(m,'object',None).name if getattr(m,'object',None) else None} for m in o.modifiers]}
  if o.type=='MESH':
   if o!=plane:
    data={'vertices':[list(v.co) for v in o.data.vertices],'edges':[list(e.vertices) for e in o.data.edges],'polygons':[list(p.vertices) for p in o.data.polygons],'polygonSmooth':[p.use_smooth for p in o.data.polygons],'polygonMaterialIndices':[p.material_index for p in o.data.polygons],'uvLayers':{uv.name:[list(q.uv) for q in uv.data] for uv in o.data.uv_layers},'materials':[m.name if m else None for m in o.data.materials]}
    weights={'groupNames':[g.name for g in o.vertex_groups],'vertices':[[[g.group,g.weight] for g in v.groups] for v in o.data.vertices]};meshes[o.name]={'geometrySHA256':h(data),'weightsSHA256':h(weights),'vertices':len(o.data.vertices),'edges':len(o.data.edges),'polygons':len(o.data.polygons)}
   for m in o.data.materials:
    if m and m.name not in materials:
     desc={'useNodes':m.use_nodes,'diffuseColor':list(m.diffuse_color),'surfaceRenderMethod':getattr(m,'surface_render_method',None),'useTransparentShadow':getattr(m,'use_transparent_shadow',None),'nodeTree':tree(m.node_tree) if m.use_nodes else None};materials[m.name]={'SHA256':h(desc),'description':desc,'foodShader':o==plane}
 arm=bpy.data.objects[record['armatures'][0]['object']];bones={z.name:{'parent':z.parent.name if z.parent else None,'matrixLocal':[list(v) for v in z.matrix_local],'headLocal':list(z.head_local),'tailLocal':list(z.tail_local),'useDeform':z.use_deform} for z in arm.data.bones};actions={}
 for clip,c in record['clips'].items():
  for target in c['actions']:
   name=target['action'];a=bpy.data.actions[name]
   curves=[{'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'leftType':k.handle_left_type,'rightType':k.handle_right_type,'left':list(k.handle_left),'right':list(k.handle_right)} for k in f.keyframe_points]} for f in na._fcurves(a)];actions[name]={'SHA256':h(curves),'fcurves':len(curves),'keyframes':sum(len(f['keys']) for f in curves),'clip':clip}
 result={'sourceSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'hashConvention':'SHA256 of JSON sort_keys=True,separators=(comma,colon),ensure_ascii=False; geometry/weights serialized by this saved script. Baseline describes native source data, not deterministic PNG bytes.','bodyAndKnifeMeshes':meshes,'bodyAndKnifeMeshCount':len(meshes),'boneRestSHA256':h(bones),'boneRest':bones,'actions':actions,'materials':materials,'sourceObjectTransforms':transforms,'excludedFromPhysicalGeometryLock':'Only held image plane local vertices/UV and permitted orthoray display-offset amplitude may change by frozen mapping; texture packed bytes replace with exact canonical artwork. All other native data locked.'}
 return result
def presentation():
 sc=bpy.context.scene;cam=sc.camera
 def vals(o,names):
  d={}
  for n in names:
   v=getattr(o,n)
   if isinstance(v,(str,int,bool,float)):d[n]=v
   else:d[n]=list(v)
  return d
 def graph(t):
  def value(v):
   if isinstance(v,(str,int,bool,float)):return v
   try:return list(v)
   except:return str(v)
  return {'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':[{'name':s.name,'index':i,'value':value(s.default_value)} for i,s in enumerate(n.inputs) if hasattr(s,'default_value')]} for n in t.nodes],'links':[(l.from_node.name,list(l.from_node.outputs).index(l.from_socket),l.to_node.name,list(l.to_node.inputs).index(l.to_socket)) for l in t.links]}
 record,root,col,arm,foodroot,plane=context()
 drivers={}
 for o in col.all_objects:
  drivers[o.name]=[{'path':f.data_path,'index':f.array_index,'type':f.driver.type,'expression':f.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path,'bone':t.bone_target,'transformSpace':t.transform_space,'transformType':t.transform_type} for t in v.targets]} for v in f.driver.variables]} for f in o.animation_data.drivers] if o.animation_data else []
 return {'scene':sc.name,'world':{'name':sc.world.name,'useNodes':sc.world.use_nodes,'color':list(sc.world.color),'graph':graph(sc.world.node_tree)},'lights':{o.name:{'matrix':[list(r) for r in o.matrix_world],'data':vals(o.data,['type','color','energy','shape','size','size_y','use_shadow'])} for o in sc.objects if o.type=='LIGHT'},'camera':{'name':cam.name,'matrixWorld':[list(r) for r in cam.matrix_world],'data':vals(cam.data,['type','ortho_scale','shift_x','shift_y','sensor_fit','clip_start','clip_end','lens'])},'render':vals(sc.render,['engine','resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent','fps','fps_base','dither_intensity','filter_size','use_compositing','use_sequencer']),'imageSettings':vals(sc.render.image_settings,['file_format','color_mode','color_depth','compression']),'cycles':vals(sc.cycles,['device','samples','seed','use_animated_seed','use_denoising','use_adaptive_sampling','adaptive_threshold','max_bounces','transparent_max_bounces','pixel_filter_type']),'view':vals(sc.view_settings,['view_transform','look','exposure','gamma']),'drivers':drivers,'rootProperties':{k:v for k,v in root.items()}}
def project(p):
 sc=bpy.context.scene;q=world_to_camera_view(sc,sc.camera,Vector(p));return [q.x*384,(1-q.y)*640]
def centroid(o,dg):
 e=o.evaluated_get(dg);return sum((e.matrix_world@v.co for v in e.data.vertices),Vector())/len(e.data.vertices)
def phase(clip,direction,index):
 record,root,col,arm,foodroot,plane=context();sc=bpy.context.scene;na.apply_clip({'root':root,'collection':col,'armature':arm},record,clip,index+1,direction,sc)
 vis={o.name:{'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'hideSet':o.hide_get()} for o in col.all_objects}
 for o in col.all_objects:o.hide_viewport=False;o.hide_set(False)
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pe=plane.evaluated_get(dg);ae=arm.evaluated_get(dg)
 physical={}
 for o in col.all_objects:
  if o.type!='MESH' or o==plane:continue
  e=o.evaluated_get(dg);me=e.to_mesh();points=[e.matrix_world@v.co for v in me.vertices];raw=b''.join(struct.pack('<fff',*p) for p in points)
  physical[o.name]={'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'worldVerticesSHA256':hashlib.sha256(raw).hexdigest(),'bounds':[[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)],'nonfiniteVertices':sum(not all(math.isfinite(x) for x in p) for p in points),'zeroAreaPolygons':sum(p.area<1e-12 for p in me.polygons),'matrix':[list(r) for r in e.matrix_world]};e.to_mesh_clear()
 palms={s:list(centroid(bpy.data.objects['chef_dalia__palm_'+s+'.001'],dg)) for s in ['L','R']};mean=[sum(palms[s][i] for s in palms)/2 for i in range(3)];image=next(n.image for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE');suv=(367.5/731,1-503.5/505) if list(image.size)==[731,505] else (633.5/1254,1-1050.5/1254);uv=[plane.data.uv_layers.active.data[i].uv.copy() for i in plane.data.polygons[0].loop_indices];su=(suv[0]-uv[0].x)/(uv[1].x-uv[0].x);sv=(suv[1]-uv[0].y)/(uv[3].y-uv[0].y);support_local=pe.data.vertices[0].co+(pe.data.vertices[1].co-pe.data.vertices[0].co)*su+(pe.data.vertices[3].co-pe.data.vertices[0].co)*sv;support=pe.matrix_world@support_local
 corners=[list(pe.matrix_world@v.co) for v in pe.data.vertices];width=(Vector(corners[1])-Vector(corners[0])).length;height=(Vector(corners[3])-Vector(corners[0])).length
 result={'clip':clip,'direction':direction,'index':index,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'rootPixel':project((0,0,0)),'cameraMatrix':[list(r) for r in sc.camera.matrix_world],'cameraProjectionMatrix':[list(r) for r in sc.camera.calc_matrix_camera(dg,x=384,y=640,scale_x=1,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'foodRootMatrix':[list(r) for r in foodroot.evaluated_get(dg).matrix_world],'planeMatrix':[list(r) for r in pe.matrix_world],'planeLocalLocation':list(plane.location),'planeLocalRotation':list(plane.rotation_euler),'foodVerticesWorld':corners,'foodCornersNative':[project(p) for p in corners],'semanticSupportLocal':list(support_local),'semanticSupportUV':suv,'semanticSupportWorld':list(support),'semanticSupportNative':project(support),'palmCentroidsWorld':palms,'palmMeanWorld':mean,'palmMeanNative':project(mean),'semanticSupportMinusPalmMeanNative':[project(support)[i]-project(mean)[i] for i in range(2)],'widthWorld':width,'heightWorld':height,'aspect':width/height,'visibility':vis,'physicalGeometry':physical,'boneMatricesWorld':{bo.name:[list(r) for r in ae.matrix_world@bo.matrix] for bo in ae.pose.bones},'knifeToRightPalmWorldError':(bpy.data.objects[root.name+'__utensil'].evaluated_get(dg).matrix_world.translation-Vector(palms['R'])).length}
 for o in col.all_objects:o.hide_viewport=vis[o.name]['hideViewport'];o.hide_set(vis[o.name]['hideSet'])
 bpy.context.view_layer.update();return result
