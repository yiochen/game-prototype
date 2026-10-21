"""Render saved native source with fixed 35-degree camera and shared pitch.
Use: blender -b restaurant-backdrop-35.blend -P render_backdrop.py
"""
from pathlib import Path
import bpy, math, json, hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
scene=bpy.data.scenes['Sushi Loop Flat Backdrop35 Study'];bpy.context.window.scene=scene
book=json.loads((ROOT/'camera.json').read_text())
cam=scene.camera
assembly=next(c for c in scene.collection.children if c.name.startswith('Flat35 Assembled Seven Tiles'))
collections=[c for c in scene.collection.children if c.name.startswith('S33_PROP_flat35-')]
for collection in collections:collection.hide_viewport=False
assembly.hide_viewport=False
proof=[]
for name in ['gate','wall-plain','assembled']:
    for collection in collections:collection.hide_render=True
    assembly.hide_render=name!='assembled'
    width=7 if name=='assembled' else book['assets'][name]['widthTiles']
    if name!='assembled':bpy.data.collections[book['assets'][name]['collection']].hide_render=False
    frame=[width*128+64,448];anchor=[frame[0]/2,416];scale=3
    scene.render.resolution_x=int(frame[0]*scale);scene.render.resolution_y=frame[1]*scale
    cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0
    bpy.context.view_layer.update()
    def pixel(co):
        p=world_to_camera_view(scene,cam,Vector(co));return Vector((p.x*scene.render.resolution_x,(1-p.y)*scene.render.resolution_y))
    initial=pixel((0,-.5,0));cam.data.shift_y=1;bpy.context.view_layer.update()
    dy=pixel((0,-.5,0)).y-initial.y
    cam.data.shift_y=(anchor[1]*scale-initial.y)/dy
    bpy.context.view_layer.update()
    scene.render.filepath=str(ROOT/'renders'/f'{name}.png')
    bpy.ops.render.render(write_still=True,scene=scene.name)
    path=Path(scene.render.filepath)
    proof.append({'id':name,'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frame':frame,'captureScale':scale,'camera':{'type':cam.data.type,'elevationDegrees':35,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y]},'baseline':list(pixel((0,-.5,0)))})
# Finalize a normal editable .blend with this study active, rather than leaving
# a library-only file that opens on an empty startup scene. This runs in this
# disposable background Blender process, never over the user's live file.
for collection in collections:
    visible=collection.name==book['assets']['gate']['collection']
    collection.hide_render=not visible;collection.hide_viewport=not visible
assembly.hide_render=True;assembly.hide_viewport=True
frame=book['assets']['gate']['frame'];anchor=book['assets']['gate']['anchor']
scene.render.resolution_x=frame[0]*3;scene.render.resolution_y=frame[1]*3
cam.data.ortho_scale=frame[0]/128;cam.data.shift_x=0;cam.data.shift_y=0
bpy.context.view_layer.update();initial=pixel((0,-.5,0))
cam.data.shift_y=1;bpy.context.view_layer.update();dy=pixel((0,-.5,0)).y-initial.y
cam.data.shift_y=(anchor[1]*3-initial.y)/dy;bpy.context.view_layer.update()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.type='MATERIAL'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'source/restaurant-backdrop-35.blend'),compress=True)
(ROOT/'render-receipt.json').write_text(json.dumps({'method':'native Blender EEVEE, no ImageGen reskin','source':'source/restaurant-backdrop-35.blend','sourceSha256':hashlib.sha256((ROOT/'source/restaurant-backdrop-35.blend').read_bytes()).hexdigest(),'recipeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'renders':proof},indent=2)+'\n')
print('BACKDROP35_COMPLETE',len(proof))
