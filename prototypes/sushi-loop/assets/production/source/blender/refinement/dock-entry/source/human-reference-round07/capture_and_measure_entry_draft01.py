"""Entry evidence-only replay of adopted discrete plan. No native project/source writes.
Run blender -b -t6 --python source/human-reference-round07/capture_and_measure_entry.py.
Exact copied plan inputs and sealed Entry06 stay immutable. No continuous-motion claim.
"""
import runpy,sys,json,math,hashlib,gzip,time
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from collision_entry import pair,tree
G=runpy.run_path(str(P/'cohort_scene_entry.py'));globals().update({k:v for k,v in G.items() if not k.startswith('__')});pose=G['pose'];B=G['B'];O=G['O'];R=G['R'];sc=G['sc'];cam=sc.camera
PLAN=B/'inputs/shared-world-pose-v1/plan.json';plan=json.loads(PLAN.read_text());assert sha(PLAN)=='394b3dfe2b59c81e263cd0a4a5afc213f6e2346c23063a524dc047057ec84293';brief=B/'brief-v4-human-reference.json';assert sha(brief)=='b40734190a858a46947d6d7e8b7c47338acee0713830c8665268a8e65df4b590'
adoption=json.loads((B/'inputs/shared-world-pose-v1/root-adoption.json').read_text());frozenInputs={str(p):sha(p)for p in (B/'inputs/shared-world-pose-v1').rglob('*')if p.is_file()};assert all(sha(B/'inputs/shared-world-pose-v1'/name)==v['sha256']for name,v in adoption['files'].items())
oldDelivery=json.loads((B/'delivery-v3.json').read_text());oldHashes={r['path']:r['sha256']for r in oldDelivery['resources'].values()};assert all(sha(B/p)==v for p,v in oldHashes.items())
FAM=O/'native-human';FAM.mkdir(exist_ok=True);(O/'measurements').mkdir(exist_ok=True)
assert sc.render.engine=='BLENDER_EEVEE'and sc.render.filter_size==.5 and sc.eevee.taa_render_samples==64

def plain(v):
 if v is None or isinstance(v,(bool,int,float,str)):return v
 if isinstance(v,bpy.types.ID):return {'IDType':type(v).__name__,'name':v.name}
 try:return [plain(q)for q in v]
 except TypeError:return str(v)
def material_state(mat):
 st={'diffuseColor':list(mat.diffuse_color),'roughness':mat.roughness,'metallic':mat.metallic,'useNodes':mat.use_nodes}
 if mat.use_nodes:
  st['nodes']=[{'name':n.name,'type':n.bl_idname,'inputs':{s.name:plain(s.default_value)for s in n.inputs if hasattr(s,'default_value')},'operation':getattr(n,'operation',None),'image':getattr(getattr(n,'image',None),'name',None)}for n in mat.node_tree.nodes];st['links']=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier)for l in mat.node_tree.links]
 return st
# Actual copied material values versus exact native frame12 source, then per-pose invariance.
materialAudit=[];materialBaseline={};snapshotBaseline={}
for group in snapshotAudit:
 for row in group['objects']:
  src=bpy.data.objects[row['sourceObject']];cp=bpy.data.objects[row['snapshotObject']];before=[material_state(m)for m in src.data.materials if m];after=[material_state(m)for m in cp.data.materials if m];assert before==after,(src.name,'material mismatch at frame12')
  key=cp.name;state=hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest();materialBaseline[key]=state;snapshotBaseline[key]=[list(cp.matrix_world@v.co)for v in cp.data.vertices];materialAudit.append({'sourceObject':src.name,'snapshotObject':key,'nativeFrame':group['nativeFrame'],'clip':group['nativeClip'],'sourceAndSnapshotChannelStatesExact':True,'materialStateSHA256':state,'sourceStates':before,'snapshotStates':after,'allCopiedAnimationsDetached':all(not m.animation_data and(not m.use_nodes or not m.node_tree.animation_data)for m in cp.data.materials if m)})

def snapshot_parity(d):
 a={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d];rot=Matrix.Rotation(a,4,'Z');rows=[]
 for name,vs in snapshotBaseline.items():
  cp=bpy.data.objects[name];actual=[cp.matrix_world@v.co for v in cp.data.vertices];expected=[rot@Vector(v)for v in vs];err=max((x-y).length for x,y in zip(actual,expected));state=hashlib.sha256(json.dumps([material_state(m)for m in cp.data.materials if m],sort_keys=True).encode()).hexdigest();assert state==materialBaseline[name];assert err<1e-5
  rows.append({'snapshotObject':name,'maximumWorldVertexErrorAgainstRigidRotatedFrame12':err,'materialStateUnchanged':True,'actualMatrixWorld':[list(r)for r in cp.matrix_world]})
 return rows

def setup():
 frame=(768,768);anchor=(384,440);sc.render.resolution_x=1536;sc.render.resolution_y=1536;cam.data.ortho_scale=6.;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*768,(1-p.y)*768))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]-base.y)/dy;bpy.context.view_layer.update();base=px((0,0,0))
 return {'logicalFrame':frame,'nativeFrame':[1536,1536],'logicalRoot':list(base),'unitX':list(px((1,0,0))-base),'unitDepth':list(px((0,-1,0))-base),'unitHeight':list(px((0,0,1))-base),'cameraWorldMatrix':[list(r)for r in cam.matrix_world],'projectionMatrix':[list(r)for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=1536,y=1536,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}
records=[];renders=[];t0=time.time()
for d in ['N','E','S','W']:
 for index,c in enumerate(plan['cases']):
  cid=c['id'];x,y=c['sourceFacingXY'];z=c['solvedRootZ'];clip=c['actorClip'];frame=c['nativeFrame']
  pose(x,y,0,d,clip,frame);full=solve(projected(geometry(hc,True)),walking_support());drift=full['solvedRootZ']-z;assert abs(drift)<1e-5
  pose(x,y,z,d,clip,frame);residual=solve(projected(geometry(hc,True)),walking_support())['solvedRootZ'];assert residual<1e-5;parity=snapshot_parity(d);human=geometry(hc);blocks=[q for q in geometry(ec)if'continuous_loadbearing'not in q['name']]
  for q in snapshots.values():blocks+=geometry(q['collection'])
  bt={q['name']:tree(q)for q in blocks};checks=[];bad=[]
  for ob in human:
   tt=tree(ob)
   for block in blocks:
    check=pair(ob,block,tt,bt[block['name']]);checks.append(check)
    if check['actualTriangleIntersectionPairs']or check['containedActorVerticesBeyondTolerance']or check['containedObstacleVerticesBeyondTolerance']:bad.append(check)
  loadbearing=geometry(fc)+[q for q in geometry(ec)if'continuous_loadbearing'in q['name']];supportChecks=[]
  for ob in human:
   if any(k in ob['name'].lower()for k in['shoe','sole','foot']):continue
   tt=tree(ob)
   for block in loadbearing:
    check=pair(ob,block,tt,tree(block));supportChecks.append(check)
    if check['actualTriangleIntersectionPairs']or check['containedActorVerticesBeyondTolerance']or check['containedObstacleVerticesBeyondTolerance']:bad.append(check)
  rec={'id':cid,'direction':d,'caseIndex':index,'sourceFacingXY':[x,y],'frozenRootZ':z,'worldRoot':list(hr.location),'actorClip':clip,'sourceNativeFrame':frame,'publishedClipIndex':c['publishedClipIndex'],'actualAuthoredRootScale':list(hr.scale),'actualRootMatrix':[list(r)for r in hr.matrix_world],'fullSupport':full,'actualPlacedFullShoeRequiredLiftResidual':residual,'directionSolveDeltaFromFrozenZ':drift,'bodyObstacleChecks':checks,'nonShoeBodyLoadbearingChecks':supportChecks,'badMeshPairs':bad,'snapshotParity':parity,'visibleShoeGeometry':[{'name':q['name'],'matrix':q['matrix'],'verticesWorld':[list(v)for v in q['vertices']],'triangles':q['triangles']}for q in geometry(hc,True)]}
  records.append(rec);assert not bad,(d,cid,bad[:2]);assert all(q['contactArea']>0 and q['fractionOfFlatSole']>.5 for q in full['perShoe'])
  for fixture in ['current-b176-hut','approved-hut01-additional']:
   snapshots['workshop-hut']['collection'].hide_render=fixture!='current-b176-hut';snapshots['approved-workshop-hut']['collection'].hide_render=fixture=='current-b176-hut';cal=setup();output=FAM/f'{d}-{index:02d}-{cid}-{fixture}.png';assert not output.exists();sc.render.filepath=str(output);bpy.ops.render.render(write_still=True);renders.append({'path':str(output.relative_to(B)),'sha256':sha(output),'direction':d,'caseIndex':index,'case':cid,'fixture':fixture,'clip':clip,'sourceNativeFrame':frame,'publishedClipIndex':c['publishedClipIndex'],'rootRotationZ':hr.rotation_euler.z,'actualRootMatrix':[list(r)for r in hr.matrix_world],'worldRoot':list(hr.location),'scale':list(hr.scale),'companionCohort':'evaluated frozen frame12; independent of actor global frame','calibration':cal})
  print('ENTRY_ROUND07_CASE',d,cid,clip,frame,'contact',[(q['contactArea'],q['fractionOfFlatSole'])for q in full['perShoe']],'residual',residual,'bad',len(bad),'elapsed',round(time.time()-t0,1),flush=True)
raw={'status':'technical evidence only; original independent judge review pending','planSHA256':sha(PLAN),'sourceHashes':sourceHashes,'snapshotParityAtSourceFrame12':snapshotAudit,'materialCohortParity':materialAudit,'cases':plan['cases'],'records':records,'renders':renders,'maximumUnintendedPairs':max(len(r['badMeshPairs'])for r in records),'scope':plan['scope']}
rawpath=O/'measurements/full-human-support-clearance.json.gz';assert not rawpath.exists()
with gzip.GzipFile(filename=str(rawpath),mode='wb',mtime=0)as f:f.write(json.dumps(raw,separators=(',',':')).encode())
compact=[{k:r[k]for k in ['id','direction','caseIndex','sourceFacingXY','frozenRootZ','worldRoot','actorClip','sourceNativeFrame','publishedClipIndex','actualAuthoredRootScale','actualRootMatrix','actualPlacedFullShoeRequiredLiftResidual','directionSolveDeltaFromFrozenZ']}|{'fullSupport':r['fullSupport'],'badMeshPairs':r['badMeshPairs'],'bodyMeshPairsChecked':len(r['bodyObstacleChecks']),'nonShoeBodyLoadbearingPairsChecked':len(r['nonShoeBodyLoadbearingChecks']),'actualTriangleIntersectionPairs':sum(q['actualTriangleIntersectionPairs']for q in r['bodyObstacleChecks']+r['nonShoeBodyLoadbearingChecks']),'containedActorVerticesBeyondTolerance':sum(q['containedActorVerticesBeyondTolerance']for q in r['bodyObstacleChecks']+r['nonShoeBodyLoadbearingChecks']),'containedObstacleVerticesBeyondTolerance':sum(q['containedObstacleVerticesBeyondTolerance']for q in r['bodyObstacleChecks']+r['nonShoeBodyLoadbearingChecks'])}for r in records]
summary={'asset':'dock-entry','round':7,'frozenBriefSHA256':sha(brief),'plan':'inputs/shared-world-pose-v1/plan.json','planSHA256':sha(PLAN),'sourceHashes':sourceHashes,'sourceProject':'source/round-06.blend','sourceProjectSHA256':sha(B/'source/round-06.blend'),'sourceArtUnchanged':True,'evidenceScope':plan['scope'],'nativeEngine':sc.render.engine,'nativeFilterSize':sc.render.filter_size,'nativeSamples':sc.eevee.taa_render_samples,'actorAuthoredScale':[1.25]*3,'sourceCompanionClipFrames':{'submarine-yellow':['dock-ready',12,11],'dock-cover':['uncover',12,11]},'sourceCompanionCohortIsolation':'Exact frame12 evaluated native meshes/matrices/material channels frozen in memory; copied material animations cleared. All36 actor samples verify invariant material hash and rigid-rotated native vertices. Original sources/actions remain unchanged.','snapshotParity':snapshotAudit,'materialCohortParity':materialAudit,'sourceFrameMapping':plan['nativeCohorts']['actor']['mapping'],'projectionScope':plan['projection']['meaning'],'authoredActorElevationDegrees':35,'derivedNativeElevationDegrees':55.00797980144134,'cases':plan['cases'],'records':compact,'renders':renders,'rawMeasurement':{'path':str(rawpath.relative_to(B)),'sha256':sha(rawpath),'bytes':rawpath.stat().st_size},'summary':{'measuredRecords':len(records),'nativeContextImages':len(renders),'minimumFlatSoleContactFraction':min(s['fractionOfFlatSole']for r in records for s in r['fullSupport']['perShoe']),'minimumShoeContactArea':min(s['contactArea']for r in records for s in r['fullSupport']['perShoe']),'maxPlacedShoeLiftResidual':max(r['actualPlacedFullShoeRequiredLiftResidual']for r in records),'maxFrozenZSolveDrift':max(abs(r['directionSolveDeltaFromFrozenZ'])for r in records),'maximumUnintendedPairs':max(len(r['badMeshPairs'])for r in records)},'originalInputBytesUnchanged':all(sha(Path(p))==v for p,v in frozenInputs.items()),'all1166PreviousResourcesUnchanged':all(sha(B/p)==v for p,v in oldHashes.items()),'reviewPolicy':'Not approval; no source/production/brief/review writes. Original judge independently evaluates all physical and visual requirements.'}
assert summary['originalInputBytesUnchanged']and summary['all1166PreviousResourcesUnchanged'];(O/'native-human-reference-validation.json').write_text(json.dumps(summary,indent=2));print('ENTRY_ROUND07_NATIVE_READY',summary['summary'],flush=True)
