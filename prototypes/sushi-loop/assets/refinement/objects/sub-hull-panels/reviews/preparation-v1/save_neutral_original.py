import bpy,json,pathlib,importlib.util,hashlib
out=pathlib.Path(__file__).resolve().parent;res=out/'resources';rig=json.loads((res/'experiment/inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in bpy.data.collections if root in list(c.objects));sc=bpy.context.scene
spec=importlib.util.spec_from_file_location('closed_native_actions',res/'blender/native_actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=coll
coll.hide_render=False;coll.hide_viewport=False
for o in coll.objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
native.apply_clip({'root':root,'collection':coll},rig,'idle',1,'S',sc)
acts={bpy.data.actions[t['action']] for c in rig['clips'].values() for t in c['actions']};path=out/'source-replay/original-collection.blend';bpy.data.libraries.write(str(path),{coll,*acts},fake_user=True,compress=True)
materials={m for o in coll.objects if o.type=='MESH' for m in o.data.materials if m};images=sorted({n.image.filepath for m in materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image})
foreign=[]
for o in coll.objects:
 if o.parent and o.parent not in list(coll.objects):foreign.append(o.name+' parent '+o.parent.name)
 for x in list(o.constraints)+list(o.modifiers):
  target=getattr(x,'target',None) or getattr(x,'object',None)
  if target and target not in list(coll.objects):foreign.append(o.name+' target '+target.name)
(out/'source-replay/original-collection-closure.json').write_text(json.dumps({'scope':'Untouched source geometry/materials/rig isolated in neutral idle, canonical S; no candidate model changes','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rootLocation':list(root.location),'rootRotation':list(root.rotation_euler),'rootScale':list(root.scale),'collection':coll.name,'meshObjects':len([o for o in coll.objects if o.type=='MESH']),'actions':len(acts),'externalImages':images,'foreignDependencies':foreign,'materialNames':sorted(m.name for m in materials)},indent=2))
print('NEUTRAL_SOURCE_CLOSURE',len(acts),images,foreign)
