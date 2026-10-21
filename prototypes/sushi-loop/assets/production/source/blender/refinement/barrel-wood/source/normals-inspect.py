import bpy
for name in ['barrel-wood__bulging_stave_10','barrel-wood__iron_band_0.67']:
 o=bpy.data.objects[name];print(name,'custom',o.data.has_custom_normals,'smooth',[p.use_smooth for p in o.data.polygons]);print('normals',[list(n.vector) for n in o.data.corner_normals][:20]);print('bevel',[(m.name,m.type,getattr(m,'harden_normals',None)) for m in o.modifiers])
