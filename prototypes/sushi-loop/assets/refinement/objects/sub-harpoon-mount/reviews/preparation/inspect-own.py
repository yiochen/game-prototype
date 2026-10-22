import bpy, json, os
from mathutils import Vector
out=os.path.dirname(__file__)
bpy.context.view_layer.update()
cols=[c for c in bpy.data.collections if 'harpoon_mount' in c.name]
def clean(x):
    if isinstance(x,(str,int,float,bool)):return x
    try:return list(x)
    except:return str(x)
records=[]
for c in cols:
    osr=[]
    for o in c.all_objects:
        rr={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'scale':list(o.scale),'rotationEuler':list(o.rotation_euler),'matrixWorld':[list(r) for r in o.matrix_world],'custom':{k:clean(o[k]) for k in o.keys()}}
        if o.type=='MESH':
            rr['verts']=len(o.data.vertices);rr['polygons']=len(o.data.polygons);rr['materials']=[m.name if m else None for m in o.data.materials]
            rr['worldBounds']=[[min((o.matrix_world@v.co)[i] for v in o.data.vertices) for i in range(3)],[max((o.matrix_world@v.co)[i] for v in o.data.vertices) for i in range(3)]]
        osr.append(rr)
    records.append({'name':c.name,'custom':{k:clean(c[k]) for k in c.keys()},'objects':osr})
actions=[]
for a in bpy.data.actions:
    if 'sub-harpoon-mount' not in a.name:continue
    rr={'name':a.name,'slots':[{'identifier':s.identifier,'handle':s.handle} for s in a.slots],'frameRange':list(a.frame_range),'curves':[]}
    for lay in a.layers:
      for strip in lay.strips:
       for slot in a.slots:
        try: bag=strip.channelbag(slot)
        except: continue
        if bag:
         for fc in bag.fcurves:
          rr['curves'].append({'path':fc.data_path,'index':fc.array_index,'keys':[[*k.co] for k in fc.keyframe_points],'interpolation':[k.interpolation for k in fc.keyframe_points]})
    actions.append(rr)
json.dump({'blend':bpy.data.filepath,'blender':bpy.app.version_string,'collections':records,'actions':actions},open(os.path.join(out,'own-native-inventory.json'),'w'),indent=2)
