import bpy,json
p=bpy.data.objects['chef_ellis__ground_root.001__held_dish-salmon__image_plane'];r=bpy.data.objects['chef_ellis__ground_root.001']
print('PLANE',json.dumps({'vertices':[list(v.co) for v in p.data.vertices],'UV':[list(x.uv) for x in p.data.uv_layers.active.data],'matrix':[list(x) for x in p.matrix_world],'loc':list(p.location),'rot':list(p.rotation_euler),'scale':list(p.scale),'props':{k:str(p[k]) for k in p.keys()}}))
print('ROOTFOOD',r['held_food_source']);print('FOODCOMP',r['food_composition'])
for m in p.data.materials:
 print('MAT',m.name,[(n.name,n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else None) for n in m.node_tree.nodes])
for im in bpy.data.images:
 print('IMAGE',im.name,list(im.size),im.alpha_mode,im.colorspace_settings.name,im.filepath,bool(im.packed_file))
