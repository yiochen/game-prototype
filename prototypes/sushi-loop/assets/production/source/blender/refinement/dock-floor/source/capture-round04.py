"""Capture reopened persisted nativefilter.5 source, unchanged camera/light/material."""
import bpy,json,math,hashlib,shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-04';(O/'native-records').mkdir(exist_ok=True);(O/'atlases').mkdir(exist_ok=True);(O/'frames').mkdir(exist_ok=True);sc=bpy.context.scene;root=bpy.data.objects['dock-floor__root'];cam=sc.camera;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();sourceSHA=sha(bpy.data.filepath)
assert abs(sc.render.filter_size-.5)<1e-9
phases=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=a;bpy.context.view_layer.update();p=O/f'frames/static-{d}/000.png';p.parent.mkdir(exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);shutil.copyfile(p,O/f'atlases/static-{d}.png');phases.append({'clip':'static','direction':d,'index':0,'path':str(p.relative_to(B)),'sha256':sha(p),'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(r) for r in root.matrix_world],'filter_size':sc.render.filter_size,'taa_render_samples':sc.eevee.taa_render_samples,'sourceFPS':sc.render.fps,'sourceFPSBase':sc.render.fps_base})
(O/'candidate-phases.json').write_text(json.dumps(phases,indent=2))
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return[p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
r=px((0,0,0));data={'projection':'top-down-oblique-square-grid','frame':[448,480],'anchor':[224,256],'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'calibration':{'root':r,**{k:[a-b for a,b in zip(px(v),r)] for k,v in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}},'nativeSampling':{'engine':sc.render.engine,'filterSize':sc.render.filter_size,'renderSamples':sc.eevee.taa_render_samples,'sourceFPS':sc.render.fps,'sourceFPSBase':sc.render.fps_base}}
(O/'native-records/camera.json').write_text(json.dumps(data,indent=2))
a=json.loads((B/'candidates/round-03/native-records/asset.json').read_text());a['nativeProject']='source/round-04.blend';(O/'native-records/asset.json').write_text(json.dumps(a,indent=2));shutil.copyfile(B/'candidates/round-03/native-records/rig.json',O/'native-records/rig.json');assert sha(bpy.data.filepath)==sourceSHA
print('REOPENED_FILTER_CAPTURE',sourceSHA,len(phases),sc.render.filter_size)
