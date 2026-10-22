"""Sampling-only native revision: persist filter.5 in NEW standalone source.
Run blender -b -t6 --python source/build-round-06.py
Retains exact original05 geometry/material/light/camera/root/settings except filter.
"""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-06';R=O/'native-records';R.mkdir(parents=True,exist_ok=True);old=B/'source/round-05.blend';new=B/'source/round-06.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();original_sha=sha(old);brief=B/'brief-v3-native-sampling.json';assert sha(brief)=='62ab23c69c337f5f84a42349f40562cce3330413fdbce4d8928c2093730ee713'
bpy.ops.wm.open_mainfile(filepath=str(old))
def val(v):
 if isinstance(v,(bool,int,float,str)) or v is None:return v
 try:return [val(x) for x in v]
 except:return str(v)
def nodes(tree):
 if not tree:return None
 out=[]
 for n in tree.nodes:
  d={'name':n.name,'type':n.bl_idname,'inputs':{s.identifier:val(s.default_value) for s in n.inputs if hasattr(s,'default_value')}}
  for k in ['operation','blend_type','noise_dimensions','normalize','interpolation','extension']:
   if hasattr(n,k):d[k]=val(getattr(n,k))
  if hasattr(n,'color_ramp'):d['colorRamp']=[{'position':e.position,'color':val(e.color)} for e in n.color_ramp.elements]
  out.append(d)
 return {'nodes':out,'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links]}
def fingerprint():
 bpy.context.view_layer.update();s=bpy.context.scene;objects=[]
 for o in s.objects:
  d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':val(o.matrix_world),'location':val(o.location),'rotation':val(o.rotation_euler),'scale':val(o.scale),'hideRender':o.hide_render,'custom':{k:val(v) for k,v in o.items()}}
  if o.type=='MESH':d['mesh']={'vertices':[val(v.co) for v in o.data.vertices],'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in o.data.polygons],'materials':[m.name for m in o.data.materials],'modifiers':[(m.name,m.type) for m in o.modifiers]}
  elif o.type=='CAMERA':d['camera']={k:val(getattr(o.data,k)) for k in ['type','ortho_scale','shift_x','shift_y','sensor_fit','clip_start','clip_end']}
  elif o.type=='LIGHT':d['light']={k:val(getattr(o.data,k)) for k in ['type','energy','color','shape','size','use_shadow']}
  objects.append(d)
 return {'objects':objects,'materials':{m.name:nodes(m.node_tree) for m in bpy.data.materials},'world':nodes(s.world.node_tree),'render':{k:val(getattr(s.render,k)) for k in ['engine','resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y','film_transparent','fps']},'view':{k:val(getattr(s.view_settings,k)) for k in ['view_transform','look','exposure','gamma']},'samples':s.eevee.taa_render_samples,'taaReprojection':s.eevee.use_taa_reprojection,'timeline':[s.frame_start,s.frame_end,s.frame_current]}
base=fingerprint();base_json=json.dumps(base,sort_keys=True);old_filter=bpy.context.scene.render.filter_size;assert old_filter==1.5;bpy.context.scene.render.filter_size=.5
assert not new.exists(),'Never overwrite a native saved round';bpy.ops.wm.save_as_mainfile(filepath=str(new));saved_sha=sha(new);bpy.ops.wm.open_mainfile(filepath=str(new));sc=bpy.context.scene;after=fingerprint();assert base_json==json.dumps(after,sort_keys=True),'Unexpected nonfilter native change';assert sc.render.filter_size==.5;assert sc.eevee.taa_render_samples==64;assert sha(old)==original_sha
record={'asset':'dock-entry','sourceOld':{'path':'source/round-05.blend','sha256':original_sha,'filter_size':old_filter},'sourceNew':{'path':'source/round-06.blend','sha256':saved_sha,'filter_size':sc.render.filter_size},'frozenBrief':'brief-v3-native-sampling.json','frozenBriefSHA256':sha(brief),'actualAfterReopen':{'engine':sc.render.engine,'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples,'taaReprojection':sc.eevee.use_taa_reprojection,'UIFPS':sc.render.fps,'UIRange':[sc.frame_start,sc.frame_end],'actionCount':len(bpy.data.actions)},'unchangedFingerprintSHA256':hashlib.sha256(base_json.encode()).hexdigest(),'geometryMaterialsLightsCameraRootsAndOtherCapturedSettingsUnchanged':True,'fingerprint':after,'oldSourceUnchanged':sha(old)==original_sha,'noPairedAppendBeforeSave':True}
(O/'sampling-persistence-audit.json').write_text(json.dumps(record,indent=2));root=bpy.data.objects['dock-entry__root'];camera=sc.camera
# Export cadence independent of unused static scene UI timeline24/1..250.
cal=json.loads((B/'source/camera.json').read_text());cal['captureSettings']={'engine':sc.render.engine,'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples,'persistedSource':str(new.relative_to(B)),'persistedSourceSHA256':saved_sha,'nativeCadenceNote':'Actual sourceUI24fps/range250, noactions; catalogstatic1frame12fps/nonloop.'};(R/'camera.json').write_text(json.dumps(cal,indent=2))
a=json.loads((B/'source/assetRecord.json').read_text());a['artStyle']['revision']='warm-soft-native-entry-round-06-native-sampling';(R/'assetRecord.json').write_text(json.dumps(a,indent=2));rig=json.loads((B/'source/rig.json').read_text());rig['source']='build-round-06.py';rig['samplingRevision']={'filter_size':.5,'staticClipFPS':12,'sourceUIFPS':24};(R/'rig.json').write_text(json.dumps(rig,indent=2))
# Same actual geometry records retained and referenced explicitly by immutable SHA;
# current measured phases/camera/settings bind NEW source and NEW actual frames.
oldvalidation=B/'candidates/round-05/native-validation.json';audit={'asset':'dock-entry','sourceProjectSHA256':saved_sha,'sourceProject':'source/round-06.blend','frozenBriefSHA256':sha(brief),'geometryEvidence':{'path':'candidates/round-05/native-validation.json','sha256':sha(oldvalidation),'identityProof':'candidates/round-06/sampling-persistence-audit.json'},'actualSettings':record['actualAfterReopen'],'renders':[]}
for d,z in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=z;bpy.context.view_layer.update();p=O/f'static-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);audit['renders'].append({'clip':'static','direction':d,'index':0,'path':str(p.relative_to(B)),'sha256':sha(p),'rootRotationZ':root.rotation_euler.z,'rootMatrix':val(root.matrix_world),'actualSceneFrame':sc.frame_current,'cameraWorld':val(camera.matrix_world),'projectionMatrix':val(camera.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)),'frameNative':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'settings':{'engine':sc.render.engine,'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples}})
audit['savedSourceUnchangedAfterCaptures']=sha(new)==saved_sha;audit['oldSourceUnchangedAfterCaptures']=sha(old)==original_sha;(O/'native-validation.json').write_text(json.dumps(audit,indent=2));print('ENTRY06_READY',saved_sha)
