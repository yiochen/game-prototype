import bpy, json, pathlib, hashlib
P=pathlib.Path(__file__).resolve().parent
src=P.parent/'backups/original.blend'
bpy.ops.wm.open_mainfile(filepath=str(src))
def mat(m): return [[float(v) for v in row] for row in m]
records=[]
for sc in bpy.data.scenes:
    records.append({'name':sc.name,'objects':len(sc.objects),'camera':sc.camera.name if sc.camera else None,'render':{'engine':sc.render.engine,'size':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filmTransparent':sc.render.film_transparent},'roots':[{'name':o.name,'type':o.type,'matrix':mat(o.matrix_world)} for o in sc.objects if not o.parent],'objectsDetail':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'dimensions':list(o.dimensions),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)} for o in sc.objects]})
out={'sourceSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'scenes':records,'cameras':[{'name':o.name,'matrix':mat(o.matrix_world),'orthoScale':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y],'sensorFit':o.data.sensor_fit} for o in bpy.data.objects if o.type=='CAMERA'],'worlds':[{'name':w.name,'nodes':[{'name':n.name,'type':n.type} for n in w.node_tree.nodes]} for w in bpy.data.worlds if w.use_nodes]}
(P/'independent-inspection.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'scenes':[(s['name'],s['objects'],s['camera']) for s in records],'sourceSHA256':out['sourceSHA256'],'camera':out['cameras']},indent=2))
