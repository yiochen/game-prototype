import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent.parent;R=P/'candidates/round-01'
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'))
s=bpy.context.scene
# Device activation is not serialized in user preferences. Match the saved recipe.
if s.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
 for d in prefs.devices:d.use=d.type=='METAL'
s.render.filepath=str(R/'reopened-S.png');bpy.ops.render.render(write_still=True)
root=bpy.data.objects['uniform35-wall-plain__root']
record={'project':'source/round-01.blend','projectSha256':hashlib.sha256((P/'source/round-01.blend').read_bytes()).hexdigest(),'render':'candidates/round-01/reopened-S.png','direction':'S','rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(row) for row in root.matrix_world],'linkedLibraries':[x.filepath for x in bpy.data.libraries],'images':[{'name':x.name,'path':x.filepath,'packed':bool(x.packed_file)} for x in bpy.data.images if x.type!='RENDER_RESULT'],'scene':s.name,'visibleCollections':[x.name for x in bpy.data.collections if not x.hide_render],'renderDevice':s.cycles.device,'pixelFilter':s.cycles.pixel_filter_type,'filterWidth':s.cycles.filter_width,'denoising':s.cycles.use_denoising}
(R/'reopened-proof.json').write_text(json.dumps(record,indent=2))
