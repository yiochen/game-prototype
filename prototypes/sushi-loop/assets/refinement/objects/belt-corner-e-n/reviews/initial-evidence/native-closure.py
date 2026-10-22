import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[2];W=next(p for p in B.parents if (p/'prototypes.json').exists());S=W/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend';F=Path(json.loads((B/'inputs/family-settings.json').read_text())['project']['path']);O=B/'reviews/initial-evidence/native';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(S));coll=bpy.data.collections['S33_FB_belt-corner-e-n.001'];root=bpy.data.objects['belt-corner-e-n__root.001'];s=bpy.data.scenes.new('IndependentCornerClosure');bpy.context.window.scene=s;s.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False
for o in coll.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
with bpy.data.libraries.load(str(F),link=False)as(a,b):b.objects=[n for n in a.objects if n=='RegisteredSquareCamera' or n.startswith(('Centered broad key','Equal cardinal fill'))];b.worlds=['WarmSoft_symmetrical_world']
for o in b.objects:
 if o:s.collection.objects.link(o)
s.camera=next(o for o in b.objects if o.type=='CAMERA');s.world=b.worlds[0];s.render.resolution_x=384;s.render.resolution_y=704;s.render.resolution_percentage=100;s.render.pixel_aspect_x=1.2206555604934692;s.render.pixel_aspect_y=1;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=1;s.cycles.use_denoising=False;s.cycles.pixel_filter_type='BOX';s.cycles.use_animated_seed=False;s.cycles.seed=0;s.render.filter_size=1;s.render.dither_intensity=0;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.render.fps=12
rec=json.loads((B/'inputs/source-rig.json').read_text())['clips']['running']['actions'][0];m=bpy.data.materials[rec['materialOwnerName']];m.node_tree.animation_data_create();a=bpy.data.actions[rec['action']];m.node_tree.animation_data.action=a;m.node_tree.animation_data.action_slot=next(sl for sl in a.slots if sl.identifier==rec['slotIdentifier']);out=[]
for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=angle
 for f in [1,25]:
  s.frame_set(f);bpy.context.view_layer.update();p=O/f'source-closure-{d}-{f:02d}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);out.append({'direction':d,'nativeFrame':f,'path':str(p.relative_to(B)),'phase':float(m.node_tree.nodes['Value'].outputs[0].default_value),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
cal=lambda v:[world_to_camera_view(s,s.camera,Vector(v)).x*384,(1-world_to_camera_view(s,s.camera,Vector(v)).y)*704]
r={'purpose':'Independent original-geometry closure render with exact original native phase action and approved family camera/lighting. Not a candidate, not asserted byte-parity with source publication. Source/target/family untouched.','camera':{'name':s.camera.name,'worldMatrix':[[float(x)for x in r]for r in s.camera.matrix_world],'orthoScale':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'root':cal((0,0,0)),'unitX':cal((1,0,0)),'unitY':cal((0,1,0)),'unitZ':cal((0,0,1))},'renders':out};(O/'closure.json').write_text(json.dumps(r,indent=2))
