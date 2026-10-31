"""Reopen exact candidate project, inspect native capture/dependency closure, optionally replay.
Usage: blender --background --threads 4 --python audit-candidate.py -- project.blend candidate-folder
"""
import bpy,bmesh,hashlib,json,math,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
args=sys.argv[sys.argv.index('--')+1:]
project=Path(args[0]).resolve();out=Path(args[1]).resolve();base=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(project));scene=bpy.context.scene;cam=scene.camera
root=bpy.data.objects['perimeter-rockery__root']
meshes=[o for o in scene.objects if o.type=='MESH']
def capture():
 def px(p):
  q=world_to_camera_view(scene,cam,Vector(p));return [q.x*384,(1-q.y)*704]
 origin=px((0,0,0))
 return {'frame':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'cameraMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'calibration':{'root':origin,'unitX':[a-b for a,b in zip(px((1,0,0)),origin)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),origin)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),origin)]}}
def geometry():
 pts=[];objects=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in meshes:
  ev=o.evaluated_get(dep);m=ev.to_mesh();v=[ev.matrix_world@x.co for x in m.vertices];pts+=v
  bm=bmesh.new();bm.from_mesh(m)
  objects.append({'name':o.name,'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)],'vertices':len(m.vertices),'faces':len(m.polygons),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces),'unboundMaterialSlots':sum(x is None for x in o.data.materials),'usedMaterialIndices':sorted(set(p.material_index for p in m.polygons))})
  bm.free();ev.to_mesh_clear()
 return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)],'objects':objects}
records=[]
for facing,angle in [('N',180),('E',90),('S',0),('W',-90)]:
 root.rotation_euler.z=math.radians(angle);scene.frame_set(1);bpy.context.view_layer.update();g=geometry()
 assert all(g['min'][i]>=(-.5,-.5,0)[i]-1e-6 and g['max'][i]<=(.5,.5,1.5)[i]+1e-6 for i in range(3))
 record={'facing':facing,'rootRotationDegrees':angle,'geometry':g,'capture':capture()}
 if '--replay' in args:
  scene.render.filepath=str(out/f'reopened-{facing}.png');bpy.ops.render.render(write_still=True);record['reopenedCapture']=str(Path(scene.render.filepath).relative_to(base));record['reopenedCaptureSHA256']=sha(scene.render.filepath)
 records.append(record)
root.rotation_euler.z=0;bpy.context.view_layer.update()
v={'project':str(project.relative_to(base)),'projectSHA256':sha(project),'blender':bpy.app.version_string,'scene':scene.name,'root':{'name':root.name,'matrixWorld':[list(r) for r in root.matrix_world]},'savedCapture':capture(),'facings':records,'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],'libraries':[x.filepath for x in bpy.data.libraries],'sceneMeshes':[o.name for o in meshes],'lights':[{'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'size':o.data.size,'matrixWorld':[list(r) for r in o.matrix_world]} for o in scene.objects if o.type=='LIGHT'],'transparentFilm':scene.render.film_transparent,'proceduralNativeMaterialsOnly':not any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes),'imageFileFormat':[scene.render.image_settings.file_format,scene.render.image_settings.color_mode,scene.render.image_settings.color_depth],'renderSettings':{'engine':scene.render.engine,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'denoising':scene.cycles.use_denoising},'captureInvariantAcrossFacings':all(x['capture']==records[0]['capture'] for x in records)}
(out/'reopened-validation.json').write_text(json.dumps(v,indent=2)+'\n');print('NATIVE_REOPENED_AUDIT_PASSED',str(out),flush=True)
