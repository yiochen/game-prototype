import bpy,sys,json,hashlib,math,os
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE/'source'))
import round01_native as native
OUT=BASE/'candidates/round-01';SC=bpy.context.scene
SHA=hashlib.sha256((BASE/'source/round-01.blend').read_bytes()).hexdigest()
def plain(x):return [list(r) for r in x]
def bbox(pts):return {'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]}
def measure(clip,d,frame):
    rig,root,motion=native.activate(clip,d,frame);dg=bpy.context.evaluated_depsgraph_get();dg.update();active=[];pts=[];contact=0;contacts=[];attach=0
    rootm=root.evaluated_get(dg).matrix_world.copy();mm=motion.evaluated_get(dg).matrix_world.copy()
    for obj in SC.objects:
        if obj.type!='MESH' or obj.hide_render:continue
        eo=obj.evaluated_get(dg);mesh=eo.to_mesh();m=eo.matrix_world;vp=[m@v.co for v in mesh.vertices];pts+=vp
        # Native attachment invariant: each mesh remains a rigid child of one coherent assembly.
        local=mm.inverted()@m;delta=max(abs(local[i][j]-obj.matrix_local[i][j]) for i in range(4) for j in range(4));attach=max(attach,delta)
        area=0
        for poly in mesh.polygons:
            if max(abs(vp[i].z) for i in poly.vertices)<1e-5:area+=poly.area*abs(motion.scale.x*motion.scale.y)
        contact+=area
        if area:contacts.append({'mesh':obj.name,'area':area})
        active.append({'name':obj.name,'variantIndex':obj.get('variantIndex'),'parent':obj.parent.name,'worldMatrix':plain(m),'localMatrix':plain(local),'evaluatedBounds':bbox(vp),'vertices':len(mesh.vertices),'polygons':len(mesh.polygons)})
        eo.to_mesh_clear()
    bb=bbox(pts);cam=native.camera_record();rootpx=cam['calibration']['root']
    projected=[]
    from bpy_extras.object_utils import world_to_camera_view
    for p in pts:
        v=world_to_camera_view(SC,SC.camera,p);projected.append([v.x*768,(1-v.y)*1408])
    pb={'min':[min(p[i] for p in projected) for i in range(2)],'max':[max(p[i] for p in projected) for i in range(2)]}
    isloop=not clip.endswith('collect');zmax=.7 if isloop else 1.3
    assert all(bb['min'][i]>=-.45001 and bb['max'][i]<=.45001 for i in [0,1]),(clip,d,frame,bb)
    assert bb['min'][2]>=-1e-5 and bb['max'][2]<=zmax+1e-5,(clip,d,frame,bb)
    assert all(pb['min'][i]>1 and pb['max'][i]<[767,1407][i] for i in [0,1]),pb
    if isloop:assert contact>1e-4,(clip,d,frame,contact)
    assert attach<1e-5,attach
    assert len(set(o['variantIndex'] for o in active))==1
    return {'clip':clip,'direction':d,'sourceFrame':frame,'index':frame-1,'sourceSHA256':SHA,'rootRotationZ':float(root.rotation_euler.z),'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':plain(rootm),'motionMatrix':plain(mm),'camera':cam,'bounds':bb,'projectedGeometryBounds':pb,'finiteGroundArea':contact,'groundSections':contacts,'attachmentMaxResidual':attach,'activeMeshes':active}
def render(rec,hold=False):
    folder=OUT/('native-holds' if hold else 'native')/rec['clip']/rec['direction'];folder.mkdir(parents=True,exist_ok=True);p=folder/(f'{rec["index"]:03}.png');SC.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    rec['path']=p.relative_to(BASE).as_posix();rec['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    return rec
mode=os.environ.get('SALVAGE_CAPTURE_MODE','all')
records=[]
for clip in native.CLIPS:
    for d in ['N','E','S','W']:
        frames=[1] if mode=='stills' else range(1,13)
        for frame in frames:
            rec=measure(clip,d,frame)
            if mode=='stills':
                folder=OUT/'diagnostic-stills';folder.mkdir(exist_ok=True);SC.render.filepath=str(folder/f'{clip}-{d}.png');bpy.ops.render.render(write_still=True)
            else:render(rec)
            records.append(rec)
            print('ROUND01_CAPTURE',len(records),clip,d,frame,flush=True)
if mode=='all':
    (OUT/'native-validation.json').write_text(json.dumps({'asset':'salvage-metal','sourceSHA256':SHA,'blenderVersion':bpy.app.version_string,'captureRecords':records},indent=2)+'\n')
    holds=[]
    for clip in native.CLIPS:
        for d in ['N','E','S','W']:
            for frame in ([13] if not clip.endswith('collect') else [13,24]):holds.append(render(measure(clip,d,frame),True))
    (OUT/'closure-hold-records.json').write_text(json.dumps({'captureRecords':holds},indent=2)+'\n')
    (OUT/'native-camera.json').write_text(json.dumps(native.camera_record(),indent=2)+'\n')
print('ROUND01_CAPTURE_FINISHED',mode,len(records),flush=True)
