import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent;E=P/'evidence';E.mkdir(exist_ok=True)
def val(x):
 if isinstance(x,(str,int,float,bool))or x is None:return x
 try:return [val(v)for v in x]
 except:return str(x)
def tree(t):
 if t is None:return None
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'attribute':getattr(n,'attribute_name',None),'vectorType':getattr(n,'vector_type',None),'from':getattr(n,'convert_from',None),'to':getattr(n,'convert_to',None),'blend':getattr(n,'blend_type',None),'clamp':getattr(n,'clamp',None),'inputs':[{'name':s.name,'value':val(s.default_value)if hasattr(s,'default_value')else None,'linked':s.is_linked}for s in n.inputs],'group':tree(n.node_tree)if hasattr(n,'node_tree')and n.node_tree else None}for n in t.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name]for l in t.links]}
def scene_data(sc):
 return {'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'shape':getattr(o.data,'shape',None),'size':getattr(o.data,'size',None),'color':list(o.data.color),'shadow':o.data.use_shadow,'matrix':list(map(list,o.matrix_world))}for o in sc.objects if o.type=='LIGHT'],'world':tree(sc.world.node_tree),'compositor':tree(sc.compositing_node_group),'render':{'engine':sc.render.engine,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'frame':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'filter':sc.render.filter_size,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'useCompositing':sc.render.use_compositing},'camera':{'matrix':list(map(list,sc.camera.matrix_world)),'ortho':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'type':sc.camera.data.type,'sensorFit':sc.camera.data.sensor_fit}}
def enable(sc,root):
 bpy.context.window.scene=sc
 for c in bpy.data.collections:
  if root.name in c.all_objects:c.hide_viewport=False;c.hide_render=False
 def visit(c):
  c.exclude=False;c.hide_viewport=False
  for v in c.children:visit(v)
 visit(bpy.context.view_layer.layer_collection)
 for o in [root]+list(root.children_recursive):o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
 sc.frame_set(1);bpy.context.view_layer.update()
allResults={}
for kind,file,rootname in [('canonical',R/'canonical-middle02.blend','wreck-middle__root'),('candidate',R/'candidate.blend','wreck-corner__root.001')]:
 bpy.ops.wm.open_mainfile(filepath=str(file));root=bpy.data.objects[rootname];sc=next(s for s in bpy.data.scenes if root.name in s.objects);enable(sc,root)
 initialRoot=list(map(list,root.matrix_world));root.location=(0,0,0);root.rotation_euler=(0,0,0);sc.frame_set(1);bpy.context.view_layer.update();mats=set();views=[]
 for d,a in ([('S',0)]if kind=='canonical'else [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]):
  root.rotation_euler.z=a;sc.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();inv=root.matrix_world.inverted();objects=[];support=[];fields=[];caps={'W':[],'N':[]};verts=[]
  for ob in root.children_recursive:
   item={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'matrixWorld':list(map(list,ob.matrix_world)),'matrixRoot':list(map(list,inv@ob.matrix_world)),'animationData':bool(ob.animation_data),'constraints':[c.type for c in ob.constraints],'instanceCollection':ob.instance_collection.name if ob.instance_collection else None,'modifiers':[{'name':m.name,'type':m.type}for m in ob.modifiers]}
   if ob.type in ['MESH','CURVE','SURFACE','FONT','META']:
    ev=ob.evaluated_get(dg);me=ev.to_mesh();mat=inv@ev.matrix_world;vs=[mat@v.co for v in me.vertices];verts.extend(vs);me.calc_loop_triangles();item['vertices']=[list(v)for v in vs];item['faces']=[list(f.vertices)for f in me.polygons];item['materials']=[m.name for m in me.materials if m];mats.update(m for m in me.materials if m)
    for t in me.loop_triangles:
     pts=[vs[i]for i in t.vertices]
     if all(abs(v.z-.04)<1e-6 for v in pts):support.append({'owner':ob.name,'vertices':[list(v)for v in pts]})
    attribute=me.attributes.get('CanonicalNormal')
    for f in me.polygons:
     pts=[vs[i]for i in f.vertices]
     for side,axis,low,high in [('W',0,-.5,-.42),('N',1,.42,.5)]:
      if kind=='canonical':continue
      if all(low-1e-7<=v[axis]<=high+1e-7 for v in pts):
       nrm=list((mat.to_3x3().inverted().transposed()@f.normal).normalized());normals=[list((mat.to_3x3().inverted().transposed()@attribute.data[k].vector).normalized())for k in f.loop_indices]if attribute else None
       info={'owner':ob.name,'side':side,'vertices':[list(v)for v in pts],'geometryNormal':nrm,'shaderCornerNormalRoot':normals,'attributeDomain':attribute.domain if attribute else None,'attributeType':attribute.data_type if attribute else None,'material':me.materials[f.material_index].name if me.materials else None}
       fields.append(info)
       if all(abs(v[axis]-(-.5 if side=='W'else .5))<1e-7 for v in pts):caps[side].append(info)
    ev.to_mesh_clear()
   objects.append(item)
  def px(pt):
   v=world_to_camera_view(sc,sc.camera,Vector(pt));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
  base=px((0,0,0));calib={'root':base,'unitX':[x-y for x,y in zip(px((1,0,0)),base)],'unitDepth':[x-y for x,y in zip(px((0,-1,0)),base)],'unitHeight':[x-y for x,y in zip(px((0,0,1)),base)]}
  view={'direction':d,'rootMatrix':list(map(list,root.matrix_world)),'objects':objects,'supportTriangles':support,'fullCollarPolygons':fields,'caps':caps,'bounds':[[min(v[i]for v in verts),max(v[i]for v in verts)]for i in range(3)],'calibration':calib}
  if kind=='candidate':
   path=E/('saved-source-'+d+'.png');sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);view['recapture']={'path':str(path.relative_to(P)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
  views.append(view)
 allResults[kind]={'sourceSHA256':hashlib.sha256(file.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'sourceInitialRootMatrix':initialRoot,'rootProperties':{k:val(root[k])for k in root.keys()},'scene':scene_data(sc),'views':views,'materials':[{'name':m.name,'tree':tree(m.node_tree)}for m in sorted(mats,key=lambda m:m.name)],'externalLibraries':[l.filepath for l in bpy.data.libraries],'imageNodes':[{'material':m.name,'image':n.image.filepath,'packed':bool(n.image.packed_file)}for m in mats for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image],'sceneGeometryOwners':[o.name for o in sc.objects if o.type in ['MESH','CURVE','SURFACE','META','FONT']and not o.hide_render]}
(P/'native-independent-audit.json').write_text(json.dumps(allResults,indent=2)+'\n');print('OWN_AUDIT_COMPLETE')
