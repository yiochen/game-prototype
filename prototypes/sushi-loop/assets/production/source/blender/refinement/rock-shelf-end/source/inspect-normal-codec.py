import bpy
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).parent/'resources/canonical-middle03.blend'))
m=bpy.data.objects['rock-shelf-middle__sculpted_core'].data
print([(a.name,a.data_type,a.domain,len(a.data),[(p.identifier,p.type) for p in a.data[0].bl_rna.properties]) for a in m.attributes]);print('CUSTOM?',m.has_custom_normals)
