import bpy,json,sys,hashlib,math,time
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;BASE=P.parent;OUT=BASE/'candidates/round-05';sys.path.insert(0,str(P));import native_actions_round05 as native
from audit_common_round05 import contacts,geometry
from semantic_round05 import digest,ROOT,PLANE,SCENE,COLL
baseline='--baseline' in sys.argv;preflight='--preflight' in sys.argv;sc=bpy.data.scenes[SCENE];bpy.context.window.scene=sc;coll=bpy.data.collections[COLL];root=bpy.data.objects[ROOT];arm=bpy.data.objects['chef_ellis__armature.001'];plane=bpy.data.objects[PLANE];asset={'collection':coll,'root':root,'armature':arm};rig=json.loads((P/'rig-round05.json').read_text());assert not coll.hide_render and not coll.hide_viewport
reference={} if baseline else {(r['clip'],r['direction'],r['index']):r for r in json.loads((OUT/'approved04-evaluated.json').read_text())}
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for device in prefs.devices:device.use=device.type=='METAL'
except Exception:pass
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def px(v):p=world_to_camera_view(sc,sc.camera,Vector(v));return [p.x*384,(1-p.y)*640]
def gsample(o,dg):
 e=o.evaluated_get(dg);m=e.to_mesh();p=[list(e.matrix_world@v.co) for v in m.vertices];n=[list(v.vector) for v in m.corner_normals];bounds=[[min(x[i] for x in p),max(x[i] for x in p)] for i in range(3)];data={'worldVerticesSHA256':digest(p),'cornerNormalsSHA256':digest(n),'topologySHA256':digest([len(m.vertices),[list(x.vertices) for x in m.edges],[(x.loop_start,x.loop_total,x.material_index,x.use_smooth) for x in m.polygons]]),'bounds':bounds,'counts':[len(m.vertices),len(m.edges),len(m.polygons)]};e.to_mesh_clear();return data
rows=[];ctrows=[];fail=[];start=time.time();maxerr=0
for c in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   native.apply_clip(asset,rig,c,i+1,d,sc);dg=bpy.context.evaluated_depsgraph_get();ct=contacts(coll,root,arm,dg);gs={o.name:gsample(o,dg) for o in coll.all_objects if o.type=='MESH' and '__image_plane' not in o.name and '__knife_' not in o.name};bounds=[[min(g['bounds'][a][0] for g in gs.values()),max(g['bounds'][a][1] for g in gs.values())] for a in range(3)];mat=Matrix(ct['props'][PLANE]['matrix']);width=(mat.to_3x3()@Vector((.28,0,0))).length;height=(mat.to_3x3()@Vector((0,max(v.co.y for v in plane.data.vertices),0))).length
   row={'clip':c,'direction':d,'index':i,'rootMatrix':ct['rootMatrix'],'rootRotationDegrees':ct['rootRotationDegrees'],'rootPixel':px((0,0,0)),'bodyGeometry':gs,'physicalBodyBounds':bounds,'contacts':ct,'quadWidthWorld':width,'quadHeightWorld':height,'quadLowerCenterWorld':list(mat.translation),'quadLowerCenterPixel':px(mat.translation)}
   if not baseline:
    ref=reference[(c,d,i)];assert gs==ref['bodyGeometry'],(c,d,i,'body-evaluated-data delta');assert ct==ref['contacts'],(c,d,i,'contact delta');assert row['rootMatrix']==ref['rootMatrix'];assert abs(width-.35)<1e-6;assert abs(height-.35*505/731)<1e-6;assert row['quadLowerCenterWorld']==ref['quadLowerCenterWorld'];row['approved04BodyParity']=True
   path=OUT/'frames'/(c+'-'+d)/(f'{i:03d}.png')
   if not baseline and not preflight:
    path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);row.update(path=str(path.relative_to(BASE)),sha256=sha(path))
   rows.append(row);ctrows.append({'clip':c,'direction':d,'index':i,**ct});(OUT/('baseline-progress.json' if baseline else 'progress.json')).write_text(json.dumps({'done':len(rows),'total':192,'current':[c,d,i],'seconds':time.time()-start}));print('FRAME',len(rows),c,d,i,'baseline' if baseline else 'candidate',flush=True)
if baseline:(OUT/'approved04-evaluated.json').write_text(json.dumps(rows,separators=(',',':')))
elif preflight:
 (OUT/'preflight-evaluated.json').write_text(json.dumps(rows,separators=(',',':')))
 for c,f in [('hold',6),('load',6),('load',12)]:
  for d in ['N','E','S','W']:
   native.apply_clip(asset,rig,c,f,d,sc);path=OUT/'representatives'/(c+'-'+d+'-'+str(f)+'.png');path.parent.mkdir(exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
else:
 (OUT/'native-frames.json').write_text(json.dumps(rows,separators=(',',':')));(OUT/'evaluated-contacts.json').write_text(json.dumps(ctrows,separators=(',',':')))
 bounds=[[min(r['physicalBodyBounds'][a][0] for r in rows),max(r['physicalBodyBounds'][a][1] for r in rows)] for a in range(3)];assert abs(bounds[2][1]-1.3984133005142212)<1e-7
 val={'asset':'chef-ellis','round':5,'ok':True,'activeBrief':'brief-v2-food.json','projectSHA256':sha(P/'round-05.blend'),'renderCount':192,'baseline':'approved04-evaluated.json','nativeRecords':'native-frames.json','approved04EvaluatedBodyGeometryExactAcrossAll192':True,'approved04FootPalmBoneKnifeFoodRootTransformsVisibilityExact':True,'physicalBodyBoundsAll192':bounds,'nominalRestHeight':1.3968749046325684,'authoredMotionMaximumZ':bounds[2][1],'quadWorldWidth':.35,'quadWorldHeight':.35*505/731,'lowerEdgeAndCameraRayOffsetAndYawUnchanged':True,'semanticAudit':'semantic-parity.json','representation':{'body':'approved04 native3D','knife':'approved04 native3D','salmon':'canonical approved packed2D'},'status':'Native evidence complete; independent visual verdict pending'};(OUT/'validation.json').write_text(json.dumps(val,indent=2))
print('EVALUATION_DONE',baseline,preflight,len(rows),flush=True)
