import sys
sys.dont_write_bytecode=True
import bpy,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parent;O=B.parent;OUT=O/'candidates/round-01';RES=B/'resources'
ANGLES={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def update():SC.frame_set(1);bpy.context.view_layer.update()
def camera(frame=(192,352),anchor=(96,248)):
 sc=SC;cam=sc.camera;scale=2
 sc.render.resolution_x=frame[0]*2;sc.render.resolution_y=frame[1]*2;sc.render.resolution_percentage=100;sc.render.pixel_aspect_x=math.sqrt(1+.7*.7);sc.render.pixel_aspect_y=1
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128;el=math.atan(1/.7)
 cam.location=(0,-10*math.cos(el),10*math.sin(el));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=cam.data.shift_y=0;update()
 def px(v):
  p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
 b=px((0,0,0));cam.data.shift_y=1;update();dy=px((0,0,0)).y-b.y;cam.data.shift_y=(anchor[1]*2-b.y)/dy;cam.data.shift_x=(frame[0]/2-anchor[0])/frame[0];update();origin=px((0,0,0))
 return {'projection':'top-down-oblique-square-grid','frame':list(frame),'anchor':list(anchor),'cellSize':128,'captureScale':2,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=sc.render.resolution_x,y=sc.render.resolution_y,scale_x=sc.render.pixel_aspect_x,scale_y=1)],'pixelAspect':[sc.render.pixel_aspect_x,1],'orthoScale':cam.data.ortho_scale,'elevationDegrees':math.degrees(el),'worldUnitsPerCell':1},'calibration':{'root':list(origin),'unitX':list(px((1,0,0))-origin),'unitDepth':list(px((0,-1,0))-origin),'unitHeight':list(px((0,0,1))-origin)},'nativeFrame':[sc.render.resolution_x,sc.render.resolution_y],'filterSize':sc.render.filter_size,'publication':'Exact native PNG bytes; no reduction'}
def mesh(name,vs,fs,mats,mi=None,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();ob=bpy.data.objects.new('reef-edge__'+name,me);COL.objects.link(ob);ob.parent=ROOT
 for m in mats:me.materials.append(m)
 for p in me.polygons:p.use_smooth=smooth;p.material_index=mi[p.index] if mi else 0
 return ob
def rock(name,loc,size,ang):
 ring=[(-.46,-.28),(-.20,-.49),(.28,-.46),(.5,-.14),(.44,.34),(.08,.5),(-.35,.42),(-.5,.09)];vs=[]
 for z,r in [(-.5,.68),(-.16,1),(.27,.90),(.49,.57)]:
  for i,(x,y) in enumerate(ring):vs.append((x*size[0]*r,y*size[1]*r,(z+.028*math.sin(i*2.1))*size[2]))
 fs=[tuple(reversed(range(8))),tuple(range(24,32))];mi=[0,1]
 for k in range(3):
  for i in range(8):fs.append((8*k+i,8*k+(i+1)%8,8*(k+1)+(i+1)%8,8*(k+1)+i));mi.append(1 if k==2 else 0)
 ob=mesh(name,vs,fs,[M['selected boulder blue'],M['selected boulder lit planes']],mi);ob.location=loc;ob.rotation_euler.z=ang
 mod=ob.modifiers.new('soft native stone shoulders','BEVEL');mod.width=.009;mod.segments=3;mod.profile=.65
 mod=ob.modifiers.new('crafted stone planes','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=28
 return ob
def tube(name,base,height,radius,lean,color):
 outer=M['teal tube coral' if color=='teal' else 'purple tube coral'];lip=M['teal rounded rim' if color=='teal' else 'purple rounded rim'];inner=M['teal inner wall' if color=='teal' else 'purple inner wall'];n=28;vs=[]
 rings=[(0,.72),(.34*height,.82),(.72*height,.94),(height-.017,1),(height-.005,1.025),(height,.88),(height-.009,.66),(height-.039,.61),(.038,.47)]
 for z,s in rings:
  f=z/height;cx=base[0]+lean[0]*f*f;cy=base[1]+lean[1]*f*f
  for i in range(n):
   a=math.tau*i/n;r=radius*s*(1+.022*math.sin(3*a+.5));vs.append((cx+r*math.cos(a),cy+r*math.sin(a),base[2]+z))
 fs=[];mi=[]
 for k in range(len(rings)-1):
  for i in range(n):fs.append((n*k+i,n*k+(i+1)%n,n*(k+1)+(i+1)%n,n*(k+1)+i));mi.append(0 if k<3 else 1 if k<6 else 2)
 fs.append(tuple(reversed(range(n*(len(rings)-1),n*len(rings)))));mi.append(2)
 return mesh(name,vs,fs,[outer,lip,inner],mi)
def build():
 global SC,COL,ROOT,M,CORE
 bpy.ops.wm.open_mainfile(filepath=str(RES/'canonical-middle02.blend'));SC=bpy.context.scene;SC.name='reef-edge native refinement round-01';COL=bpy.data.collections['reef-middle'];COL.name='reef-edge';ROOT=bpy.data.objects['reef-middle__root'];ROOT.name='reef-edge__root';CORE=bpy.data.objects['reef-middle__continuous_core'];CORE.name='reef-edge__continuous_core'
 for ob in list(COL.objects):
  if ob not in [ROOT,CORE]:bpy.data.objects.remove(ob,do_unlink=True)
 M={m.name:m for m in bpy.data.materials}
 # Interior sculpt only: canonical complete .08 endpoint bands remain literally untouched.
 for v in CORE.data.vertices:
  x,y,z=v.co
  if abs(x)<.32 and z>.05:
   w=(1-(abs(x)/.32)**2)**2
   v.co.z+=w*(.011*math.sin((y+.38)*7)-.006)*min(1,z/.18)
 CORE.data.update()
 rock('back_crown',(0,.255,.358),(.36,.20,.20),-.09)
 rock('central_saddle',(.045,.10,.429),(.32,.26,.11),.12)
 rock('front_ledge',(-.015,-.245,.365),(.35,.235,.16),-.14)
 rock('left_reef_mass',(-.28,.09,.413),(.22,.27,.18),-.17)
 rock('right_reef_mass',(.285,.12,.410),(.22,.26,.16),.19)
 tube('green_focal',(.030,.155,.431),.244,.068,(.008,.013),'teal')
 tube('green_left_branch',(-.045,.16,.427),.166,.047,(-.056,.025),'teal')
 tube('green_right_branch',(.110,.16,.425),.186,.049,(.049,.020),'teal')
 tube('green_foreground',(.010,.045,.424),.117,.044,(-.025,-.033),'teal')
 tube('violet_left',(-.25,-.205,.357),.247,.057,(-.008,-.013),'purple')
 tube('violet_left_bud',(-.185,-.25,.344),.150,.035,(.008,-.019),'purple')
 tube('violet_left_branch',(-.311,-.192,.350),.164,.037,(-.019,.015),'purple')
 tube('violet_right',(.245,-.205,.358),.229,.056,(.012,-.009),'purple')
 tube('violet_right_bud',(.182,-.248,.346),.142,.034,(-.004,-.018),'purple')
 tube('violet_right_branch',(.307,-.187,.348),.158,.036,(.023,.022),'purple')
 for i,(x,y,z,r) in enumerate([(-.120,-.18,.385,.045),(.118,-.14,.398,.038),(-.31,.275,.333,.038),(.31,-.03,.403,.032)]):
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(x,y,z));ob=bpy.context.object
  for c in list(ob.users_collection):c.objects.unlink(ob)
  COL.objects.link(ob);ob.name='reef-edge__cyan_pebble_'+str(i);ob.parent=ROOT;ob.scale=(r,r*.82,r*.58);ob.data.materials.append(M['teal tube coral'])
  for p in ob.data.polygons:p.use_smooth=True
 ROOT['assetId']='reef-edge';ROOT['functionalEnvelope']=[1,.76,.68];ROOT['ports']='W/E exact asymmetric reef-section-v1';ROOT['endpointBands']='canonical-middle02 .08'
 SC.render.filter_size=.01;SC.eevee.taa_render_samples=64;SC.render.fps=12;ROOT.rotation_euler.z=0;camera();update()
 # Remove orphaned canonical decorative meshes; keep only actual native-used datums.
 for me in list(bpy.data.meshes):
  if me.users==0:bpy.data.meshes.remove(me)
 bpy.ops.wm.save_as_mainfile(filepath=str(B/'round-01.blend'),compress=True)
def render(p):p.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(p);bpy.ops.render.render(write_still=True)
def capture_heroes(target,root,kind):
 records=[]
 for d,a in ANGLES.items():
  root.rotation_euler.z=a;root.location=(0,0,0);rec=camera();p=target/f'{d}/000.png';render(p)
  records.append({'direction':d,'clip':'static','frame':1,'index':0,'rootRotationZ':root.rotation_euler.z,'actualRootMatrix':[list(r) for r in root.matrix_world],'camera':rec,'path':str(p.relative_to(O)),'sha256':sha(p)})
  if kind=='candidate':
   for q in [OUT/f'frames/static/{d}/000.png',OUT/f'atlases/static-{d}.png']:q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
   if d=='S':write(OUT/'published-camera.json',rec)
 return records
def append_col(file,colname):
 with bpy.data.libraries.load(str(file),link=False) as (src,dst):dst.collections=[colname]
 c=dst.collections[0];SC.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
 for ob in c.all_objects:ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
 update();r=next(ob for ob in c.all_objects if ob.type=='EMPTY' and ob.parent is None)
 return c,r
if '--replay' in sys.argv:
 OUT=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
 if OUT.exists():raise FileExistsError(OUT)
 bpy.ops.wm.open_mainfile(filepath=str(B/'round-01.blend'));SC=bpy.context.scene;COL=bpy.data.collections['reef-edge'];ROOT=bpy.data.objects['reef-edge__root'];CORE=bpy.data.objects['reef-edge__continuous_core']
else:
 if (B/'round-01.blend').exists() or OUT.exists():raise FileExistsError('immutable round already exists')
 build()
OUT.mkdir(parents=True,exist_ok=True)
log={'sourceSHA256':sha(B/'round-01.blend'),'nativeSource':'source/round-01.blend','captureRecords':capture_heroes(OUT/'native/static',ROOT,'candidate')}
if '--singles' not in sys.argv:
 COL.hide_render=True
 CC,CR=append_col(RES/'canonical-middle02.blend','reef-middle')
 log['canonicalHeroes']=capture_heroes(OUT/'evidence/sprites/middle',CR,'canonical');CC.hide_render=True
 corners={}
 for key in ['corner','end']:
  c,r=append_col(RES/'original-context.blend','S33_PROP_reef-'+key+'.001');corners[key]=(c,r);c.hide_render=True
  c.hide_render=False;log[key+'Heroes']=capture_heroes(OUT/f'evidence/sprites/{key}',r,'context-provisional');c.hide_render=True
 # copy actual canonical collection for second native neighbor.
 cc=bpy.data.collections.new('canonical native neighbor');SC.collection.children.link(cc);mp={}
 for ob in CC.objects:n=ob.copy();cc.objects.link(n);mp[ob]=n
 for ob,n in mp.items():
  if ob.parent in mp:n.parent=mp[ob.parent]
 croot=mp[CR];cc.hide_render=True
 layouts={'primary':[('middle',CC,CR,-1,0,0),('edge',COL,ROOT,0,0,0),('middle',cc,croot,1,0,0)],'topology':[('middle',CC,CR,-1,0,0),('edge',COL,ROOT,0,0,0),('corner',*corners['corner'],1,0,0),('middle',cc,croot,1,1,math.pi/2),('end',*corners['end'],1,2,math.pi/2)]}
 log['contexts']=[]
 for kind,layout in layouts.items():
  for d,a in ANGLES.items():
   for c in [CC,COL,cc,*[v[0] for v in corners.values()]]:c.hide_render=True
   rows=[]
   for key,c,r,x,y,angle in layout:
    c.hide_render=False;r.rotation_euler.z=a+angle;r.location=(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),0);update();rows.append({'asset':key,'authoredRoot':[x,y,0],'authoredAngle':angle,'rootRotationZ':r.rotation_euler.z,'actualRootMatrix':[list(q) for q in r.matrix_world]})
   rec=camera((704,864),(352,560));p=OUT/f'evidence/native-{kind}-{d}.png';render(p);log['contexts'].append({'kind':kind,'direction':d,'camera':rec,'roots':rows,'path':str(p.relative_to(O)),'sha256':sha(p)})
write(OUT/'capture-measurements.json',log)
print('REEF_EDGE_CAPTURE_COMPLETE',flush=True)
