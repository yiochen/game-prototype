import bpy,json,pathlib,hashlib,sys,importlib.util
HERE=pathlib.Path(__file__).resolve().parent;OBJ=HERE.parent;RT='--runtime' in sys.argv
R=json.loads((OBJ/('inputs/runtime-variants/export/source/customer-rosa/rig.json' if RT else 'inputs/source-rig.json')).read_text());root=bpy.data.objects[R['groundRootObject']];c=root.users_collection[0];sc=bpy.context.scene
spec=importlib.util.spec_from_file_location('rosa_native',HERE/'resources/native_actions.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
# Native body fingerprint excludes only the documented camera-facing 2D meal composition.
body=[]
for o in c.all_objects:
 if o.type!='MESH' or '__held_' in o.name or '__knife_' in o.name:continue
 name=o.name.replace('S10 meal ','').replace('Rosa refined runtime ','Rosa refined ')
 body.append({'name':name,'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'faceMaterials':[p.material_index for p in o.data.polygons],'weights':[[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in o.data.vertices],'materials':[{'color':list(m.diffuse_color),'nodes':[(p.type,[(i.name,str(i.default_value)) for i in p.inputs if hasattr(i,'default_value') and not i.is_linked]) for p in m.node_tree.nodes if p.type=='BSDF_PRINCIPLED']} for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]})
body.sort(key=lambda x:x['name']);blob=json.dumps(body,sort_keys=True,separators=(',',':')).encode();out=OBJ/'candidates/round-05'/('runtimeVariants' if RT else '');out.mkdir(parents=True,exist_ok=True)
(out/'body-identity.json').write_text(json.dumps({'nativeBodySHA256':hashlib.sha256(blob).hexdigest(),'meshCount':len(body),'vertexCount':sum(len(x['vertices']) for x in body),'exclusions':['canonical camera-facing 2D meal','source hidden utensil'],'normalizedOnly':['runtime object name prefix'],'packedImages':[{'name':i.name,'sha256':hashlib.sha256(i.packed_file.data).hexdigest()} for i in bpy.data.images if i.packed_file]},indent=2)+'\n')
if not RT:
 for l in sc.view_layers[0].layer_collection.children:l.exclude=l.collection!=c
 c.hide_viewport=False;c.hide_render=False
 n.apply_clip({'root':root,'collection':c},R,'stand',1,'S',sc)
 for i in range(2):sc.render.filepath=str(out/f'repeatability-{i}.png');bpy.ops.render.render(write_still=True)
