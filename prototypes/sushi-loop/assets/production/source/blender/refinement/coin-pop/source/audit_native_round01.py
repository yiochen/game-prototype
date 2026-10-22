import bpy,json,bmesh,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent.parent;C=O/'candidates/round-01'
D={'blenderVersion':bpy.app.version_string,'sourceProjectSHA256':hashlib.sha256((O/'source/round-01.blend').read_bytes()).hexdigest(),'cameraCount':len([o for o in bpy.data.objects if o.type=='CAMERA']),'activeCamera':bpy.context.scene.camera.name,'meshes':[],'lights':[],'materials':[],'images':[],'drivers':[]}
for o in bpy.data.objects:
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);D['meshes'].append({'name':o.name,'vertices':len(bm.verts),'faces':len(bm.faces),'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'signedVolume':bm.calc_volume(signed=True),'modifiers':[m.type for m in o.modifiers],'parent':o.parent.name if o.parent else None});bm.free()
 if o.type=='LIGHT':D['lights'].append({'name':o.name,'type':o.data.type,'power':o.data.energy,'size':o.data.size,'location':list(o.location)})
 if o.animation_data:
  for f in o.animation_data.drivers:D['drivers'].append({'object':o.name,'dataPath':f.data_path,'arrayIndex':f.array_index,'expression':f.driver.expression})
for m in bpy.data.materials:
 if m.users:
  D['materials'].append({'name':m.name,'nodeTypes':[n.bl_idname for n in m.node_tree.nodes] if m.node_tree else []})
for im in bpy.data.images:
 if im.users:D['images'].append({'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'source':im.source})
D['noShadowBearingGround']=not any('ground' in o.name.lower() and o.type=='MESH' for o in bpy.data.objects)
(C/'native-scene-audit.json').write_text(json.dumps(D,indent=2))
print(json.dumps(D,indent=2))
