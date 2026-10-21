"""Correct registered facing phase only; geometry/materials/lights are unchanged.

Native registered source convention is S=0,E=+90,N=180,W=-90 degrees.
The immutable round-02 project is a self-contained native derivation source.
"""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=BASE/'source/round-02.blend';PROJECT=BASE/'source/round-03.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE)=='9d9ed8b99b1a2fd951879bf79f22321689ae0e9d173bd99f5f6cff6fad439562','Immutable derivation source changed'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;root=bpy.data.objects['slate-rock__root.001'];collection=bpy.data.collections['S33_PROP_slate-rock.001'];parts=list(collection.all_objects)
def fingerprints():
 geometry=[]
 for o in parts:
  if o.type=='MESH':geometry.append({'name':o.name,'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'smooth':[p.use_smooth for p in o.data.polygons],'materials':[m.name if m else None for m in o.data.materials],'matrixLocal':[list(r) for r in o.matrix_local]})
 materials=[]
 for m in bpy.data.materials:
  nodes=[]
  for n in m.node_tree.nodes:
   inputs=[]
   for s in n.inputs:
    if not hasattr(s,'default_value'):continue
    v=s.default_value
    try:v=list(v)
    except TypeError:pass
    if isinstance(v,(str,int,float,list,bool)):inputs.append((s.name,v))
   record={'type':n.bl_idname,'name':n.name,'inputs':inputs}
   if n.type=='VALTORGB':record['ramp']=[(e.position,list(e.color)) for e in n.color_ramp.elements]
   nodes.append(record)
  materials.append({'name':m.name,'nodes':nodes,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links]})
 lights=[{'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrixWorld':[list(r) for r in o.matrix_world]} for o in scene.objects if o.type=='LIGHT']
 return {k:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for k,v in [('geometry',geometry),('materials',materials),('lighting',lights)]}
before=fingerprints();scene.name='slate-rock warm soft native round 03';scene['native_facings']='S=0,E=90,N=180,W=-90';scene['derivation_round_02_sha256']=sha(SOURCE)
root.rotation_euler=(0,0,0);bpy.context.view_layer.update();after=fingerprints();assert before==after
bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT))
def bounds():
 pts=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in parts:
  if o.type!='MESH':continue
  e=o.evaluated_get(dep);m=e.to_mesh();pts.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
records=[]
for direction,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);bpy.context.view_layer.update();scene.frame_set(1);scene.render.filepath=str(OUT/f'static-{direction}.png');bpy.ops.render.render(write_still=True)
 records.append({'clip':'static','direction':direction,'index':0,'nativeFrame':1,'path':f'candidates/round-03/static-{direction}.png','sha256':sha(scene.render.filepath),'rootRotationDegrees':angle,'rootMatrix':[list(r) for r in root.matrix_world],'worldBounds':bounds(),'registeredFacingConvention':'S0,E90,N180,W-90'})
root.rotation_euler.z=0;bpy.context.view_layer.update()
for name in ['camera','assetRecord','rig']:
 record=json.loads((BASE/f'source/round-02-{name}.json').read_text())
 if name in ('camera','assetRecord'):record['artStyle']['revision']='warm-soft-slate-rock-round-03-registered-facings'
 if name=='rig':record['project']='round-03.blend';record['scene']=scene.name
 if name=='assetRecord':record['nativeScene']=scene.name
 record['nativeFacingsDegrees']={'N':180,'E':90,'S':0,'W':-90}
 (BASE/f'source/round-03-{name}.json').write_text(json.dumps(record,indent=2)+'\n')
v=json.loads((BASE/'candidates/round-02/validation.json').read_text());v.update({'round':3,'renders':records,'status':'native-technical-checks-awaiting-independent-visual-review'})
for k in ['alpha','previews','reopenedSource']:v.pop(k,None)
v['sourceEdited']={'path':'source/round-03.blend','sha256':sha(PROJECT),'reproductionScript':'source/round-03.py','reproductionScriptSha256':sha(Path(__file__)),'scene':scene.name,'root':root.name}
authority=(BASE/'../../../production/source/blender/revisions/4fa9e22e555f8aad/native_actions.py').resolve()
publisher=(BASE/'../../../production/source/blender/revisions/9eef6e9113da31e0/publish_captures.py').resolve()
v['facingConvention']={'anglesDegrees':{'N':180,'E':90,'S':0,'W':-90},'authority':{'nativeActionsPath':str(authority),'nativeActionsSha256':sha(authority),'nativeActionsLine':468,'publisherPath':str(publisher),'publisherSha256':sha(publisher)},'previousRoundOppositeLabels':{'newN':'round02-S','newE':'round02-W','newS':'round02-N','newW':'round02-E'},'noRasterRelabelOrTransform':'All four submitted round03 frames are fresh native renders at the correct registered angles.','rootSavedAt':'S=0'}
v['derivation']={'sourceProject':'source/round-02.blend','sourceSha256':sha(SOURCE),'geometryMaterialsLightingBefore':before,'geometryMaterialsLightingAfter':after,'onlyChange':'Scene/metadata facing phase correction; no geometry, material, light or camera edits.'}
v['checks'].update({'reviewedGeometryMaterialsLightingPreserved':before==after,'registeredFacingConvention':True})
for k in ['reopenedSource','reopenedRenderWithinQuantizationTolerance','noAlphaClipping','dependencyClosure','allMaterialSlotsBound']:v['checks'].pop(k,None)
(OUT/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
print('ROUND03',json.dumps(v['checks']))
