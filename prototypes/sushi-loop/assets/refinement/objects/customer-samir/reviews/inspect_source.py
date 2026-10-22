import bpy,json,pathlib,sys
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir')
rig=json.loads((P/'inputs/source-rig.json').read_text())
root=bpy.data.objects.get(rig['groundRootObject'])
report={'file':bpy.data.filepath,'root':root.name if root else None,'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None,'objects':len(s.objects),'collections':[c.name for c in s.collection.children],'render':[s.render.resolution_x,s.render.resolution_y], 'world':s.world.name if s.world else None} for s in bpy.data.scenes], 'collections':[{'name':c.name,'objects':len(c.all_objects),'renderHidden':c.hide_render,'viewportHidden':c.hide_viewport} for c in bpy.data.collections if root in list(c.all_objects)]}
if root:
 c=next(c for c in bpy.data.collections if root in list(c.all_objects) and c.name.startswith('S33_CHARACTER_'))
 report['objects']=[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parent_type':o.parent_type,'bone':o.parent_bone,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale),'custom':{k:str(v) for k,v in o.items()},'materials':[m.name for m in o.data.materials if m] if o.type=='MESH' else []} for o in c.all_objects]
 report['images']=[{'name':i.name,'filepath':i.filepath,'size':list(i.size),'packed':len(i.packed_file.data) if i.packed_file else 0} for i in bpy.data.images if i.type=='IMAGE']
(P/'reviews/source-inventory.json').write_text(json.dumps(report,indent=2))
print('INVENTORY',report['file'], report['root'],report['scenes'],report['collections'])
