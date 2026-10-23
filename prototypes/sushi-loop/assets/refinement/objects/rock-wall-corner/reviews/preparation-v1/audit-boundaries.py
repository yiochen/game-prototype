import bpy,json
from pathlib import Path
OUT=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(OUT/'resources/approved-middle/project.blend'))
me=bpy.data.objects['rock-wall-middle__continuous_carved_stone'].data;me.update();attrs=me.color_attributes['stone_albedo'];loopFor={}
for l in me.loops:
 if l.vertex_index not in loopFor:loopFor[l.vertex_index]=l.index
rings={}
for x,label in [(-.5,'W'),(.5,'E')]:
 rings[label]=[{'index':v.index,'position':list(v.co),'nativeAlbedoLinearRGBA':list(attrs.data[v.index].color),'customCornerNormal':list(me.corner_normals[loopFor[v.index]].vector)} for v in me.vertices if abs(v.co.x-x)<1e-7]
a,b=rings['W'],rings['E'];rep={'compositorGroup':bpy.context.scene.compositing_node_group.name if bpy.context.scene.compositing_node_group else None,'source':'resources/approved-middle/project.blend','mesh':me.name,'periodicRingSamples':len(a),'rings':rings,'maxOppositeRingColorDifference':max(abs(a[i]['nativeAlbedoLinearRGBA'][j]-b[i]['nativeAlbedoLinearRGBA'][j]) for i in range(len(a)) for j in range(4)),'maxOppositeYZDifference':max(abs(a[i]['position'][j]-b[i]['position'][j]) for i in range(len(a)) for j in [1,2]),'joinTreatment':'Canonical geometric relief fades to exact zero with flat tangent at port planes. Shared line sampled albedo/crown profiles and seam normals must match after appropriate native rotation/translation; elsewhere corner stone layout may improve. Native material attribute, no external images.'}
(OUT/'canonical-boundary-samples.json').write_text(json.dumps(rep,indent=2)+'\n');print('BOUNDARY_DONE')
