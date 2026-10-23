import sys,json,hashlib,importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
import bpy
P=Path(__file__).resolve().parent;R=P/'resources';scene=bpy.context.scene
rig=json.loads((R/'inputs/source-rig.json').read_text());root=bpy.data.objects[rig['groundRootObject']];col=next(c for c in scene.collection.children if root in list(c.all_objects));asset={'root':root,'collection':col}
s=importlib.util.spec_from_file_location('boundary_reopen_native',R/'native_actions.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.apply_clip(asset,rig,'scroll',1,'S',scene)
report={'source':bpy.data.filepath,'nativeFilter':scene.render.filter_size,'resolution':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'rootLocation':list(root.location),'rootScale':list(root.scale),'meshes':[],'ownExternalImages':[]}
for o in col.all_objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();coords=[list(v.co) for v in me.vertices];report['meshes'].append({'name':o.name,'localBounds':[[min(v[a] for v in coords),max(v[a] for v in coords)] for a in range(3)],'area':sum(p.area for p in me.polygons),'shapeKeyCount':len(o.data.shape_keys.key_blocks) if o.data.shape_keys else 0,'materialSlots':[x.name for x in o.data.materials]});ev.to_mesh_clear()
 for material in o.data.materials:
  for n in material.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image:report['ownExternalImages'].append(n.image.filepath)
assert report['resolution']==[512,512]
assert all(max(abs(x) for x in o['localBounds'][0])<=.5 and max(abs(x) for x in o['localBounds'][1])<=.5 for o in report['meshes'])
assert next(o['area'] for o in report['meshes'] if 'full_square' in o['name'])==1
out=Path(bpy.data.filepath).parent/'saved-source-reopen-audit.json';out.write_text(json.dumps(report,indent=2)+'\n');print('REOPEN_FILTER',scene.render.filter_size,'EXACT_GEOMETRY_OK')
