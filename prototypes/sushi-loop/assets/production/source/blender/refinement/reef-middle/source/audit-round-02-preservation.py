import sys
sys.dont_write_bytecode=True
import bpy,json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'candidates/round-02'
def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def value(v):
    if isinstance(v,(str,int,float,bool)):return v
    try:return list(v)
    except TypeError:return str(v)
def extract(path):
    bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;bpy.context.view_layer.update();coral={};mats={}
    for o in bpy.data.collections['reef-middle'].objects:
        if o.type!='MESH' or not any(o.name.startswith('reef-middle__'+p) for p in ['teal_','purple_','cyan_pebble_']):continue
        data={'vertices':[list(v.co) for v in o.data.vertices],'polygons':[list(p.vertices) for p in o.data.polygons],'smooth':[p.use_smooth for p in o.data.polygons],'materialSlots':[m.name for m in o.data.materials],'materialIndices':[p.material_index for p in o.data.polygons],'matrix':[list(r) for r in o.matrix_world]}
        coral[o.name]={'dataSHA256':h(data),'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)}
        for m in o.data.materials:
            rec={'diffuseColor':list(m.diffuse_color),'nodes':[{'type':n.bl_idname,'name':n.name,'inputs':{s.identifier:value(s.default_value) for s in n.inputs if hasattr(s,'default_value')},'ramps':[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements] if n.type=='VALTORGB' else None} for n in m.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]}
            mats[m.name]=h(rec)
    lights=[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT']
    cam=sc.camera
    capture={'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shifts':[cam.data.shift_x,cam.data.shift_y],'frame':[sc.render.resolution_x,sc.render.resolution_y],'percentage':sc.render.resolution_percentage,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'filter':sc.render.filter_size,'fps':sc.render.fps,'frameCurrent':sc.frame_current,'viewTransform':sc.view_settings.view_transform,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma}
    return {'sourceSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'coralAndPebbleGeometry':coral,'coralAndPebbleMaterialGraphs':mats,'lighting':lights,'worldBackgroundInputs':{s.identifier:value(s.default_value) for s in sc.world.node_tree.nodes.get('Background').inputs if hasattr(s,'default_value')},'capture':capture}
old=extract(BASE/'round-01.blend');new=extract(BASE/'round-02.blend')
checks={'coralAndPebbleNativeGeometryPreserved':old['coralAndPebbleGeometry']==new['coralAndPebbleGeometry'],'coralAndPebbleNativeMaterialsPreserved':old['coralAndPebbleMaterialGraphs']==new['coralAndPebbleMaterialGraphs'],'actualLightRigPreserved':old['lighting']==new['lighting'],'worldBackgroundPreserved':old['worldBackgroundInputs']==new['worldBackgroundInputs'],'savedCameraRootFrameFilterAndColorManagementPreserved':old['capture']==new['capture']}
(OUT/'round-01-preservation.json').write_text(json.dumps({'method':'Fresh background Blender read-only open of both exact saved native projects, hashing actual mesh/transform/material data and comparing actual saved light/camera/filter fields. No source resaves.','round01':old,'round02':new,'checks':checks},indent=2)+'\n')
print(json.dumps(checks));assert all(checks.values())
