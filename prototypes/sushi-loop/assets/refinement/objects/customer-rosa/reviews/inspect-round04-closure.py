import sys
sys.dont_write_bytecode=True
import bpy,pathlib,json,hashlib
O=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-rosa');records={}
for kind,filename,prefix in [('main','round-04.blend',''),('runtime','round-04-runtime.blend','S10 meal ')]:
 bpy.ops.wm.open_mainfile(filepath=str(O/'source'/filename));root=bpy.data.objects[prefix+'customer_rosa__ground_root.001'];col=root.users_collection[0];scene=next(s for s in bpy.data.scenes if root.name in s.objects);images={};meshes=[];materials=set()
 for o in col.all_objects:
  if o.type!='MESH':continue
  meshes.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'representation':o.get('representation'),'armatureModifiers':[m.object.name for m in o.modifiers if m.type=='ARMATURE' and m.object]})
  for mat in o.data.materials:
   if not mat:continue
   materials.add(mat.name)
   if mat.use_nodes:
    for node in mat.node_tree.nodes:
     if node.type=='TEX_IMAGE' and node.image:
      im=node.image;images[im.name]={'size':list(im.size),'packed':im.packed_file is not None,'sha256':hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,'filepath':im.filepath}
 records[kind]={'projectSHA256':hashlib.sha256((O/'source'/filename).read_bytes()).hexdigest(),'scene':scene.name,'collection':col.name,'linkedLibraries':[lib.filepath for lib in bpy.data.libraries],'images':images,'meshes':meshes,'materials':sorted(materials),'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'position':list(o.location),'size':o.data.size} for o in scene.objects if o.type=='LIGHT' and not o.hide_render],'worldBackgrounds':[{'strength':n.inputs['Strength'].default_value,'color':list(n.inputs['Color'].default_value)} for n in scene.world.node_tree.nodes if n.type=='BACKGROUND']}
(O/'reviews/round04-independent-native-closure.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps({k:{'meshCount':len(v['meshes']),'linkedLibraries':v['linkedLibraries'],'images':v['images'],'lights':len(v['lights'])} for k,v in records.items()},indent=2))
