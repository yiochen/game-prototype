import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parents[1];O=P/'reviews/round-01-native-replay';O.mkdir(exist_ok=True)
S=bpy.context.scene;R=next(o for o in S.objects if o.get('production_id')=='decor-foreground-rock');C=S.camera
M=[o for o in S.objects if o.type=='MESH'];D=bpy.context.evaluated_depsgraph_get()
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bounds(pts):return {'min':[min(p[i]for p in pts)for i in range(3)],'max':[max(p[i]for p in pts)for i in range(3)]}
def serial(v):
 if isinstance(v,(int,float,str,bool))or v is None:return v
 try:return [serial(i)for i in v]
 except:return str(v)
def nodegraph(tree):
 return {'nodes':[{'name':n.name,'type':n.bl_idname,'operation':getattr(n,'operation',None),'blendType':getattr(n,'blend_type',None),'inputs':[{'name':i.name,'value':serial(getattr(i,'default_value',None))}for i in n.inputs]}for n in tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name]for l in tree.links]}
def appearance():return {'materials':{m.name:nodegraph(m.node_tree)for o in M for m in o.data.materials if m and m.use_nodes},'world':nodegraph(S.world.node_tree),'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'matrixWorld':[list(r)for r in o.matrix_world],'size':getattr(o.data,'size',None)}for o in S.objects if o.type=='LIGHT'],'camera':{'matrix':[list(r)for r in C.matrix_world],'type':C.data.type,'orthoScale':C.data.ortho_scale,'sensorFit':C.data.sensor_fit,'shift':[C.data.shift_x,C.data.shift_y],'pixelAspect':[S.render.pixel_aspect_x,S.render.pixel_aspect_y]}}
def fingerprint():return hashlib.sha256(json.dumps(appearance(),sort_keys=True).encode()).hexdigest()
def px(v):
 p=world_to_camera_view(S,C,Vector(v));return [p.x*S.render.resolution_x,(1-p.y)*S.render.resolution_y]
bpy.context.view_layer.update();a=appearance();savedRoot=[list(r)for r in R.matrix_world];allpts=[];meshrows=[]
for o in M:
 e=o.evaluated_get(D);me=e.to_mesh();pts=[R.matrix_world.inverted()@o.matrix_world@v.co for v in me.vertices];allpts+=pts;bm=bmesh.new();bm.from_mesh(me)
 meshrows.append({'name':o.name,'parent':o.parent.name if o.parent else None,'evaluatedBounds':bounds(pts),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'looseVertices':sum(not v.link_faces for v in bm.verts),'faceCount':len(me.polygons),'vertexCount':len(me.vertices),'uvLayers':list(me.uv_layers.keys()),'shapeKeys':bool(o.data.shape_keys),'animationData':bool(o.animation_data),'modifierTypes':[m.type for m in o.modifiers]});bm.free();e.to_mesh_clear()
rec={'project':bpy.data.filepath,'projectSHA256':hashfile(Path(bpy.data.filepath)),'scene':S.name,'root':R.name,'rootProperties':{k:str(R[k])for k in R.keys()},'initialSavedRootMatrix':savedRoot,'rootLocalBounds':bounds(allpts),'meshes':meshrows,'camera':a['camera'],'cameraElevationDegrees':math.degrees(math.atan2(C.location.z,math.hypot(C.location.x,C.location.y))),'resolution':[S.render.resolution_x,S.render.resolution_y],'resolutionPercentage':S.render.resolution_percentage,'frameCurrent':S.frame_current,'fps':S.render.fps,'fpsBase':S.render.fps_base,'filmTransparent':S.render.film_transparent,'renderEngine':S.render.engine,'compositorEnabled':S.use_nodes,'sequencerEnabled':S.render.use_sequencer,'allObjectTypes':{o.name:o.type for o in S.objects},'worldAndMaterials':a,'externalLibraries':[l.filepath for l in bpy.data.libraries],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)}for i in bpy.data.images if i.type not in ['RENDER_RESULT','COMPOSITING']],'actions':list(bpy.data.actions.keys()),'armatures':list(bpy.data.armatures.keys()),'shapeKeys':list(bpy.data.shape_keys.keys()),'facings':{}}
origin=px((0,0,0));rec['calibration']={'root':origin,'unitX':[v-u for v,u in zip(px((1,0,0)),origin)],'unitDepth':[v-u for v,u in zip(px((0,-1,0)),origin)],'unitHeight':[v-u for v,u in zip(px((0,0,1)),origin)]}
f=fingerprint()
for direction,deg in [('N',180),('E',90),('S',0),('W',-90)]:
 R.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();S.render.filepath=str(O/f'static-{direction}.png');bpy.ops.render.render(write_still=True,scene=S.name)
 rec['facings'][direction]={'rootDegrees':deg,'appearanceCameraLightMaterialFingerprint':fingerprint(),'unchangedAppearanceCameraLightMaterial':fingerprint()==f,'render':str((O/f'static-{direction}.png').relative_to(P)),'renderSHA256':hashfile(O/f'static-{direction}.png')}
rec['sourceFileUnchanged']=hashfile(Path(bpy.data.filepath))==rec['projectSHA256'];(P/'reviews/round-01-native-audit.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps({'audit':str(P/'reviews/round-01-native-audit.json'),'sourceFileUnchanged':rec['sourceFileUnchanged'],'bounds':rec['rootLocalBounds'],'facings':rec['facings']},indent=2))
