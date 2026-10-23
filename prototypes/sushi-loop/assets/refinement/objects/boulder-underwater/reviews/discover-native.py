import bpy,json,hashlib,sys,math
from pathlib import Path
p=Path(bpy.data.filepath)
root=bpy.data.objects.get('S33 production concept cobalt-crags root')
assert root, 'No named boulder root'
parts=[]
def descend(o):
 for child in o.children:
  parts.append(child);descend(child)
descend(root)
bpy.context.view_layer.update()
def mtx(m):return [[float(x) for x in r] for r in m]
def bounds(objs):
 pts=[o.matrix_world@v.co for o in objs if o.type=='MESH' for v in o.data.vertices]
 lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
 return {'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}
r={'project':str(p),'projectSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'groundRoot':{'name':root.name,'matrixWorld':mtx(root.matrix_world),'location':list(root.location),'scale':list(root.scale),'rotationEuler':list(root.rotation_euler),'customProperties':{k:str(root[k]) for k in root.keys()}},'physicalBounds':bounds(parts),'parts':[],'assetCollections':[{'name':c.name,'objects':len(c.all_objects)} for c in root.users_collection],'scenes':[],'externalResources':{'images':[{'name':im.name,'filepath':im.filepath,'packed':bool(im.packed_file),'source':im.source} for im in bpy.data.images if im.source=='FILE'],'libraries':[l.filepath for l in bpy.data.libraries]}}
for o in parts:
 r['parts'].append({'name':o.name,'type':o.type,'matrixWorld':mtx(o.matrix_world),'bounds':bounds([o]) if o.type=='MESH' else None,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None,'modifiers':[{'type':x.type,'name':x.name} for x in o.modifiers],'materialSlots':[x.material.name if x.material else None for x in o.material_slots],'customProperties':{k:str(o[k]) for k in o.keys()}})
for s in bpy.data.scenes:
 if root.name not in s.objects:continue
 r['scenes'].append({'name':s.name,'activeCamera':s.camera.name if s.camera else None,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'cameras':[{'name':o.name,'type':o.data.type,'orthographicScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],'matrixWorld':mtx(o.matrix_world)} for o in s.objects if o.type=='CAMERA']})
out=Path(sys.argv[sys.argv.index('--')+1]);out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
