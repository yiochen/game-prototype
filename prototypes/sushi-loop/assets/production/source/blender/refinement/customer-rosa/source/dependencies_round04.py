import bpy,json,pathlib,hashlib
H=pathlib.Path(__file__).resolve().parent;O=H.parent;report={}
for label,file in [('main','round-04.blend'),('runtime','round-04-runtime.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(H/file));sc=bpy.context.scene
 images=[dict(name=i.name,filepath=i.filepath,packed=bool(i.packed_file),sha256=hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else None,size=list(i.size)) for i in bpy.data.images if i.users]
 report[label]={'project':str((H/file).relative_to(O)),'sha256':hashlib.sha256((H/file).read_bytes()).hexdigest(),'libraries':[l.filepath for l in bpy.data.libraries],'activeImages':images,'allActiveImagesPacked':all(i['packed'] for i in images),'missingExternalFiles':[],'scene':sc.name,'camera':sc.camera.name,'engine':sc.render.engine,'worldNodes':[dict(type=n.type,color=list(n.inputs['Color'].default_value),strength=n.inputs['Strength'].default_value) for n in sc.world.node_tree.nodes if n.type=='BACKGROUND'],'lights':[dict(name=o.name,type=o.data.type,energy=o.data.energy,position=list(o.location),size=o.data.size) for o in sc.objects if o.type=='LIGHT']}
 assert not report[label]['libraries'] and report[label]['allActiveImagesPacked']
(O/'candidates/round-04/dependencies.json').write_text(json.dumps(report,indent=2)+'\n')
