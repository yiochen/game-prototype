import sys
sys.dont_write_bytecode=True
import bpy,json
from pathlib import Path
BASE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(BASE/'resources/source/original.blend'))
c=bpy.data.collections['S33_PROP_reef-middle.001'];sc=next(s for s in bpy.data.scenes if c.name in s.collection.children)
r={'savedRender':{'filterSize':sc.render.filter_size,'engine':sc.render.engine,'frame':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'libraries':[l.filepath for l in bpy.data.libraries],'assetMaterials':{},'objects':{},'onlyNativeMeshArtwork':True}
for o in c.all_objects:
 r['objects'][o.name]={'type':o.type,'actions':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'hasCustomNormals':getattr(o.data,'has_custom_normals',None) if o.type=='MESH' else None,'dataAnimation':bool(o.data.animation_data) if o.type=='MESH' else None,'shapeKeys':bool(o.data.shape_keys) if o.type=='MESH' else None,'modifiers':[m.type for m in o.modifiers]}
 if o.type!='MESH':continue
 for m in o.data.materials:
  if m.name in r['assetMaterials']:continue
  nt=m.node_tree;active=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'].links[0].from_node
  ramp=[]
  for n in nt.nodes:
   if n.type=='VALTORGB':ramp.append({'name':n.name,'interpolation':n.color_ramp.interpolation,'elements':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]})
  r['assetMaterials'][m.name]={'materialAnimation':bool(m.animation_data),'nodeTreeAnimation':bool(nt.animation_data),'images':[{'node':n.name,'image':n.image.name if n.image else None} for n in nt.nodes if n.type=='TEX_IMAGE'],'activeSurface':active.name,'activeType':active.type,'roughness':active.inputs['Roughness'].default_value,'specularIORLevel':active.inputs['Specular IOR Level'].default_value,'baseColorUpstream':[[l.from_node.name,l.from_socket.name] for l in active.inputs['Base Color'].links],'ramps':ramp}
(BASE/'evidence/extra-native-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print('EXTRA_AUDIT_COMPLETE')
