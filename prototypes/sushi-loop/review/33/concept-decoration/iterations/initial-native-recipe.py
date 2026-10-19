"""Concept-matched native decoration assemblies. Fixed, explicitly placed forms; no random generator.
Source concept crops and measured mesh/camera receipts accompany the static asset review.
"""
import bpy, math, json, hashlib, sys, uuid, contextlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
CELL=128; FRAME=[192,768]; ROOT=[96,688]; SCALE=4; HEIGHT=.7;FOOTING_TRANSITION=.42
DIRS={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
COLORS={'cobalt':'326BBC','cobaltTop':'397CCD','cobaltDark':'2857A3','slate':'62627B','slateTop':'79778B','slateDark':'505369','pink':'F23E86','pinkLight':'FF639C','pinkInside':'9E1D58','violet':'7650E6','violetInside':'3B2797','green':'48B92D','greenLight':'79D833','greenDark':'268D30','moss':'75CE27','pale':'D5E3E5','paleSide':'B4CBD3','crack':'5A7B8D','wood':'AB642B','woodLight':'C98037','woodDark':'77431F','soil':'393D2B','orange':'F7722C','white':'FFF0DA','charcoal':'303947','yellow':'F6CA35','lantern':'FFE761','ocean':'19B3C8','cream':'EED29D'}
# Reference rectangles use unchanged 1024×1536 approved concept images.
DESIGNS=[
 ('ocean-floor','underwater','Ocean bed','ground',0,(418,430,570,575),'Continuous turquoise square bed.'),
 ('cobalt-crags','underwater','Cobalt crag bank','rock',2.55,(879,389,1024,657),'Interlocking broad blue boulders; uneven shoulders and broad polygon crowns.'),
 ('cobalt-shelf','underwater','Low cobalt shoulder','rock',1.05,(1,1104,155,1288),'A low bank of overlapping blue facets between taller silhouettes.'),
 ('pink-coral','underwater','Fanned pink and violet coral','coral',1.45,(11,1248,248,1474),'Several thick hollow fingers fan from a low common reef; pink leads, violet supports.'),
 ('kelp-fan','underwater','Branching kelp fan','plant',2.12,(902,113,1024,367),'Thick angular green ribbons branch and curve; no thin grass blades.'),
 ('pale-column','underwater','Broken pale column','ruin',1.88,(790,678,929,946),'Broad pale broken pillar, fluted facets, cracks, lime growth at crown and foot.'),
 ('reef-face','underwater','Mossy stone face','ruin',2.18,(772,158,931,395),'Angular pale face, heavy brow, nose and ears, with bright moss on top and sides.'),
 ('restaurant-floor','restaurant','Cream floor','ground',0,(204,1090,330,1215),'Continuous warm cream square bed.'),
 ('slate-bank','restaurant','Slate rock bank','rock',2.35,(1,925,128,1150),'Subdued grey-violet rock perimeter, broad crowns and dark lower facets.'),
 ('angular-shrub','restaurant','Dense angular shrub','plant',1.55,(0,1216,211,1536),'Full green branching mass nestled among slate stones, with staggered angular tips.'),
 ('wood-planter','restaurant','Honey-wood planter','planter',1.78,(861,1215,1024,1420),'Broad square wood box, dark soil, closely packed angular green foliage.'),
 ('crate-stack','restaurant','Stacked honey-wood crates','crate',1.32,(838,169,943,338),'Offset full wooden crates with thick corner framing and diagonal boards.'),
 ('cone-curb','restaurant','Construction corner','construction',1.05,(0,1109,149,1261),'Warm orange and cream cone against a striped curb and low slate stones.'),
 ('lantern-garden','restaurant','Golden lantern and shrub','lantern',2.22,(648,44,786,291),'Warm golden lantern on a thick timber support, beside dense greenery.'),
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,indent=2)+'\n')
def rows(m):return [[float(v) for v in r] for r in m]
@contextlib.contextmanager
def active(scene):
 old=bpy.context.window.scene
 try:bpy.context.window.scene=scene;yield
 finally:bpy.context.window.scene=old
class Piece:
 def __init__(self,scene,prefix,ident,height):
  self.id=ident;self.shade_height=max(height,.5);self.col=bpy.data.collections.new(prefix+' '+ident);scene.collection.children.link(self.col)
  self.root=bpy.data.objects.new(prefix+' '+ident+' root',None);self.col.objects.link(self.root);self.parts=[];self.mats={}
 def mat(self,color):
  if color in self.mats:return self.mats[color]
  h=COLORS.get(color,color);rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
  m=bpy.data.materials.new(self.col.name+' '+color);m.use_nodes=True;m.diffuse_color=(*rgb,1);nodes=m.node_tree.nodes;links=m.node_tree.links;nodes.clear()
  output=nodes.new('ShaderNodeOutputMaterial');emit=nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(*rgb,1);links.new(emit.outputs[0],output.inputs['Surface'])
  if color not in ('ocean','cream','lantern','yellow'):
   geom=nodes.new('ShaderNodeNewGeometry');xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(geom.outputs['Position'],xyz.inputs[0])
   span=nodes.new('ShaderNodeMapRange');span.inputs['From Min'].default_value=0;span.inputs['From Max'].default_value=self.shade_height;links.new(xyz.outputs['Z'],span.inputs['Value'])
   ramp=nodes.new('ShaderNodeValToRGB');base=.21 if color.startswith(('cobalt','slate')) else .37;ramp.color_ramp.elements[0].color=(base,base*1.07,base*1.2,1);ramp.color_ramp.elements[1].color=(1,1,1,1);links.new(span.outputs['Result'],ramp.inputs[0])
   dot=nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';links.new(geom.outputs['Normal'],dot.inputs[0]);links.new(geom.outputs['Incoming'],dot.inputs[1]);absolute=nodes.new('ShaderNodeMath');absolute.operation='ABSOLUTE';links.new(dot.outputs['Value'],absolute.inputs[0])
   gain=nodes.new('ShaderNodeMath');gain.operation='MULTIPLY_ADD';gain.inputs[1].default_value=.20;gain.inputs[2].default_value=.80;links.new(absolute.outputs[0],gain.inputs[0])
   mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=(*rgb,1);links.new(ramp.outputs['Color'],mix.inputs[2])
   tone=nodes.new('ShaderNodeMixRGB');tone.blend_type='MULTIPLY';tone.inputs[0].default_value=1;links.new(mix.outputs[0],tone.inputs[1]);links.new(gain.outputs[0],tone.inputs[2]);links.new(tone.outputs[0],emit.inputs['Color'])
  self.mats[color]=m;return m
 def mesh(self,name,verts,faces,color,role='body'):
  data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update();o=bpy.data.objects.new(self.col.name+' '+name,data);self.col.objects.link(o);o.parent=self.root;o.data.materials.append(self.mat(color));o['studyRole']=role;self.parts.append(o);return o
 def block(self,name,x,y,z,w,d,h,color,bevel=.035):
  b=min(bevel,w*.2,d*.2,h*.24);outline=[(-w/2+b,-d/2),(w/2-b,-d/2),(w/2,-d/2+b),(w/2,d/2-b),(w/2-b,d/2),(-w/2+b,d/2),(-w/2,d/2-b),(-w/2,-d/2+b)]
  verts=[]
  for zz,inset in [(z,b),(z+b,0),(z+h-b,0),(z+h,b)]:
   for xx,yy in outline:verts.append((x+xx*(1-2*inset/w),y+yy*(1-2*inset/d),zz))
  faces=[tuple(reversed(range(8))),tuple(range(24,32))]+[(r*8+i,r*8+(i+1)%8,(r+1)*8+(i+1)%8,(r+1)*8+i) for r in range(3) for i in range(8)]
  return self.mesh(name,verts,faces,color)
 def boulder(self,name,x,y,z,w,d,h,color='cobalt',variant=0):
  # Three drawn contours, with broad shallow crowns, not procedural random pillars.
  contours=[ [(-.5,-.32),(-.30,-.5),(.24,-.5),(.5,-.25),(.5,.30),(.27,.5),(-.28,.5),(-.5,.25)], [(-.5,-.30),(-.24,-.5),(.31,-.5),(.5,-.22),(.5,.25),(.23,.5),(-.35,.5),(-.5,.21)], [(-.5,-.24),(-.31,-.5),(.28,-.5),(.5,-.30),(.5,.30),(.29,.5),(-.25,.5),(-.5,.31)] ]
  contour=contours[variant%3];verts=[]
  for level,(zz,scale,dx,dy) in enumerate([(0,1,0,0),(.55,.97,.008,-.009),(.91,.74,-.035,.015),(1,.52,-.045,.025)]):
   for i,(xx,yy) in enumerate(contour):
    dz=[0,.018,-.012,.025,.008,-.02,.01,-.015][i] if level==3 else 0
    verts.append((x+w*(xx*scale+dx),y+d*(yy*scale+dy),z+h*zz+dz))
  faces=[tuple(reversed(range(8))),tuple(range(24,32))]+[(r*8+i,r*8+(i+1)%8,(r+1)*8+(i+1)%8,(r+1)*8+i) for r in range(3) for i in range(8)]
  o=self.mesh(name,verts,faces,color);o.data.materials.append(self.mat('slateTop' if color=='slate' else 'cobaltTop' if color=='cobalt' else color));o.data.materials.append(self.mat('slateDark' if color=='slate' else 'cobaltDark' if color=='cobalt' else color))
  for i,p in enumerate(o.data.polygons):p.material_index=1 if i==1 or i in (18,21,24) else 2 if i in (2,8,13) else 0
 def sweep(self,name,points,radii,color,role='vegetation',sides=7):
  verts=[]
  for j,p in enumerate(points):
   p=Vector(p);axis=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(j-1,0)]);axis.normalize();side=axis.cross(Vector((0,1,0)))
   if side.length<.001:side=axis.cross(Vector((1,0,0)))
   side.normalize();up=axis.cross(side).normalized()
   for i in range(sides):verts.append(tuple(p+radii[j]*(math.cos(i*math.tau/sides)*side+math.sin(i*math.tau/sides)*up)))
  faces=[tuple(reversed(range(sides))),tuple(range((len(points)-1)*sides,len(points)*sides))]+[(j*sides+i,j*sides+(i+1)%sides,(j+1)*sides+(i+1)%sides,(j+1)*sides+i) for j in range(len(points)-1) for i in range(sides)]
  return self.mesh(name,verts,faces,color,role)
 def coral(self,name,x,y,h,r,dx,dy,color='pink'):
  n=12;verts=[];z=.055
  for t,rr in [(0,.78),(.32,.98),(.72,1),(1,1.08),(1,.70),(.80,.63)]:
   for i in range(n):
    a=i*math.tau/n;verts.append((x+dx*t+r*rr*math.cos(a),y+dy*t+r*rr*math.sin(a),z+h*t))
  faces=[tuple(reversed(range(n)))]+[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(5) for i in range(n)]+[tuple(range(5*n,6*n))]
  o=self.mesh(name,verts,faces,color,'vegetation');o.data.materials.append(self.mat('violetInside' if color=='violet' else 'pinkInside'))
  for i,p in enumerate(o.data.polygons):
   if i>4*n:p.material_index=1
 def kelp(self,name,x,y,h,dx,dy=0):
  z=.065;pts=[(x,y,z),(x-.035,y+.01,z+h*.24),(x+.04,y-.008,z+h*.47),(x+dx*.55,y+dy*.5,z+h*.70),(x+dx,y+dy,z+h*.91),(x+dx-.012,y+dy,z+h)]
  self.sweep(name,pts,[.092,.103,.091,.083,.055,.014],'green')
  self.sweep(name+' fork',[(x+.04,y-.008,z+h*.47),(x-.10,y+.025,z+h*.63),(x-.08,y+.035,z+h*.79)],[.069,.074,.016],'greenLight')
 def shrub(self,name,x,y,z,h=.95,spread=.36):
  # Pointed broad faceted leaves around thick branching stems, following the concept.
  for i,(dx,dy,t) in enumerate([(-.16,.02,.74),(.13,.05,.86),(-.04,-.12,1),(.11,-.09,.56),(-.12,-.08,.53)]):
   dx*=spread/.36;dy*=spread/.36
   self.sweep(name+' stem '+str(i),[(x,y,z),(x+dx*.45,y+dy*.45,z+h*t*.45),(x+dx,y+dy,z+h*t*.92)],[.045,.055,.022],'greenDark')
   cx=x+dx*.72;cy=y+dy*.72;zz=z+h*t*.42;w=.16*(spread/.36);d=.145*(spread/.36)
   verts=[(cx-w/2,cy,zz),(cx,cy-d/2,zz+.06),(cx+w/2,cy,zz),(cx,cy+d/2,zz+.04),(x+dx-w*.55,y+dy,z+h*t*.79),(x+dx,y+dy-d*.55,z+h*t*.82),(x+dx+w*.55,y+dy,z+h*t*.78),(x+dx,y+dy+d*.55,z+h*t*.83),(x+dx*1.2,y+dy*1.2,z+h*t)]
   self.mesh(name+' broad leaf '+str(i),verts,[(0,1,2,3),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0),(4,8,5),(5,8,6),(6,8,7),(7,8,4)],'greenLight' if i%3==0 else 'green','vegetation')
 def moss(self,name,x,y,z,s=.12):
  self.block(name,x,y,z,s,s*.85,s*.85,'moss',.012)
 def rock_bank(self,color,height):
  self.boulder('broad front shoulder',-.19,-.27,0,.62,.46,height*.46,color,0)
  self.boulder('back left crown',-.245,.18,0,.51,.64,height*.82,color,1)
  self.boulder('back right crown',.235,.17,0,.53,.66,height,color,2)
  self.boulder('right front ledge',.275,-.28,0,.45,.44,height*.60,color,1)
 def crate(self,name,x,y,z,w,d,h):
  self.block(name+' box',x,y,z,w,d,h,'wood',.018)
  for xx in [x-w/2+.045,x+w/2-.045]:self.block(name+' front upright',xx,y-d/2-.006,z,.085,.035,h,'woodLight',.008)
  for zz in [z,z+h-.085]:self.block(name+' front rail',x,y-d/2-.008,zz,w,.04,.085,'woodLight',.006)
  # Diagonal braces lie just in front of each real crate front plane.
  for sign in [-1,1]:self.sweep(name+' diagonal '+str(sign),[(x-sign*(w/2-.09),y-d/2-.033,z+.105),(x+sign*(w/2-.09),y-d/2-.033,z+h-.105)],[.032,.032],'woodDark','body',4)
 def build(self):
  if self.id in ('ocean-floor','restaurant-floor'):
   self.mesh('shared continuous ground',[(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[(0,1,2,3)],'ocean' if self.id=='ocean-floor' else 'cream');return
  if self.id in ('cobalt-crags','cobalt-shelf','slate-bank'):
   self.rock_bank('slate' if self.id=='slate-bank' else 'cobalt',{'cobalt-crags':2.55,'cobalt-shelf':1.05,'slate-bank':2.35}[self.id]);return
  if self.id=='pink-coral':
   self.boulder('low encrusting reef',0,0,0,1,1,.085,'violet',0)
   for name,x,y,h,r,dx,dy,c in [('central',0,.20,1.36,.13,0,.04,'pink'),('left',-.23,.10,1.06,.125,-.105,.03,'pink'),('right',.23,.14,1.14,.12,.11,.01,'pink'),('front-left',-.24,-.27,.72,.115,-.07,-.02,'pink'),('front-right',.23,-.25,.83,.12,.08,-.03,'pink'),('violet rear',-.12,.30,.94,.10,-.05,.035,'violet'),('violet front',.04,-.29,.60,.115,.02,-.035,'violet')]:self.coral(name,x,y,h,r,dx,dy,c)
   return
  if self.id=='kelp-fan':
   self.boulder('low rhizome and pebbles',0,0,0,1,1,.09,'greenDark',0)
   for i,(x,y,h,dx,dy) in enumerate([(-.27,.27,1.80,.035,0),(.13,.27,2.02,.095,.02),(.30,-.02,1.62,.045,-.01),(-.27,-.05,1.51,.03,0),(-.19,-.31,1.32,.04,0),(.19,-.30,1.50,.07,0),(.02,.02,1.81,.02,.015)]):self.kelp('ribbon '+str(i),x,y,h,dx,dy)
   return
  if self.id=='pale-column':
   self.block('square ruined foot',0,0,0,1,1,.25,'paleSide',.07)
   outline=[(-.34,-.25),(-.19,-.35),(.24,-.35),(.34,-.19),(.34,.25),(.19,.34),(-.23,.34),(-.34,.18)]
   vv=[(x,y,.22) for x,y in outline]+[(x,y,1.63+v) for (x,y),v in zip(outline,[.02,-.04,0,.09,.10,.035,-.015,.025])]
   self.mesh('broad fractured pillar',vv,[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)],'pale')
   for x,y,z in [(-.20,-.30,.24),(.04,-.32,.24),(.29,-.13,.24),(-.22,.15,1.68),(.10,.18,1.67),(.20,.02,1.65),(-.31,.04,.26)]:self.moss('lime growth',x,y,z,.14)
   self.sweep('fracture on front',[(-.03,-.353,1.56),(.045,-.353,1.29),(-.01,-.353,1.05),(.07,-.353,.88)],[.008]*4,'crack','body',4);return
  if self.id=='reef-face':
   self.boulder('footing rubble',0,0,0,1,1,.25,'cobalt',0)
   self.block('broad carved head',0,.03,.24,.68,.58,1.42,'pale',.10)
   self.block('tall forehead',0,.015,1.54,.74,.59,.38,'pale',.06)
   self.block('heavy brow',0,-.33,1.31,.82,.15,.19,'paleSide',.025)
   for x in [-.19,.19]:self.block('deep eye',x,-.27,1.17,.18,.075,.13,'crack',.025)
   self.block('nose bridge',0,-.295,.80,.17,.27,.51,'pale',.032)
   self.block('nose base',0,-.34,.79,.25,.25,.14,'paleSide',.022)
   self.block('closed mouth',0,-.275,.62,.34,.06,.04,'crack',.012)
   self.block('lower lip',0,-.29,.55,.36,.10,.11,'paleSide',.025)
   for x in [-.38,.38]:self.block('ear',x,.04,1.01,.14,.24,.34,'paleSide',.06)
   for x,y,z,s in [(-.22,.1,1.91,.19),(.10,.13,1.91,.22),(.27,-.01,1.90,.12),(.37,.10,.33,.15),(.38,.15,.52,.12),(-.34,-.17,.28,.13)]:self.moss('moss on face',x,y,z,s)
   return
  if self.id=='angular-shrub':
   self.boulder('slate undergrowth left',-.23,.02,0,.54,.96,.35,'slate',1);self.boulder('slate undergrowth right',.23,0,0,.54,1,.24,'slate',2)
   for i,(x,y,z,h) in enumerate([(-.24,.23,.15,1.27),(.20,.22,.13,1.45),(-.22,-.26,.16,1.02),(.22,-.25,.13,1.15),(0,-.02,.20,1.38)]):self.shrub('dense shrub '+str(i),x,y,z,h,.37)
   return
  if self.id=='wood-planter':
   self.block('full wooden planter',0,0,0,1,1,.57,'woodDark',.025)
   for i in range(5):
    x=-.40+i*.2;self.block('front plank '+str(i),x,-.483,.035,.19,.034,.53,'wood' if i%2 else 'woodLight',.007)
    self.block('rear plank '+str(i),x,.483,.035,.19,.034,.53,'wood',.007)
    y=-.40+i*.2;self.block('side plank L'+str(i),-.483,y,.035,.034,.19,.53,'wood',.007);self.block('side plank R'+str(i),.483,y,.035,.034,.19,.53,'woodLight',.007)
   self.block('dark recessed soil',0,0,.54,.88,.88,.035,'soil',.012)
   for i,(x,y,h) in enumerate([(-.22,.22,.96),(.20,.20,1.15),(-.21,-.19,.86),(.21,-.20,.93),(0,0,1.18)]):self.shrub('planter foliage '+str(i),x,y,.56,h,.36)
   return
  if self.id=='crate-stack':
   self.crate('front crate',-.19,-.12,0,.62,.62,.70);self.crate('rear crate',.19,.18,0,.62,.64,.68);self.crate('upper small crate',.14,.13,.68,.54,.56,.57);return
  if self.id=='cone-curb':
   self.boulder('low slate corner',.17,.17,0,.66,.66,.62,'slate',1)
   self.block('front charcoal curb',0,-.425,0,1,.15,.15,'charcoal',.014);self.block('side charcoal curb',-.425,0,0,.15,1,.15,'charcoal',.014)
   for i in range(3):
    self.block('front yellow stripe '+str(i),-.35+i*.35,-.425,.145,.16,.15,.012,'yellow',.003)
    self.block('side yellow stripe '+str(i),-.425,-.35+i*.35,.145,.15,.16,.012,'yellow',.003)
   self.block('cone square base',-.12,-.13,.15,.53,.53,.10,'orange',.055)
   # Four-sided cone with a broad cream safety band.
   for name,z,r1,r2,h,c in [('lower orange',.25,.20,.135,.29,'orange'),('cream band',.54,.135,.097,.17,'white'),('upper orange',.71,.097,.045,.23,'orange')]:
    vv=[(-.12+sx*r,-.13+sy*r,zz) for zz,r in [(z,r1),(z+h,r2)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]];self.mesh(name,vv,[(0,3,2,1),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)],c)
   return
  if self.id=='lantern-garden':
   self.block('timber base',-.14,.05,0,.72,.90,.40,'wood',.035);self.block('lantern post',-.18,.13,.36,.20,.20,1.81,'woodDark',.022)
   self.block('hanging arm',-.16,-.08,1.98,.18,.50,.14,'wood',.02)
   self.sweep('warm paper lantern',[(-.16,-.18,1.02),(-.16,-.18,1.12),(-.16,-.18,1.70),(-.16,-.18,1.80)],[.19,.235,.235,.19],'lantern','body',12)
   for z in [1.03,1.24,1.56,1.76]:self.sweep('lantern ring',[(-.16,-.18,z),(-.16,-.18,z+.035)],[.233,.233],'yellow','body',12)
   for x in [-.32,0]:self.block('lantern vertical rib',x,-.36,1.10,.025,.03,.62,'yellow',.006)
   self.boulder('side garden stone',.28,-.1,0,.44,.80,.27,'slate',1)
   self.shrub('lantern-side shrub',.26,.11,.12,1.13,.30);self.shrub('front shrub',.25,-.28,.12,.73,.29)
   return
  raise ValueError(self.id)

def camera(scene,profile="oblique70"):
 c=scene.camera;scene.render.resolution_x=FRAME[0]*SCALE;scene.render.resolution_y=FRAME[1]*SCALE
 ordinary=profile=="ordinary35"
 scene.render.pixel_aspect_x=1 if ordinary else math.sqrt(1+HEIGHT*HEIGHT);scene.render.pixel_aspect_y=1
 a=math.radians(35) if ordinary else math.atan(1/HEIGHT);c.data.type='ORTHO';c.data.sensor_fit='HORIZONTAL';c.data.ortho_scale=FRAME[0]/CELL
 c.location=(0,-10*math.cos(a),10*math.sin(a));c.rotation_euler=(-c.location).to_track_quat('-Z','Y').to_euler();c.data.shift_x=c.data.shift_y=0
 def px(p):
  v=world_to_camera_view(scene,c,Vector(p));return Vector((v.x*FRAME[0]*SCALE,(1-v.y)*FRAME[1]*SCALE))
 bpy.context.view_layer.update();o=px((0,0,0));c.data.shift_x=1;bpy.context.view_layer.update();dx=px((0,0,0)).x-o.x;c.data.shift_x=(ROOT[0]*SCALE-o.x)/dx
 c.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-o.y;c.data.shift_y=(ROOT[1]*SCALE-o.y)/dy;bpy.context.view_layer.update()
 origin=px((0,0,0));vectors=[px(p)-origin for p in [(1,0,0),(0,-1,0),(0,0,1)]]
 assert (origin-Vector([v*SCALE for v in ROOT])).length<.05
 depth_factor=math.sin(a) if ordinary else 1
 height_factor=math.cos(a) if ordinary else HEIGHT
 for actual,expected in zip(vectors,[(CELL*SCALE,0),(0,CELL*SCALE*depth_factor),(0,-CELL*SCALE*height_factor)]):assert (actual-Vector(expected)).length<.05
 matrix=c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=FRAME[0]*SCALE,y=FRAME[1]*SCALE,scale_x=scene.render.pixel_aspect_x,scale_y=1)
 return {'worldMatrix':rows(c.matrix_world),'projectionMatrix':rows(matrix),'profile':profile,'heightRatio':height_factor,'depthRatio':depth_factor,'elevationDegrees':math.degrees(a),'pixelAspect':[scene.render.pixel_aspect_x,1],'calibration':{'root':list(origin/SCALE),'x':list(vectors[0]/SCALE),'depth':list(vectors[1]/SCALE),'height':list(vectors[2]/SCALE)}}
def settings(scene):
 scene.render.engine='BLENDER_EEVEE';scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.resolution_percentage=100
 scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1

def geometry(col):
 dep=bpy.context.evaluated_depsgraph_get();out=[];allv=[]
 for o in col.all_objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(dep);me=ev.to_mesh()
  try:
   vv=[list(ev.matrix_world@v.co) for v in me.vertices];allv+=vv;out.append({'name':o.name,'vertices':vv,'faces':[list(f.vertices) for f in me.polygons],'role':o.get('studyRole','body')})
  finally:ev.to_mesh_clear()
 lo=[min(v[i] for v in allv) for i in range(3)];hi=[max(v[i] for v in allv) for i in range(3)]
 return {'objects':out,'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}
def pose(man,ident,direction):
 for item in man['objects']:
  c=bpy.data.collections[item['collection']];c.hide_render=item['id']!=ident;c.hide_viewport=item['id']!=ident
  r=bpy.data.objects[item['rootObject']];r.rotation_euler.z=DIRS[direction] if item['id']==ident else 0
 bpy.context.view_layer.update()

def create(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);assert not (out/'concept-decoration.blend').exists()
 prefix='S33 concept decor '+uuid.uuid4().hex[:8];scene=bpy.data.scenes.new(prefix)
 man={'schemaVersion':1,'scene':scene.name,'cellSize':CELL,'frameSize':FRAME,'root':ROOT,'sourceScale':SCALE,'heightRatio':HEIGHT,'directions':list(DIRS),'nativeProject':'concept-decoration.blend','sourceHash':sha(__file__),'objects':[],'status':'authored','scope':'Concept-referenced static native asset review; final style reskin and production rollout await review.'}
 with active(scene):
  settings(scene);scene.camera=bpy.data.objects.new(prefix+' camera',bpy.data.cameras.new(prefix+' camera'));scene.collection.objects.link(scene.camera)
  scene.world=bpy.data.worlds.new(prefix+' world');scene.world.use_nodes=True;next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=0
  for ident,theme,name,kind,height,crop,description in DESIGNS:
   model=Piece(scene,prefix,ident,height);model.build();man['objects'].append({'id':ident,'theme':theme,'name':name,'kind':kind,'heightBand':'ground' if kind=='ground' else 'tall' if height>2 else 'medium' if height>1 else 'low','collection':model.col.name,'rootObject':model.root.name,'images':{},'receipts':{},'referenceCrop':crop,'description':description})
  for item in man['objects']:
   pose(man,item['id'],'S');g=geometry(bpy.data.collections[item['collection']]);item['bounds']={k:g[k] for k in ('min','max','dimensions')};item['height']=g['max'][2]
   projected=[-v[1]-.7*v[2] for p in g['objects'] for v in p['vertices']];item['baselineSilhouetteHeight']=max(projected)-min(projected)
   assert item['height']*math.cos(math.radians(35))<3,(item['id'],item['height'])
   assert min(g['min'][:2])>=-.501 and max(g['max'][:2])<=.501,(item['id'],item['bounds'])
   write(out/('geometry/'+item['id']+'.json'),g);item['geometry']='geometry/'+item['id']+'.json';item['geometrySHA256']=sha(out/item['geometry'])
  man['camera']=camera(scene);pose(man,'pink-coral','S');bpy.data.libraries.write(str(out/man['nativeProject']),{scene},fake_user=True,compress=True)
 man['nativeProjectSHA256']=sha(out/man['nativeProject']);write(out/'study.json',man);return {'scene':scene.name,'objects':len(man['objects']),'manifest':str(out/'study.json')}

@contextlib.contextmanager
def capture_projection(collection,profile):
 saved=[]
 try:
  if profile=='ordinary35':
   for obj in collection.all_objects:
    if obj.type!='MESH':continue
    original=[v.co.copy() for v in obj.data.vertices];saved.append((obj,original));inverse=obj.matrix_world.inverted()
    for v in obj.data.vertices:
     world=obj.matrix_world@v.co
     blend=max(0,1-max(0,world.z)/FOOTING_TRANSITION)**2
     world.y*=1+(1/math.sin(math.radians(35))-1)*blend
     v.co=inverse@world
    obj.data.update()
   bpy.context.view_layer.update()
  yield
 finally:
  for obj,original in saved:
   for v,co in zip(obj.data.vertices,original):v.co=co
   obj.data.update()
  bpy.context.view_layer.update()

def capture(out):
 out=Path(out);man=json.loads((out/'study.json').read_text());assert sha(out/man['nativeProject'])==man['nativeProjectSHA256'];scene=bpy.data.scenes[man['scene']]
 with active(scene):
  settings(scene)
  for item in man['objects']:
   item['profiles']={}
   for profile in (['oblique70'] if item['heightBand']=='ground' else ['oblique70','ordinary35']):
    item['profiles'][profile]={'images':{},'receipts':{}}
    for facing in (['S'] if item['heightBand']=='ground' else DIRS):
     pose(man,item['id'],facing);cam=camera(scene,profile);g=geometry(bpy.data.collections[item['collection']]);assert min(g['min'][:2])>=-.501 and max(g['max'][:2])<=.501,(item['id'],g['min'],g['max'])
     img=f"sprites/{profile}/{item['id']}/{facing}.png";target=out/img;target.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(target)
     with capture_projection(bpy.data.collections[item['collection']],profile):
      capture_g=geometry(bpy.data.collections[item['collection']]);bpy.ops.render.render(write_still=True,scene=scene.name)
      capture_path=f"capture-geometry/{profile}/{item['id']}/{facing}.json";write(out/capture_path,capture_g)
     rec={'id':item['id'],'facing':facing,'bounds':{k:g[k] for k in ('min','max','dimensions')},'camera':cam,'frameSize':FRAME,'root':ROOT,'sourceScale':SCALE,'nativeProjectSHA256':man['nativeProjectSHA256'],'image':img,'imageSHA256':sha(target),'rootMatrix':rows(bpy.data.objects[item['rootObject']].matrix_world),'captureGeometry':capture_path,'captureGeometrySHA256':sha(out/capture_path),'squareFooting':profile=='ordinary35','footingTransitionHeight':FOOTING_TRANSITION if profile=='ordinary35' else 0}
     path=f"cameras/{profile}/{item['id']}/{facing}.json";write(out/path,rec);item['profiles'][profile]['images'][facing]=img;item['profiles'][profile]['receipts'][facing]=path
     print('DECOR_CAPTURE '+profile+'/'+item['id']+'/'+facing,flush=True)
   item['images']=item['profiles']['oblique70']['images'];item['receipts']=item['profiles']['oblique70']['receipts']
 man['status']='captured';write(out/'study.json',man)
if __name__=='__main__' and '--capture' in sys.argv:capture(sys.argv[sys.argv.index('--capture')+1])
