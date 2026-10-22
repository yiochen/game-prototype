"""Portable native inlet construction and registered EEVEE capture. Blender 5.2."""
import bpy, math, json, pathlib, hashlib, sys
sys.dont_write_bytecode=True
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE=pathlib.Path(__file__).resolve().parent
E=HERE.parent
R=HERE/'resources'
OUT=E/'candidates/round-01'
FACINGS={'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2}
def savej(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def bounds(ps):return [[min(p[i] for p in ps) for i in range(len(ps[0]))],[max(p[i] for p in ps) for i in range(len(ps[0]))]]
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,hex,rough=.36,metal=0,coat=.15):
 m=bpy.data.materials.new(name);m.use_nodes=True
 c=tuple(srgb(int(hex[i:i+2],16)/255) for i in (0,2,4))
 m.diffuse_color=(*c,1);p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.32;p.inputs['Specular IOR Level'].default_value=.32
 return m
def mesh(name,vs,fs,mats,inds=None,parent=None,bevel=0):
 me=bpy.data.meshes.new(name+'__mesh');me.from_pydata(vs,[],fs);me.update()
 o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent or ROOT
 for m in mats:me.materials.append(m)
 if inds:
  for f,k in zip(me.polygons,inds):f.material_index=k
 if bevel:
  b=o.modifiers.new('Real rounded edges','BEVEL');b.width=bevel;b.segments=4
  b.affect='EDGES';b.limit_method='ANGLE'
  bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=b.name);o.select_set(False)
 for f in o.data.polygons:f.use_smooth=True
 w=o.modifiers.new('Area weighted normals','WEIGHTED_NORMAL');w.keep_sharp=True;w.weight=50
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=w.name);o.select_set(False)
 return o
def cube(name,center,size,m,bevel=.01,parent=None):
 x,y,z=[v/2 for v in size]
 vs=[(a*x,b*y,c*z) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1),(1,-1,-1),(1,-1,1),(1,1,1),(1,1,-1)]]
 fs=[(0,4,5,1),(4,7,6,5),(7,3,2,6),(3,0,1,2),(1,5,6,2),(3,7,4,0)]
 o=mesh(name,vs,fs,[m],parent=parent,bevel=bevel);o.location=center;return o
def rounded(w,h,r,n=6):
 pts=[]
 for cx,cy,a in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for j in range(n+1):
   t=math.radians(a+j*90/n);pts.append((cx+r*math.cos(t),cy+r*math.sin(t)))
 return pts
def loft(name,loops,mats,mi=None,parent=None):
 vs=[p for ring in loops for p in ring];n=len(loops[0]);fs=[];ids=[]
 for k in range(len(loops)-1):
  for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j));ids.append(mi[k] if mi else 0)
 return mesh(name,vs,fs,mats,ids,parent)
def ring_xz(name,w,h,thick,depth,y,z,m,parent=None):
 outer=rounded(w,h,min(.04,h/4));inner=rounded(w-2*thick,h-2*thick,min(.025,(h-2*thick)/4))
 loops=[]
 for pts,yy in [(outer,y+depth/2),(outer,y-depth/2),(inner,y-depth/2),(inner,y+depth/2),(outer,y+depth/2)]:loops.append([(x,yy,z+zz) for x,zz in pts])
 return loft(name,loops,[m],parent=parent)
def cylinder(name,center,r,depth,m,axis='Z',parent=None,n=24):
 bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=depth,location=(0,0,0));o=bpy.context.object;o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 COL.objects.link(o);o.parent=parent or ROOT
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 o.location=center;o.data.materials.append(m)
 b=o.modifiers.new('Rounded hardware','BEVEL');b.width=min(r*.32,.005);b.segments=3
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=b.name)
 for f in o.data.polygons:f.use_smooth=True
 w=o.modifiers.new('Hardware normals','WEIGHTED_NORMAL');w.keep_sharp=True;bpy.ops.object.modifier_apply(modifier=w.name)
 return o
def empty(name,location=(0,0,0),parent=None):
 o=bpy.data.objects.new(name,None);COL.objects.link(o);o.location=location;o.parent=parent;return o
def setup():
 global COL,ROOT,SCENE
 bpy.ops.wm.read_factory_settings(use_empty=True);SCENE=bpy.context.scene
 COL=bpy.data.collections.new('REFINED__sub-collector-inlet');SCENE.collection.children.link(COL)
 ROOT=empty('collector__root');ROOT['asset_id']='sub-collector-inlet';ROOT['axis_convention']='X=x; depth=-Y; height=Z';ROOT['visual_height']=.55;ROOT['footprint_cells']='[1,1]';ROOT['ground_root']='[0,0,0]';ROOT['neutral_adoption']='idle frame1 canonical S only'
 cyan=mat('Inlet | soft cyan enamel','69C6DA',.31,0,.24)
 inside=mat('Inlet | cool inner enamel','76B4C4',.43,0,.13)
 rim=mat('Inlet | rolled pale edge','9BE2EA',.28,0,.22)
 yellow=mat('Inlet | warm golden protective lip','FFB509',.32,0,.24)
 yellow2=mat('Inlet | amber inset','DB8D0C',.42,0,.14)
 dark=mat('Inlet | charcoal mouth','263F4C',.4,.08,.10)
 recess=mat('Inlet | recessed throat','132A37',.65,0,0)
 metal=mat('Inlet | satin metal','91A6AD',.33,.42,.08)
 gasket=mat('Inlet | graphite gasket','40535D',.65,0,0)
 cube('collector__protective_shoe',(0,-.067,.058),(.78,.40,.086),yellow,.026)
 cube('collector__undersole',(0,-.062,.025),(.748,.376,.028),gasket,.013)
 cube('collector__front_inset',(0,-.264,.060),(.36,.012,.038),yellow2,.007)
 for x in [-.305,.305]:
  cylinder('collector__lip_bolt_'+str(x),(x,-.167,.104),.024,.012,metal)
 # Stable compression collar supports the genuinely hollow mouth sleeve.
 cube('collector__lower_collar',(0,-.038,.122),(.64,.298,.065),gasket,.024)
 sleeve=empty('collector__mouth_sleeve',(0,0,.133),ROOT)
 # Closed continuous thick funnel: outer lower, outer upper, rim, inner upper, inner floor.
 specs=[(.61,.278,.028,-.04,.0),(.70,.325,.045,-.04,.227),(.692,.317,.042,-.04,.247),(.595,.225,.038,-.04,.247),(.565,.20,.032,-.04,.224),(.43,.135,.025,-.045,.045)]
 loops=[[(x,y+cy,z) for x,y in rounded(w,h,r)] for w,h,r,cy,z in specs]
 shell=loft('collector__hollow_enamel_shell',loops,[cyan,rim,inside],mi=[0,1,1,2,2],parent=sleeve)
 # Close floor and underside with native polygons (no image/alpha surface).
 n=len(loops[-1]);vs=loops[-1];floor=mesh('collector__inner_floor',vs,[tuple(range(n))],[inside],parent=sleeve)
 # Internal angled throat goes down to the front vertical intake.
 cube('collector__inner_throat',(0,-.058,.055),(.36,.115,.022),recess,.012,sleeve)
 # Side sleeves/rear ribs finish otherwise broad shell panels.
 for x in [-.334,.334]:
  cube('collector__side_shoulder_'+str(x),(x,-.035,.128),(.038,.242,.072),metal,.012)
  cylinder('collector__side_pivot_'+str(x),(x+(.018 if x>0 else -.018),-.17,.217),.023,.018,metal,'X')
 for x in [-.215,.215]:
  cube('collector__rear_rib_'+str(x),(x,.113,.259),(.043,.025,.12),cyan,.011)
 # Recessed front mouth and its broad softened surround.
 mouth=empty('collector__mouth_pulse',(0,-.220,.217),ROOT)
 ring_xz('collector__mouth_surround',.548,.236,.042,.033,0,0,dark,mouth)
 cube('collector__dark_mouth',(0,.014,0),(.455,.018,.150),recess,.018,mouth)
 # Single connected guard cage rocks on a real lower cross-shaft.
 guard=empty('collector__guard_rock',(0,-.249,.119),ROOT)
 ring_xz('collector__guard_cage',.466,.215,.020,.023,0,.105,metal,guard)
 for x in [-.15,0,.15]:
  cylinder('collector__guard_bar_'+str(x),(x,0,.105),.0145,.195,metal,'Z',guard)
 cylinder('collector__lower_guard_shaft',(0,-.249,.119),.019,.52,metal,'X')
 for x in [-.27,.27]:
  cube('collector__bearing_'+str(x),(x,-.234,.123),(.041,.055,.055),yellow2,.012)
 # Rear tongue is an intentional structural insertion into the finite body seat.
 tongue=cube('collector__rear_seat_tongue',(0,.163,.285),(.50,.13,.15),metal,.008)
 tongue['attachment_role']='intentional contiguous finite seat insertion; all other hull penetration is unwanted'
 cube('collector__rear_seat_gasket',(0,.106,.285),(.55,.024,.17),gasket,.011)
 cube('collector__rear_service_inset',(0,.232,.283),(.20,.012,.075),gasket,.012)
 for x in [-.191,.191]:cylinder('collector__seat_bolt_'+str(x),(x,.232,.285),.018,.015,metal,'Y')
 mouthref=empty('collector__actual_mouth',(0,-.215,.217),ROOT);mouthref['axis_local']='[0,-1,0]'
 # Create native actions: pulse is a small contraction of the intake sleeve and dark mouth,
 # guard rocking stays the same functional gesture as the source.
 owners=[sleeve,mouth,guard];neutral={o.name:{'location':list(o.location),'rotation_euler':list(o.rotation_euler),'scale':list(o.scale)} for o in owners}
 actions={}
 for clip in ['idle','active']:
  actions[clip]={}
  for o in owners:
   o.animation_data_clear()
   for fr in range(1,2 if clip=='idle' else 14):
    for ch,v in neutral[o.name].items():setattr(o,ch,v)
    if clip=='active':
     phase=2*math.pi*(fr-1)/12
     if o==sleeve:o.scale.z=.96+.12*math.sin(phase+.55)
     if o==mouth:o.scale.z=.93+.12*math.sin(phase+.55)
     if o==guard:o.rotation_euler.x=.195*math.sin(phase+.55)
    for ch in ['location','rotation_euler','scale']:o.keyframe_insert(ch,frame=fr)
   a=o.animation_data.action;a.name='INLET_NATIVE__'+clip+'__'+o.name;a.use_fake_user=True
   for layer in a.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for f in bag.fcurves:
       for k in f.keyframe_points:k.interpolation='LINEAR'
   actions[clip][o.name]=a.name
 ROOT['nativeActions']=json.dumps(actions);ROOT['neutralTransforms']=json.dumps(neutral)
 # Registered original standalone camera. Derive shift from original measured root only.
 camera=json.loads((R/'05-source-camera.json').read_text()) if (R/'05-source-camera.json').exists() else json.loads(next(R.glob('*-source-camera.json')).read_text())
 cd=bpy.data.cameras.new('Registered standalone camera');cam=bpy.data.objects.new('Registered standalone camera',cd);SCENE.collection.objects.link(cam);SCENE.camera=cam;cam.matrix_world=Matrix(camera['camera']['worldMatrix']);cd.type='ORTHO';cd.sensor_fit='HORIZONTAL';cd.ortho_scale=1.5;cd.shift_x=0;cd.shift_y=0;cd.clip_start=.01;cd.clip_end=1000
 SCENE.render.resolution_x=768;SCENE.render.resolution_y=1408;SCENE.render.resolution_percentage=100;SCENE.render.pixel_aspect_x=camera['camera']['pixelAspect'][0];SCENE.render.pixel_aspect_y=1
 def px(p):
  q=world_to_camera_view(SCENE,cam,Vector(p));return [q.x*768,(1-q.y)*1408]
 bpy.context.view_layer.update();base=px((0,0,0));cd.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-base[1];cd.shift_y=(992-base[1])/dy
 # EEVEE is the actual production renderer; no shadow plane or post-processing.
 SCENE.render.engine='BLENDER_EEVEE'
 SCENE.eevee.taa_render_samples=48
 SCENE.render.filter_size=.5;SCENE.render.film_transparent=True;SCENE.render.image_settings.file_format='PNG';SCENE.render.image_settings.color_mode='RGBA';SCENE.render.image_settings.color_depth='8';SCENE.render.fps=12
 SCENE.view_settings.view_transform='AgX';SCENE.view_settings.look='AgX - Medium High Contrast';SCENE.view_settings.exposure=0;SCENE.view_settings.gamma=1
 world=bpy.data.worlds.new('Symmetric soft studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.72,.75,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.23;SCENE.world=world
 def light(name,loc,power,size):
  d=bpy.data.lights.new(name,'AREA');o=bpy.data.objects.new(name,d);SCENE.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,.18))-o.location).to_track_quat('-Z','Y').to_euler();d.energy=power;d.shape='DISK';d.size=size;d.color=(1,.945,.86)
 light('Soft centered overhead',(0,0,4.5),200,3.5)
 for x,y in [(3,0),(-3,0),(0,3),(0,-3)]:light('Equal cardinal fill '+str((x,y)),(x,y,2.7),85,3.5)
 SCENE['nativeCaptureScale']=4;SCENE['publishedSourceScale']=2;SCENE['wholeFramePublication']='Pillow BOX 768x1408 to384x704, no fitting or repair';SCENE['lightingSymmetry']='one overhead and four equal cardinal area fills, symmetric constant world';SCENE['groundShadow']='no ground object'
 apply_clip(SCENE,COL,'idle','S',1)
 bpy.context.view_layer.update()
 bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-01.blend'),compress=True)
 savej(HERE/'round-01-settings.json',settings(SCENE,ROOT))
 return SCENE,COL,ROOT
def apply_clip(scene,col,clip,direction,fr):
 root=next(o for o in col.objects if o.name=='collector__root');acts=json.loads(root['nativeActions'])
 for owner,an in acts[clip].items():
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[an];o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
 root.rotation_euler.z=FACINGS[direction];scene.frame_set(fr);bpy.context.view_layer.update()
def settings(s,root):
 cam=s.camera
 def px(p):
  q=world_to_camera_view(s,cam,Vector(p));return [q.x*s.render.resolution_x,(1-q.y)*s.render.resolution_y]
 return {'engine':s.render.engine,'filterSize':s.render.filter_size,'nativeFrame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'logicalFrame':[192,352],'logicalRoot':[96,248],'nativeCaptureScale':4,'publishedSourceScale':2,'camera':{'worldMatrix':[list(r) for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'elevationDegrees':math.degrees(math.atan2(cam.location.z,-cam.location.y))},'calibration':{'root':px((0,0,0)),'unitX':px((1,0,0)),'unitY':px((0,1,0)),'unitZ':px((0,0,1))},'lights':[{'name':o.name,'position':list(o.location),'rotation':list(o.rotation_euler),'power':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'],'world':{'name':s.world.name,'strength':s.world.node_tree.nodes['Background'].inputs['Strength'].default_value},'colorManagement':{'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'fps':s.render.fps,'rootMatrix':[list(r) for r in root.matrix_world],'resources':{'libraries':[l.filepath for l in bpy.data.libraries],'images':[i.filepath for i in bpy.data.images if i.source=='FILE']},'publication':'complete native frame BOX reduction; no per-view adjustments','groundShadow':'no ground geometry'}
if __name__=='__main__':
 s,c,r=setup()
 if '--draft' in sys.argv:
  for di in 'NESW':
   apply_clip(s,c,'idle',di,1);s.render.filepath=str(OUT/'draft'/('idle-'+di+'.png'));pathlib.Path(s.render.filepath).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
