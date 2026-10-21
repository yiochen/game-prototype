import bpy,json,hashlib,bmesh
from pathlib import Path
base=Path(__file__).resolve().parent.parent;out=base/'candidates/round-03'
v=json.loads((out/'validation.json').read_text());sc=bpy.context.scene
v['dependencies']={'libraries':[{'path':l.filepath,'name':l.name} for l in bpy.data.libraries],'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images if i.source=='FILE'],'packed':all(i.packed_file for i in bpy.data.images if i.source=='FILE')}
v['projectReopenAudit']={'scene':sc.name,'camera':sc.camera.name,'objectCount':len(sc.objects),'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'renderEngine':sc.render.engine,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end],'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'],'actions':[a.name for a in bpy.data.actions if a.users>0],'sourceProjectSHA256':hashlib.sha256((base/'source/round-03.blend').read_bytes()).hexdigest(),'externalDependencyCount':len(bpy.data.libraries)+sum(i.source=='FILE' and not i.packed_file for i in bpy.data.images)}
(out/'validation.json').write_text(json.dumps(v,indent=2)+'\n')
print('AUDIT',json.dumps(v['dependencies']),len(v['projectReopenAudit']['actions']),'actions')
