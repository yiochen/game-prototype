"""Native crafted wreck END round 01. Canonical full-collar method derived from exact approved middle02; own terminal/interior rebuilt inside frozen own budget. Background Blender; no raster art or repair.
Usage: blender -b --factory-startup --python source/reproduce-round02.py [-- --output PATH --probe]
All dependencies are private sibling resources. The original source is retained for provenance, not modified.
"""
import bpy,math,json,hashlib,sys,argparse
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; BASE=HERE.parent; RES=HERE/'round01-resources'
parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(BASE/'candidates/round-01'));parser.add_argument('--probe',action='store_true');parser.add_argument('--recapture',action='store_true')
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=Path(args.output);OUT.mkdir(parents=True,exist_ok=True)
contract=json.loads((RES/'canonical/wreck-middle/root-native-contract.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,d:Path(p).write_text(json.dumps(d,indent=2)+'\n')
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
if not args.recapture:
 bpy.ops.wm.open_mainfile(filepath=str(RES/'canonical/wreck-middle/native.blend'))
 for c in list(bpy.context.scene.collection.children):
  for o in list(c.all_objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
 for m in list(bpy.data.materials):
  if m.users==0:bpy.data.materials.remove(m)
sc=bpy.context.scene;sc.name='Wreck end crafted native round01'
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.image_settings.compression=15
sc.render.film_transparent=True;sc.render.filter_size=.01;sc.render.dither_intensity=0;sc.render.fps=12;sc.frame_start=1;sc.frame_end=1;sc.frame_set(1)
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
if hasattr(sc,'eevee'):
 for n in ['taa_render_samples','taa_samples']:
  if hasattr(sc.eevee,n):setattr(sc.eevee,n,64);break
sc.render.use_persistent_data=True

def linear(v):return ((v+.055)/1.055)**2.4 if v>.04045 else v/12.92
def color(h):return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def material(name,h,rough=.65,metal=.03):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=color(h)
 nt=m.node_tree;nt.nodes.clear();o=nt.nodes.new('ShaderNodeOutputMaterial');bs=nt.nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;bs.inputs['Specular IOR Level'].default_value=.18
 geom=nt.nodes.new('ShaderNodeNewGeometry');sep=nt.nodes.new('ShaderNodeSeparateXYZ');r=nt.nodes.new('ShaderNodeMapRange');r.inputs['From Min'].default_value=.04;r.inputs['From Max'].default_value=.78;r.inputs['To Min'].default_value=.66;r.inputs['To Max'].default_value=1.03;r.clamp=True
 mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[1].default_value=color(h)
 nt.links.new(geom.outputs['Position'],sep.inputs[0]);nt.links.new(sep.outputs['Z'],r.inputs['Value']);nt.links.new(r.outputs['Result'],mul.inputs[2]);nt.links.new(mul.outputs[0],bs.inputs['Base Color']);nt.links.new(bs.outputs[0],o.inputs[0])
 return m
if not args.recapture:
 wood=material('Blue painted timber - canonical height albedo','168FE1',.62,.025)
 wood2=material('Blue painted timber - lower layered hue','1378CB',.68,.02)
 iron=material('Slate iron - canonical soft edge','344E69',.53,.16)
 ironedge=material('Soft worn iron bevels','718B96',.62,.10)
 pale=material('Pale worn metal fasteners','B6C7BA',.49,.2)
 wear=material('Restrained cream paint wear','C5CEAD',.78,.01)
 grain=material('Shallow blue grain grooves','1863A0',.83,0)
 col=bpy.data.collections.new('S33_PROP_wreck-end.001');sc.collection.children.link(col)
 root=bpy.data.objects.new('wreck-end__root.001',None);col.objects.link(root);root['asset_id']='wreck-end';root['visual_height']=.78;root['footprint']=[1,1];root['socket_names']=[]
 def mesh(name,vs,fs,mats,indices=None,normals=None):
  me=bpy.data.meshes.new(name+' mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root
  for m in mats:me.materials.append(m)
  if indices:
   for p,i in zip(me.polygons,indices):p.material_index=i
  if normals:
   for p in me.polygons:p.use_smooth=True
   me.normals_split_custom_set(normals)
  return o
 def smoothfade(x):
  t=max(0,min(1,(.42-abs(x))/.14));return t*t*t*(t*(t*6-15)+10)
 def profile(x,y0,y1,z0,z1,kind):
  f=smoothfade(x);r={'lower':.026,'upper':.023,'rear':.012}[kind]*f;k=.2928932188134524*r
  yc=(y0+y1)/2;zc=(z0+z1)/2
  p=[(y0,z0),(yc,z0),(y1,z0),(y1,zc),(y1,z1),(yc,z1),(y0,z1),(y0,zc)]
  for i in [0,2,4,6]:
   if kind=='lower' and i in [0,2]:continue
   y,z=p[i];p[i]=(y+(k if y==y0 else -k),z+(k if z==z0 else -k))
  crown=(.014 if kind=='lower' else .009 if kind=='upper' else .004)*f
  for i in [4,5,6]:p[i]=(p[i][0],p[i][1]+crown)
  return p
 def rail(kind,section):
  ring=section['authoredRingVertices'];y0,z0=ring[0][1:];y1,z1=ring[2][1:]
  xs=[-.5,-.42,-.39,-.35,-.28,-.16,0,.12,.2,.28,.34]
  profiles=[profile(x,y0,y1,z0,z1,kind) for x in xs];vs=[(x,y,z) for x,ps in zip(xs,profiles) for y,z in ps]
  fs=[];ns=[];mi=[]
  def normal(i,j,side):
   if abs(xs[i])>=.42:return [(0,0,-1),(0,0,-1),(0,1,0),(0,1,0),(0,0,1),(0,0,1),(0,-1,0),(0,-1,0)][side]
   ps=profiles[i];a=Vector(ps[side]);b=Vector(ps[(side+1)%8]);v=b-a;n=Vector((v.y,-v.x)).normalized()
   prev=Vector(ps[(j-1)%8]);cur=Vector(ps[j]);nxt=Vector(ps[(j+1)%8]);v1=cur-prev;v2=nxt-cur
   av=Vector((v1.y,-v1.x)).normalized()+Vector((v2.y,-v2.x)).normalized();av.normalize()
   f=smoothfade(xs[i]);n=(n*(1-f)+av*f).normalized()
   if kind=='lower' and side in [0,1]:n=Vector((0,-1))
   e=1e-5;pm=profile(xs[i]-e,y0,y1,z0,z1,kind)[j];pp=profile(xs[i]+e,y0,y1,z0,z1,kind)[j];dy=(pp[0]-pm[0])/(2*e);dz=(pp[1]-pm[1])/(2*e)
   return tuple(Vector((-n.x*dy-n.y*dz,n.x,n.y)).normalized())
  fs.append(tuple(reversed(range(8))));ns.extend([(-1,0,0)]*8);mi.append(1 if kind=='rear' else 0)
  for i in range(len(xs)-1):
   for j in range(8):
    jj=(j+1)%8;fs.append((i*8+j,i*8+jj,(i+1)*8+jj,(i+1)*8+j));ns.extend([normal(i,j,j),normal(i,jj,j),normal(i+1,jj,j),normal(i+1,j,j)])
    mi.append(1 if kind=='rear' or (kind=='upper' and j in [6,7]) else 0)
  fs.append(tuple((len(xs)-1)*8+j for j in range(8)));ns.extend([(1,0,0)]*8);mi.append(1 if kind=='rear' else 0)
  mats=[]
  for original in [wood if kind!='lower' else wood2,iron]:
   name=original.name+' - explicit canonical normal'
   m=bpy.data.materials.get(name)
   if not m:
    m=original.copy();m.name=name;nt=m.node_tree;attr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='CanonicalNormal';tr=nt.nodes.new('ShaderNodeVectorTransform');tr.vector_type='NORMAL';tr.convert_from='OBJECT';tr.convert_to='WORLD';norm=nt.nodes.new('ShaderNodeVectorMath');norm.operation='NORMALIZE';nt.links.new(attr.outputs['Vector'],tr.inputs['Vector']);nt.links.new(tr.outputs['Vector'],norm.inputs[0]);nt.links.new(norm.outputs['Vector'],next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED').inputs['Normal'])
   mats.append(m)
  o=mesh('wreck-end__'+kind+'_canonical_rail',vs,fs,mats,mi,ns)
  field=o.data.attributes.new('CanonicalNormal','FLOAT_VECTOR','CORNER')
  for d,n in zip(field.data,ns):d.vector=n
  return o
 for s in contract['finitePorts']['E']['sections']:
  kind='lower' if 'lower' in s['name'] else 'upper' if 'upper' in s['name'] else 'rear';rail(kind,s)
 def box(name,center,size,mat,bevel=.015):
  x,y,z=center;dx,dy,dz=[v/2 for v in size]
  vs=[(x+sx*dx,y+sy*dy,z+sz*dz) for sx,sy,sz in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
  fs=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
  o=mesh(name,vs,fs,[mat,ironedge] if mat==iron else [mat]);b=o.modifiers.new('Rounded native crafted edge','BEVEL');b.width=bevel;b.segments=4;b.affect='EDGES';b.profile=.5
  if mat==iron:b.material=1
  for p in o.data.polygons:p.use_smooth=True
  w=o.modifiers.new('Weighted broad face normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=40
  return o
 # Round02: two rear-set interior timbers preserve a continuous open rail reveal
 # across bays in N rather than stopping it at module ends. Collar geometry,
 # material/normal fields, support and all hardware remain unchanged.
 box('wreck-end__inset_timber_low',(-.0175,.10,.297),(.67,.28,.174),wood,.029)
 box('wreck-end__inset_timber_high',(-.0175,.15,.4695),(.67,.14,.141),wood2,.028)
 for i,x in enumerate([-.215,.205]):
  box('wreck-end__iron_strap_'+str(i),(x,.007,.431),(.095,.418,.67),iron,.021)
  box('wreck-end__fastener_plate_'+str(i),(x,-.207,.342),(.132,.035,.16),iron,.019)
  for j,z in enumerate([.305,.377]):
   bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1,location=(x,-.227,z));o=bpy.context.object;o.name='wreck-end__pale_bolt_'+str(i)+str(j)
   for c in list(o.users_collection):c.objects.unlink(o)
   col.objects.link(o);o.parent=root;o.scale=(.022,.009,.022);o.data.materials.append(pale)
   for p in o.data.polygons:p.use_smooth=False
  # Rear fastening remains legible in the opposite facing.
  box('wreck-end__rear_plate_'+str(i),(x,.228,.445),(.115,.027,.135),iron,.015)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1,location=(x,.247,.445));o=bpy.context.object;o.name='wreck-end__rear_bolt_'+str(i)
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);o.parent=root;o.scale=(.022,.009,.022);o.data.materials.append(pale)
 def line(name,points,mat,radius):
  cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=12;cu.bevel_depth=radius;cu.bevel_resolution=2
  sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
  for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
  o=bpy.data.objects.new(name,cu);col.objects.link(o);o.parent=root;cu.materials.append(mat);return o
 # Native shallow grain and short worn paint slivers; all terminate well inside collars.
 for i,(z,y) in enumerate([(.385,.105),(.542,.14),(.216,-.075),(.754,-.025)]):
  line('wreck-end__grain_'+str(i),[(-.34,y,z),(-.11,y+.007,z+.001),(.12,y-.005,z),(.28,y+.004,z)],grain,.0021)
 for i,(x,z,y) in enumerate([(-.32,.217,-.116),(.25,.754,-.055),(-.04,.542,.13)]):
  line('wreck-end__worn_edge_'+str(i),[(x-.028,y,z),(x,y+.004,z+.001),(x+.031,y+.003,z)],wear,.0026)
 # Own crafted terminal. Exact lowest bevel support X[.312,.368]/Y±.203 at Z.04.
 terminal=box('wreck-end__finished_terminal',(.34,0,.4075),(.08,.43,.735),iron,.012)
 # Real shallow recessed terminal fasteners. The relief never changes its finite bottom support.
 bpy.context.view_layer.objects.active=terminal
 for m in list(terminal.modifiers):
  if m.type=='BEVEL':bpy.ops.object.modifier_apply(modifier=m.name)
  elif m.type=='WEIGHTED_NORMAL':terminal.modifiers.remove(m)
 for j,(y,z) in enumerate([(-.125,.24),(.125,.24),(-.125,.59),(.125,.59)]):
  bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.026,depth=.034,location=(.389,y,z),rotation=(0,math.pi/2,0))
  cut=bpy.context.object;cut.name='temporary_native_terminal_recess'
  mod=terminal.modifiers.new('Native recessed fastener bore','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut
  bpy.context.view_layer.objects.active=terminal;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(.375,y,z))
  bolt=bpy.context.object;bolt.name='wreck-end__recessed_terminal_fastener_'+str(j)
  for c in list(bolt.users_collection):c.objects.unlink(bolt)
  col.objects.link(bolt);bolt.parent=root;bolt.scale=(.0035,.021,.021);bolt.data.materials.append(pale)
  for p in bolt.data.polygons:p.use_smooth=True
 wn=terminal.modifiers.new('Weighted terminal face normals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=40
 for j,y in enumerate([-.125,.125]):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(.34,y,.772))
  o=bpy.context.object;o.name='wreck-end__terminal_crown_fastener_'+str(j)
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o);o.parent=root;o.scale=(.017,.021,.006);o.data.materials.append(pale)
  for p in o.data.polygons:p.use_smooth=True
 # Exact canonical world/light/camera objects retained from approved native source.
 cam=sc.camera

else:
 root=bpy.data.objects['wreck-end__root.001'];col=bpy.data.collections['S33_PROP_wreck-end.001'];cam=sc.camera

def configure(frame=(192,352),anchor=(96,248)):
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 el=math.atan(1/.7);cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y;cam.data.shift_y=(anchor[1]*2-base.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];bpy.context.view_layer.update()
 r=px((0,0,0));return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(row) for row in cam.matrix_world],'projectionMatrix':[list(row) for row in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=sc.render.pixel_aspect_y)],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(el)},'calibration':{'root':list(r),'unitX':list(px((1,0,0))-r),'unitDepth':list(px((0,-1,0))-r),'unitHeight':list(px((0,0,1))-r)}}
def enable_own():
 def en(lc):
  lc.exclude=False;lc.hide_viewport=False
  for c in lc.children:en(c)
 en(bpy.context.view_layer.layer_collection)
 col.hide_viewport=False;col.hide_render=False
 for o in col.all_objects:o.hide_viewport=False;o.hide_render=False;o.hide_set(False)
 bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
enable_own()
configure();root.rotation_euler.z=0;root.location=(0,0,0);root.scale=(1,1,1);bpy.context.view_layer.update()
if not args.recapture:
 bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-01.blend'),compress=True)
records=[]
directions=['S'] if args.probe else ['N','E','S','W']
for d in directions:
 root.rotation_euler.z=ANGLES[d];root.location=(0,0,0);bpy.context.view_layer.update();camera=configure()
 path=OUT/'native/static'/d/'000.png';path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 records.append({'direction':d,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':[list(row) for row in root.matrix_world],'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'sourceFilterSize':sc.render.filter_size,'camera':camera,'frame':sc.frame_current,'path':str(path.relative_to(OUT)),'sha256':sha(path),'sourceSHA256':sha(HERE/'round-01.blend')})
write(OUT/'capture-records.json',{'blender':bpy.app.version_string,'sourceSHA256':sha(HERE/'round-01.blend'),'captureRecords':records,'publication':'Direct native2 PNG identity; no crop/repair/reduction','lighting':{'worldStrength':.28,'overhead':[195,8,[0,0,5]],'cardinals':{'count':4,'energy':114,'size':8,'radius':6,'z':4,'shadows':False},'horizontalSymmetry':4}})
if not args.probe:
 write(OUT/'published-camera.json',records[0]['camera'])
 # True finite chain: own end0, exact approved middle02(-1,0), exact approved edge02(-2,0).
 neighbors=[]
 for asset in ['wreck-middle','wreck-edge']:
  path=RES/'canonical'/asset/'native.blend'
  with bpy.data.libraries.load(str(path),link=False) as (a,b):
   names=[name for name in a.collections if 'wreck' in name.lower()]
   assert len(names)==1,(asset,names)
   b.collections=names
  c=b.collections[0];sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
  rr=next(o for o in c.all_objects if o.type=='EMPTY' and o.parent is None)
  for ob in c.all_objects:ob.hide_viewport=False;ob.hide_render=False;ob.hide_set(False)
  neighbors.append((asset,c,rr,sha(path)))
 assembly=[]
 for d in ['N','E','S','W']:
  a=ANGLES[d];root.rotation_euler.z=a;root.location=(0,0,0)
  for i,(_,c,rr,_) in enumerate(neighbors,1):
   rr.rotation_euler=(0,0,a);rr.scale=(1,1,1);rr.location=Vector((-i,0,0));rr.location.rotate(__import__('mathutils').Euler((0,0,a)))
  bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
  vertical=d in ['E','W'];frame=(192,608) if vertical else (448,352)
  anchor=(96,504 if d=='W' else 248) if vertical else (352 if d=='S' else 96,248)
  camera=configure(frame,anchor)
  path=OUT/'connected-native'/f'{d}.png';path.parent.mkdir(parents=True,exist_ok=True);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  assembly.append({'kind':'actual-native-end-middle02-edge02','direction':d,'rootRotationZ':a,'actualRootMatrix':[list(row) for row in root.matrix_world],'camera':camera,'path':str(path.relative_to(OUT)),'sha256':sha(path),'logicalFrame':list(frame),'logicalRoot':list(anchor),'authoredModuleRootsBeforeRotation':[[0,0,0],[-1,0,0],[-2,0,0]],'actualModuleRootMatrices':[[list(row) for row in rr.matrix_world] for rr in [root]+[n[2] for n in neighbors]],'referenceSources':[{'asset':n[0],'sha256':n[3]} for n in neighbors],'internalCaps':'Actual coincident finite canonical end caps retained; no overlap or deletion','visibility':[{'collection':c.name,'hideRender':c.hide_render,'allOwnObjectsRender':all(not o.hide_render for o in c.all_objects)} for c in [col]+[n[1] for n in neighbors]]})
 write(OUT/'native-assembly-records.json',{'sourceSHA256':sha(HERE/'round-01.blend'),'captureRecords':assembly})
print('WRECK_END_NATIVE_COMPLETE',OUT)
