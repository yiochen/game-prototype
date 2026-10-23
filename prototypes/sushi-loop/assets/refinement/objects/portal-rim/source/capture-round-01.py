"""Clean saved-source replay, all48 native captures and actual geometry evidence."""
import bpy, sys, math, json, hashlib, time
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;C=S.parent/'candidates/round-01';C.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,indent=2)+'\n')
def matrix(m):return [list(r) for r in m]
def bounds(a):
    a=list(a)
    return [[min(v[i] for v in a) for i in range(3)],[max(v[i] for v in a) for i in range(3)]] if a else None
def digestpoints(a):return hashlib.sha256(json.dumps([list(v) for v in a],separators=(',',':')).encode()).hexdigest()
def hull(points):
    p=sorted(set((round(float(v[0]),8),round(float(v[1]),8)) for v in points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    if len(p)<3:return p
    lo=[]
    for v in p:
        while len(lo)>=2 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
        lo.append(v)
    hi=[]
    for v in reversed(p):
        while len(hi)>=2 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
        hi.append(v)
    return lo[:-1]+hi[:-1]
def section(vertices,edges):
    pts=[]
    for i,j in edges:
        a=vertices[i];b=vertices[j]
        if abs(a.z)<1e-8:pts.append(a)
        if abs(b.z)<1e-8:pts.append(b)
        if a.z*b.z<0:pts.append(a+(b-a)*(-a.z/(b.z-a.z)))
    h=hull(pts);area=abs(sum(h[i][0]*h[(i+1)%len(h)][1]-h[(i+1)%len(h)][0]*h[i][1] for i in range(len(h)))/2) if h else 0
    return {'z':0,'polygonXY':h,'area':area,'finitePositive':area>1e-8}
def contains(tree,point,direction):
    count=0;origin=point.copy();distance=0
    for i in range(32):
        hit,normal,index,d=tree.ray_cast(origin,direction,10-distance)
        if hit is None:break
        count+=1;distance+=d+1e-6;origin=hit+direction*1e-6
    return bool(count%2)

source=Path(bpy.data.filepath);source_sha=sha(source)
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
col=bpy.data.collections['S33_PROP_portal_rim.002'];root=bpy.data.objects['portal_rim__root.002'];own=list(col.all_objects)
def unhide(lc):
    lc.exclude=False;lc.hide_viewport=False
    for child in lc.children:unhide(child)
for vl in sc.view_layers:vl.use=True;unhide(vl.layer_collection)
for c in [sc.collection,col,*col.children_recursive]:c.hide_viewport=False;c.hide_render=False
for o in own:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
sc.render.threads_mode='FIXED';sc.render.threads=4
def px(p):
    v=world_to_camera_view(sc,sc.camera,Vector(p));return [v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y]
def camera_record():
    origin=px((0,0,0));cal={'root':origin}
    for name,p in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]:cal[name]=[v-origin[i] for i,v in enumerate(px(p))]
    return {'projection':'top-down-oblique-square-grid','frame':[192,384],'anchor':[96,288],'cellSize':128,'captureScale':4,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':matrix(sc.camera.matrix_world),'projectionMatrix':matrix(sc.camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134,'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y]},'calibration':cal,'artStyle':{'revision':'warm-soft-native-round-01','recipe':'round-01-settings.json','lighting':'centered broad overhead plus four equal cardinal soft fills','groundShadow':'no floor and no directional ground cast','materials':'native geometry and Principled shaders; no image textures or compositor paint'}}

frames={};capture_records=[];closure={};failures=[]
budget=[[-.73,-.30,-.06],[.73,.30,1.48]]
for facing,deg in [('N',180),('E',90),('S',0),('W',-90)]:
    frames[facing]=[]
    for i in range(13):
        sc.frame_set(i+1);root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
        inv=root.matrix_world.inverted();objects={};trees={};allraw=[];allev=[];canonicalraw=[];canonicalev=[];projected=[];contacts={}
        for o in own:
            eo=o.evaluated_get(dg)
            rec={'type':o.type,'parent':o.parent.name if o.parent else None,'collections':[c.name for c in o.users_collection],'matrixWorld':matrix(eo.matrix_world),'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'hideRender':o.hide_render,'visible':o.visible_get()}
            if o.type=='MESH':
                raw=[o.matrix_world@v.co for v in o.data.vertices];me=eo.to_mesh();ev=[eo.matrix_world@v.co for v in me.vertices]
                canraw=[inv@p for p in raw];canev=[inv@p for p in ev]
                allraw.extend(raw);allev.extend(ev);canonicalraw.extend(canraw);canonicalev.extend(canev);projected.extend(px(v) for v in ev)
                trees[o.name]=BVHTree.FromPolygons(ev,[list(p.vertices) for p in me.polygons])
                rec.update(rawAuthoredBounds=bounds(raw),evaluatedModifierBounds=bounds(ev),rawCanonicalSBounds=bounds(canraw),evaluatedCanonicalSBounds=bounds(canev),rawVertexCount=len(raw),evaluatedVertexCount=len(ev),rawGeometrySHA256=digestpoints(raw),evaluatedGeometrySHA256=digestpoints(ev),materials=[s.material.name if s.material else None for s in o.material_slots])
                if o.name in ['portal_rim__support_left','portal_rim__support_right']:
                    contacts[o.name]={'raw':section(raw,[e.vertices[:] for e in o.data.edges]),'evaluated':section(ev,[e.vertices[:] for e in me.edges])}
                eo.to_mesh_clear()
            objects[o.name]=rec
        entry=root.matrix_world@Vector((0,0,.74));axis=(root.matrix_world.to_3x3()@Vector((0,1,0))).normalized()
        nearest=min((tree.find_nearest(entry)[3] for tree in trees.values()))
        rayhits=[]
        for name,tree in trees.items():
            hit=tree.ray_cast(entry-axis*.3,axis,.6)
            if hit[0] is not None:rayhits.append(name)
        witnesses=[]
        tests=[('core-channel',(.608,0,.74),['portal_rim__cyan_continuous_band','portal_rim__aqua_channel']),('channel-rail',(.630,0,.74),['portal_rim__aqua_channel','portal_rim__outer_structural_rail'])]
        for side,label in [(-1,'left'),(1,'right')]:tests.append(('ground-support-to-ring-'+label,(side*.440,0,.285),['portal_rim__support_'+label,'portal_rim__saddle_'+str(side),'portal_rim__outer_structural_rail','portal_rim__aqua_channel']))
        for label,p,names in tests:
            wp=root.matrix_world@Vector(p);inside={name:contains(trees[name],wp,axis) for name in names}
            witnesses.append({'name':label,'pointCanonicalS':p,'pointWorld':list(wp),'insideEvaluatedMeshes':inside,'allInside':all(inside.values())})
        rawbox=bounds(canonicalraw);evbox=bounds(canonicalev)
        budgetok=all(rawbox[0][j]>=budget[0][j]-1e-5 and rawbox[1][j]<=budget[1][j]+1e-5 and evbox[0][j]>=budget[0][j]-1e-5 and evbox[1][j]<=budget[1][j]+1e-5 for j in range(3))
        screenbox=bounds([Vector((p[0],p[1],0)) for p in projected])
        epx=px(entry);rpx=px(root.matrix_world.translation)
        entryrec={'rootRelative':[0,0,.74],'world':list(entry),'nativePixel':epx,'logicalRelativeToRoot':[(epx[j]-rpx[j])/4 for j in range(2)],'nearestEvaluatedSurfaceDistance':nearest,'normalAxisSegmentHits':rayhits,'openCenter':not rayhits and nearest>.4}
        record={'direction':facing,'clip':'idle','frameIndex':i,'blenderFrame':i+1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world),'camera':camera_record(),'rawAuthoredBounds':bounds(allraw),'evaluatedModifierBounds':bounds(allev),'rawCanonicalSBounds':rawbox,'evaluatedCanonicalSBounds':evbox,'canonicalBudgetPass':budgetok,'projectedEvaluatedBounds':screenbox,'entryOpening':entryrec,'finiteGroundContacts':contacts,'connectionInteriorWitnesses':witnesses,'objects':objects}
        if not budgetok or not entryrec['openCenter'] or not all(c['evaluated']['finitePositive'] for c in contacts.values()) or not all(w['allInside'] for w in witnesses):failures.append({'facing':facing,'frame':i,'budget':budgetok,'opening':entryrec['openCenter'],'contacts':contacts,'witnesses':witnesses})
        frames[facing].append(record)
        if i==12:
            first=frames[facing][0]
            closure[facing]={'frame13Equals1ObjectMatrices':all(objects[n]['matrixWorld']==first['objects'][n]['matrixWorld'] for n in objects),'frame13Equals1Geometry':all(objects[n].get('evaluatedGeometrySHA256')==first['objects'][n].get('evaluatedGeometrySHA256') for n in objects),'excludedFromAtlas':True}
            continue
        path=C/'raw/idle'/facing/f'{i:03d}.png';path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);start=time.monotonic();bpy.ops.render.render(write_still=True)
        capture_records.append({k:record[k] for k in ['direction','clip','frameIndex','blenderFrame','rootRotationZ','rootMatrix','camera','rawAuthoredBounds','evaluatedModifierBounds','rawCanonicalSBounds','evaluatedCanonicalSBounds','canonicalBudgetPass','projectedEvaluatedBounds','entryOpening']}|{'path':str(path.relative_to(C)),'sha256':sha(path),'seconds':time.monotonic()-start})
        write(C/'capture-progress.json',{'done':len(capture_records),'total':48,'last':str(path.relative_to(C))});print('PORTAL_NATIVE',len(capture_records),str(path.relative_to(C)),flush=True)

write(C/'native-measurements.json',{'asset':'portal-rim','sourceSHA256':source_sha,'rootObject':root.name,'measurementPolicy':'Clean saved-source load; scene/viewlayer/ancestry/own visibility enabled, depsgraph updated before every measurement. Raw authored vertices and evaluated modifiers separated. CanonicalS is inverse actual cardinal root. Finite ground sections from actual edge-plane intersections; connection witnesses tested inside actual evaluated BVHs.','frames':frames,'loopClosure':closure,'failures':failures})
native_camera=capture_records[0]['camera'];write(C/'records/native-camera.json',native_camera)
asset=json.loads((S/'round-01-resources/inputs/source-assetRecord.json').read_text());asset['artStyle']=native_camera['artStyle'];write(C/'records/native-assetRecord.json',asset)
rig=json.loads((S/'round-01-rig.json').read_text());write(C/'records/native-rig.json',rig)
published_camera=json.loads(json.dumps(native_camera));published_camera['captureScale']=2;published_camera['nativeCaptureScale']=4;published_camera['nativeFrame']=[768,1536];published_camera['publishedFrame']=[384,768];published_camera['publication']='Uniform entire768x1536 native canvas to384x768 LANCZOS; no fitting or image repair.'
for key,values in published_camera['calibration'].items():published_camera['calibration'][key]=[v/2 for v in values]
write(C/'records/camera.json',published_camera);asset['scale']=2;asset['nativeCaptureScale']=4;asset['nativeFrame']=[768,1536];write(C/'records/assetRecord.json',asset);write(C/'records/rig.json',rig)
validation={'asset':'portal-rim','round':'round-01','source':str(source.relative_to(S.parent)),'sourceSHA256':source_sha,'sourceSHA256AfterCapture':sha(source),'blenderVersion':bpy.app.version_string,'rootObject':root.name,'nativeFrame':[768,1536],'nativeCaptureScale':4,'publishedFrame':[384,768],'sourceScale':2,'logicalFrame':[192,384],'logicalRoot':[96,288],'camera':native_camera,'captureRecords':capture_records,'measurementLedger':'native-measurements.json','nativeGeometryMeasurements':{f:[r['objects'] for r in rs] for f,rs in frames.items()},'loopClosure':closure,'physicalChecks':{'allPhaseBudget':not any(not r['canonicalBudgetPass'] for rs in frames.values() for r in rs),'finiteStableGroundContacts':all(all(v['evaluated']['finitePositive'] for v in r['finiteGroundContacts'].values()) for rs in frames.values() for r in rs),'coherentConnectionInteriorWitnesses':all(all(w['allInside'] for w in r['connectionInteriorWitnesses']) for rs in frames.values() for r in rs),'openEntryCenter':all(r['entryOpening']['openCenter'] for rs in frames.values() for r in rs),'sourceUnchangedByCapture':sha(source)==source_sha},'failures':failures,'approval':False}
write(C/'nativeValidation.json',validation)
print('PORTAL_CAPTURE_COMPLETE',json.dumps({'count':len(capture_records),'failures':len(failures),'closure':closure}),flush=True)
assert not failures,failures[:1]
