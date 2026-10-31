"""Blender 5.2 native cabinet variant; preserve original camera, world and five balanced lights.
Run: Blender --background backups/original.blend --threads 4 --python source/recipe-draft01.py
"""
import bpy,bmesh,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent; EXP=HERE.parent
ROUND='draft-01'; OUT=EXP/'candidates'/ROUND; OUT.mkdir(exist_ok=True,parents=True)
scene=bpy.context.scene; cam=scene.camera
source=json.loads((HERE/'independent-inspection.json').read_text())
root=bpy.data.objects['garbage-shelving__root']
for ob in list(bpy.data.objects):
 if ob not in [root,cam] and ob.type!='LIGHT':bpy.data.objects.remove(ob,do_unlink=True)
root.animation_data_clear();root.rotation_euler=(0,0,0);root.location=(0,0,0);root.scale=(1,1,1)
root['asset']='garbage-cabinet';root['modelingPolicy']='Authorized 2x1 squat broken sideboard variant, static four facings'
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
for ma in list(bpy.data.materials):
 if ma.users==0:bpy.data.materials.remove(ma)
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def color(h):return tuple(srgb(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def mat(name,h,rough=.55,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=color(h);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color(h);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Specular IOR Level'].default_value=.22;return m
def wood(name,cols,axis='X'):
 m=mat(name,cols[1],.52);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');sc=n.new('ShaderNodeVectorMath');sc.operation='MULTIPLY';sc.inputs[1].default_value={'X':(.75,3.5,2),'Y':(3.5,.75,2),'Z':(3.5,3.5,.7)}[axis];l.new(tc.outputs['Generated'],sc.inputs[0]);no=n.new('ShaderNodeTexNoise');no.inputs['Scale'].default_value=1.9;no.inputs['Detail'].default_value=1.4;no.inputs['Roughness'].default_value=.6;l.new(sc.outputs['Vector'],no.inputs['Vector']);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements.remove(r.color_ramp.elements[1]);r.color_ramp.elements[0].position=.23;r.color_ramp.elements[0].color=color(cols[0]);r.color_ramp.elements.new(.52).color=color(cols[1]);r.color_ramp.elements.new(.78).color=color(cols[2]);l.new(no.outputs['Fac'],r.inputs['Fac']);l.new(r.outputs['Color'],p.inputs['Base Color']);return m
woodmain=wood('Honey oak horizontal',['AE6626','CC8734','DA9B45']);woodalt=wood('Honey oak top neighboring board',['AF6727','D18C39','E0A34E']);woodpost=wood('Honey oak upright',['9F5924','BD7630','D59644'],'Z');woodside=wood('Honey oak side panel',['A16029','BF7D33','D59846'],'Y');interior=wood('Cabinet interior warm oak',['89562B','AD783C','BD8A4C'])
edge=mat('Soft worn honey wood edges','D99A4B',.44);end=mat('Upright warm endgrain','C3853D',.6);grain=mat('Sparse native wood grain','A7652C',.7)
metal=mat('Graphite iron fittings','454B4D',.38,.65);metalEdge=mat('Rounded restrained iron highlights','7C8584',.3,.7);olive=mat('Muted olive storage carton','777B48',.8);tan=mat('Worn tan storage carton','AE8D5D',.8);tape=mat('Faded linen packing tape','C4AE85',.85)
parts=[]
def mesh(name,vs,fs,ma):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(ma);me.update();o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.parent=root;parts.append(o);return o
def finish(o,bev=.014,edgeMa=None):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 if edgeMa:o.data.materials.append(edgeMa)
 if bev:
  m=o.modifiers.new('Real softened edges','BEVEL');m.width=bev;m.segments=3;m.limit_method='ANGLE';m.harden_normals=True
  if edgeMa:m.material=1
 for p in o.data.polygons:p.use_smooth=True
 m=o.modifiers.new('Stable broad face normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=50
 return o
def cube(name,loc,dims,ma,bev=.014,ed=edge):
 x,y,z=[v/2 for v in dims];vs=[(a*x+loc[0],b*y+loc[1],c*z+loc[2]) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]];fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)];return finish(mesh(name,vs,fs,ma),bev,ed)
def curve(name,coords,rad=.0015,ma=grain):
 c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=1;c.bevel_depth=rad;c.bevel_resolution=2;s=c.splines.new('POLY');s.points.add(len(coords)-1)
 for p,v in zip(s.points,coords):p.co=(*v,1)
 o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.data.materials.append(ma);o.parent=root;parts.append(o);return o
def sphere(name,loc,r,ma,scale=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=r,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma);o.parent=root;parts.append(o)
 for p in o.data.polygons:p.use_smooth=True
 return o
def plank(j):
 yc=(j-1)*.306;length=1.95;width=.298;t=.125;xs=[-.975,-.88,-.6,-.25,.12,.47,.72,.89,.975];N=len(xs);vs=[]
 for side in [-1,1]:
  for i,x in enumerate(xs):
   yy=yc+side*width/2
   if side==-1 and j==0 and i==6: yy+=.065
   if side==1 and j==1 and i==7:yy-=.045
   zz=1.10+.004*math.sin(x*4+j)-.008*(1-(x/.975)**2)
   vs.extend([(x,yy,zz-t/2),(x,yy,zz+t/2)])
 fs=[]
 for i in range(N-1):
  a=2*i;b=2*(i+1);c=2*(N+i);d=2*(N+i+1);fs.extend([(a,c,d,b),(a+1,b+1,d+1,c+1),(a,b,b+1,a+1),(c+1,d+1,d,c)])
 fs.extend([(0,1,2*N+1,2*N),(2*(N-1),2*(2*N-1),2*(2*N-1)+1,2*(N-1)+1)])
 finish(mesh('Top broad plank %s'%j,vs,fs,woodmain if j!=1 else woodalt),.016,edge)
 for lane in range(2):
  pts=[]
  for i in range(29):
   x=-.83+i*1.66/28;y=yc+(lane-.5)*.10+.008*math.sin(x*6+j*2);z=1.10+t/2+.004*math.sin(x*4+j)-.008*(1-(x/.975)**2)+.0005;pts.append((x,y,z))
  curve('Top sparse grain %s-%s'%(j,lane),pts,.0014)
for j in range(3):plank(j)
# Four short, broad wood feet with true horizontal z=0 contact.
for x in[-.78,.78]:
 for y in[-.25,.25]:cube('Short grounded foot',(x,y,.11),(.18,.19,.22),woodpost,.013,end)
# Low enclosed carcase: open front only, no ground plane or detached scrap.
cube('Thick lower storage sill',(0,0,.255),(1.79,.74,.13),woodmain,.018)
for x in[-.84,.84]:
 cube('Cabinet side substantial panel',(x,.015,.65),(.13,.69,.68),woodside,.015,end)
 for y in[-.29,.31]:cube('Side corner upright',(x,y,.65),(.16,.13,.72),woodpost,.013,end)
# Closed rear has restrained plank divisions and rails.
for i in range(5):cube('Rear oak panel %s'%i,((i-2)*.322,.342,.65),(.316,.07,.65),woodpost,.009,end)
for z in [.34,.97]:cube('Rear horizontal frame',(0,.376,z),(1.64,.068,.095),woodmain,.012)
cube('Front upper cabinet rail',(0,-.29,.982),(1.72,.11,.10),woodmain,.013)
cube('Interior center shelf',(0,.04,.325),(1.50,.60,.055),interior,.010,end)
# Hinged doors are distinct native assemblies. Local pivots preserve plausible hinge contact.
def door_transform(ob,pivot,rz,ry=0):
 M=Matrix.Translation(Vector(pivot))@Matrix.Rotation(rz,4,'Z')@Matrix.Rotation(ry,4,'Y')
 for v in ob.data.vertices:v.co=M@v.co
 return ob
left=[]
# Left attached crooked leaf, low free edge and small opening angle inside footprint.
for x in [.06,.60]:left.append(cube('Left door substantial stile',(x,0,0),(.105,.085,.66),woodpost,.014,end))
for z in[-.27,.27]:left.append(cube('Left door horizontal rail',(.33,-.004,z),(.46,.105,.10),woodmain,.014))
for i in range(3):
 x=.172+i*.158;left.append(cube('Left door inset panel %s'%i,(x,.012,0),(.153,.054,.46),woodpost,.008,end))
for ob in left:door_transform(ob,(-.83,-.27,.606),math.radians(-16),math.radians(7))
for z in [.36,.80]:
 # Hinges are attached to carcase outer stile, with restrained raised hardware.
 cube('Attached left iron hinge',(-.825,-.339,z),(.067,.045,.115),metal,.012,metalEdge)
p=Vector((.548,-.068,-.05));M=Matrix.Translation(Vector((-.83,-.27,.606)))@Matrix.Rotation(math.radians(-16),4,'Z')@Matrix.Rotation(math.radians(7),4,'Y');sphere('Left round iron knob',M@p,.043,metalEdge,(1,.58,1))
# Right region: still attached at the outer hinges, crooked board-built leaf with localized break.
right=[]
for x in[-.625,-.055]:right.append(cube('Right door slanted stile',(x,0,0),(.08,.082,.64),woodpost,.012,end))
for z in[-.268,.268]:right.append(cube('Right door worn crossrail',(-.34,.016,z),(.49,.071,.082),woodmain,.012))
for i in range(3):
 x=-.49+i*.17;z=.015 if i!=0 else .09;h=.50 if i!=0 else .35
 ob=cube('Right damaged vertical board %s'%i,(x,-.03,z),(.158,.075,h),woodpost,.01,end);right.append(ob)
for ob in right:door_transform(ob,(.83,-.27,.60),math.radians(13),math.radians(-6))
for z in [.36,.80]:cube('Attached right iron hinge',(.83,-.335,z),(.060,.04,.108),metal,.011,metalEdge)
p=Vector((-.15,-.09,-.01));M=Matrix.Translation(Vector((.83,-.27,.60)))@Matrix.Rotation(math.radians(13),4,'Z')@Matrix.Rotation(math.radians(-6),4,'Y');sphere('Right round iron knob',M@p,.044,metalEdge,(1,.58,1))
# Subdued partly visible parcels in exposed central storage cavity, no loose outside debris.
def carton(name,loc,dims,ma):
 cube(name,loc,dims,ma,.015,tape);x,y,z=loc;w,d,h=dims
 cube(name+' top tape',(x,y,z+h/2+.001),(.065,d-.02,.004),tape,.002,None);cube(name+' front tape',(x,y-d/2-.002,z),(.065,.004,h-.02),tape,.002,None)
carton('Interior tan parcel',(-.02,-.03,.54),(.30,.36,.38),tan)
carton('Interior olive small parcel',(-.08,-.235,.415),(.31,.21,.20),olive)
carton('Rear muted parcel',(.37,.10,.49),(.26,.26,.30),tan)
# Sparse native vertical grain on front doors; recessed-looking tone and very low relief.
# Keep all capture/light/color settings inherited. CPU bounded process; no changed camera fitting.
scene.render.threads_mode='FIXED';scene.render.threads=4
scene.frame_set(1);root.rotation_euler.z=0;bpy.context.view_layer.update()
for me in list(bpy.data.meshes):
 if me.users==0:bpy.data.meshes.remove(me)
for ma in list(bpy.data.materials):
 if ma.users==0:bpy.data.materials.remove(ma)
# Convert curves to editable geometry, apply real bevels and normals for portable exact model.
for ob in parts:
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 if ob.type=='CURVE':bpy.ops.object.convert(target='MESH')
 for mo in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mo.name)
 bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/(ROUND+'.blend')),compress=True)
def matrix(m):return [list(r) for r in m]
def camera_record():
 dg=bpy.context.evaluated_depsgraph_get();p=lambda v:world_to_camera_view(scene,cam,Vector(v));r=p((0,0,0))
 return {'matrixWorld':matrix(cam.matrix_world),'projection':matrix(cam.calc_matrix_camera(dg,x=896,y=1344,scale_x=scene.render.pixel_aspect_x,scale_y=scene.render.pixel_aspect_y)),'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'sensorFit':cam.data.sensor_fit,'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'frame':[scene.render.resolution_x,scene.render.resolution_y],'rootPixel':[r.x*896,(1-r.y)*1344]}
D={'blender':bpy.app.version_string,'sourceInspection':'independent-inspection.json','camera':camera_record(),'lights':[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'matrix':matrix(o.matrix_world)} for o in scene.objects if o.type=='LIGHT'],'views':{},'objects':[{'name':o.name,'type':o.type,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in parts],'resources':{'images':len(bpy.data.images),'libraries':len(bpy.data.libraries),'allMaterialsNativeNodes':True}}
for facing,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=angle;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();vs=[];local=[]
 for ob in parts:
  eo=ob.evaluated_get(dg);me=eo.to_mesh();vs.extend([eo.matrix_world@v.co for v in me.vertices]);local.extend([root.matrix_world.inverted()@eo.matrix_world@v.co for v in me.vertices]);eo.to_mesh_clear()
 ps=[world_to_camera_view(scene,cam,v) for v in vs]
 D['views'][facing]={'rootMatrix':matrix(root.matrix_world),'rootLocation':list(root.location),'rootScale':list(root.scale),'worldMin':[min(v[i] for v in vs) for i in range(3)],'worldMax':[max(v[i] for v in vs) for i in range(3)],'localMin':[min(v[i] for v in local) for i in range(3)],'localMax':[max(v[i] for v in local) for i in range(3)],'projectedBounds':[min(v.x*896 for v in ps),min((1-v.y)*1344 for v in ps),max(v.x*896 for v in ps),max((1-v.y)*1344 for v in ps)]}
 scene.render.filepath=str(OUT/(facing+'.png'));bpy.ops.render.render(write_still=True)
(OUT/'native-measurements.json').write_text(json.dumps(D,indent=2)+'\n')
print('CABINET_FINISHED',OUT)
