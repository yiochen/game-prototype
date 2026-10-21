import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
family=json.loads((P/'inputs/family-settings.json').read_text());recipe=json.loads((P/'source/round-01-recipe.json').read_text());LIB=Path(recipe['familySettings']['nativeLibrary']);LIB=LIB if LIB.is_file() else P/'candidates/round-01/dependencies/entrance-native.blend';assert sha(LIB)==family['nativeProjectSha256']
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'))
s=bpy.context.scene
if s.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
W=bpy.data.collections['S33_PROP_uniform35-wall-plain'];original=list(W.objects)
root=bpy.data.objects['uniform35-wall-plain__root'];root.location.x=0
placements=[];groups={0:original}
for tile in [1,2,7,8,9,10]:
 mapping={o:o.copy() for o in original}
 for old,new in mapping.items():new.name=f'context-wall-{tile}__'+old.name;W.objects.link(new)
 for old,new in mapping.items():
  if old.parent in mapping:new.parent=mapping[old.parent]
 mapping[root].location.x=tile;groups[tile]=list(mapping.values())
for tile in [0,1,2,7,8,9,10]:placements.append({'asset':'backdrop-wall','worldRoot':[tile,0,0],'tileX':tile,'nativePaste':[tile*384,0]})
with bpy.data.libraries.load(str(LIB),link=False) as (a,b):b.collections=['S33_PROP_uniform35-gate']
G=b.collections[0];s.collection.children.link(G);G.hide_render=False;G.hide_viewport=False
for o in G.all_objects:o.hide_render=False;o.hide_viewport=False
for lc in s.view_layers[0].layer_collection.children:lc.exclude=False;lc.hide_viewport=False
groot=next(o for o in G.all_objects if o.name.startswith('uniform35-gate__root'));groot.location=(4.5,0,0);groot.rotation_euler=(0,0,0)
placements.append({'asset':'backdrop-entrance','worldRoot':[4.5,0,0],'tileStart':3,'nativePaste':[1152,0],'sourceNativeProject':str(LIB),'sourceSha256':sha(LIB)})
c=s.camera;c.location.x=5;s.render.resolution_x=4416;s.render.resolution_y=1344;c.data.ortho_scale=11.5;c.data.shift_y=family['capture']['wall']['shift'][1]*1.5/11.5
bpy.context.view_layer.update();bpy.ops.file.pack_all()
s.render.filepath=str(R/'native-joined-raw.png');bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-01-join-context.blend'));bpy.ops.render.render(write_still=True)
joined={'nativeFrame':[4416,1344],'pixelPitch':384,'worldPitch':1,'placements':placements,'cameraWorldMatrix':[list(r) for r in c.matrix_world],'orthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'sourceProject':str(LIB),'sourceSha256':sha(LIB),'rootRotationZ':0,'noRasterRepair':True}
# Separate native scene showing three repeated candidate walls with no entrance.
G.hide_render=True
for tile,objects in groups.items():
 for o in objects:o.hide_render=tile not in [0,1,2]
c.location.x=1;s.render.resolution_x=1344;c.data.ortho_scale=3.5;c.data.shift_y=family['capture']['wall']['shift'][1]*1.5/3.5
bpy.context.view_layer.update();s.render.filepath=str(R/'native-repeated-raw.png');bpy.ops.render.render(write_still=True)
repeat={'nativeFrame':[1344,1344],'pixelPitch':384,'wallRoots':[[x,0,0] for x in [0,1,2]],'cameraWorldMatrix':[list(r) for r in c.matrix_world],'orthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'rootRotationZ':0}
(R/'native-context-records.json').write_text(json.dumps({'joined':joined,'repeated':repeat},indent=2))
print('NATIVE_CONTEXT_READY')
