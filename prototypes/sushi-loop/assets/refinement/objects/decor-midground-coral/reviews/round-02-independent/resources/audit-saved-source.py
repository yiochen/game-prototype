import bpy,json,math,pathlib,hashlib,struct
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
O=pathlib.Path(__file__).parents[3];B=pathlib.Path(__file__).parents[1];C=O/'candidates/round-02';sc=bpy.context.scene
col=bpy.data.collections['decor-midground-coral refined'];root=bpy.data.objects['decor-midground-coral root'];cam=sc.camera
# Enable real collection in the active evaluated view layer before all sampling.
def enable(lc):
 if lc.collection==col:lc.exclude=False;lc.hide_viewport=False
 for c in lc.children:enable(c)
enable(bpy.context.view_layer.layer_collection);col.hide_viewport=False;col.hide_render=False
for o in col.all_objects:o.hide_set(False)
bpy.context.view_layer.update()
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def mat(m):return [list(r)for r in m]
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pp=[root.matrix_world.inverted()@ev.matrix_world@v.co for v in me.vertices];ff=[list(p.vertices)for p in me.polygons];ev.to_mesh_clear();return pp,ff
meshes=[o for o in col.all_objects if o.type=='MESH'];corals=[o for o in meshes if o.animation_data and o.animation_data.action];rocks=[o for o in meshes if o.get('role')=='reef'];accents=[o for o in meshes if o.get('role')=='accent']
def digest(pp):return hashlib.sha256(b''.join(struct.pack('<fff',*v)for v in pp)).hexdigest()
def bounds(pp):return [[min(p[i]for p in pp),max(p[i]for p in pp)]for i in range(3)]
def actualBaseIndices(o):
 me=o.data;minimum=min(v.co.z for v in me.vertices)
 faces=[p for p in me.polygons if p.normal.z<-.9 and all(abs(me.vertices[i].co.z-minimum)<1e-5 for i in p.vertices)]
 if len(faces)!=1:raise ValueError('Ambiguous actual finite bottom face '+o.name)
 return list(faces[0].vertices)
baseIndices={o.name:actualBaseIndices(o)for o in corals+accents}
def ground():
 pp=[];ff=[]
 for o in rocks:
  p,f=points(o);off=len(pp);pp+=p;ff += [[v+off for v in face]for face in f]
 return BVHTree.FromPolygons(pp,ff,all_triangles=False),pp
records=[];geometries={};reefHashes=set();intersections=[]
def sample(frame,direction):
 whole=[];byname={};tree,rp=ground();reefHashes.add(digest(rp));ts={};supports=[]
 for o in meshes:
  pp,ff=points(o);whole+=pp;byname[o.name]=digest(pp)
  if o in corals:ts[o.name]=BVHTree.FromPolygons(pp,ff,all_triangles=False)
  if o.name in baseIndices:
   values=[]
   for i in baseIndices[o.name]:
    p=pp[i];hit,*_=tree.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3);values.append(hit.z-p.z if hit else None)
   supports.append({'owner':o.name,'indices':baseIndices[o.name],'supported':sum(v is not None and v>=-1e-5 for v in values),'total':len(values),'minimumPenetration':min(v for v in values if v is not None)if any(v is not None for v in values)else None})
 for i,o in enumerate(corals):
  for other in corals[i+1:]:
   pairs=ts[o.name].overlap(ts[other.name])
   if pairs:intersections.append({'direction':direction,'frame':frame,'owners':[o.name,other.name],'triangleOverlapPairs':len(pairs)})
 return {'direction':direction,'nativeFrame':frame,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'rootLocation':list(root.location),'rootScale':list(root.scale),'boundsRoot':bounds(whole),'geometryByOwner':byname,'finiteSupport':supports}
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 for f in range(1,14):
  root.rotation_euler.z=angle;sc.frame_set(f);bpy.context.view_layer.update();r=sample(f,d);records.append(r);geometries[d,f]=r['geometryByOwner']
quarter=[];root.rotation_euler.z=0
for i in range(49):
 f=1+i/4;sc.frame_set(math.floor(f),subframe=f-math.floor(f));bpy.context.view_layer.update();quarter.append(sample(f,'S-quarter'))
# Neutral geometry requires detaching all actual coral actions before zeroing, then restoring actual slots.
saved=[]
for o in corals:
 ad=o.animation_data;saved.append((o,ad.action,ad.action_slot));ad.action=None;o.rotation_euler=(0,0,0)
bpy.context.view_layer.update();neutral=bounds([p for o in meshes for p in points(o)[0]])
for o,action,slot in saved:o.animation_data.action=action;o.animation_data.action_slot=slot
ownership=[]
for o in list(bpy.data.objects)+list(bpy.data.meshes)+list(bpy.data.materials)+list(bpy.data.worlds)+list(bpy.data.lights)+list(bpy.data.node_groups):
 for owner in [o]+([o.node_tree]if hasattr(o,'node_tree')and o.node_tree else []):
  ad=getattr(owner,'animation_data',None)
  if ad:
   curves=[]
   if ad.action:
    for l in ad.action.layers:
     for st in l.strips:
      for bag in st.channelbags:
       for fc in bag.fcurves:curves.append({'path':fc.data_path,'index':fc.array_index,'keys':[[float(k.co.x),float(k.co.y),k.interpolation]for k in fc.keyframe_points]})
   ownership.append({'owner':owner.name,'type':owner.bl_rna.identifier,'action':ad.action.name if ad.action else None,'slot':ad.action_slot.identifier if ad.action and ad.action_slot else None,'curves':curves,'drivers':[{'path':fc.data_path,'expression':fc.driver.expression}for fc in ad.drivers],'nlaTracks':len(ad.nla_tracks)})
recorded=json.loads((O/'inputs/source-camera.json').read_text());bpy.context.view_layer.update()
projected=cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)
def px(p):
 v=world_to_camera_view(sc,cam,Vector(p));return[v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
p0=px((0,0,0));actualCamera={'worldMatrix':mat(cam.matrix_world),'projectionMatrix':mat(projected),'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'root':p0,'unitX':[a-b for a,b in zip(px((1,0,0)),p0)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),p0)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),p0)]}
recaptures=[]
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=angle;sc.frame_set(4);bpy.context.view_layer.update();p=B/'recapture'/f'{d}-003.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 recaptures.append({'direction':d,'nativeFrame':4,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'path':str(p.relative_to(O)),'sha256':sha(p)});print('JUDGE_RECAPTURE',d,flush=True)
result={'asset':'decor-midground-coral','candidatePacketSHA256':sha(C/'packet.json'),'sourceSHA256':sha(O/'source/round-02.blend'),'blender':bpy.app.version_string,'camera':actualCamera,'worldMatrixDifference':max(abs(actualCamera['worldMatrix'][i][j]-recorded['camera']['worldMatrix'][i][j])for i in range(4)for j in range(4)),'projectionMatrixDifference':max(abs(actualCamera['projectionMatrix'][i][j]-recorded['camera']['projectionMatrix'][i][j])for i in range(4)for j in range(4)),'collection':col.name,'ownedMeshes':[o.name for o in meshes],'discoveredCoralActionOwners':[o.name for o in corals],'staticReefMeshes':[o.name for o in rocks],'accentMeshes':[o.name for o in accents],'allPhaseRecords':records,'quarterPhaseRecords':quarter,'neutralBounds':neutral,'coralSurfaceIntersections':intersections,'staticReefGeometryHashCount':len(reefHashes),'closure':{d:geometries[d,1]==geometries[d,13]for d in 'NESW'},'temporalOwnership':ownership,'libraries':[l.filepath for l in bpy.data.libraries],'actualTextures':[{'material':m.name,'image':n.image.filepath if n.image else None}for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],'shapes':[o.name for o in meshes if o.data.shape_keys],'constraints':[{'owner':o.name,'type':c.type}for o in col.all_objects for c in o.constraints],'materials':[{'name':m.name,'users':m.users,'nodes':[n.type for n in m.node_tree.nodes]}for m in bpy.data.materials if m.node_tree],'lightRig':[{'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'shape':o.data.shape}for o in sc.objects if o.type=='LIGHT'],'world':[{'name':n.name,'type':n.type,'color':list(n.inputs['Color'].default_value),'strength':n.inputs['Strength'].default_value}for n in sc.world.node_tree.nodes if n.type=='BACKGROUND'],'engine':sc.render.engine,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'nativeAA':{'samples':sc.cycles.samples,'denoise':sc.cycles.use_denoising,'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'filter':sc.cycles.pixel_filter_type,'width':sc.cycles.filter_width,'viewTransform':sc.view_settings.view_transform,'compositor':sc.use_nodes},'recaptures':recaptures,'scope':'Independent read-only background inspection and recapture. Saved source unchanged. All required native phases plus49quarter samples; no new model construction.'}
(B/'native-proof.json').write_text(json.dumps(result,indent=2)+'\n');print('JUDGE_NATIVE_COMPLETE',flush=True)
