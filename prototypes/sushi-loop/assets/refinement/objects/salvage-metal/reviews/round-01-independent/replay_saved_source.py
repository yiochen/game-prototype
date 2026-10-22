import sys,json,hashlib,math,importlib.util
sys.dont_write_bytecode=True
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent;OBJ=P.parent.parent;C=OBJ/'candidates/round-01';sc=bpy.context.scene
rig=json.loads(sc['salvage_round01_rig']);roots=rig['variantRoots'];meshes=[o for o in sc.objects if o.type=='MESH'];actions={a.name:a for a in bpy.data.actions}
def plain(x):return [list(r) for r in x]
def bounds(pts):return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
def activate(clip,direction,frame):
 entry=rig['clips'][clip];vi=entry['variantIndex']
 for idx,n in enumerate(roots):
  root=bpy.data.objects[n];root.hide_render=False;root.hide_viewport=False;root.hide_set(False);root.rotation_euler=(0,0,math.radians({'S':0,'E':90,'N':180,'W':-90}[direction]));assembly=next(o for o in root.children if o.type=='EMPTY');assembly.animation_data_clear();assembly.location=(0,0,0);assembly.scale=(1,1,1);assembly.rotation_euler=(0,0,0);assembly.hide_set(False)
 for o in meshes:o.hide_render=o.get('variantIndex')!=vi;o.hide_viewport=False;o.hide_set(False)
 for target in entry['actions']:
  owner=bpy.data.objects[target['ownerName']];owner.animation_data_create();owner.animation_data.action=actions[target['action']];owner.animation_data.action_slot=next(s for s in owner.animation_data.action.slots if s.identifier==target['slotIdentifier'])
 sc.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update();return entry,dg
records=[];samples=[]
for clip,recipe in rig['clips'].items():
 for d in ['N','E','S','W']:
  for f in list(range(1,13))+([13] if recipe['loop'] else [13,24]):
   entry,dg=activate(clip,d,f);vi=entry['variantIndex'];root=bpy.data.objects[entry['variantRoot']];owner=bpy.data.objects[entry['actions'][0]['ownerName']];rootE=root.evaluated_get(dg);motion=owner.evaluated_get(dg);raw=[];ev=[];active=[];area=0;attach=0
   for o in meshes:
    if o.hide_render:continue
    eo=o.evaluated_get(dg);me=eo.to_mesh();vp=[eo.matrix_world@v.co for v in me.vertices];rp=[o.matrix_world@v.co for v in o.data.vertices];raw+=rp;ev+=vp
    local=motion.matrix_world.inverted()@eo.matrix_world;attach=max(attach,max(abs(local[i][j]-o.matrix_local[i][j]) for i in range(4) for j in range(4)))
    for poly in me.polygons:
     if all(abs(vp[i].z)<1e-5 for i in poly.vertices):area+=poly.area*motion.scale.x*motion.scale.y
    active.append({'name':o.name,'variantIndex':o['variantIndex'],'parent':o.parent.name,'localMatrix':plain(local),'worldMatrix':plain(eo.matrix_world),'rawBounds':bounds(rp),'evaluatedBounds':bounds(vp)})
    eo.to_mesh_clear()
   cam=sc.camera;v=world_to_camera_view(sc,cam,Vector((0,0,0)));rootpx=[v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y];r={'clip':clip,'direction':d,'nativeFrame':f,'rootRotationZ':rootE.rotation_euler.z,'rootMatrix':plain(rootE.matrix_world),'motionMatrix':plain(motion.matrix_world),'rawBounds':bounds(raw),'evaluatedBounds':bounds(ev),'finiteGroundArea':area,'attachmentResidual':attach,'activeMeshes':active,'rootPixels':rootpx};records.append(r)
   if (f==1 and clip in ['shimmer','b-shimmer','c-shimmer']) or (d=='S' and f in [7,12,13,24] and clip.endswith('collect')):
    rel=Path('native-replay')/clip/d/f'{f-1:03d}.png';out=P/rel;out.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(out);bpy.ops.render.render(write_still=True);samples.append({'clip':clip,'direction':d,'nativeFrame':f,'path':str(rel),'candidate':str((C/('native' if f<=12 else 'native-holds')/clip/d/f'{f-1:03d}.png').relative_to(OBJ))})
(P/'native-replay.json').write_text(json.dumps({'source':str(Path(bpy.data.filepath)),'sourceSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'blenderVersion':bpy.app.version_string,'camera':{'worldMatrix':plain(sc.camera.matrix_world),'orthoScale':sc.camera.data.ortho_scale,'frame':[sc.render.resolution_x,sc.render.resolution_y],'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'objects':[{'name':o.name,'parent':o.parent.name if o.parent else None,'type':o.type,'vertexCount':len(o.data.vertices) if o.type=='MESH' else None} for o in sc.objects],'externalImages':[i.filepath for i in bpy.data.images if i.source=='FILE'],'linkedLibraries':[l.filepath for l in bpy.data.libraries],'records':records,'renderedSamples':samples},indent=2)+'\n');print('INDEPENDENT_SAVED_SOURCE_REPLAY',len(records),len(samples),flush=True)
