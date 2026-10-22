import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
H=Path(__file__).resolve().parent;O=H.parents[1]/'candidates/stage1-v6';bpy.ops.wm.open_mainfile(filepath=str(H/'submarine-stage1.blend'));s=bpy.context.scene;c=s.camera;r=bpy.data.objects['submarine-yellow__root'];bpy.context.view_layer.update()
def vv(x):return [float(v) for v in x]
def px(p):
 q=world_to_camera_view(s,c,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
p0=Vector(px((0,0,0)))
record={'sourceSHA256':hashlib.sha256((H/'submarine-stage1.blend').read_bytes()).hexdigest(),'Blender':bpy.app.version_string,'savedActualEngine':s.render.engine,'savedActualSamples':s.eevee.taa_render_samples,'savedActualFilterSize':s.render.filter_size,'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filmTransparent':s.render.film_transparent,'fps':s.render.fps,'rootMatrix':[vv(x) for x in r.matrix_world],'nativeRoot':px((0,0,0)),'unitBasis':{n:vv(Vector(px(p))-p0) for n,p in [('X',(1,0,0)),('Y',(0,1,0)),('Z',(0,0,1))]},'cameraMatrix':[vv(x) for x in c.matrix_world],'orthoScale':c.data.ortho_scale,'shiftY':c.data.shift_y,'legacyReferences':{k:vv(bpy.data.objects[k].location) for k in ['sub_harpoon','sub_collector']},'actualMountLocalMatrices':{o.name:[vv(x) for x in o.matrix_local] for o in bpy.data.objects if o.name.startswith('MOUNT__')},'lighting':[{'name':o.name,'position':vv(o.location),'power':o.data.energy,'size':o.data.size,'type':o.data.type} for o in s.objects if o.type=='LIGHT'],'noGroundReceiver':not any(o.type=='MESH' and o.parent is None for o in s.objects),'colorManagement':{'transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma}}
(O/'reopened-source-settings.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
