"""Independent source/camera feasibility inspection; never saves the input blend."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'inputs/approved-world-model.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='1d9bc1fa321e705154e2c36fec41fd4092ba843f233d938f02b69e761881837c'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
s=bpy.context.scene
def obj(o):
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,
    'matrix':[list(r) for r in o.matrix_world], 'hideRender':o.hide_render,'hideViewport':o.hide_viewport,
    'hideGet':o.hide_get(),'collections':[c.name for c in o.users_collection]}
 if o.type=='MESH':
  d.update({'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),
            'materials':[m.name if m else None for m in o.data.materials],
            'modifiers':[{'name':m.name,'type':m.type,'showRender':m.show_render,'showViewport':m.show_viewport} for m in o.modifiers]})
  if o.data.shape_keys:
   k=o.data.shape_keys
   d['shapeKeys']={x.name:x.value for x in k.key_blocks}
   d['activeAction']=k.animation_data.action.name if k.animation_data and k.animation_data.action else None
 if o.type=='LIGHT':d.update({'energy':o.data.energy,'color':list(o.data.color),'lightType':o.data.type})
 return d
def layer(l):return {'name':l.name,'exclude':l.exclude,'holdout':l.holdout,'indirectOnly':l.indirect_only,'children':[layer(c) for c in l.children]}
report={'blender':bpy.app.version_string,'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'scenes':[x.name for x in bpy.data.scenes],'scene':s.name,'frame':s.frame_current,
 'activeClip':s.get('activeClip'),'rootName':s.get('studyRoot'),'objects':[obj(o) for o in s.objects],
 'collections':[{'name':c.name,'hideRender':c.hide_render,'hideViewport':c.hide_viewport,'objects':[o.name for o in c.objects]} for c in bpy.data.collections],
 'viewLayers':[{'name':v.name,'use':v.use,'layer':layer(v.layer_collection)} for v in s.view_layers],
 'render':{'engine':s.render.engine,'size':[s.render.resolution_x,s.render.resolution_y],
           'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'percentage':s.render.resolution_percentage,
           'samples':s.cycles.samples,'seed':s.cycles.seed,'animatedSeed':s.cycles.use_animated_seed,
           'transparent':s.render.film_transparent,'fileFormat':s.render.image_settings.file_format,
           'colorMode':s.render.image_settings.color_mode,'colorDepth':s.render.image_settings.color_depth,
           'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},
 'world':s.world.name if s.world else None,'worldNodes':[n.type for n in s.world.node_tree.nodes] if s.world and s.world.use_nodes else [],
 'compositor':[(n.name,n.type) for n in s.compositing_node_group.nodes] if s.compositing_node_group else [],
 'images':[{'name':i.name,'source':i.source,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images],
 'libraries':[l.filepath for l in bpy.data.libraries]}
(ROOT/'source/inspection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'scene':report['scene'],'frame':report['frame'],'activeClip':report['activeClip'],
                  'objects':report['objects'],'collections':report['collections'],'viewLayers':report['viewLayers'],
                  'render':report['render'],'images':report['images'],'libraries':report['libraries']},indent=2))
# Only restore visibility and change the UI camera/resolution for this feasibility image.
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
def show_layer(l):
 l.exclude=False;l.holdout=False;l.indirect_only=False
 for c in l.children:show_layer(c)
for v in s.view_layers:v.use=True;show_layer(v.layer_collection)
for o in s.objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
contract=json.loads((ROOT/'inputs/camera-contract.json').read_text())
cam=bpy.data.cameras.new('Plant independent UI inspection camera')
cam.type='ORTHO';cam.ortho_scale=contract['ortho_scale'];cam.shift_x=0;cam.shift_y=0
co=bpy.data.objects.new(cam.name,cam);s.collection.objects.link(co)
co.matrix_world=Matrix(contract['world_matrix']);s.camera=co
s.render.resolution_x=s.render.resolution_y=384
s.render.pixel_aspect_x=s.render.pixel_aspect_y=1
bpy.context.view_layer.update()
s.render.filepath=str(ROOT/'source/inspection-goods.png')
bpy.ops.render.render(write_still=True,scene=s.name)
