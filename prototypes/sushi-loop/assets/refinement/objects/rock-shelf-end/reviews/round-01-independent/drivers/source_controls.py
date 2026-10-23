import sys
sys.dont_write_bytecode=True
import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];s=bpy.context.scene;c=s.camera
r={'actualLinkedLibraries':[l.filepath for l in bpy.data.libraries],'cameraType':c.data.type,'sensorFit':c.data.sensor_fit,'cameraMatrix':[list(row) for row in c.matrix_world],'renderEngine':s.render.engine,'samples':s.eevee.taa_render_samples,'filmTransparent':s.render.film_transparent,'filterSize':s.render.filter_size,'fps':s.render.fps,'frameCurrent':s.frame_current,'frameRange':[s.frame_start,s.frame_end],'sceneProperties':{k:s[k] for k in s.keys()},'rootProperties':{k:bpy.data.objects['rock-shelf-end__root'][k] for k in bpy.data.objects['rock-shelf-end__root'].keys()},'compositorNodeCount':len(s.compositing_node_group.nodes),'compositorContrast':s.compositing_node_group.get('contrastFactor'),'savedImageFileDependencies':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE' and i.users]}
(R/'measurements/source-controls.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
