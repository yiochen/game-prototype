"""Sushi Loop issue33 native Blender MCP capture runtime.
Execute/import in Blender. Existing unrelated scenes remain untouched.
"""
import bpy, math, json, os, sys, time, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT = Path(__file__).parent / 'export'
OUT.mkdir(exist_ok=True)
SCENE_NAME='Sushi33 Production'
assets={}
jobs=[]
job_status={'state':'idle','done':0,'total':0,'error':None}

def scene():
    sc=bpy.data.scenes.get(SCENE_NAME) or bpy.data.scenes.new(SCENE_NAME)
    bpy.context.window.scene=sc
    return sc

def camera_record(sc,cam,projection,frame,root,scale,elevation=None):
    return {'projection':'character-orthographic' if projection=='character-orthographic' else 'top-down-oblique-square-grid','frame':list(frame),'anchor':list(root),'cellSize':128,'captureScale':scale,'fps':12,
      'axes':{'x':'X','depth':'-Y','height':'Z'},
      'camera':{'type':'orthographic','worldMatrix':[list(row) for row in cam.matrix_world],
      'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],
      'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':elevation if elevation is not None else 35 if projection=='character-orthographic' else 45}}

def configure_camera(projection='square-top-front-oblique',frame=(192,320),root=(96,248),scale=4,elevation_degrees=None):
    sc=scene();sc.render.engine='BLENDER_EEVEE'
    sc.render.resolution_x=frame[0]*scale;sc.render.resolution_y=frame[1]*scale;sc.render.resolution_percentage=100
    sc.render.pixel_aspect_x=1 if projection=='character-orthographic' else math.sqrt(2);sc.render.pixel_aspect_y=1
    cam=sc.objects.get('S33 Capture Camera')
    if cam is None:
        cam=bpy.data.objects.new('S33 Capture Camera',bpy.data.cameras.new('S33 Capture Camera'));sc.collection.objects.link(cam)
    sc.camera=cam;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
    elevation_value=elevation_degrees if elevation_degrees is not None else 35 if projection=='character-orthographic' else 45
    elevation=math.radians(elevation_value)
    cam.location=(0,-10*math.cos(elevation),10*math.sin(elevation));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
    def px(v):
        p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
    base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y
    cam.data.shift_y=(root[1]*scale-base.y)/dy
    # X ground origin is centered in authored frames. Preserve fixed registration.
    cam.data.shift_x=(frame[0]/2-root[0])/frame[0]
    bpy.context.view_layer.update()
    projected=px((0,0,0));X=px((1,0,0))-projected;D=px((0,-1,0))-projected;H=px((0,0,1))-projected
    assert (projected-Vector((root[0]*scale,root[1]*scale))).length<.05,(projected,root)
    if projection!='character-orthographic':
        assert abs(X.x-128*scale)<.05 and abs(D.y-128*scale)<.05 and abs(H.y+128*scale)<.05,(X,D,H)
    sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    sc.render.fps=12
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
    sc.world=sc.world or bpy.data.worlds.new('S33 Soft World');sc.world.use_nodes=True
    background=next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND');background.inputs['Color'].default_value=(.72,.80,1,1);background.inputs['Strength'].default_value=.7
    for name,loc,power,size in [('S33 Key',(-3,-4,7),450,5),('S33 Fill',(4,-1,3),160,4),('S33 Rim',(1,4,5),200,3)]:
        light=sc.objects.get(name)
        if light is None:
            data=bpy.data.lights.new(name,'AREA');light=bpy.data.objects.new(name,data);sc.collection.objects.link(light)
        light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.location=loc;light.rotation_euler=(-light.location).to_track_quat('-Z','Y').to_euler()
    sc.render.image_settings.compression=30
    record=camera_record(sc,cam,projection,frame,root,scale,elevation_value)
    record['calibration']={'root':list(projected),'unitX':list(X),'unitDepth':list(D),'unitHeight':list(H)}
    return record

def register(asset_id,asset,projection='square-top-front-oblique',frame=(192,320),root=(96,248),scale=4):
    asset['id']=asset_id;asset['projection']=projection;asset['frame']=frame;asset['anchor']=root;asset['scale']=scale
    assets[asset_id]=asset
    return asset

def show_only(asset_id):
    sc=scene()
    # Failed authoring attempts can leave an unregistered collection. Never let
    # those leak into another object's capture; this isolated scene is ours.
    for collection in sc.collection.children:
        collection.hide_render=True;collection.hide_viewport=True
    for aid,asset in assets.items():asset['collection'].hide_render=aid!=asset_id;asset['collection'].hide_viewport=aid!=asset_id
    asset=assets[asset_id];asset['collection'].hide_render=False;asset['collection'].hide_viewport=False
    return asset

def preview(asset_id,clip=None,direction='S',t=.25):
    a=show_only(asset_id);clip=clip or next(iter(a['clips']))
    a['pose'](clip,t);a['root'].rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[direction]
    record=configure_camera(a['projection'],a['frame'],a['anchor'],a['scale'],a.get('camera_elevation_degrees'))
    path=OUT/'validation'/asset_id;path.mkdir(parents=True,exist_ok=True)
    scene().render.filepath=str(path/(clip+'-'+direction+'.png'))
    started=time.monotonic();bpy.ops.render.render(write_still=True,scene=SCENE_NAME)
    (path/'camera.json').write_text(json.dumps(record,indent=2)+'\n')
    return {'image':scene().render.filepath,'seconds':time.monotonic()-started,'camera':record}

def save_project(name='sushi-loop-world-library.blend'):
    folder=OUT/'source';folder.mkdir(exist_ok=True)
    path=folder/name
    bpy.data.libraries.write(str(path),{scene()},fake_user=True,compress=True)
    return str(path)

def queue_capture(asset_ids):
    if job_status['state']=='rendering':raise RuntimeError('Capture already running')
    jobs.clear()
    for aid in asset_ids:
        a=assets[aid]
        for clip,recipe in a['clips'].items():
            count=recipe['frames']
            for direction in ['N','E','S','W']:
                for i in range(count):jobs.append((aid,clip,direction,i,count))
    job_status.update(state='rendering',done=0,total=len(jobs),error=None,started=time.time())
    def step():
        if not jobs:job_status['state']='complete';return None
        try:
            aid,clip,direction,i,count=jobs.pop(0);a=show_only(aid)
            a['pose'](clip,i/count if a['clips'][clip].get('loop') else i/max(1,count-1))
            a['root'].rotation_euler.z={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[direction]
            record=configure_camera(a['projection'],a['frame'],a['anchor'],a['scale'],a.get('camera_elevation_degrees'))
            path=OUT/'raw-frames'/aid/(clip+'-'+direction);path.mkdir(parents=True,exist_ok=True)
            scene().render.filepath=str(path/(f'{i:03d}.png'));bpy.ops.render.render(write_still=True,scene=SCENE_NAME)
            source=OUT/'source'/aid;source.mkdir(parents=True,exist_ok=True)
            (source/'camera.json').write_text(json.dumps(record,indent=2)+'\n')
            (source/'asset.json').write_text(json.dumps({k:a[k] for k in ['id','projection','frame','anchor','scale','clips','footprint','height','sockets','ports','flow','camera_elevation_degrees','nonblocking','depth_layer','composition_context'] if k in a},indent=2)+'\n')
            job_status.update(done=job_status['done']+1,current=[aid,clip,direction,i],updated=time.time())
            (OUT/'capture-status.json').write_text(json.dumps(job_status,indent=2)+'\n')
            return .01
        except Exception as exc:
            import traceback
            job_status.update(state='failed',error=traceback.format_exc())
            (OUT/'capture-status.json').write_text(json.dumps(job_status,indent=2)+'\n');return None
    bpy.app.timers.register(step,first_interval=.1)
    return dict(job_status)
