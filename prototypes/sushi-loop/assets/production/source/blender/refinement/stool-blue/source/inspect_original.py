import bpy,json
from mathutils import Vector
p='/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=p)
def mat(o): return [list(r) for r in o.matrix_world]
def box(o): return [list(o.matrix_world@Vector(x)) for x in o.bound_box] if o.type=='MESH' else None
out={'scenes':[],'collections':[],'objects':[]}
for s in bpy.data.scenes: out['scenes'].append({'name':s.name,'camera':s.camera.name if s.camera else None,'render':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage], 'pixel':[s.render.pixel_aspect_x,s.render.pixel_aspect_y], 'engine':s.render.engine})
for c in bpy.data.collections:
 if 'stool' in c.name.lower(): out['collections'].append({'name':c.name,'objects':[o.name for o in c.all_objects]})
for o in bpy.data.objects:
 if 'stool_blue' in o.name.lower() or 'stool-blue' in o.name.lower():
  out['objects'].append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':mat(o),'dimensions':list(o.dimensions),'bounds':box(o),'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polys':len(o.data.polygons) if o.type=='MESH' else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else None,'modifiers':[{'name':m.name,'type':m.type, 'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers], 'props':dict(o.items())})
for o in bpy.data.objects:
 if o.type=='CAMERA': out.setdefault('cameras',[]).append({'name':o.name,'matrix':mat(o),'type':o.data.type,'ortho_scale':o.data.ortho_scale,'shift_x':o.data.shift_x,'shift_y':o.data.shift_y})
open('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/stool-blue/source/original-inspection.json','w').write(json.dumps(out,indent=2,default=str))
print(json.dumps(out,indent=2,default=str))
