import bpy,json,pathlib,importlib.util
P=pathlib.Path(__file__).parent;O=P.parent;r=json.loads((O/'inputs/source-rig.json').read_text());root=bpy.data.objects[r['groundRootObject']];c=root.users_collection[0];a=next(o for o in c.all_objects if o.type=='ARMATURE');sc=next(s for s in bpy.data.scenes if root.name in s.objects);bpy.context.window.scene=sc
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=c
c.hide_viewport=False;c.hide_render=False
spec=importlib.util.spec_from_file_location('na',P/'resources/native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
p=next(o for o in c.all_objects if '__held_' in o.name and o.type=='MESH')
for clip in ['stand','eat','panic']:
 n.apply_clip(dict(root=root,collection=c),r,clip,1,'S',sc)
 print('PLANE',clip,'scale',list(p.scale),'root',list(root.scale),'parentScale',list(p.parent.scale),'matrix',[list(x) for x in p.matrix_world],'vertex',[list(v.co) for v in p.data.vertices], 'rot',list(p.rotation_euler),'parentInv',[list(x) for x in p.matrix_parent_inverse])
