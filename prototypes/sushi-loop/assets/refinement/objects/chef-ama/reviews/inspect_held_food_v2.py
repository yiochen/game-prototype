import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-ama');OUT=P/'reviews/held-food-v2-evidence';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(P.parents[2]/'production/source/blender'))
import native_actions as NA
brief=json.loads((P/'brief-v2-held-food.json').read_text());rig=json.loads((P/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in bpy.data.collections if root in list(c.all_objects));sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc
coll.hide_render=False;coll.hide_viewport=False
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False
bpy.context.view_layer.update();plane=next(o for o in coll.all_objects if '__image_plane' in o.name);holder=plane.parent;asset={'root':root,'collection':coll,'id':'chef-ama'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def driverinfo(o):
 return [{'path':fc.data_path,'index':fc.array_index,'expression':fc.driver.expression,'variables':[{'name':v.name,'type':v.type,'targets':[{'id':t.id.name if t.id else None,'dataPath':t.data_path} for t in v.targets]} for v in fc.driver.variables]} for fc in o.animation_data.drivers] if o.animation_data else []
def props(o):
 return {'name':o.name,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrixParentInverse':[list(r) for r in o.matrix_parent_inverse],'rayFlags':{k:getattr(o,k,None) for k in ['visible_camera','visible_diffuse','visible_glossy','visible_transmission','visible_volume_scatter','visible_shadow']},'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'drivers':driverinfo(o)}
def xy(v):
 a=world_to_camera_view(sc,sc.camera,v);return [a.x*sc.render.resolution_x,(1-a.y)*sc.render.resolution_y]
verts=[list(v.co) for v in plane.data.vertices];ymin=min(v[1] for v in verts);ymax=max(v[1] for v in verts);xmin=min(v[0] for v in verts);xmax=max(v[0] for v in verts);canonical=brief['foodDependency'];height=(xmax-xmin)*canonical['canonicalSize'][1]/canonical['canonicalSize'][0]
out={'sourcePath':bpy.data.filepath,'sourceSHA256':sha(Path(bpy.data.filepath)),'backupSHA256':sha((P/brief['source']['backup']).resolve()),'canonicalPath':str((P/canonical['artwork']).resolve()),'canonicalSHA256':sha((P/canonical['artwork']).resolve()),'plane':props(plane),'holder':props(holder),'root':props(root),'vertices':verts,'faces':[list(f.vertices) for f in plane.data.polygons],'uv':[list(l.uv) for l in plane.data.uv_layers.active.data],'localWidth':xmax-xmin,'localHeight':ymax-ymin,'bottomY':ymin,'fullCanonicalLocalHeightAtSameWidth':height,'expectedNewTopY':ymin+height,'expectedLocalTopDelta':height-(ymax-ymin),'materials':[],'phases':[],'nativeRenderControls':[],'camera':{'name':sc.camera.name,'world':[list(r) for r in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'frame':[sc.render.resolution_x,sc.render.resolution_y],'rootPixel':xy(Vector((0,0,0))),'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]}}
for m in plane.data.materials:
 nodes=[]
 for n in m.node_tree.nodes:
  rec={'name':n.name,'type':n.type,'inputs':{i.name:(list(i.default_value) if hasattr(i.default_value,'__iter__') else i.default_value) for i in n.inputs if hasattr(i,'default_value') and isinstance(i.default_value,(float,int,bool)) or hasattr(i,'default_value') and hasattr(i.default_value,'__iter__')}}
  if n.type=='TEX_IMAGE':rec['image']={'name':n.image.name,'size':list(n.image.size),'path':n.image.filepath,'packed':bool(n.image.packed_file),'SHA256':hashlib.sha256(n.image.packed_file.data).hexdigest() if n.image.packed_file else None,'alphaMode':n.image.alpha_mode,'colorSpace':n.image.colorspace_settings.name,'extension':n.extension,'interpolation':n.interpolation}
  nodes.append(rec)
 out['materials'].append({'name':m.name,'nodes':nodes,'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links]})
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   NA.apply_clip(asset,rig,clip,i+1,d,sc);dg=bpy.context.evaluated_depsgraph_get();ev=plane.evaluated_get(dg);corners=[ev.matrix_world@v.co for v in ev.data.vertices];bottom=[ev.matrix_world@v.co for v in ev.data.vertices if abs(v.co.y-ymin)<1e-6];mid=sum(bottom,Vector())/len(bottom)
   # Mathematical top-only canonical rectangle, for clearance expectation only; actual source geometry/image is not changed.
   canonicalCorners=[ev.matrix_world@Vector((v.co.x,(ymin+height) if v.co.y>ymin+1e-6 else ymin,v.co.z)) for v in ev.data.vertices]
   out['phases'].append({'clip':clip,'direction':d,'index':i,'planeHideRender':plane.hide_render,'holderHideRender':holder.hide_render,'planeVisibleInScene':not plane.hide_render and not holder.hide_render,'rootRotationZ':root.rotation_euler.z,'planeMatrixWorld':[list(r) for r in ev.matrix_world],'worldCorners':[list(v) for v in corners],'projectedCorners':[xy(v) for v in corners],'bottomWorldMidpoint':list(mid),'bottomProjected':xy(mid),'actualWorldWidth':(corners[1]-corners[0]).length,'actualWorldHeight':(corners[3]-corners[0]).length,'canonicalExpectedCorners':[list(v) for v in canonicalCorners],'canonicalExpectedProjectedCorners':[xy(v) for v in canonicalCorners],'canonicalExpectedWidth':(canonicalCorners[1]-canonicalCorners[0]).length,'canonicalExpectedHeight':(canonicalCorners[3]-canonicalCorners[0]).length})
# Preserve the actual saved scene's native renderer; configure installed Metal device only to execute that GPU setting.
if sc.render.engine=='CYCLES' and sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for dev in prefs.devices:dev.use=(dev.type=='METAL')
out['renderer']={'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'animatedSeed':sc.cycles.use_animated_seed,'denoising':sc.cycles.use_denoising,'adaptiveSampling':sc.cycles.use_adaptive_sampling,'adaptiveThreshold':sc.cycles.adaptive_threshold,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'compression':sc.render.image_settings.compression,'devices':[{'name':v.name,'type':v.type,'use':v.use} for v in bpy.context.preferences.addons['cycles'].preferences.devices]}
for clip,d,i,label in [('hold','S',0,'hold-S-000-a'),('hold','S',0,'hold-S-000-b'),('hold','N',5,'hold-N-005'),('load','E',5,'load-E-005'),('load','W',5,'load-W-005'),('work','S',0,'work-S-000'),('idle','S',0,'idle-S-000')]:
 NA.apply_clip(asset,rig,clip,i+1,d,sc);sc.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True,scene=sc.name);out['nativeRenderControls'].append({'clip':clip,'direction':d,'index':i,'path':str((OUT/(label+'.png')).relative_to(P)),'sha256':sha(OUT/(label+'.png')),'purpose':'Unchanged approved-source render; no food/body/camera/material/light edits.'})
(OUT/'source-inspection.json').write_text(json.dumps(out,indent=2)+'\n')
print('AMA_HELD_V2_SOURCE',json.dumps({k:out[k] for k in ['sourceSHA256','backupSHA256','canonicalSHA256','localWidth','localHeight','fullCanonicalLocalHeightAtSameWidth','expectedLocalTopDelta','renderer','nativeRenderControls']},indent=2))
