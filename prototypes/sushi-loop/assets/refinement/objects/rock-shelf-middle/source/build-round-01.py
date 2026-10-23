"""Canonical low shelf: native geometry/material/rig and reproducible all4 captures.
Run /opt/homebrew/bin/blender -b -P build-round-01.py -- [preview|capture].
No original or reviewed preparation file is modified. No external texture dependency.
"""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;EXP=BASE.parent;OUT=EXP/'candidates'/'round-01';OUT.mkdir(parents=True,exist_ok=True)
MODE=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'preview'
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.name='rock-shelf-middle native round-01'
coll=bpy.data.collections.new('rock-shelf-middle canonical LOW shelf');s.collection.children.link(coll)
root=bpy.data.objects.new('rock-shelf-middle__root',None);coll.objects.link(root)
root['asset']='rock-shelf-middle';root['ports']='W X=-0.5; E X=+0.5; finite six point section-v1';root['clip']='static';root['frames']=1;root['fps']=12;root['loop']=False
# Native crown plate grooves. End bands are constant geometry/albedo/normal fields.
def smooth(a,b,t):
 t=max(0,min(1,(t-a)/(b-a)));return t*t*(3-2*t)
def taper(x):return 1-smooth(.34,.42,abs(x))
def segdist(x,y,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)));return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy)
lines=[[(-.44,.17),(-.28,.12),(-.10,.035),(.10,-.04),(.27,-.15),(.44,-.19)],[(-.17,.39),(-.13,.22),(-.10,.035)],[(.10,-.04),(.24,.16),(.27,.39)],[(-.44,-.22),(-.25,-.17),(-.12,-.27),(-.08,-.39)]]
def crown(x,y):
 w=taper(x);d=min(segdist(x,y,a,b) for line in lines for a,b in zip(line,line[1:]))
 broad=.008*math.sin(8*x+2*y)*math.sin(6*y-2*x)+.008*math.cos(5*x-7*y)+.003
 groove=.027*math.exp(-(d/.022)**2)
 # Two embedded low pebble seats; flattened stone accents cannot exceed .45.
 bowl=.030*math.exp(-(((x+.27)/.10)**2+((y-.27)/.10)**2)*2)+.028*math.exp(-(((x-.28)/.095)**2+((y+.27)/.09)**2)*2)
 z=.43+w*(broad-groove-bowl)
 return min(.449,z),d,w
verts=[];faces=[];normals=[];colors=[];facekind=[]
def color_at(x,y,z,kind='body'):
 h=max(0,min(1,z/.43));base=(.052+.028*h,.19+.22*h,.39+.25*h)
 if kind=='body':
  sidecut=math.exp(-((z-(.14+.025*math.sin(x*8)))/.018)**2)*taper(x)
  shade=1-.21*sidecut;base=tuple(v*shade for v in base)
 if kind=='top':
  zz,d,w=crown(x,y);shade=1-.22*math.exp(-(d/.024)**2)*w
  shift=.03*math.sin(x*12+y*8)*w
  base=(.07+shift*.5,.40+shift*.6,.65+shift*.2);base=tuple(c*shade for c in base)
 return (*base,1)
def V(p,kind='body'):
 verts.append(p);colors.append(color_at(*p,kind));return len(verts)-1
def F(v,kind='body'):
 faces.append(v);facekind.append(kind)
# Grid top (x and y native positions fixed; no perview operation).
xs=[-.42+i*.84/88 for i in range(89)];ys=[-.39+j*.78/78 for j in range(79)]
grid=[[V((x,y,crown(x,y)[0]),'top') for y in ys] for x in xs]
for i in range(88):
 for j in range(78):F([grid[i][j],grid[i+1][j],grid[i+1][j+1],grid[i][j+1]],'top')
# Ring around cross-section: base -Y, base+Y, vertical+Y and shoulder, top+Y, top-Y, shoulder-Y.
# 33 points along the five non-top profile edges; no extra endpoint vertices.
sections=[(-.45,0),(.45,0)]
for k in range(1,9):sections.append((.45,.28*k/8))
for k in range(1,9):sections.append((.45-.06*k/8,.28+.15*k/8))
# No separate top span; reuse top-grid boundaries.
for k in range(1,9):sections.append((-.39-.06*k/8,.43-.15*k/8))
for k in range(1,8):sections.append((-.45,.28*(1-k/8)))
rings=[]
for i,x in enumerate(xs):
 ring=[]
 for q,(y,z) in enumerate(sections):
  if q==17:ring.append(grid[i][-1]);continue
  if q==18:pass
  # subtly rounded, broad side courses, attenuated to exactly constant endpoint bands.
  sign=1 if y>0 else -1
  yy=y
  if z>0 and z<.43:
   yy-=sign*taper(x)*math.sin(math.pi*z/.43)**2*(.009*(.6+.4*math.cos(13*x+3*z))+.015*math.exp(-((z-(.14+.025*math.sin(x*8)))/.022)**2))
  # top edge on -Y is q18? connect via explicit below (section sequence after +Ytop skips -Ytop).
  ring.append(V((x,yy,z)))
 rings.append(ring)
# sections: [0base-Y,1base+Y,2..9vertical+,10..17shoulder+top,18..25shoulder-minus,26..32vertical-minus]
# Insert reused -Y top before q18, then side faces close bottom.
for i,ring in enumerate(rings):ring.insert(18,grid[i][0])
for i in range(88):
 for q in range(len(rings[i])):
  if q==17:continue # top surface is grid
  q2=(q+1)%len(rings[i]);F([rings[i][q],rings[i+1][q],rings[i+1][q2],rings[i][q2]],'body')
# Correct outward winding (current top grid +Z; side path is CCW looking +X, x strips require reverse).
for k,kind in enumerate(facekind):
 if kind=='body':faces[k]=list(reversed(faces[k]))
# True endpoint caps have exactly six vertices. Transition ngons preserve all collinear inner samples.
profile=[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]
# Inner ring index breakpoints corresponding to canonical profile; +Ytop17,-Ytop18, -Yshoulder26.
indices=[0,1,9,17,18,26]
for end,x,ri in [('W',-.5,0),('E',.5,88)]:
 cap=[V((x,y,z),'top' if z==.43 else 'body') for y,z in profile]
 mid=[V((math.copysign(.44,x),y,z),'top' if z==.43 else 'body') for y,z in profile]
 F(cap if end=='E' else list(reversed(cap)),'cap')
 for q in range(6):
  band=[cap[q],cap[(q+1)%6],mid[(q+1)%6],mid[q]]
  if end=='W':band=list(reversed(band))
  F(band,'top' if q==3 else 'body')
 inner=rings[ri]
 for q in range(6):
  a=indices[q];b=indices[(q+1)%6]
  if q==3:seq=list(reversed(grid[ri])) # +Y to -Y
  else:
   seq=[];k=a
   while True:
    seq.append(inner[k])
    if k==b:break
    k=(k+1)%len(inner)
  vv=[mid[q],mid[(q+1)%6]]+list(reversed(seq))
  # path cap profile positive normal +X; side from W->inner uses reversed profile.
  if end=='W':vv=list(reversed(vv))
  F(vv,'top' if q==3 else 'body')
mesh=bpy.data.meshes.new('rock-shelf-middle sculpted continuous low core');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('rock-shelf-middle__sculpted_core',mesh);coll.objects.link(o);o.parent=root
# Recalculate outward mesh normals. Cap vertices are isolated from smoothed exposed surfaces by custom corner normals.
import bmesh
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free();mesh.update()
attribute=mesh.color_attributes.new(name='rock_shelf_albedo',type='FLOAT_COLOR',domain='POINT')
for i,col in enumerate(colors):attribute.data[i].color=col
for p,kind in zip(mesh.polygons,facekind):p.use_smooth=kind!='cap'
# Compute geometric smooth normals on exposed faces only. Endcaps do not bend the crown or side band.
def native_normal(vi,kind,pnormal):
 x,y,z=verts[vi]
 if kind=='cap':return pnormal
 if pnormal.z<-.9:return Vector((0,0,-1))
 if kind=='top':
  e=.0001;dx=(crown(x+e,y)[0]-crown(x-e,y)[0])/(2*e);dy=(crown(x,y+e)[0]-crown(x,y-e)[0])/(2*e)
  # A broad rounded shoulder normal, preserved identically at both endpoint bands.
  dy-=(1-taper(x))*(.35/.94)*y/.39+taper(x)*math.copysign(.37*smooth(.35,.39,abs(y)),y)
  return Vector((-dx,-dy,1)).normalized()
 if z>=.28:
  t=max(0,min(1,(z-.28)/.15));return Vector((0,math.copysign(1-.65*t,y),.94*t)).normalized()
 return Vector((0,math.copysign(1,y),0))
custom=[]
for p,kind in zip(mesh.polygons,facekind):
 for vi in p.vertices:custom.append(tuple(native_normal(vi,kind,p.normal)))
mesh.normals_split_custom_set(custom)
# Native private shader. Material albedo is vertex authored, retained as an inspectable point attribute.
m=bpy.data.materials.new('rock-shelf-middle canonical blue cyan stone v1');m.use_nodes=True
n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
a=n.new('ShaderNodeAttribute');a.attribute_name='rock_shelf_albedo';l.new(a.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.40;bs.inputs['Specular IOR Level'].default_value=.24;bs.inputs['Coat Weight'].default_value=.12;bs.inputs['Coat Roughness'].default_value=.35
mesh.materials.append(m)
# Flattened native embedded pebble forms. Actual maxZ below .45; attached, not floating.
def pebble(name,cx,cy,rx,ry,h,color):
 zbase=crown(cx,cy)[0]-.007
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,radius=1,location=(cx,cy,zbase))
 ob=bpy.context.object;ob.name=name
 for c in list(ob.users_collection):c.objects.unlink(ob)
 coll.objects.link(ob);ob.parent=root
 ob.scale=(rx,ry,h);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for v in ob.data.vertices:
  # native asymmetric gently faceted flattening
  v.co.x*=1+.04*math.sin(v.co.y*83);v.co.z=min(v.co.z,.449-zbase)
 for p in ob.data.polygons:p.use_smooth=True
 pm=bpy.data.materials.new(name+' private blue-lavender stone');pm.use_nodes=True;ps=pm.node_tree.nodes.get('Principled BSDF');ps.inputs['Base Color'].default_value=(*color,1);ps.inputs['Roughness'].default_value=.32;ps.inputs['Specular IOR Level'].default_value=.28
 ob.data.materials.append(pm)
 return ob
pebble('rock-shelf-middle__embedded_stone_A',-.27,.27,.067,.060,.043,(.11,.27,.48))
pebble('rock-shelf-middle__embedded_stone_B',.28,-.27,.065,.054,.042,(.12,.31,.48))
pebble('rock-shelf-middle__embedded_chip',.187,-.273,.025,.024,.012,(.06,.28,.42))
# Symmetric broad finite area rig. One rig for all4 single and joined captures.
rig=bpy.data.collections.new('rock-shelf-middle private symmetric native rig');s.collection.children.link(rig)
def light(name,power,loc,size,target):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
 ob=bpy.data.objects.new(name,data);rig.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
light('shelf broad centered overhead',1200,(0,0,18),15,(0,0,0))
for x,y in [(15,0),(0,15),(-15,0),(0,-15)]:light('shelf symmetric cardinal '+str((x,y)),1250,(x,y,9),12,(0,0,.2))
s.world=bpy.data.worlds.new('shelf transparent zero-strength world');s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=32;s.render.filter_size=.5;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.image_settings.compression=20;s.render.dither_intensity=0;s.render.fps=12;s.frame_start=s.frame_end=1;s.frame_set(1)
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
# Frozen RGB grade cloned before use; alpha bypasses grade.
import importlib.util
spec=importlib.util.spec_from_file_location('private_frozen_grade',BASE/'resources/catalog_style.py');style=importlib.util.module_from_spec(spec);spec.loader.exec_module(style);style.ensure_compositor(s)
cam=bpy.data.objects.new('rock-shelf-middle registered55.0079798 camera',bpy.data.cameras.new('registered orthographic'));rig.objects.link(cam);s.camera=cam

def camera(frame,anchor,scale=4):
 s.render.resolution_x=frame[0]*scale;s.render.resolution_y=frame[1]*scale;s.render.resolution_percentage=100;s.render.pixel_aspect_x=math.sqrt(1+.7*.7);s.render.pixel_aspect_y=1
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(s,cam,Vector(v));return Vector((p.x*s.render.resolution_x,(1-p.y)*s.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
 origin=px((0,0,0));record={'frame':list(frame),'anchor':list(anchor),'scale':scale,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'elevationDegrees':math.degrees(el),'orthoScale':cam.data.ortho_scale,'worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=s.render.resolution_x,y=s.render.resolution_y,scale_x=s.render.pixel_aspect_x,scale_y=s.render.pixel_aspect_y)],'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)}}
 assert (origin-Vector((anchor[0]*scale,anchor[1]*scale))).length<.05
 return record
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
record=camera((192,352),(96,248));root.rotation_euler.z=0;bpy.context.view_layer.update()
# Store native recipe text inside .blend and explicit JSON metadata. No linked or packed unrelated assets.
t=bpy.data.texts.new('build-round-01.py');t.write(Path(__file__).read_text())
s['publication']='native filter0.5; uniform whole-frame BOX4x-to2x';s['asset']='rock-shelf-middle';s['static']=True;s['loop']=False
if MODE=='preview':
 s.render.filepath=str(OUT/'working-S.png');bpy.ops.render.render(write_still=True)
else:
 # Editable standalone save precedes capture assembly; source retains only private asset/rig.
 bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'round-01.blend'),compress=True)
 (OUT/'camera-single.json').write_text(json.dumps(record,indent=2))
 for d,angle in angles.items():
  root.rotation_euler.z=angle;bpy.context.view_layer.update();record=camera((192,352),(96,248));s.render.filepath=str(OUT/f'native-{d}-4x.png');bpy.ops.render.render(write_still=True);(OUT/f'camera-{d}.json').write_text(json.dumps(record,indent=2))
 root.rotation_euler.z=0;bpy.context.view_layer.update()
 assembly=bpy.data.collections.new('capture_only_3middle_strip');s.collection.children.link(assembly);ar=bpy.data.objects.new('capture_only_strip_root',None);assembly.objects.link(ar)
 for offset in (-1,0,1):
  for original in list(coll.objects):
   if original.type!='MESH':continue
   ob=original.copy();ob.data=original.data;assembly.objects.link(ob);ob.parent=ar;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=original.matrix_world.copy();ob.location.x+=offset
 coll.hide_render=True
 for d,angle in angles.items():
  ar.rotation_euler.z=angle;bpy.context.view_layer.update();record=camera((448,608),(224,376));s.render.filepath=str(OUT/f'native-strip-{d}-4x.png');bpy.ops.render.render(write_still=True);(OUT/f'camera-strip-{d}.json').write_text(json.dumps(record,indent=2))
 print('ALL4 NATIVE CAPTURE COMPLETE')
