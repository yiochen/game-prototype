import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-01';R.mkdir(parents=True,exist_ok=True)
F=P/'inputs/family-settings.json'
assert F.is_file(),'Frozen family settings are required before native final renders'
family=json.loads(F.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve_family(key):
 value=family[key];pp=Path(value)
 paths=[P/'candidates/round-01/dependencies/entrance-native.blend',pp,P/pp,P.parent/'backdrop-entrance'/pp]
 for path in paths:
  if path.is_file():return path.resolve()
 raise FileNotFoundError((key,value))
LIB=resolve_family('nativeProject')
assert sha(LIB)==family['nativeProjectSha256'],'Family native bytes changed'
bpy.ops.wm.open_mainfile(filepath=str(P/'source/geometry-stage.blend'))
sc=bpy.context.scene;W=bpy.data.collections['S33_PROP_uniform35-wall-plain'];W.hide_render=False;W.hide_viewport=False
# Record native assignment roles, then append exact material graphs from the family.
assignments={o.name:[m.name for m in o.data.materials] for o in W.objects if o.type=='MESH'}
for o in W.objects:
 if o.type=='MESH':o.data.materials.clear()
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
for w in list(bpy.data.worlds):bpy.data.worlds.remove(w)
with bpy.data.libraries.load(str(LIB),link=False) as (a,b):
 b.materials=[n for n in a.materials if n in family['materials']]
 b.worlds=[family['worldName']]
 b.objects=list(family['lights'])
sc.world=bpy.data.worlds[family['worldName']]
for name in family['lights']:
 ob=bpy.data.objects[name];sc.collection.objects.link(ob)
# Source profiles must have the exact shared protected material, while new interior forms use the base family roles.
protected=[]
for o in W.objects:
 if o.type!='MESH':continue
 shared=any(abs(abs((o.matrix_world@v.co).x)-.5)<1e-5 for v in o.data.vertices)
 if shared:protected.append(o.name)
 for name in assignments[o.name]:
  resolved=name+'__protected_profile' if shared and name+'__protected_profile' in bpy.data.materials else name
  o.data.materials.append(bpy.data.materials[resolved])
# Copy the frozen renderer and registered narrow camera. No fitting, cropping or image-side repair.
c=sc.camera;wall=family['capture']['wall'];c.matrix_world=Matrix(wall['worldMatrix']);c.data.type='ORTHO';c.data.ortho_scale=wall['orthoScale'];c.data.sensor_fit='HORIZONTAL';c.data.shift_x=wall['shift'][0];c.data.shift_y=wall['shift'][1]
rr=family['rendering'];sc.render.engine=rr['engine'];sc.cycles.samples=rr['samples'];sc.cycles.use_denoising=rr.get('useDenoising',rr.get('denoising',True));sc.cycles.denoiser=rr.get('denoiser') or 'OPENIMAGEDENOISE';sc.cycles.pixel_filter_type=rr.get('nativePixelFilter',rr['pixelFilter']);sc.cycles.filter_width=rr.get('nativeFilterWidth',rr['filterWidth']);sc.cycles.transparent_max_bounces=rr['transparentMaxBounces'];sc.cycles.seed=0
if rr['device']=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
 sc.cycles.device='GPU'
else:sc.cycles.device='CPU'
sc.view_settings.view_transform=rr['viewTransform'];sc.view_settings.look=rr['look'];sc.view_settings.exposure=rr['exposure'];sc.view_settings.gamma=rr['gamma']
sc.render.resolution_x=576;sc.render.resolution_y=1344;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.fps=12
bpy.data.objects['uniform35-wall-plain__root'].rotation_euler=(0,0,0)
# Clean local dependency closure before saving the immutable round.
for _ in range(3):bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
bpy.ops.file.pack_all();bpy.context.view_layer.update()
recipe={'schemaVersion':1,'asset':'backdrop-wall','round':'round-01','blender':bpy.app.version_string,'baseSource':str((P/'../../backups/927a8a59e8d0f1e9-restaurant-backdrop-35.blend').resolve()),'sourceSha256':sha((P/'../../backups/927a8a59e8d0f1e9-restaurant-backdrop-35.blend').resolve()),'geometryRecipe':'source/build_geometry.py','geometryStageSha256':sha(P/'source/geometry-stage.blend'),'familySettings':{'path':'inputs/family-settings.json','sha256':sha(F),'nativeLibrary':str(LIB),'nativeLibrarySha256':sha(LIB)},'nativeModeling':json.loads((P/'source/geometry-stage.json').read_text()),'protectedSourceProfiles':protected,'camera':{'worldMatrix':[list(row) for row in c.matrix_world],'type':c.data.type,'orthoScale':c.data.ortho_scale,'sensorFit':c.data.sensor_fit,'shift':[c.data.shift_x,c.data.shift_y],'frame':[576,1344],'pixelAspect':[1,1],'sourceScale':3,'logicalFrame':[192,448],'logicalRoot':[96,416],'frontContactWorldPoint':[0,-.5,0],'sourcePhase':'S0'},'renderer':{**rr,'actualDevice':sc.cycles.device,'actualSamples':sc.cycles.samples,'actualPixelFilter':sc.cycles.pixel_filter_type,'actualFilterWidth':sc.cycles.filter_width,'seed':sc.cycles.seed},'lighting':{'worldName':sc.world.name,'worldNodes':family['world'],'lights':family['lights'],'horizontalLightContract':family['horizontalLightContract'],'directionalGroundShadow':False,'groundObject':None},'materials':{m.name:family['materials'][m.name] for m in bpy.data.materials if m.name in family['materials']},'dependencies':{'transientAppendedLibraryContainersBeforeSave':len(bpy.data.libraries),'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.type!='RENDER_RESULT']},'reconstruction':'No AI image textures, target billboard, raster fitting, painted seams or per-view adjustments. Geometry is directly editable native Blender mesh.'}
(P/'source/round-01-recipe.json').write_text(json.dumps(recipe,indent=2))
# Save before rendering; a reopened independent render will prove the saved bytes reproduce it.
sc.render.filepath=str(R/'static-S-000.png');bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-01.blend'))
exec(compile((P/'source/audit_native.py').read_text(),str(P/'source/audit_native.py'),'exec'))
bpy.ops.render.render(write_still=True)
print('ROUND01_NATIVE_CAPTURE_READY')
