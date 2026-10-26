"""Front-facing UI portraits from the existing native chef models.
Run through Blender MCP. Separate capture scene; source meshes/materials are appended,
never modified in the canonical project or the already open Blender scenes.
"""
from pathlib import Path
import bpy, json, re, hashlib, importlib.util
from mathutils import Vector
GAME = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
SOURCE = GAME/'assets/production/source/blender/sushi-loop-world-library.blend'
RECORDS = GAME/'assets/production/source/native-records'
CHEFS = ['lena','omar','ama','mateo','noor','dalia','ellis','rowan']
SCENE_NAME = 'Sushi Loop UI Chef Portraits v1'

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def key(name): return re.sub(r'\.\d+(?=__|$)','',name)

def build():
    prior=bpy.context.window.scene
    scene=bpy.data.scenes.new(SCENE_NAME)
    scene.render.engine=prior.render.engine
    rigs={slug:json.loads((RECORDS/('chef-'+slug)/'rig.json').read_text()) for slug in CHEFS}
    with bpy.data.libraries.load(str(SOURCE),link=False) as (src,dst):
        names=[next(n for n in src.collections if n.startswith('S33_CHARACTER_chef_'+slug+'.')) for slug in CHEFS]
        action_names=list(dict.fromkeys(a['action'] for rig in rigs.values() for a in rig['clips']['idle']['actions']))
        dst.collections=list(names);dst.actions=list(action_names)
    collections=dict(zip(CHEFS,dst.collections));actions=dict(zip(action_names,dst.actions))
    for slug,collection in collections.items():
        scene.collection.children.link(collection);collection.hide_render=False;collection.hide_viewport=False
        collection['ui_chef_id']=slug
        objects={key(o.name):o for o in collection.all_objects}
        for item in rigs[slug]['clips']['idle']['actions']:
            assert item['ownerType']=='Object'
            owner=objects[key(item['ownerName'])];action=actions[item['action']]
            owner.animation_data_create();owner.animation_data.action=action
            slots=list(action.slots)
            slot=next((s for s in slots if s.identifier==item.get('slotIdentifier')),slots[0] if slots else None)
            if slot:owner.animation_data.action_slot=slot
            for track in owner.animation_data.nla_tracks:track.mute=True
        root=objects[key(rigs[slug]['groundRootObject'])];root.rotation_euler.z=0;root.location=(0,0,0)
        for obj in collection.all_objects:
            if any(x in obj.name for x in ['__held_','__knife_','__utensil']):obj.hide_render=True
    camera_data=bpy.data.cameras.new('UI chef front orthographic')
    camera=bpy.data.objects.new('UI chef front orthographic',camera_data);scene.collection.objects.link(camera)
    assert 'ORTHO' in [x.identifier for x in camera_data.bl_rna.properties['type'].enum_items]
    camera_data.type='ORTHO';camera_data.ortho_scale=1.45;camera_data.sensor_fit='HORIZONTAL'
    camera.location=(0,-10,.85);camera.rotation_euler=(Vector((0,0,.85))-camera.location).to_track_quat('-Z','Y').to_euler();scene.camera=camera
    scene.render.resolution_x=512;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.render.pixel_aspect_x=scene.render.pixel_aspect_y=1
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=50
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.dither_intensity=0
    faceted=module('ui_portrait_faceted',SOURCE.parent/'catalog_faceted.py');lighting=faceted.ensure_lights(scene)
    style=module('ui_portrait_grade',SOURCE.parent/'catalog_style.py');style.ensure_compositor(scene)
    scene.frame_set(1)
    scene['ui_portrait_source']=str(SOURCE);scene['ui_portrait_capture']='eye-level orthographic front; 0 degree elevation; fixed camera and scale for all eight chefs'
    bpy.context.window.scene=prior
    return {'scene':scene,'collections':collections,'rigs':rigs,'lighting':lighting}

CAPTURE = build()

def render_one(slug):
    scene=CAPTURE['scene'];prior=bpy.context.window.scene
    try:
        bpy.context.window.scene=scene
        for name,col in CAPTURE['collections'].items():col.hide_render=(name!=slug);col.hide_viewport=(name!=slug)
        scene.frame_set(1);scene.view_layers[0].update()
        path=OUT/(slug+'-front.png');scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True,scene=scene.name)
        return {'chef':slug,'file':str(path),'bytes':path.stat().st_size}
    finally:bpy.context.window.scene=prior

def finish():
    scene=CAPTURE['scene'];cam=scene.camera
    data={'source':str(SOURCE.relative_to(GAME)),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'projection':'character-orthographic','camera':{'view':'front','elevationDegrees':0,'orthographicScale':1.45,'frame':[512,640],'pixelAspect':[1,1],'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=512,y=640)]},'pose':'Existing saved idle action at frame 1, facing S; held food and utensils hidden for UI portrait','lighting':CAPTURE['lighting'],'bustCrop':{'sourceRectangle':[64,24,384,512],'usage':'CSS clip of the same front render; chest up, original pixel aspect'},'chefs':[]}
    for slug in CHEFS:
        path=OUT/(slug+'-front.png');data['chefs'].append({'id':slug,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rig_sha256':hashlib.sha256((RECORDS/('chef-'+slug)/'rig.json').read_bytes()).hexdigest()})
    (OUT/'camera-and-provenance.json').write_text(json.dumps(data,indent=2)+'\n')
    bpy.data.libraries.write(str(OUT/'chef-ui-front-views.blend'),{scene},fake_user=True,compress=True)
    return data
