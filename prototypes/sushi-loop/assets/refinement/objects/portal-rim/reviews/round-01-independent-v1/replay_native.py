"""Independent saved-source native replay/measurements. Never saves model bytes."""
import bpy,sys,json,math,hashlib,time,itertools
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parents[1];C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def w(n,d):(P/n).write_text(json.dumps(d,indent=2)+'\n')
def matrix(m):return [list(x) for x in m]
def bounds(v):return [[min(p[a] for p in v) for a in range(3)],[max(p[a] for p in v) for a in range(3)]] if v else None
def hull(pts):
 pts=sorted(set((round(float(v.x),8),round(float(v.y),8)) for v in pts))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lo=[];hi=[]
 for p in pts:
  while len(lo)>1 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
  lo.append(p)
 for p in reversed(pts):
  while len(hi)>1 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
  hi.append(p)
 return lo[:-1]+hi[:-1]
def section(v,e):
 pts=[]
 for edge in e:
  a,b=[v[i] for i in edge]
  if abs(a.z)<1e-8:pts.append(a)
  if abs(b.z)<1e-8:pts.append(b)
  if a.z*b.z<0:pts.append(a+(b-a)*(-a.z/(b.z-a.z)))
 h=hull(pts);area=abs(sum(h[i][0]*h[(i+1)%len(h)][1]-h[(i+1)%len(h)][0]*h[i][1] for i in range(len(h)))/2) if h else 0
 return {'planeZ':0,'hullXY':h,'area':area}
def inside(tree,p,d):
 n=0;origin=p.copy()
 for i in range(128):
  hit,normal,index,dist=tree.ray_cast(origin,d,10)
  if hit is None:break
  n+=1;origin=hit+d*1e-6
 return n%2==1
source=Path(bpy.data.filepath);sourceSHA=sha(source);assert sourceSHA=='b50941fdefc5acfcaa040479227b517164ddedd886671a9130d014f2f7ceea60'
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=bpy.data.collections['S33_PROP_portal_rim.002'];root=bpy.data.objects['portal_rim__root.002'];own=list(col.all_objects)
def layers(l):
 yield l
 for c in l.children:yield from layers(c)
for l in layers(sc.view_layers[0].layer_collection):l.exclude=False;l.hide_viewport=False
for c in [sc.collection,col,*col.children_recursive]:c.hide_render=False;c.hide_viewport=False
for o in own:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
sc.view_layers[0].update();bpy.context.evaluated_depsgraph_get().update()
sc.render.threads_mode='FIXED';sc.render.threads=4
materials={s.material for o in own for s in o.material_slots if s.material}
audit={'sourceSHA256':sourceSHA,'blenderVersion':bpy.app.version_string,'scene':sc.name,'collection':col.name,'root':root.name,'objects':len(own),'meshes':[],'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'externalParents':[o.name for o in own if o.parent and o.parent not in own],'modifiers':{o.name:[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers] for o in own},'shapeKeys':[o.name for o in own if o.type=='MESH' and o.data.shape_keys],'armatures':[o.name for o in own if o.type=='ARMATURE'],'materials':[],'lights':[{'name':o.name,'type':o.data.type,'power':o.data.energy,'size':getattr(o.data,'size',None),'color':list(o.data.color),'matrixWorld':matrix(o.matrix_world)} for o in sc.objects if o.type=='LIGHT'],'worldNodes':[{'type':n.type,'strength':n.inputs['Strength'].default_value if n.type=='BACKGROUND' else None} for n in sc.world.node_tree.nodes] if sc.world and sc.world.use_nodes else [],'render':{'engine':sc.render.engine,'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'fps':sc.render.fps,'fpsBase':sc.render.fps_base,'filterSize':sc.render.filter_size,'ditherIntensity':sc.render.dither_intensity,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None}}
for o in own:
 if o.type!='MESH':continue
 m=o.data;counts={}
 for f in m.polygons:
  for e in f.edge_keys:counts[e]=counts.get(e,0)+1
 m.calc_loop_triangles();vol=sum(m.vertices[t.vertices[0]].co.dot(m.vertices[t.vertices[1]].co.cross(m.vertices[t.vertices[2]].co))/6 for t in m.loop_triangles)
 audit['meshes'].append({'object':o.name,'boundaryEdges':sum(v==1 for v in counts.values()),'nonManifoldEdges':sum(v>2 for v in counts.values()),'localSignedVolume':vol,'vertices':len(m.vertices),'polygons':len(m.polygons),'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'actionFrameRange':list(o.animation_data.action.frame_range) if o.animation_data and o.animation_data.action else None})
for m in sorted(materials,key=lambda m:m.name):audit['materials'].append({'name':m.name,'nodes':[{'type':n.type,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__iter__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(int,float,bpy.types.bpy_prop_array))},'ramp':[(e.position,list(e.color)) for e in n.color_ramp.elements] if hasattr(n,'color_ramp') else None} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]})
w('source-audit.json',audit)
def px(p):
 q=world_to_camera_view(sc,sc.camera,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def cam():
 origin=px((0,0,0));return {'name':sc.camera.name,'type':sc.camera.data.type,'sensorFit':sc.camera.data.sensor_fit,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'worldMatrix':matrix(sc.camera.matrix_world),'projectionMatrix':matrix(sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'calibration':{'root':origin,**{k:[v-origin[i] for i,v in enumerate(px(p))] for k,p in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}}}
pairs=[['portal_rim__support_left','portal_rim__saddle_-1'],['portal_rim__support_right','portal_rim__saddle_1'],['portal_rim__saddle_-1','portal_rim__outer_structural_rail'],['portal_rim__saddle_1','portal_rim__outer_structural_rail'],['portal_rim__outer_structural_rail','portal_rim__aqua_channel'],['portal_rim__aqua_channel','portal_rim__cyan_continuous_band']]
frames={};captures=[]
for facing,deg in [('N',180),('E',90),('S',0),('W',-90)]:
 frames[facing]=[]
 for i in range(13):
  sc.frame_set(i+1);root.rotation_euler.z=math.radians(deg);sc.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update();inv=root.matrix_world.inverted();trees={};boxes={};objs={};rv=[];ev=[];contacts={}
  for o in own:
   obj={'matrixWorld':matrix(o.matrix_world),'scale':list(o.scale),'location':list(o.location),'rotationEuler':list(o.rotation_euler),'hideRender':o.hide_render,'visible':o.visible_get()}
   if o.type=='MESH':
    eo=o.evaluated_get(dg);me=eo.to_mesh();r=[o.matrix_world@v.co for v in o.data.vertices];v=[eo.matrix_world@x.co for x in me.vertices];canr=[inv@x for x in r];cane=[inv@x for x in v];rv.extend(canr);ev.extend(cane);trees[o.name]=BVHTree.FromPolygons(v,[list(f.vertices) for f in me.polygons]);boxes[o.name]=bounds(v);obj.update(rawAuthoredBounds=bounds(r),evaluatedModifierBounds=bounds(v),rawCanonicalBounds=bounds(canr),evaluatedCanonicalBounds=bounds(cane),evaluatedGeometrySHA256=hashlib.sha256(json.dumps([list(x) for x in v],separators=(',',':')).encode()).hexdigest())
    if o.name in ['portal_rim__support_left','portal_rim__support_right']:contacts[o.name]={'raw':section(r,[list(e.vertices) for e in o.data.edges]),'evaluated':section(v,[list(e.vertices) for e in me.edges])}
    eo.to_mesh_clear()
   objs[o.name]=obj
  axis=(root.matrix_world.to_3x3()@Vector((0,1,0))).normalized();entry=root.matrix_world@Vector((0,0,.74));hits=[n for n,t in trees.items() if t.ray_cast(entry-axis*.3,axis,.6)[0] is not None];nearest=min(t.find_nearest(entry)[3] for t in trees.values());connection=[]
  for a,b in pairs:
   low=[max(boxes[a][0][j],boxes[b][0][j]) for j in range(3)];high=[min(boxes[a][1][j],boxes[b][1][j]) for j in range(3)];overlap=trees[a].overlap(trees[b]);witness=None
   if all(high[j]>low[j] for j in range(3)):
    for q in itertools.product([.1,.3,.5,.7,.9],repeat=3):
     point=Vector([low[j]+q[j]*(high[j]-low[j]) for j in range(3)])
     if inside(trees[a],point,axis) and inside(trees[b],point,axis):witness=list(point);break
   connection.append({'meshes':[a,b],'surfaceTriangleIntersectionCount':len(overlap),'independentInteriorGridWitnessWorld':witness,'intersectsOrInteriorWitness':bool(overlap) or witness is not None})
  entryPixel=px(entry);rootPixel=px(root.matrix_world.translation)
  record={'direction':facing,'clip':'idle','frameIndex':i,'nativeFrame':i+1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world),'camera':cam(),'rawCanonicalBounds':bounds(rv),'evaluatedCanonicalBounds':bounds(ev),'finiteGroundContacts':contacts,'entryOpening':{'world':list(entry),'logicalRelative':[(entryPixel[j]-rootPixel[j])/4 for j in range(2)],'nearestSurfaceDistance':nearest,'normalSegmentHits':hits},'connections':connection,'objects':objs}
  frames[facing].append(record)
  if i==12:continue
  target=P/'raw/idle'/facing/f'{i:03d}.png';target.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(target);bpy.ops.render.render(write_still=True,scene=sc.name);captures.append({'direction':facing,'frameIndex':i,'path':str(target.relative_to(O)),'sha256':sha(target),'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world)})
  print('JUDGE_NATIVE',len(captures),facing,i,flush=True)
w('native-replay.json',{'sourceSHA256':sourceSHA,'sourceSHA256After':sha(source),'blenderVersion':bpy.app.version_string,'camera':cam(),'captureRecords':captures,'frames':frames,'connectionMethod':'Independent evaluated BVH surface intersection plus automatic overlap-AABB interior sample search, not editor-supplied witness coordinates. Native captures are unmodified full saved frame.','approval':False})
print('JUDGE_NATIVE_COMPLETE',len(captures),flush=True)
