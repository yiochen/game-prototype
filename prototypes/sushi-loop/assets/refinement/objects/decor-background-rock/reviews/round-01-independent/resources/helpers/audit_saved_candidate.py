"""Independent exact saved-source inspection/replay. No source saves or geometry edits."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;SC=bpy.context.scene
ROOT=bpy.data.objects['S33 production concept cobalt-shelf root.001'];COL=ROOT.users_collection[0];OWN=[ROOT]+list(ROOT.children_recursive);CAM=SC.camera
def plain(v):
    if isinstance(v,(str,float,int,bool)) or v is None:return v
    try:return [plain(x) for x in v]
    except:return str(v)
def bounds(p):return {'min':[min(v[a] for v in p) for a in range(3)],'max':[max(v[a] for v in p) for a in range(3)]}
def props(o):return {k:plain(o[k]) for k in o.keys() if k!='_RNA_UI'}
def animation(o):
    ad=getattr(o,'animation_data',None)
    return {'activeAction':ad.action.name if ad and ad.action else None,'nlaCount':len(ad.nla_tracks) if ad else 0,'drivers':[{'path':f.data_path,'expression':f.driver.expression} for f in ad.drivers] if ad else []}
def tree(t):
    if not t:return None
    return {'name':t.name,'animation':animation(t),'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'inputs':{str(i)+':'+s.name:plain(s.default_value) for i,s in enumerate(n.inputs) if hasattr(s,'default_value')},'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'group':tree(n.node_tree) if n.type=='GROUP' else None,'ramp':[{'position':x.position,'color':plain(x.color)} for x in n.color_ramp.elements] if hasattr(n,'color_ramp') else None} for n in t.nodes],'links':[[x.from_node.name,x.from_socket.name,x.to_node.name,x.to_socket.name] for x in t.links]}
def enable(lc):
    hit=lc.collection==COL
    for c in lc.children:hit=enable(c) or hit
    if hit:lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False;lc.collection.hide_render=False
    return hit
saved={'scene':SC.name,'rootMatrix':plain(ROOT.matrix_world),'rootRotation':plain(ROOT.rotation_euler),'rootScale':plain(ROOT.scale),'frameCurrent':SC.frame_current,'frameRange':[SC.frame_start,SC.frame_end],'fps':SC.render.fps,'camera':CAM.name,'resolution':[SC.render.resolution_x,SC.render.resolution_y,SC.render.resolution_percentage],'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y],'filterSize':SC.render.filter_size,'filmTransparent':SC.render.film_transparent,'engine':SC.render.engine,'view':SC.view_settings.view_transform,'look':SC.view_settings.look,'exposure':SC.view_settings.exposure,'gamma':SC.view_settings.gamma,'dither':SC.render.dither_intensity,'collection':COL.name,'collectionHideRender':COL.hide_render,'collectionHideViewport':COL.hide_viewport}
for vl in SC.view_layers:enable(vl.layer_collection)
for o in OWN:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
SC.frame_set(1);ROOT.rotation_euler.z=0;bpy.context.view_layer.update();DG=bpy.context.evaluated_depsgraph_get();DG.update()
materials={m.name:m for o in OWN if o.type=='MESH' for m in o.data.materials if m}
owners={}
def add(o,label):
    if o is not None:owners[o.as_pointer()]=(o,label)
def addtree(t,label):
    if t is None or t.as_pointer() in owners:return
    add(t,label)
    for n in t.nodes:
        if n.type=='GROUP':addtree(n.node_tree,label+'/'+n.name)
for o in SC.objects:
    add(o,'object/'+o.name);add(o.data,'data/'+o.name)
    if o.type=='MESH':add(o.data.shape_keys,'shape/'+o.name)
for m in materials.values():add(m,'material/'+m.name);addtree(m.node_tree,'materialTree/'+m.name)
add(SC,'scene');add(SC.world,'world');addtree(SC.world.node_tree,'worldTree');addtree(SC.compositing_node_group,'compositor')
temporal=[{'label':label,'name':o.name}|animation(o) for o,label in owners.values()]
objectRecords=[];BVH={};grounded=[]
for o in OWN:
    rec={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrixWorld':plain(o.matrix_world),'properties':props(o),'constraints':[{'name':x.name,'type':x.type,'target':getattr(getattr(x,'target',None),'name',None)} for x in o.constraints],
         'modifiers':[{'name':m.name,'type':m.type,'render':m.show_render,'viewport':m.show_viewport,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None),'target':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers]}
    if o.type=='MESH':
        raw=[o.matrix_world@v.co for v in o.data.vertices];ev=o.evaluated_get(DG);me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];me.calc_loop_triangles();tris=[list(t.vertices) for t in me.loop_triangles];edgeuses={}
        for face in me.polygons:
            for edge in face.edge_keys:
                key=tuple(sorted(edge));edgeuses[key]=edgeuses.get(key,0)+1
        volume=sum(pts[t[0]].dot(pts[t[1]].cross(pts[t[2]]))/6 for t in tris);z0=sum(abs(v.z)<1e-6 for v in pts)
        if z0:grounded.append(o.name)
        BVH[o.name]=BVHTree.FromPolygons(pts,tris,all_triangles=True)
        rec.update(rawAuthoredBounds=bounds(raw),evaluatedBounds=bounds(pts),rawVertices=len(raw),evaluatedVertices=len(pts),polygons=len(me.polygons),triangles=len(tris),signedVolume=volume,groundVertices=z0,boundaryEdges=sum(n==1 for n in edgeuses.values()),nonManifoldEdges=sum(n!=2 for n in edgeuses.values()),finiteCoordinates=all(math.isfinite(v) for p in pts for v in p),uvLayers=[u.name for u in o.data.uv_layers],shapeKeys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],rawCustomNormals=o.data.has_custom_normals,evaluatedCustomNormals=me.has_custom_normals,materialSlots=[m.name for m in o.data.materials if m])
        ev.to_mesh_clear()
    objectRecords.append(rec)
intersections=[];graph={n:set() for n in BVH}
names=list(BVH)
for i,a in enumerate(names):
    for b in names[i+1:]:
        hits=BVH[a].overlap(BVH[b])
        if hits:intersections.append({'objects':[a,b],'intersectingTrianglePairs':len(hits)});graph[a].add(b);graph[b].add(a)
reached=set(grounded);todo=list(grounded)
while todo:
    for n in graph[todo.pop()]-reached:reached.add(n);todo.append(n)
def px(p):
    v=world_to_camera_view(SC,CAM,Vector(p));return Vector((v.x*SC.render.resolution_x,(1-v.y)*SC.render.resolution_y))
base=px((0,0,0));camera={'name':CAM.name,'type':CAM.data.type,'worldMatrix':plain(CAM.matrix_world),'projectionMatrix':plain(CAM.calc_matrix_camera(DG,x=SC.render.resolution_x,y=SC.render.resolution_y,scale_x=SC.render.pixel_aspect_x,scale_y=SC.render.pixel_aspect_y)),'orthoScale':CAM.data.ortho_scale,'shift':[CAM.data.shift_x,CAM.data.shift_y],'clip':[CAM.data.clip_start,CAM.data.clip_end],'calibration':{'root':plain(base),'unitX':plain(px((1,0,0))-base),'unitDepth':plain(px((0,-1,0))-base),'unitHeight':plain(px((0,0,1))-base)}}
lightRecord=[{'name':o.name,'matrixWorld':plain(o.matrix_world),'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'shape':getattr(o.data,'shape',None),'color':plain(o.data.color),'hideRender':o.hide_render} for o in SC.objects if o.type=='LIGHT']
sourceHash=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest();captures=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
    ROOT.rotation_euler.z=math.radians(degrees);SC.frame_set(1);bpy.context.view_layer.update();DG=bpy.context.evaluated_depsgraph_get();DG.update();rawpts=[];evalpts=[]
    for o in OWN:
        if o.type!='MESH':continue
        rawpts.extend(o.matrix_world@v.co for v in o.data.vertices);ev=o.evaluated_get(DG);me=ev.to_mesh();evalpts.extend(ev.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
    path=HERE/'native-replay'/direction/'000.png';path.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    captures.append({'direction':direction,'clip':'static','frameIndex':0,'nativeFrame':1,'rootRotationZ':ROOT.rotation_euler.z,'rootRotationDegrees':math.degrees(ROOT.rotation_euler.z),'actualRootMatrix':plain(ROOT.matrix_world),'rawAuthoredBounds':bounds(rawpts),'evaluatedBounds':bounds(evalpts),'envelopePass':all(-.500001<=v[0]<=.500001 and -.500001<=v[1]<=.500001 and -.000001<=v[2]<=1.075001 for v in evalpts),'path':str(path.relative_to(OBJ)),'sourceSHA256':sourceHash});print('INDEPENDENT_NATIVE_REPLAY',direction,flush=True)
ROOT.rotation_euler.z=0;samples=[]
for frame in [1,2,12]:
    SC.frame_set(frame);bpy.context.view_layer.update();DG=bpy.context.evaluated_depsgraph_get();DG.update();state={}
    for o in OWN:
        value={'matrix':plain(o.matrix_world),'hideRender':o.hide_render}
        if o.type=='MESH':ev=o.evaluated_get(DG);me=ev.to_mesh();value['vertices']=[plain(ev.matrix_world@v.co) for v in me.vertices];ev.to_mesh_clear()
        state[o.name]=value
    samples.append({'nativeFrame':frame,'evaluatedStateSHA256':hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()})
result={'asset':'decor-background-rock','candidatePacketSHA256':'20f3fe4297877ecc50affda4574c2ade50482e7068bd9d457fbfb3e6ff2bc54c','sourceFile':str(Path(bpy.data.filepath)),'sourceSHA256':sourceHash,'blender':bpy.app.version_string,'savedState':saved,'enabledActualViewLayerBeforeSampling':True,'rootProperties':props(ROOT),'objects':objectRecords,'sceneObjects':[{'name':o.name,'type':o.type,'owned':o in OWN} for o in SC.objects],
        'materials':{n:{'users':m.users,'actualObjectOwners':[o.name for o in bpy.data.objects if o.type=='MESH' and any(s.material==m for s in o.material_slots)],'properties':props(m),'tree':tree(m.node_tree)} for n,m in materials.items()},'world':tree(SC.world.node_tree),'compositor':tree(SC.compositing_node_group),'lights':lightRecord,'camera':camera,'captureRecords':captures,'staticTemporalOwners':temporal,'noTemporalChannels':all(not r['activeAction'] and not r['nlaCount'] and not r['drivers'] for r in temporal),'staticProbeFrames':samples,'staticInvariance':len({s['evaluatedStateSHA256'] for s in samples})==1,'groundedNativeMeshes':grounded,'surfaceIntersectionGraph':intersections,'allNativeMeshesConnectedToGroundedMass':set(names)<=reached,
        'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'texts':[t.name for t in bpy.data.texts]},'scope':'Read exact saved source, enable actual collection/object ancestry, measure/recapture fixed existing camera/material/light and four cardinal static root poses. No source save, geometry construction, per-view fitting, grading or pixel repair.'}
(HERE/'independent-native-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('INDEPENDENT_NATIVE_COMPLETE',flush=True)
