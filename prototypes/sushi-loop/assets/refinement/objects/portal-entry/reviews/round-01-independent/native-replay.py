import bpy,math,json,hashlib,sys,time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01';SOURCE=O/'source/round-01.blend';OUT=H/'native';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,indent=2)+'\n')
def mat(x):return [list(r) for r in x]
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return [plain(x) for x in v]
 except:return str(v)
def bounds(pp):
 return {'min':[min(v[a] for v in pp) for a in range(3)],'max':[max(v[a] for v in pp) for a in range(3)]} if pp else None
def hull_area(pts):
 ps=sorted(set((round(p[0],9),round(p[1],9)) for p in pts))
 if len(ps)<3:return 0
 def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
 lo=[];hi=[]
 for p in ps:
  while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 for p in reversed(ps):
  while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 hs=lo[:-1]+hi[:-1]
 return abs(sum(hs[i][0]*hs[(i+1)%len(hs)][1]-hs[(i+1)%len(hs)][0]*hs[i][1] for i in range(len(hs)))/2)
assert Path(bpy.data.filepath).resolve()==SOURCE.resolve();assert sha(SOURCE)=='dc8f792ad097e30096719a075042e040b928ef8c79b58941061651192bfe4f36'
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=bpy.data.collections['S33_PROP_portal_rim.003'];root=bpy.data.objects['portal_rim__root.003'];cam=sc.camera
saved={'scene':sc.name,'collection':col.name,'root':root.name,'sourceSHA256':sha(SOURCE),'blenderVersion':bpy.app.version_string,'sceneFrame':[sc.frame_start,sc.frame_end,sc.frame_current],'renderFPS':[sc.render.fps,sc.render.fps_base]}
def enable(l):
 l.exclude=False;l.hide_viewport=False
 for x in l.children:enable(x)
enable(sc.view_layers[0].layer_collection)
for c in [col,*col.children_recursive]:c.hide_render=False;c.hide_viewport=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();own=sorted(col.all_objects,key=lambda o:o.name);meshes=[o for o in own if o.type=='MESH'];supports=[o for o in meshes if 'fixed navy support' in o.name];rim=next(o for o in meshes if o.name=='portal_entry | continuous cyan rim')
assert len(supports)==2
W,HPIX=sc.render.resolution_x,sc.render.resolution_y
assert [W,HPIX]==[768,1536];assert cam.data.type=='ORTHO' and abs(cam.data.ortho_scale-1.5)<1e-6 and cam.data.sensor_fit=='HORIZONTAL';assert abs(sc.render.pixel_aspect_x-1.2206555604934692)<1e-7
sc.render.use_persistent_data=True
# All source action bindings are evaluated as saved, not reconstructed from the editor recipe.
actions=[]
for o in own:
 if o.animation_data and o.animation_data.action:
  a=o.animation_data.action;fs=[f for l in a.layers for s in l.strips for cb in s.channelbags for f in cb.fcurves];actions.append({'owner':o.name,'action':a.name,'frameRange':list(a.frame_range),'curves':[{'dataPath':f.data_path,'axis':f.array_index,'keys':[[*k.co,k.interpolation] for k in f.keyframe_points]} for f in fs],'nlaTracks':[{'name':t.name,'mute':t.mute} for t in o.animation_data.nla_tracks]})
materials=[]
for m in sorted({s.material for o in meshes for s in o.material_slots if s.material},key=lambda m:m.name):
 materials.append({'name':m.name,'properties':{k:plain(v) for k,v in m.items()},'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:plain(s.default_value) for s in n.inputs if hasattr(s,'default_value')}} for n in m.node_tree.nodes],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]})
write('source-inspection.json',{'saved':saved,'ownership':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection],'dataLibrary':o.data.library.filepath if o.data and o.data.library else None,'objectLibrary':o.library.filepath if o.library else None,'modifiers':[{'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None),'showRender':m.show_render,'showViewport':m.show_viewport} for m in o.modifiers],'constraints':[c.type for c in o.constraints],'shapeKeys':list(o.data.shape_keys.key_blocks.keys()) if o.type=='MESH' and o.data.shape_keys else []} for o in own],'actions':actions,'materials':materials,'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrixWorld':mat(o.matrix_world)} for o in sc.objects if o.type=='LIGHT'],'world':[{'color':list(n.inputs['Color'].default_value),'strength':n.inputs['Strength'].default_value} for n in sc.world.node_tree.nodes if n.type=='BACKGROUND'],'render':{'engine':sc.render.engine,'resolution':[W,HPIX],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'dither':sc.render.dither_intensity,'filmTransparent':sc.render.film_transparent,'compositing':sc.render.use_compositing,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'colorMode':sc.render.image_settings.color_mode},'externalImageNodes':[{'object':o.name,'material':s.material.name,'node':n.name,'path':n.image.filepath if n.image else None} for o in meshes for s in o.material_slots if s.material and s.material.use_nodes for n in s.material.node_tree.nodes if n.type=='TEX_IMAGE'],'armatures':[o.name for o in own if o.type=='ARMATURE']})
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return [p.x*W,(1-p.y)*HPIX]
sc.frame_set(1);sc.view_layers[0].update();zero=px((0,0,0));camera={'sourceSHA256':sha(SOURCE),'cameraWorldMatrix':mat(cam.matrix_world),'projectionMatrix':mat(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=W,y=HPIX,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'frame':[W,HPIX],'root':zero,'unitX':[px((1,0,0))[j]-zero[j] for j in range(2)],'unitDepth':[px((0,-1,0))[j]-zero[j] for j in range(2)],'unitHeight':[px((0,0,1))[j]-zero[j] for j in range(2)]};write('camera.json',camera)
records=[]
for d,deg in [('N',180),('E',90),('S',0),('W',-90)]:
 folder=OUT/d;folder.mkdir(exist_ok=True)
 for i in range(12):
  root.rotation_euler.z=math.radians(deg);sc.frame_set(i+1);sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update();inv=root.matrix_world.inverted();ra=[];eva=[];mrecords=[];sv=[];sf=[];bvhs={};sections=[]
  for o in meshes:
   e=o.evaluated_get(dg);me=e.to_mesh();raw=[o.matrix_world@v.co for v in o.data.vertices];ev=[e.matrix_world@v.co for v in me.vertices];faces=[tuple(p.vertices) for p in me.polygons];bvhs[o.name]=BVHTree.FromPolygons(ev,faces);offset=len(sv);sv.extend(ev);sf.extend(tuple(v+offset for v in f) for f in faces);ra.extend(inv@p for p in raw);eva.extend(inv@p for p in ev)
   mrecords.append({'name':o.name,'rawBoundsCanonicalS':bounds([inv@p for p in raw]),'evaluatedBoundsCanonicalS':bounds([inv@p for p in ev]),'rootRelativeMatrix':mat(inv@e.matrix_world),'rawVertices':len(raw),'evaluatedVertices':len(ev),'rawPolygons':len(o.data.polygons),'evaluatedPolygons':len(me.polygons),'zeroAreaFaces':sum(p.area<1e-12 for p in me.polygons),'visible':o.visible_get()})
   if o in supports:
    pts=[]
    for edge in me.edges:
     a,b=[ev[v] for v in edge.vertices]
     if a.z*b.z<0:pts.append(list(a+(b-a)*(-a.z/(b.z-a.z))))
     elif abs(a.z)<1e-8:pts.append(list(a))
     elif abs(b.z)<1e-8:pts.append(list(b))
    sections.append({'name':o.name,'rootRelativeMatrix':mat(inv@e.matrix_world),'points':pts,'xyConvexHullArea':hull_area(pts),'bounds':bounds(pts)})
   e.to_mesh_clear()
  allbvh=BVHTree.FromPolygons(sv,sf);center=root.matrix_world@Vector((0,0,.74));axis=root.matrix_world.to_3x3()@Vector((0,1,0));rays=[]
  for dx,dz in [(0,0),(-.06,0),(.06,0),(0,-.06),(0,.06)]:
   p=root.matrix_world@Vector((dx,0,.74+dz))
   for sign in [-1,1]:
    hit=allbvh.ray_cast(p,axis*sign,.6);rays.append({'offsetXZ':[dx,dz],'sign':sign,'hit':list(hit[0]) if hit[0] else None})
  joins=[{'support':o.name,'continuousRimIntersectionPairs':len(bvhs[o.name].overlap(bvhs[rim.name]))} for o in supports];rb=bounds(ra);eb=bounds(eva);limits=[(-.74,.74),(-.30,.30),(-.06,1.5)];within=all(b['min'][j]>=lo-1e-5 and b['max'][j]<=hi+1e-5 for j,(lo,hi) in enumerate(limits) for b in [rb,eb])
  path=folder/f'{i:03d}.png';assert not path.exists();sc.render.filepath=str(path);start=time.monotonic();bpy.ops.render.render(write_still=True,scene=sc.name)
  records.append({'direction':d,'index':i,'frame':i+1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'rootPixel':px((0,0,0)),'entryWorld':list(center),'entryPixel':px(center),'rawBoundsCanonicalS':rb,'evaluatedBoundsCanonicalS':eb,'withinFrozenBudget':within,'supportSections':sections,'supportRimIntersections':joins,'apertureRays':rays,'nearestEntrySurfaceDistance':allbvh.find_nearest(center)[3],'objects':mrecords,'path':str(path.relative_to(H)),'sha256':sha(path),'seconds':time.monotonic()-start})
  write('native-measurements.json',{'asset':'portal-entry','sourceSHA256':sha(SOURCE),'views':records});print('INDEPENDENT_NATIVE',d,i,within,flush=True)
assert len(records)==48
# Native terminal remains stable when the saved one-shot curves are evaluated beyond the last published phase.
root.rotation_euler.z=0;sc.frame_set(12);sc.view_layers[0].update();terminal={o.name:mat(root.matrix_world.inverted()@o.matrix_world) for o in own};sc.frame_set(24);sc.view_layers[0].update();after={o.name:mat(root.matrix_world.inverted()@o.matrix_world) for o in own};write('terminal-source-hold.json',{'nativeLastFrame':12,'nativeLaterFrame':24,'allOwnedMatricesSame':terminal==after,'terminal':terminal,'later':after,'sourceSHA256':sha(SOURCE)});print('INDEPENDENT_NATIVE_COMPLETE',flush=True)
