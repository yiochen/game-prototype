import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[1]
src=ROOT/'inputs/plant-tuned.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
s=bpy.context.scene
def proj(p):
 q=world_to_camera_view(s,s.camera,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
report={'blender':bpy.app.version_string,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'scenes':[x.name for x in bpy.data.scenes],'scene':s.name,'sceneProperties':dict(s.items()),'engine':s.render.engine,'samples':s.cycles.samples,'resolution':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'rootPixels':proj((0,0,0)),'unitX':proj((1,0,0)),'unitDepth':proj((0,-1,0)),'camera':{'name':s.camera.name,'matrix':[list(x) for x in s.camera.matrix_world],'ortho':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},'objects':[],'images':[],'materials':[]}
for o in s.objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'animation':o.animation_data is not None,'custom':dict(o.items())}
 if o.type=='MESH':
  coords=[o.matrix_world@v.co for v in o.data.vertices]
  d.update({'vertices':len(coords),'bounds':{'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]},'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers],'materials':[m.name for m in o.data.materials],'shapeKeys':o.data.shape_keys is not None})
 if o.type=='LIGHT':d.update({'energy':o.data.energy,'lightType':o.data.type})
 report['objects'].append(d)
for im in bpy.data.images:report['images'].append({'name':im.name,'source':im.source,'filepath':im.filepath,'packed':bool(im.packed_file)})
for m in bpy.data.materials:report['materials'].append({'name':m.name,'nodes':[n.type for n in m.node_tree.nodes] if m.use_nodes else []})
(ROOT/'source/inspection.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
print(json.dumps(report,indent=2,default=str))
s.cycles.samples=24
s.render.filepath=str(ROOT/'source/inspection-S.png')
bpy.ops.render.render(write_still=True)
