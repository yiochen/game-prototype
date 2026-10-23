import bpy,sys,math,json,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;OUT=RES.parent/'baseline';OUT.mkdir(exist_ok=True)
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};records=[]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def configure(sc,scale,frame=(192,352),anchor=(96,248),filt=.01):
    cam=sc.camera;sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1;sc.render.filter_size=filt
    cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
    el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
    base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
    r=px((0,0,0));return {'frame':list(frame),'root':list(anchor),'scale':scale,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filter':sc.render.filter_size,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'ortho':cam.data.ortho_scale,'cameraWorld':[list(row) for row in cam.matrix_world],'calibration':{'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)}}
def render(sc,name,meta):
    p=OUT/(name+'.png');p.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
    records.append({'path':str(p.relative_to(OUT)),**meta,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def layers(l):
    l.exclude=False;l.hide_viewport=False
    for c in l.children:layers(c)
bpy.ops.wm.open_mainfile(filepath=str(RES/'native/source-library.blend'))
sc=next(s for s in bpy.data.scenes if s.get('source')=='native_actions.py');bpy.context.window.scene=sc
root=bpy.data.objects['wreck-edge__root.001'];col=next(c for c in bpy.data.collections if root.name in c.objects)
for c in sc.collection.children:c.hide_render=c!=col;c.hide_viewport=c!=col
layers(sc.view_layers[0].layer_collection);root.rotation_euler=(0,0,0);root.location=(0,0,0);sc.frame_set(1)
sc.render.engine='BLENDER_EEVEE';sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
load('historical_style',RES/'historical/catalog_style.py').ensure_compositor(sc)
load('historical_lights',RES/'historical/catalog_faceted.py').ensure_lights(sc)
camera=configure(sc,4,filt=1.5);render(sc,'historical-native4-S',{'kind':'original historical4x replay','direction':'S','camera':camera,'rootMatrix':[list(r) for r in root.matrix_world],'sourceSHA256':hashlib.sha256((RES/'native/source-library.blend').read_bytes()).hexdigest()})
# Diagnostic only: append the untouched derivative into the exact approved native rig.
# This preserves original meshes/materials; no model, shader or .blend is saved.
bpy.ops.wm.open_mainfile(filepath=str(RES/'native/canonical-middle02.blend'));sc=bpy.context.scene
canon=bpy.data.objects['wreck-middle__root'];canoncol=bpy.data.collections['Wreck middle authored candidate']
with bpy.data.libraries.load(str(RES/'native/source-library.blend'),link=False) as (src,dst):dst.collections=['S33_PROP_wreck-edge.001']
col=dst.collections[0];sc.collection.children.link(col);col.hide_render=False;col.hide_viewport=False;layers(sc.view_layers[0].layer_collection)
root=next(o for o in col.objects if o.get('asset_id')=='wreck-edge');root.location=(0,0,0);sc.frame_set(1)
canoncol.hide_render=True
for d,a in ANGLES.items():
    root.rotation_euler.z=a;bpy.context.view_layer.update();camera=configure(sc,2)
    render(sc,'original-canonical-rig/'+d,{'kind':'unchanged derivative in canonical rig diagnostic, not candidate','direction':d,'camera':camera,'rootMatrix':[list(r) for r in root.matrix_world]})
canoncol.hide_render=False
originals=list(canoncol.objects)
for d,a in ANGLES.items():
    root.rotation_euler.z=a;canon.rotation_euler.z=a;canon.location=Vector((-1,0,0));canon.location.rotate(__import__('mathutils').Euler((0,0,a)))
    clones={}
    for o in originals:
        cp=o.copy();canoncol.objects.link(cp);clones[o]=cp
    for o,cp in clones.items():cp.parent=clones.get(o.parent);cp.matrix_parent_inverse=o.matrix_parent_inverse.copy()
    other=clones[canon];other.rotation_euler.z=a;other.location=Vector((1,0,0));other.location.rotate(__import__('mathutils').Euler((0,0,a)))
    bpy.context.view_layer.update();vertical=d in ['E','W'];camera=configure(sc,2,(192,608) if vertical else (448,352),(96,376) if vertical else (224,248))
    render(sc,'mixed-native/'+d,{'kind':'unchanged derivative center + exact approved middle02 both sides; baseline only','direction':d,'camera':camera,'moduleRootMatrices':{'middleAtMinus1':[list(r) for r in canon.matrix_world],'derivativeCenter':[list(r) for r in root.matrix_world],'middleAtPlus1':[list(r) for r in other.matrix_world]},'ports':'actual E-to-W sections; unit pitch, proper roots; original caps retained; no geometry or raster overlap adjustment'})
    for cp in clones.values():bpy.data.objects.remove(cp,do_unlink=True)
(OUT/'capture-records.json').write_text(json.dumps({'blender':bpy.app.version_string,'scope':'source and native connection baselines only; no candidate or approval','records':records},indent=2)+'\n')
print('BASELINE_COMPLETE',len(records))
