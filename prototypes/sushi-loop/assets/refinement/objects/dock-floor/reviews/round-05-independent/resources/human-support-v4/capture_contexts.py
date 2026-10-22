"""Render frozen shared-plan native cohorts in memory. Never save a blend."""
import runpy,sys,json,hashlib,math
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;G=runpy.run_path(str(P/'cohort_scene.py'));globals().update({k:v for k,v in G.items()if k not in ['__name__','__file__']});planfile=O/'shared-world-pose-plan.json';planSHA=sha(planfile);assert planSHA=='394b3dfe2b59c81e263cd0a4a5afc213f6e2346c23063a524dc047057ec84293';plan=json.loads(planfile.read_text());out=O/'native-human-context';out.mkdir(exist_ok=True)
frame=(896,896);anchor=(448,512);cam=sc.camera;sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*frame[0],(1-p.y)*frame[1]))
base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]-base.y)/dy;bpy.context.view_layer.update();origin=px((0,0,0));cal={'logicalFrame':frame,'nativeFrame':[q*2 for q in frame],'logicalAnchor':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin),'cameraMatrix':[list(r)for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]}
assert abs(cal['unitX'][0]-128)<1e-3 and abs(cal['unitDepth'][1]-128)<1e-3
initial={str(p.relative_to(B)):sha(p)for p in[F,E,A,ORIG,AH]};renders=[];sections=[]
def inside2(p,t):
 return all((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])>=-1e-9 for a,b in zip(t['xy'],t['xy'][1:]+t['xy'][:1]))
def value(t,p):return t['plane'][0]*p[0]+t['plane'][1]*p[1]+t['plane'][2]
for d in ['N','E','S','W']:
 for case in plan['cases']:
  x,y=case['sourceFacingXY'];z=case['solvedRootZ'];pose(x,y,z,d,case['actorClip'],case['nativeFrame']);support=walking_support();shoes=geometry(hc,True)
  for shoe in shoes:
   ts=projected([shoe]);lo,hi=shoe['bounds'];pts=[]
   # Actual vertical lower-envelope rays on three transverse sections, plus footprint grid.
   for i in range(1,12):
    for k in range(1,24):
     p=(lo[0]+(hi[0]-lo[0])*i/12,lo[1]+(hi[1]-lo[1])*k/24);st=[t for t in ts if inside2(p,t)]
     if not st:continue
     bottom=min(value(t,p)for t in st);su=[t for t in support if t['bbox'][0]-1e-9<=p[0]<=t['bbox'][2]+1e-9 and t['bbox'][1]-1e-9<=p[1]<=t['bbox'][3]+1e-9 and inside2(p,t)];top=max([0]+[value(t,p)for t in su]);pts.append({'xy':p,'lowestShoeZ':bottom,'upperSupportZ':top,'gap':bottom-top,'supportOwners':sorted(set(t['owner']for t in su if abs(value(t,p)-top)<1e-5))})
   sections.append({'direction':d,'case':case['id'],'shoe':shoe['name'],'rayCount':len(pts),'minimumGap':min(p['gap']for p in pts),'maximumGap':max(p['gap']for p in pts),'finiteContactRays':sum(abs(p['gap'])<1e-5 for p in pts),'rays':pts})
  for fixture in ['current-b176','approved-hut01']:
   snapshots['workshop-hut']['collection'].hide_render=fixture!='current-b176';snapshots['approved-workshop-hut']['collection'].hide_render=fixture!='approved-hut01'
   path=out/f'{fixture}-{d}-{case["id"]}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   bounds=[]
   for ob in geometry(hc):
    for v in ob['vertices']:bounds.append(list(px(v)))
   renders.append({'path':str(path.relative_to(B)),'sha256':sha(path),'direction':d,'fixture':fixture,'case':case,'actualWorldActorRoot':list(hr.location),'actualAuthoredRootScale':list(hr.scale),'actualSceneActorFrame':sc.frame_current,'companionPhase':'Independent exact evaluated dock-ready/uncover12; static hut selected by fixture','actorPixelBounds':[[min(p[i]for p in bounds)for i in[0,1]],[max(p[i]for p in bounds)for i in[0,1]]],'calibration':cal})
   print('NATIVE_CONTEXT',fixture,d,case['id'],flush=True)
report={'sharedPlan':{'path':str(planfile.relative_to(B)),'sha256':planSHA},'scope':'Common 55.00798degree environment native technical complete-body context. Primary actual consumer uses unchanged published35degree actor sprites; no pixel-parity claim between different camera projections. Nine discrete representative poses only, no continuous stair locomotion or door traversal.','sourceHashesBefore':initial,'sourceHashesAfter':{str(p.relative_to(B)):sha(p)for p in[F,E,A,ORIG,AH]},'noSourceBlendSaved':True,'snapshotNativeParity':snapshotAudit,'renders':renders,'renderSettings':{'engine':sc.render.engine,'samples':sc.eevee.taa_render_samples if hasattr(sc.eevee,'taa_render_samples')else 64,'filterSize':sc.render.filter_size,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'transparent':sc.render.film_transparent},'calibration':cal};assert report['sourceHashesBefore']==report['sourceHashesAfter'];(O/'native-human-context-validation.json').write_text(json.dumps(report,indent=2));(O/'physical-shoe-sections-rays.json').write_text(json.dumps({'sharedPlanSHA256':planSHA,'method':'Actual evaluated visible full-shoe lower envelope vs actual upward support upper envelope at 253 grid rays per shoe; supplements exact full triangle overlap law, not a replacement.','toleranceWorld':1e-5,'records':sections,'minimumGap':min(r['minimumGap']for r in sections)},indent=2));print('NATIVE_CAPTURE_DONE',len(renders),flush=True)
