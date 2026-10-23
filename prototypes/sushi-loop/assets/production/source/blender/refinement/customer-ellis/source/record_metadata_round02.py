import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;MODE=sys.argv[sys.argv.index('--')+1]
record=json.loads((HERE/'resources'/f'{MODE}-rig.json').read_text());root=bpy.data.objects[record['groundRootObject']];sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0];cam=sc.camera;sc.render.resolution_x=384;sc.render.resolution_y=640;sc.render.resolution_percentage=100;bpy.context.view_layer.update()
def px(co):
 p=world_to_camera_view(sc,cam,Vector(co));return [p.x*384,(1-p.y)*640]
ground=px((0,0,0));camera={'projection':'character-orthographic','frame':[192,320],'anchor':[96,248],'cellSize':128,'captureScale':2,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=384,y=640,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':35},'calibration':{'root':ground,'unitX':[a-b for a,b in zip(px((1,0,0)),ground)],'unitDepth':[a-b for a,b in zip(px((0,-1,0)),ground)],'unitHeight':[a-b for a,b in zip(px((0,0,1)),ground)]},'nativeProjectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'artStyle':{'revision':'warm-soft-cartoon-ellis-round02','lighting':'170W4.2 overhead + four equal95W4 cardinal fills at radius3 Z2.2; world0; no ground','roughness':'role-specific.42-.75','worldLighting':True,'nativeMaterialPalette':'golden skin; blue-black hair; blue shirt; navy trousers/shoes','compositor':False}}
prefix='round-02' if MODE=='main' else 'round-02-runtime'
(HERE/(prefix+'-camera.json')).write_text(json.dumps(camera,indent=2)+'\n')
asset=json.loads((HERE/'resources'/f'original-{MODE}-asset.json').read_text());asset['scale']=2;asset['artStyle']=camera['artStyle'];asset['captureFingerprint']=hashlib.sha256(json.dumps(camera,sort_keys=True).encode()).hexdigest();(HERE/(prefix+'-asset.json')).write_text(json.dumps(asset,indent=2)+'\n')
print('ELLIS_METADATA',MODE,ground,cam.name,flush=True)
