"""Reproduce unadapted saved kelp, with exact frozen historical capture law."""
import bpy,json,math,sys,hashlib,importlib.util,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;OBJ=BASE.parent;RES=BASE/'round-01-resources'
OUT=OBJ/'candidates'/'round-01';OUT.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('frozen_capture_geometry',RES/'concept_decoration_geometry.py');frozen=importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
sc=bpy.data.scenes['S33 Native Asset Library Export'];bpy.context.window.scene=sc
root=bpy.data.objects['S33 production concept kelp-fan root'];col=bpy.data.collections['S33 production concept kelp-fan']
meshes=sorted([o for o in col.all_objects if o.type=='MESH'],key=lambda o:o.name)
assert len({o.data.as_pointer() for o in meshes})==len(meshes),'Shared data would be adapted twice'
assert all(not o.modifiers and not o.data.shape_keys for o in meshes),'Explicit evaluation-order contract'
source_sha=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()
original={o.name:[v.co.copy()for v in o.data.vertices]for o in meshes}
test='--test' in sys.argv
dest=OUT/os.environ.get('KELP_LOOKDEV_NAME','lookdev-v02') if test else OUT
dest.mkdir(parents=True,exist_ok=True)
def matrix(m):return [[float(v)for v in row]for row in m]
def bounds(pts):return [[min(v[i]for v in pts),max(v[i]for v in pts)]for i in range(3)]
def worldverts(o):return [o.matrix_world@v.co for v in o.data.vertices]
def tree(o):return BVHTree.FromPolygons(worldverts(o),[list(p.vertices)for p in o.data.polygons])
def inside(t,p):
    direction=Vector((.962,.213,.168)).normalized();start=Vector(p);hits=0
    for j in range(64):
        hit,normal,index,d=t.ray_cast(start,direction,100)
        if hit is None:break
        hits+=1;start=hit+direction*1e-6
    return hits%2==1
def point_record(t,p):
    near,normal,index,d=t.find_nearest(p)
    return {'inside':inside(t,p),'surfaceDistance':d,'signedNormalDistance':(p-near).dot(normal)}
cam=sc.camera
def pix(p):
    c=world_to_camera_view(sc,cam,Vector(p));return [c.x*768,(1-c.y)*1920]
origin=pix((0,0,0))
camera={'frame':[192,480],'anchor':[96,384],'captureScale':4,'fps':12,'nativeFrame':[768,1920],'camera':{'type':'orthographic','worldMatrix':matrix(cam.matrix_world),'projectionMatrix':matrix(cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1920,scale_x=1,scale_y=1)),'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'calibration':{'root':origin,'unitX':[a-b for a,b in zip(pix((1,0,0)),origin)],'unitDepth':[a-b for a,b in zip(pix((0,-1,0)),origin)],'unitHeight':[a-b for a,b in zip(pix((0,0,1)),origin)]},'adapter':'Exact frozen ordinary35 context manager after phase/facing. Data coords→world→height-dependent worldY scale→inverse. Render evaluated geometry; finally original restore.'}
records=[];first={};closure=[]
facings={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
for direction,angle in facings.items():
    for frame in ([1] if test else range(1,14)):
        sc.frame_set(frame);root.rotation_euler=(0,0,angle);bpy.context.view_layer.update()
        pre={o.name:worldverts(o)for o in meshes};pts=[v for vs in pre.values()for v in vs]
        bases=[o for o in meshes if o.get('role')=='grounded-cobalt'];base_trees=[tree(o)for o in bases]
        contacts=[]
        for o in meshes:
            if o.get('role') not in ['primary-frond','attached-fork']:continue
            cap=[pre[o.name][i]for i in list(o['capRingIndices'])]
            cap.append(sum(cap,Vector())/(len(cap)))
            if o.get('role')=='primary-frond':
                measurements=[[point_record(t,p)for t in base_trees]for p in cap]
                flags=[any(q['inside']for q in m)for m in measurements]
                contacts.append({'owner':o.name,'kind':'root-cap-vertices-and-center-in-finite-cobalt','testedPoints':len(cap),'allEmbedded':all(flags),'pointsWorld':[list(p)for p in cap],'insideAtLeastOne':flags,'maximumRequiredPenetration':min(min(q['surfaceDistance']for q in m if q['inside']) for m in measurements if any(q['inside']for q in m)) if any(flags)else None})
            else:
                t=tree(bpy.data.objects[o['primary']]);m=[point_record(t,p)for p in cap]
                contacts.append({'owner':o.name,'kind':'fork-cap-vertices-and-center-in-own-primary','primary':o['primary'],'testedPoints':len(cap),'allEmbedded':all(q['inside']for q in m),'pointsWorld':[list(p)for p in cap],'measurements':m})
        r={'direction':direction,'nativeFrame':frame,'index':frame-1 if frame<=12 else None,'closureOnly':frame==13,'rootRotationZ':root.rotation_euler.z,'rootMatrix':matrix(root.matrix_world),'sourceSHA256':source_sha,'unadaptedEnvelope':bounds(pts),'objectWorldMatrices':{o.name:matrix(o.matrix_world)for o in meshes},'finiteContacts':contacts}
        if frame==1:first[direction]=pre
        if frame==13:
            r['closureMaxWorldDelta']=max((a-b).length for o in meshes for a,b in zip(first[direction][o.name],pre[o.name]));closure.append({'direction':direction,'maxWorldVertexDelta':r['closureMaxWorldDelta']})
        native=dest/('native-closure' if frame==13 else 'native')/'idle'/direction/(f'{frame-1:03d}.png');native.parent.mkdir(parents=True,exist_ok=True)
        assert not native.exists(),'Preserve prior captures'
        try:
            with frozen.capture_projection(col,'ordinary35'):
                post={o.name:worldverts(o)for o in meshes};maxlaw=0;maxeval=0
                dg=bpy.context.evaluated_depsgraph_get()
                for o in meshes:
                    ev=o.evaluated_get(dg);me=ev.to_mesh();evaluated=[ev.matrix_world@v.co for v in me.vertices]
                    for before,after,evv in zip(pre[o.name],post[o.name],evaluated):
                        expect=before.copy();blend=max(0,1-max(0,before.z)/.42)**2;expect.y*=1+(1/math.sin(math.radians(35))-1)*blend
                        maxlaw=max(maxlaw,(expect-after).length);maxeval=max(maxeval,(after-evv).length)
                    ev.to_mesh_clear()
                r['adapterEvidence']={'formulaMaximumWorldError':maxlaw,'postAdapterVsEvaluatedMaximumError':maxeval,'preBounds':bounds(pts),'postBounds':bounds([p for vs in post.values()for p in vs]),'order':['native action scene evaluation','proper root facing and dependency graph update','exact frozen adapter once per unique mesh data','mesh and view layer update','evaluated order/law measurement','native EEVEE render','finally restore original authoring mesh coords']}
                sc.render.filepath=str(native);bpy.ops.render.render(write_still=True,scene=sc.name)
        finally:
            r['restorationMaximumDataError']=max((v.co-original[o.name][i]).length for o in meshes for i,v in enumerate(o.data.vertices))
        r['nativePath']=str(native.relative_to(OBJ));r['nativeSHA256']=hashlib.sha256(native.read_bytes()).hexdigest();records.append(r)
        print('KELP_CAPTURE',direction,frame,'physical',r['unadaptedEnvelope'],'contacts',all(c['allEmbedded']for c in contacts),'law',maxlaw,'eval',maxeval,flush=True)
    if test and direction=='E':break

ground=[]
sc.frame_set(1);root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
for o in meshes:
    if o.get('role')!='grounded-cobalt':continue
    vs=worldverts(o)
    for poly in o.data.polygons:
        ps=[vs[i]for i in poly.vertices]
        if all(abs(v.z)<1e-6 for v in ps):ground.append({'owner':o.name,'polygonXY':[[v.x,v.y]for v in ps],'area':poly.area})
ledger={'asset':'decor-kelp','blender':bpy.app.version_string,'sourceSHA256':source_sha,'nativeCamera':camera,'renderRecipe':{'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples,'filter':sc.render.filter_size,'nativeResolution':[768,1920],'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'symmetricLights':[{'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size}for o in sc.objects if o.type=='LIGHT'],'groundShadowReceiver':False},'captureRecords':records,'groundSupport':{'actualFiniteBottomFaces':ground,'totalIndividualFaceArea':sum(p['area']for p in ground),'method':'Actual transformed finite bottom mesh faces atZ0; root/fork cap16 vertices plus center checked by odd ray intersections against actual closed finite mesh BVHs through every phase/facing. Overlapping stone face areas are not a union-area claim.'},'closure':closure,'noSharedMeshData':True,'noRuntimeModifiersOrShapeKeys':True,'savedSourceUnadapted':True,'lawMaximumError':max(r['adapterEvidence']['formulaMaximumWorldError']for r in records),'evaluationMaximumError':max(r['adapterEvidence']['postAdapterVsEvaluatedMaximumError']for r in records),'restorationMaximumError':max(r['restorationMaximumDataError']for r in records)}
(dest/'native-validation.json').write_text(json.dumps(ledger,indent=2)+'\n');(dest/'native-camera.json').write_text(json.dumps(camera,indent=2)+'\n')
print('KELP_CAPTURE_COMPLETE',str(dest))
