"""Private native round01 runtime. No production imports or raster alterations."""
import bpy, math, json, hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

FACING={'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2}
ROOT='creature-fish__ground_root.001'
ARM='creature-fish__armature.001'
COLL='S33_CFX_creature-fish.001'

def apply(clip,frame=1,direction='S'):
    arm=bpy.data.objects[ARM];arm.animation_data_create()
    action=bpy.data.actions[f'S33_NATIVE__creature-fish__{clip}__creature-fish__armature.001']
    arm.animation_data.action=action
    arm.animation_data.action_slot=action.slots[0]
    root=bpy.data.objects[ROOT];root.rotation_euler=(0,0,FACING[direction])
    s=bpy.context.scene;s.frame_set(frame);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
    return arm,root

def mat(m):return [[float(x) for x in r] for r in m]
def bounds(p):return {'min':[min(v[i] for v in p) for i in range(3)],'max':[max(v[i] for v in p) for i in range(3)]}
def camera_record():
    s=bpy.context.scene;c=s.camera
    def px(v):
        q=world_to_camera_view(s,c,Vector(v));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
    p=px((0,0,0))
    return {'projection':'character-orthographic','frame':[448,512],'anchor':[224,352],'cellSize':128,'captureScale':4,'fps':12,
     'camera':{'type':'orthographic','orthoScale':c.data.ortho_scale,'sensorFit':c.data.sensor_fit,'shiftX':c.data.shift_x,'shiftY':c.data.shift_y,
      'worldMatrix':mat(c.matrix_world),'projectionMatrix':mat(c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=1,scale_y=1)),
      'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'worldUnitsPerCell':1,'elevationDegrees':35},
     'calibration':{'root':p,'unitX':[v-p[i] for i,v in enumerate(px((1,0,0)))],'unitDepth':[v-p[i] for i,v in enumerate(px((0,-1,0)))],'unitHeight':[v-p[i] for i,v in enumerate(px((0,0,1)))]}}

def measure(clip,frame,direction,include_vertices=False):
    arm,root=apply(clip,frame,direction);s=bpy.context.scene;dg=bpy.context.evaluated_depsgraph_get()
    raw=[];ev=[];rel=[];per=[];attachments={}
    for o in sorted(bpy.data.collections[COLL].all_objects,key=lambda o:o.name):
        if o.type!='MESH':continue
        rp=[o.matrix_world@v.co for v in o.data.vertices]
        e=o.evaluated_get(dg);m=e.to_mesh();ep=[e.matrix_world@v.co for v in m.vertices]
        loc=[arm.matrix_world.inverted()@p for p in ep]
        raw.extend(rp);ev.extend(ep);rel.extend(loc)
        per.append({'object':o.name,'rawAuthoredBounds':bounds(rp),'evaluatedModifierBounds':bounds(ep),'vertices':len(ep),
         'armatureOwner':arm.name,'parent':o.parent.name,'vertexGroups':[g.name for g in o.vertex_groups]})
        if any(x in o.name for x in ['eye','mouth','fin']):
            attachments[o.name]={'armatureRelativeCentroid':[sum(p[i] for p in loc)/len(loc) for i in range(3)],'weightsNormalized':all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in o.data.vertices),'sameArmatureModifier':any(mod.type=='ARMATURE' and mod.object==arm for mod in o.modifiers)}
        e.to_mesh_clear()
    projected=[world_to_camera_view(s,s.camera,p) for p in ev]
    row={'clip':clip,'direction':direction,'index':frame-1,'frame':frame,'closingKey':frame==13,
     'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':mat(root.matrix_world),
     'cameraMatrix':mat(s.camera.matrix_world),'camera':{'orthoScale':s.camera.data.ortho_scale,'sensorFit':s.camera.data.sensor_fit,'shiftX':s.camera.data.shift_x,'shiftY':s.camera.data.shift_y,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]},
     'rawAuthoredBounds':bounds(raw),'evaluatedModifierBounds':bounds(ev),'perObjectBounds':per,
     'armatureMatrix':mat(arm.matrix_world),'boneMatrices':{b.name:mat(b.matrix) for b in arm.pose.bones},
     'cameraBoundsNormalized':{'min':[min(p[i] for p in projected) for i in range(2)],'max':[max(p[i] for p in projected) for i in range(2)]},
     'socketsWorld':{k:list(root.matrix_world@Vector(v)) for k,v in json.loads(root['sockets']).items()},
     'effectiveOwnership':{'scene':s.name,'viewLayer':bpy.context.view_layer.name,'collection':COLL,'collectionHideViewport':bpy.data.collections[COLL].hide_viewport,'collectionHideRender':bpy.data.collections[COLL].hide_render,'visibleOwnedMeshes':len(per)},
     'attachmentStructuralChecks':attachments}
    if include_vertices:return row,rel
    return row
