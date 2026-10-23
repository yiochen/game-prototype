import bpy,json,os
from mathutils import Vector
base=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
colls=[c for c in bpy.data.collections if 'ellis' in c.name.lower()]
print('COLLECTIONS',[(c.name,len(c.all_objects),c.hide_viewport,c.hide_render) for c in colls])
col=max(colls,key=lambda c:len(c.all_objects))
sc=bpy.data.scenes.new('ELLIS_EDITOR_INSPECTION');sc.collection.children.link(col);bpy.context.window.scene=sc
col.hide_viewport=False;col.hide_render=False
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=False;lc.hide_viewport=False
for o in col.all_objects:o.hide_set(False)
bpy.context.view_layer.update()
objects=[]
for o in col.all_objects:
 objects.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'bone':o.parent_bone,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale),'dims':list(o.dimensions),'verts':len(o.data.vertices) if o.type=='MESH' else None,'materials':[m.name for m in o.data.materials] if o.type=='MESH' else None,'mods':[(m.name,m.type) for m in o.modifiers],'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'props':{k:str(o[k])[:300] for k in o.keys()}})
report={'collection':col.name,'scenes':[s.name for s in bpy.data.scenes],'objects':objects,'cameras':[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'ortho':o.data.ortho_scale,'shift_y':o.data.shift_y} for o in bpy.data.objects if o.type=='CAMERA'],'actions':[a.name for a in bpy.data.actions if 'chef-ellis' in a.name]}
with open(base+'/candidates/inspection/source-inspection.json','w') as f:json.dump(report,f,indent=2)
print('OBJECTS',json.dumps(objects,indent=2))
