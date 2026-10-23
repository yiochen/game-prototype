"""Render-only reopen validation. Never executes authoring recipe or saves source.
blender -b source/round-02.blend --python source/render-only-replay.py
"""
import bpy,json,math,hashlib,struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'candidates/round-02/replay';OUT.mkdir(exist_ok=True)
sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['rock-wall-end__root'];coll=bpy.data.collections['rock-wall-end__asset'];project=BASE/'source/round-02.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def record():
 return {'frame':[sc.render.resolution_x,sc.render.resolution_y],'camera':{'type':cam.data.type,'worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'calibration':{'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in [0,1]]}},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'denoising':sc.cycles.use_denoising,'pixelFilter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'dither':sc.render.dither_intensity,'transparent':sc.render.film_transparent,'compositor':sc.use_nodes,'fps':sc.render.fps,'frame':sc.frame_current},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'shadow':o.data.use_shadow,'angle':o.data.angle,'matrix':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],'worldStrength':next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value}
root.rotation_euler=(0,0,0);bpy.context.view_layer.update();audit={'asset':'rock-wall-end','projectSHA256Before':sha(project),'renderOnly':True,'authoringRecipeExecuted':False,'sceneSaved':False,'actual':record(),'views':{},'materials':[],'topology':[],'resourceClosure':{}}
usedm={m for o in coll.objects if o.type=='MESH' for m in o.data.materials}
for m in usedm:
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');audit['materials'].append({'name':m.name,'nodes':[{'type':n.type,'name':n.name,'attribute':getattr(n,'layer_name',None)} for n in m.node_tree.nodes],'links':[{'fromNode':l.from_node.name,'fromSocket':l.from_socket.name,'toNode':l.to_node.name,'toSocket':l.to_socket.name} for l in m.node_tree.links],'roughness':p.inputs['Roughness'].default_value,'specularIORLevel':p.inputs['Specular IOR Level'].default_value,'emissionStrength':p.inputs['Emission Strength'].default_value})
for ob in coll.objects:
 if ob.type!='MESH':continue
 me=ob.data;edges={};degenerate=0;reversed_count=0
 for p in me.polygons:
  if p.area<1e-12:degenerate+=1
  ids=list(p.vertices)
  for i in range(len(ids)):
   key=tuple(sorted([ids[i],ids[(i+1)%len(ids)]]));edges[key]=edges.get(key,0)+1
  # Side outward expected from cross-section; cap side expected by name.
  n=p.normal;c=p.center
  expected=(n.x if 'finished_E' in ob.name else -n.x if 'W_connector' in ob.name else n.y*c.y+n.z*(c.z-.55))
  if expected < -.02:reversed_count+=1
 audit['topology'].append({'name':ob.name,'vertices':len(me.vertices),'polygons':len(me.polygons),'zeroAreaFaces':degenerate,'boundaryEdges':sum(c==1 for c in edges.values()),'edgesWithMoreThanTwoFaces':sum(c>2 for c in edges.values()),'outwardHeuristicNegativeFaces':reversed_count,'note':'Separate side and cap surface borders coincide geometrically; heuristic includes valid carved grooves and is diagnostic, not a winding certificate.','coordinateSHA256':hashlib.sha256(b''.join(struct.pack('fff',*v.co) for v in me.vertices)).hexdigest(),'customNormals':me.has_custom_normals,'uvLayers':[u.name for u in me.uv_layers]})
audit['resourceClosure']={'usedImageTextureNodes':[{'material':m.name,'node':n.name,'image':n.image.name if n.image else None} for m in usedm for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],'images':[{'name':i.name,'source':i.source,'filepath':i.filepath,'packed':bool(i.packed_file)} for i in bpy.data.images if i.type!='RENDER_RESULT'],'libraries':[l.filepath for l in bpy.data.libraries],'actions':[a.name for a in bpy.data.actions],'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'],'sceneMeshes':[o.name for o in sc.objects if o.type=='MESH'],'targetCardAbsent':not any(n.type=='TEX_IMAGE' for m in usedm for n in m.node_tree.nodes),'sourceIsStandalone':len([o for o in sc.objects if o.type=='MESH'])==3}
for direction,degrees in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(degrees);bpy.context.view_layer.update();p=OUT/f'native-{direction}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 audit['views'][direction]={'direction':direction,'rootRotationZ':root.rotation_euler.z,'rootRotationDegrees':math.degrees(root.rotation_euler.z),'actualRootMatrix':[list(r) for r in root.matrix_world],'rootPx':px((0,0,0)),'path':str(p.relative_to(BASE))}
audit['projectSHA256After']=sha(project);assert audit['projectSHA256Before']==audit['projectSHA256After']
(OUT/'replay-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('END_RENDER_ONLY_REPLAY_DONE')
