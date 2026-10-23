import bpy, json, math
from pathlib import Path
from mathutils import Vector
BASE=Path(__file__).resolve().parents[1]
def rows(x): return [list(v) for v in x]
def obj(o):
    d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'worldMatrix':rows(o.matrix_world),'hideRender':o.hide_render,'properties':dict(o.items())}
    if o.type=='MESH':
        d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),materials=[m.name if m else None for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],bounds=[list(o.matrix_world@Vector(v)) for v in o.bound_box])
    return d
assets=[]
for sc in bpy.data.scenes:
    matched=[o for o in sc.objects if 'stool_wood' in o.name]
    if not matched: continue
    cam=sc.camera
    assets.append({'scene':sc.name,'properties':dict(sc.items()),'render':{'engine':sc.render.engine,'resolution':[sc.render.resolution_x,sc.render.resolution_y,sc.render.resolution_percentage],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'transparent':sc.render.film_transparent},'camera':{'name':cam.name,'matrix':rows(cam.matrix_world),'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit} if cam else None,'objects':[obj(o) for o in matched],'lights':[dict(obj(o),energy=o.data.energy,color=list(o.data.color),shape=getattr(o.data,'shape',None),size=getattr(o.data,'size',None)) for o in sc.objects if o.type=='LIGHT']})
out={'blender':bpy.app.version_string,'filepath':bpy.data.filepath,'scenes':assets,'materials':[]}
for m in bpy.data.materials:
    if m.name not in {n for a in assets for o in a['objects'] for n in o.get('materials',[])}:continue
    out['materials'].append({'name':m.name,'diffuse':list(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value')},'operation':getattr(n,'operation',None)} for n in m.node_tree.nodes] if m.node_tree else []})
(BASE/'source/source-inspection.json').write_text(json.dumps(out,indent=2,default=str))
print(json.dumps(out,indent=2,default=str))
