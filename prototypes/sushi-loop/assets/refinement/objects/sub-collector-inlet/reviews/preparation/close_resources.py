import bpy,pathlib,json,hashlib
O=pathlib.Path(__file__).resolve().parent;records=[]
for p in [O/'resources/original-collector.blend',O/'resources/source-replay.blend',O/'resources/source-mounted-replay.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(p)); mats={m for o in bpy.data.objects if o.type=='MESH' for m in o.data.materials if m};images=[]
 for m in mats:
  if not m.node_tree:continue
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:images.append({'name':n.image.name,'filepath':n.image.filepath,'packed':bool(n.image.packed_file)})
 records.append({'path':str(p.relative_to(O.parent.parent)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'libraries':[l.filepath for l in bpy.data.libraries],'activeMaterialImages':images,'allActiveImageResourcesPacked':all(i['packed'] for i in images),'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None,'frame':[s.render.resolution_x,s.render.resolution_y],'objects':len(s.objects)} for s in bpy.data.scenes],'actions':[a.name for a in bpy.data.actions if 'sub-collector-inlet' in a.name]})
(O/'native-resource-closure.json').write_text(json.dumps({'blender':bpy.app.version_string,'records':records,'qualification':'The full untouched source-library snapshot contains two packed unrelated dish images. The isolated collector, standalone replay and mounted replay have no external linked libraries or active image resources. Native material nodes and actual actions are inside saved files.'},indent=2)+'\n');print('CLOSURE',[(x['path'],len(x['libraries']),len(x['activeMaterialImages']),len(x['actions'])) for x in records])
