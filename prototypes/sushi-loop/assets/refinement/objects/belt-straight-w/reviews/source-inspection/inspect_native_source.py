import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

EXP=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
BRIEF=json.loads((EXP/'brief.json').read_text())
SOURCE=(EXP/BRIEF['source']['project']).resolve()
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
COL=bpy.data.collections.get('S33_FB_belt-straight-w.001')
assert COL, [x.name for x in bpy.data.collections if 'belt-straight-w' in x.name]
SC=next(s for s in bpy.data.scenes if COL in list(s.collection.children_recursive))
bpy.context.window.scene=SC
ROOT=bpy.data.objects['belt-straight-w__root.001']
raw_camera={'name':SC.camera.name if SC.camera else None,'matrix': [list(x) for x in SC.camera.matrix_world] if SC.camera else None,'ortho': SC.camera.data.ortho_scale if SC.camera else None,'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y]}
before={'collectionHideViewport':COL.hide_viewport,'collectionHideRender':COL.hide_render,'rootRotation':list(ROOT.rotation_euler),'objects':{o.name:{'viewport':o.hide_viewport,'render':o.hide_render,'hideGet':o.hide_get()} for o in COL.all_objects}}
for c in bpy.data.collections: c.hide_viewport=False; c.hide_render=False
def unhide_layer(lc):
    lc.exclude=False; lc.hide_viewport=False
    for child in lc.children: unhide_layer(child)
for vl in SC.view_layers: unhide_layer(vl.layer_collection)
for o in SC.objects: o.hide_viewport=False; o.hide_render=False; o.hide_set(False)
ROOT.rotation_euler.z=0
bpy.context.view_layer.update()
DG=bpy.context.evaluated_depsgraph_get(); DG.update()
objects=[]
allpts=[]
for o in COL.all_objects:
    record={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotationEuler':list(o.rotation_euler),'scale':list(o.scale),'matrixWorld':[list(x) for x in o.matrix_world],'properties':{k:o[k] for k in o.keys()}}
    if o.type=='MESH':
        eo=o.evaluated_get(DG); mesh=eo.to_mesh()
        pts=[eo.matrix_world@v.co for v in mesh.vertices]; allpts.extend(pts)
        record.update(verticesLocal=[list(v.co) for v in o.data.vertices],verticesWorld=[list(p) for p in pts],faces=[list(p.vertices) for p in o.data.polygons],materials=[m.name if m else None for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type} for m in o.modifiers],uv={uv.name:[list(v.uv) for v in uv.data] for uv in o.data.uv_layers})
        record['bounds']=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
        record['endProfilesX']={str(x):[list(p) for p in pts if abs(p.x-x)<1e-6] for x in (-.5,.5)}
        eo.to_mesh_clear()
    objects.append(record)
rig=json.loads((EXP/'inputs/source-rig.json').read_text())
action_bindings=[]
for target in rig['clips']['running']['actions']:
    owner=bpy.data.materials[target['materialOwnerName']].node_tree
    action=bpy.data.actions[target['action']]
    owner.animation_data_create()
    original_assignment=owner.animation_data.action.name if owner.animation_data.action else None
    owner.animation_data.action=action
    owner.animation_data.action_slot=next(s for s in action.slots if s.identifier==target['slotIdentifier'])
    action_bindings.append({'ownerMaterial':target['materialOwnerName'],'originalAssignment':original_assignment,'assignedAction':action.name,'assignedSlot':owner.animation_data.action_slot.identifier})
materials=[]
for mat in {m for o in COL.all_objects if o.type=='MESH' for m in o.data.materials if m}:
    nt=mat.node_tree; anim=nt.animation_data
    nodes=[]
    for n in nt.nodes:
        row={'name':n.name,'type':n.bl_idname,'inputs':{f'{i}:{s.name}':list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value for i,s in enumerate(n.inputs) if hasattr(s,'default_value')}}
        if n.type=='VALUE':row['value']=n.outputs[0].default_value
        for k in ('operation','vector_type','texture_mapping','uv_map'):
            if hasattr(n,k) and isinstance(getattr(n,k),(str,int,float,bool)): row[k]=getattr(n,k)
        nodes.append(row)
    action=anim.action if anim else None
    curves=[]
    if action:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for fc in bag.fcurves:curves.append({'path':fc.data_path,'index':fc.array_index,'keys':[{'frame':k.co.x,'value':k.co.y,'interpolation':k.interpolation} for k in fc.keyframe_points]})
    phases=[]
    for f in range(1,26):SC.frame_set(f);DG.update();phases.append(nt.nodes['Value'].outputs[0].default_value if nt.nodes.get('Value') else None)
    materials.append({'name':mat.name,'nodeTree':nt.name,'action':action.name if action else None,'slot':anim.action_slot.identifier if anim and anim.action_slot else None,'curves':curves,'phasesFrames1through25':phases,'nodes':nodes,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in nt.links]})

# Reconstruct the authoritative registered record in memory, without saving source.
CM=json.loads((EXP/'inputs/source-camera.json').read_text()); CA=CM['camera']
SC.render.resolution_x=384;SC.render.resolution_y=704;SC.render.resolution_percentage=100
SC.render.pixel_aspect_x=CA['pixelAspect'][0];SC.render.pixel_aspect_y=CA['pixelAspect'][1]
CAM=bpy.data.objects.new('Judge_registered_W_camera',bpy.data.cameras.new('Judge_registered_W_camera'))
SC.collection.objects.link(CAM);SC.camera=CAM;CAM.data.type='ORTHO';CAM.data.sensor_fit='AUTO'
FAM=json.loads((EXP/'inputs/family-settings.json').read_text())
CAM.data.ortho_scale=FAM['capture']['orthoScale'];CAM.data.shift_x=FAM['capture']['shift'][0];CAM.data.shift_y=FAM['capture']['shift'][1]
CAM.matrix_world=Matrix(CA['worldMatrix']);bpy.context.view_layer.update();DG.update()
def px(v):
    p=world_to_camera_view(SC,CAM,Vector(v));return [p.x*384,(1-p.y)*704]
origin=px((0,0,0)); proj=lambda v:[(p-o)/2 for p,o in zip(px(v),origin)]
# Source UV.x is incoming0 -> outgoing1: derive world endpoints from actual UV mesh.
deck=next(o for o in COL.all_objects if o.type=='MESH' and 'connected_straight_deck' in o.name)
uv=deck.data.uv_layers.active
uv_world=[{'world':list(deck.matrix_world@deck.data.vertices[loop.vertex_index].co),'uv':list(uv.data[i].uv)} for i,loop in enumerate(deck.data.loops)]
endpoints={}
for key,u in [('incoming',0),('outgoing',1)]:
    ps=[Vector(x['world']) for x in uv_world if abs(x['uv'][0]-u)<1e-6]
    endpoints[key]=sum(ps,Vector())/len(ps)
portviews={}
for direction,degrees in {'S':0,'E':90,'N':180,'W':-90}.items():
    ROOT.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();DG.update()
    r=Matrix.Rotation(math.radians(degrees),3,'Z')
    portviews[direction]={key:{'world':list(r@v),'logicalRootRelative':proj(r@v)} for key,v in endpoints.items()}
ROOT.rotation_euler.z=0;bpy.context.view_layer.update();DG.update()
SC.frame_set(1)
inspection={'sourcePath':str(SOURCE),'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'collection':COL.name,'scene':SC.name,'rawActiveCameraNotAuthoritative':raw_camera,'beforeUnhide':before,'unhideProcedure':'All collection viewport/render, all layer exclusions/viewport and all object viewport/render/hide_set cleared in headless memory; depsgraph explicitly updated before measurement. No source save.','boundsAtPublisherS':[[min(p[i] for p in allpts) for i in range(3)],[max(p[i] for p in allpts) for i in range(3)]],'objects':objects,'materials':materials,'deckUVWorldLoopsAtPublisherS':uv_world,'intrinsicEndpointsAtPublisherS':{k:list(v) for k,v in endpoints.items()},'derivedPortsByPublisherFacing':portviews,'registeredCamera':{'matrix':[list(x) for x in CAM.matrix_world],'projectionMatrix':[list(x) for x in CAM.calc_matrix_camera(DG,x=384,y=704,scale_x=SC.render.pixel_aspect_x,scale_y=SC.render.pixel_aspect_y)],'originSourceScale2':origin,'unitXSourceScale2':[v-o for v,o in zip(px((1,0,0)),origin)],'unitDepthSourceScale2':[v-o for v,o in zip(px((0,-1,0)),origin)],'unitHeightSourceScale2':[v-o for v,o in zip(px((0,0,1)),origin)]},'resources':{'images':[{'name':im.name,'source':im.source,'filepath':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE'],'libraries':[{'name':lib.name,'filepath':lib.filepath} for lib in bpy.data.libraries]}}
inspection['sourceRigActionBindings']=action_bindings
(OUT/'native-source-inspection.json').write_text(json.dumps(inspection,indent=2,default=str)+'\n')
print('JUDGE_NATIVE_SOURCE_INSPECTION',str(OUT/'native-source-inspection.json'))
