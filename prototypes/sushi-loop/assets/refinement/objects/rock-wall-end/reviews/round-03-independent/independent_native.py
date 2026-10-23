import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(__file__).resolve().parent;BASE=OUT/'resources/experiment';DEST=OUT/'native-replay';DEST.mkdir(exist_ok=True)
project=BASE/'source/round-03.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sc=bpy.context.scene;cam=sc.camera;root=bpy.data.objects['rock-wall-end__root'];coll=bpy.data.collections['rock-wall-end__asset']
root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
def px(p):
 q=world_to_camera_view(sc,cam,Vector(p));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
def samples(ob,plane):
 me=ob.data;loops={}
 for i,l in enumerate(me.loops):loops.setdefault(l.vertex_index,[]).append(i)
 rows=[]
 for v in me.vertices:
  if abs(v.co.x-plane)<1e-7:
   ns=[me.corner_normals[i].vector for i in loops[v.index]];n=sum((Vector(n) for n in ns),Vector())/len(ns)
   rows.append({'y':v.co.y,'z':v.co.z,'color':list(me.color_attributes['stone_albedo'].data[v.index].color),'normal':list(n)})
 return rows
side=bpy.data.objects['rock-wall-end__continuous_worn_cobalt'];west=samples(side,-.5)
meshes=[o for o in coll.objects if o.type=='MESH'];vs=[o.matrix_world@v.co for o in meshes for v in o.data.vertices]
bm=bmesh.new()
for o in meshes:bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.normal_update()
bottom=[f for f in bm.faces if all(abs(v.co.z)<1e-8 for v in f.verts)]
closure={'vertices':len(bm.verts),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'wireEdges':sum(e.is_wire for e in bm.edges),'nonTwoFaceEdges':sum(len(e.link_faces)!=2 for e in bm.edges),'inconsistentWindingEdges':sum(len(e.link_faces)==2 and not e.is_contiguous for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-12 for f in bm.faces),'signedVolume':bm.calc_volume(signed=True),'bottomFaceCount':len(bottom),'bottomSurfaceArea':sum(f.calc_area() for f in bottom),'bottomBounds':{'min':[min(v.co[i] for f in bottom for v in f.verts) for i in range(3)],'max':[max(v.co[i] for f in bottom for v in f.verts) for i in range(3)]}}
bm.free()
materials=[]
for m in {m for o in meshes for m in o.data.materials}:
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');materials.append({'name':m.name,'nodes':[n.type for n in m.node_tree.nodes],'roughness':p.inputs['Roughness'].default_value,'specular':p.inputs['Specular IOR Level'].default_value,'emission':p.inputs['Emission Strength'].default_value,'links':[(l.from_node.type,l.from_socket.name,l.to_node.type,l.to_socket.name) for l in m.node_tree.links]})
audit={'candidateSHA256Before':sha(project),'rootMatrix':[list(r) for r in root.matrix_world],'bounds':{'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)]},'closure':closure,'camera':{'matrix':[list(r) for r in cam.matrix_world],'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'root':px((0,0,0)),'unitX':[px((1,0,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitDepth':[px((0,-1,0))[i]-px((0,0,0))[i] for i in [0,1]],'unitHeight':[px((0,0,1))[i]-px((0,0,0))[i] for i in [0,1]]},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'denoising':sc.cycles.use_denoising,'filter':sc.cycles.pixel_filter_type,'filterWidth':sc.cycles.filter_width,'view':sc.view_settings.view_transform,'look':sc.view_settings.look,'exposure':sc.view_settings.exposure,'gamma':sc.view_settings.gamma,'transparent':sc.render.film_transparent,'dither':sc.render.dither_intensity,'compositorGroup':sc.compositing_node_group.name if sc.compositing_node_group else None},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'angle':o.data.angle,'shadow':o.data.use_shadow,'matrix':[list(r) for r in o.matrix_world]} for o in sc.objects if o.type=='LIGHT'],'worldStrength':next(n for n in sc.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value,'materials':materials,'timing':{'fps':sc.render.fps,'frame':sc.frame_current,'actions':[a.name for a in bpy.data.actions],'armatures':[o.name for o in sc.objects if o.type=='ARMATURE'],'shapeKeys':[o.name for o in meshes if o.data.shape_keys]},'resources':{'images':[(i.name,i.source,i.filepath) for i in bpy.data.images if i.type!='RENDER_RESULT'],'libraries':[l.filepath for l in bpy.data.libraries],'modifiers':{o.name:[m.type for m in o.modifiers] for o in meshes}},'views':{}}
# Append only the canonical collection to measure its real E port; then remove it.
with bpy.data.libraries.load(str(BASE/'inputs/approved-middle/project.blend'),link=False) as(src,dst):dst.collections=['rock-wall-middle__asset']
mc=dst.collections[0];ms=next(o for o in mc.objects if 'continuous_carved' in o.name);canonical=samples(ms,.5)
rows=[]
for a in west:
 b=min(canonical,key=lambda b:(a['y']-b['y'])**2+(a['z']-b['z'])**2)
 rows.append({'positionDelta':math.hypot(a['y']-b['y'],a['z']-b['z']),'albedoDelta':max(abs(a['color'][i]-b['color'][i]) for i in range(4)),'normalDelta':(Vector(a['normal'])-Vector(b['normal'])).length})
audit['mandatoryWestToCanonicalE']={'count':len(rows),'planeMin':min(v.co.x for v in side.data.vertices),'maxProfileDelta':max(r['positionDelta'] for r in rows),'maxAlbedoDelta':max(r['albedoDelta'] for r in rows),'maxMeanLoopNormalDelta':max(r['normalDelta'] for r in rows),'canonicalSHA256':sha(BASE/'inputs/approved-middle/project.blend')}
for o in list(mc.objects):bpy.data.objects.remove(o,do_unlink=True)
bpy.data.collections.remove(mc)
for d,deg in {'N':180,'E':90,'S':0,'W':-90}.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(DEST/f'native-{d}.png');bpy.ops.render.render(write_still=True);audit['views'][d]={'rotationDegrees':math.degrees(root.rotation_euler.z),'rootMatrix':[list(r) for r in root.matrix_world],'rootPixel':px((0,0,0))}
audit['candidateSHA256After']=sha(project)
(OUT/'independent-native-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print('JUDGE_NATIVE_DONE')
