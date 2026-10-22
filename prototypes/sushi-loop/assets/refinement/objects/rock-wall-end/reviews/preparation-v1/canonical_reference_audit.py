"""Read/render exact approved-middle source and an ephemeral end/middle assembly.
Run Blender -b resources/approved-middle/project.blend --python this_file.py.
No source saving or authoring recipes are executed.
"""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parent;RES=OUT/'resources';DEST=OUT/'canonical-baseline';DEST.mkdir(exist_ok=True)
sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['rock-wall-middle__root'];coll=bpy.data.collections['rock-wall-middle__asset']
side=bpy.data.objects['rock-wall-middle__continuous_carved_stone'];me=side.data
root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def vv(p):return [float(v) for v in p]
loops={}
for i,l in enumerate(me.loops):loops.setdefault(l.vertex_index,[]).append(i)
ports={}
for sign in [-1,1]:
 samples=[]
 for v in me.vertices:
  if abs(v.co.x-sign*.5)<1e-7:
   ns=[me.corner_normals[i].vector for i in loops[v.index]]
   n=sum((Vector(n) for n in ns),Vector())/len(ns)
   samples.append({'y':v.co.y,'z':v.co.z,'colorLinearRGBA':vv(me.color_attributes['stone_albedo'].data[v.index].color),'cornerNormals':[vv(n) for n in ns],'meanCornerNormal':vv(n)})
 ports['W' if sign<0 else 'E']=sorted(samples,key=lambda v:(v['y'],v['z']))
(OUT/'canonical-port-samples.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256((RES/'approved-middle/project.blend').read_bytes()).hexdigest(),'mesh':side.name,'meaning':'Actual per-vertex side boundary samples. E aligns end W after middle center -1 and end center0. Equal profile/normal/material at cut; sampling density is descriptive and may be interpolated without geometric/material discontinuity.','samples':ports},indent=2)+'\n')
audit={'scene':sc.name,'sourceSHA256':hashlib.sha256((RES/'approved-middle/project.blend').read_bytes()).hexdigest(),'sourceUntouched':True,'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'camera':{'matrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in [0,1]]},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'denoising':sc.cycles.use_denoising,'pixelFilter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'seed':sc.cycles.seed,'dither':sc.render.dither_intensity,'compositor':sc.use_nodes,'view':sc.view_settings.view_transform,'look':sc.view_settings.look},'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'hasCustomNormals':o.data.has_custom_normals,'materials':[m.name for m in o.data.materials]} for o in coll.objects if o.type=='MESH'],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'angle':o.data.angle,'shadow':o.data.use_shadow,'matrix':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],'worldStrength':next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value,'resources':{'images':[{'name':i.name,'type':i.source,'path':i.filepath} for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]},'views':{}}
for face,deg in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(DEST/f'middle-native-{face}.png');bpy.ops.render.render(write_still=True)
 audit['views'][face]={'rotationDegrees':deg,'root':px((0,0,0)),'render':f'canonical-baseline/middle-native-{face}.png'}
# Join sources in the same symmetric canonical lighting. This is a geometry/material
# diagnostic, distinct from original-material/original-light source captures.
root.rotation_euler.z=0
with bpy.data.libraries.load(str(RES/'original-source.blend'),link=False) as (src,dst):dst.collections=['S33_PROP_rock-wall-end.001']
endcoll=dst.collections[0];sc.collection.children.link(endcoll);endcoll.hide_render=False;endcoll.hide_viewport=False
eroot=next(o for o in endcoll.all_objects if o.type=='EMPTY' and 'root' in o.name)
for ob in endcoll.all_objects:ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
assembly=bpy.data.objects.new('diagnostic-assembly-root',None);sc.collection.objects.link(assembly)
root.parent=assembly;eroot.parent=assembly;root.location=(-.5,0,0);eroot.location=(.5,0,0);eroot.rotation_euler=(0,0,0);eroot.scale=(1,1,1)
# Only the exact middle exterior side and west cap contribute to the connected scene.
bpy.data.objects['rock-wall-middle__E_connector_stone'].hide_render=True
sc.render.resolution_x=1280;sc.render.resolution_y=1920;cam.data.ortho_scale=2.5
def setroot(target):
 for _ in range(2):
  base=px((0,0,0));old=cam.data.shift_y;cam.data.shift_y=old+1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-base[1];cam.data.shift_y=old+(target-base[1])/delta;bpy.context.view_layer.update()
setroot(1280)
audit['assembly']={'purpose':'new diagnostic only: original end material/geometry in approved-middle camera/light; not source replay nor candidate','middleRootLocal':[-.5,0,0],'endRootLocal':[.5,0,0],'connectorCenter':[0,0,0],'cellPitchNative':512,'frame':[1280,1920],'assemblyRoot':px((0,0,0)),'internalMiddleEastCapHidden':True,'endCoreUnchanged':True,'noAddedOverlap':True,'views':{}}
for face,deg in {'S':0,'E':90,'N':180,'W':-90}.items():
 assembly.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(DEST/f'joined-native-{face}.png');bpy.ops.render.render(write_still=True);audit['assembly']['views'][face]={'rotationDegrees':deg,'render':f'canonical-baseline/joined-native-{face}.png'}
(OUT/'canonical-reference-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('CANONICAL_REFERENCE_DONE')
