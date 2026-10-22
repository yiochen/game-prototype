import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
O=Path(__file__).resolve().parent;R=O/'resources';D=O/'replay';D.mkdir(exist_ok=True)
# First measure the actual immutable canonical endpoint, independent of editor intent tables.
bpy.ops.wm.open_mainfile(filepath=str(R/'canonical-middle.blend'))
me=bpy.data.objects['rock-wall-middle__continuous_carved_stone'].data
loops={}
for lp in me.loops:loops.setdefault(lp.vertex_index,lp.index)
canon={}
for sign,label in [(-.5,'W'),(.5,'E')]:
 pts=[v for v in me.vertices if abs(v.co.x-sign)<1e-7]
 canon[label]=[{'p':list(v.co),'c':list(me.color_attributes['stone_albedo'].data[v.index].color),'n':list(me.corner_normals[loops[v.index]].vector)} for v in pts]
def nearest(y,z,port):
 best=None;pts=canon['E' if port=='W' else 'W']
 for a,b in zip(pts,pts[1:]+pts[:1]):
  ay,az=a['p'][1:];by,bz=b['p'][1:];dy,dz=by-ay,bz-az;l=dy*dy+dz*dz;t=max(0,min(1,((y-ay)*dy+(z-az)*dz)/l)) if l else 0;dist=math.hypot(y-ay-dy*t,z-az-dz*t)
  if best is None or dist<best[0]:best=(dist,a,b,t)
 dist,a,b,t=best;c=[(1-t)*a['c'][i]+t*b['c'][i] for i in range(4)];n=Vector([(1-t)*a['n'][i]+t*b['n'][i] for i in range(3)]);n.normalize()
 if port=='N':n=Vector((-n.y,n.x,n.z))
 return dist,c,n
bpy.ops.wm.open_mainfile(filepath=str(R/'round-05.blend'));sc=bpy.context.scene;root=bpy.data.objects['rock-wall-corner__root'];col=bpy.data.collections['rock-wall-corner__asset'];cam=sc.camera;root.rotation_euler.z=0;sc.frame_set(1);bpy.context.view_layer.update()
objects=[];allpts=[];boundary=[]
for ob in col.all_objects:
 d={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'modifiers':[m.type for m in ob.modifiers]}
 if ob.type=='MESH':
  me=ob.data;pts=[ob.matrix_world@v.co for v in me.vertices];allpts+=pts;d.update(vertices=len(pts),faces=len(me.polygons),smoothFaces=sum(f.use_smooth for f in me.polygons),bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],materials=[m.name for m in me.materials])
  # Actual border loops along a port; do not compare internal cap surfaces to the outer profile.
  for poly in me.polygons:
   for li in poly.loop_indices:
    lp=me.loops[li];v=me.vertices[lp.vertex_index].co
    for port in ['W','N']:
     on=lambda p:abs(p.x+.5)<1e-7 if port=='W' else abs(p.y-.5)<1e-7
     if 'connector' in ob.name or 'support' in ob.name or not on(v):continue
     if not any(i!=lp.vertex_index and on(me.vertices[i].co) for i in poly.vertices):continue
     dist,c,n=nearest(v.y if port=='W' else -v.x,v.z,port);actual=Vector(me.corner_normals[li].vector);color=me.color_attributes['stone_albedo'].data[lp.vertex_index].color
     boundary.append({'mesh':ob.name,'port':port,'vertex':lp.vertex_index,'p':list(v),'profileDistance':dist,'albedoMaxDelta':max(abs(color[i]-c[i]) for i in range(4)),'loopNormalDelta':(actual-n).length})
 objects.append(d)
# Compact unique boundary sample residuals; source loops are measured directly above.
unique={}
for x in boundary:
 key=(x['mesh'],x['port'],x['vertex']);old=unique.get(key)
 if old is None or x['loopNormalDelta']>old['loopNormalDelta']:unique[key]=x
boundary=list(unique.values())
mat=next(ob.data.materials[0] for ob in col.all_objects if ob.type=='MESH');nt=mat.node_tree;p=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
def px(v):
 q=world_to_camera_view(sc,cam,Vector(v));return [q.x*sc.render.resolution_x,(1-q.y)*sc.render.resolution_y]
report={'sourceSHA256':hashlib.sha256((R/'round-05.blend').read_bytes()).hexdigest(),'scene':sc.name,'rootMatrix':[list(r) for r in root.matrix_world],'objects':objects,'bounds':[[min(p[i] for p in allpts) for i in range(3)],[max(p[i] for p in allpts) for i in range(3)]],'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'frame':[sc.render.resolution_x,sc.render.resolution_y],'basis':{k:(px(v) if k=='root' else [px(v)[i]-px((0,0,0))[i] for i in [0,1]]) for k,v in [('root',(0,0,0)),('X',(1,0,0)),('depth',(0,-1,0)),('height',(0,0,1))]}},'render':{'engine':sc.render.engine,'samples':sc.cycles.samples,'seed':sc.cycles.seed,'filter':sc.cycles.pixel_filter_type,'storedFilterSize':sc.render.filter_size,'denoise':sc.cycles.use_denoising,'compositor':sc.compositing_node_group.name if sc.compositing_node_group else None,'viewTransform':sc.view_settings.view_transform,'fps':sc.render.fps,'frameRange':[sc.frame_start,sc.frame_end]},'material':{'nodes':[(n.type,n.name) for n in nt.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in nt.links],'roughness':p.inputs['Roughness'].default_value,'specular':p.inputs['Specular IOR Level'].default_value,'emission':p.inputs['Emission Strength'].default_value},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'useShadow':o.data.use_shadow,'rotation':list(o.rotation_euler)} for o in sc.objects if o.type=='LIGHT'],'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[i.filepath for i in bpy.data.images if i.source!='VIEWER'],'actions':len(bpy.data.actions)},'boundarySamples':boundary,'views':{}}
sc.render.threads_mode='FIXED';sc.render.threads=4
for d,deg in {'N':180,'E':90,'S':0,'W':-90}.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update();sc.render.filepath=str(D/f'native-static-{d}.png');bpy.ops.render.render(write_still=True);report['views'][d]={'matrix':[list(r) for r in root.matrix_world],'rootPixel':px((0,0,0))}
(O/'native-independent-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('INDEPENDENT_AUDIT_REPLAY_DONE')
