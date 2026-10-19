"""Isolated native decoration coverage study. Author with Blender MCP, capture via CLI.
No production scene mutations. Static shape/layout study, not final reskinned art.
"""
import bpy, math, json, hashlib, sys, argparse, uuid, contextlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
CELL=128; FRAME=[192,768]; ROOT=[96,688]; SCALE=4; HEIGHT=.7
PROJECTED_HEIGHTS={'low-rock':.9,'coral':1.45,'column':1.8,'kelp':2.0,'spire':2.3}
FOOTING_TRANSITION=.42
DIRS={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
COLORS={'rock':'347AC4','rockLight':'3C80C8','rockDark':'3074BC','sand':'2AADC0','coral':'E94781','coralLight':'F66E99','coralDark':'972D67','purple':'8754CF','blueCoral':'407BEE','orangeCoral':'F59A38','kelp':'43A447','kelpLight':'76C942','kelpDark':'237746','stone':'CADBD8','stoneSide':'9ABCBF'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(d,indent=2)+'\n')
def rows(m):return [[float(v) for v in r] for r in m]
@contextlib.contextmanager
def active(scene):
 old=bpy.context.window.scene
 try:
  bpy.context.window.scene=scene
  yield
 finally:bpy.context.window.scene=old
class Piece:
 def __init__(self,scene,prefix,ident):
  self.id=ident;self.col=bpy.data.collections.new(prefix+' '+ident);scene.collection.children.link(self.col)
  self.root=bpy.data.objects.new(prefix+' '+ident+' root',None);self.col.objects.link(self.root);self.mats={};self.parts=[]
 def mat(self,color):
  if color in self.mats:return self.mats[color]
  h=COLORS.get(color,color);rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
  m=bpy.data.materials.new(self.col.name+' '+color);m.use_nodes=True;m.diffuse_color=(*rgb,1)
  nodes=m.node_tree.nodes;links=m.node_tree.links
  nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');emit=nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(*rgb,1);emit.inputs['Strength'].default_value=1
  links.new(emit.outputs[0],output.inputs['Surface'])
  if color.startswith('rock'):
   # Light-independent surface tone: height and surface slope, never light azimuth.
   pos=nodes.new('ShaderNodeNewGeometry');xyz=nodes.new('ShaderNodeSeparateXYZ')
   span=nodes.new('ShaderNodeMapRange');span.inputs['From Min'].default_value=0;span.inputs['From Max'].default_value=max(.5,self.base_height)
   ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.17,.23,.34,1);ramp.color_ramp.elements[1].color=(1,1,1,1)
   mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=(*rgb,1)
   links.new(pos.outputs['Position'],xyz.inputs[0]);links.new(xyz.outputs['Z'],span.inputs['Value']);links.new(span.outputs['Result'],ramp.inputs[0]);links.new(ramp.outputs['Color'],mix.inputs[2])
   normal=nodes.new('ShaderNodeSeparateXYZ');slope=nodes.new('ShaderNodeMath');slope.operation='ABSOLUTE';gain=nodes.new('ShaderNodeMath');gain.operation='MULTIPLY_ADD';gain.inputs[1].default_value=.16;gain.inputs[2].default_value=.84
   final=nodes.new('ShaderNodeMixRGB');final.blend_type='MULTIPLY';final.inputs[0].default_value=1
   links.new(pos.outputs['Normal'],normal.inputs[0]);links.new(normal.outputs['Z'],slope.inputs[0]);links.new(slope.outputs[0],gain.inputs[0]);links.new(mix.outputs[0],final.inputs[1]);links.new(gain.outputs[0],final.inputs[2]);links.new(final.outputs[0],emit.inputs['Color'])
  self.mats[color]=m;return m
 def mesh(self,name,verts,faces,color):
  d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new(self.col.name+' '+name,d);self.col.objects.link(o);o.parent=self.root;o.data.materials.append(self.mat(color));self.parts.append(o);return o
 def rock(self,name,x,y,w,d,h,color='rock',z=0,seed=0):
  # Broad eight-sided footprint; asymmetric top planes rather than a rectangular plinth.
  outline=[(-.5,-.31),(-.31,-.5),(.32,-.5),(.5,-.29),(.5,.33),(.30,.5),(-.34,.5),(-.5,.29)]
  verts=[(x+a*w,y+b*d,z) for a,b in outline]
  verts += [(x+a*w*.84+.023*w*math.sin(seed),y+b*d*.82,z+h*(.72+.13*math.sin(i*1.7+seed))) for i,(a,b) in enumerate(outline)]
  verts += [(x-w*.08,y+d*.05,z+h)]
  faces=[tuple(reversed(range(8)))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]+[(i+8,(i+1)%8+8,16) for i in range(8)]
  o=self.mesh(name,verts,faces,color);o.data.materials.append(self.mat('rockLight' if color=='rock' else color));o.data.materials.append(self.mat('rockDark' if color=='rock' else color))
  for i,p in enumerate(o.data.polygons):p.material_index=1 if i>8 and i%3==0 else 2 if i in (2,7) else 0
  return o
 def tube(self,name,x,y,z,h,r,color,lean=0):
  # Squat organic sponge: swollen body, curved centre and thick flared scalloped lip.
  n=14;verts=[]
  rings=[(0,.68),(.20,.94),(.47,1.08),(.74,.96),(.93,1.17),(1,1.24),(.98,.81),(.78,.67),(.50,.43)]
  for t,rad in rings:
   cx=x+lean*math.sin(t*1.8);cy=y+.012*math.sin(t*2.5)
   for i in range(n):
    a=i*math.tau/n;wave=1+.065*math.sin(a*3+t*2)
    verts.append((cx+r*rad*wave*math.cos(a),cy+r*rad*wave*math.sin(a),z+h*t+(.009*math.sin(a*3) if t>.9 else 0)))
  faces=[tuple(reversed(range(n)))]+[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(rings)-1) for i in range(n)]+[tuple(range((len(rings)-1)*n,len(rings)*n))]
  o=self.mesh(name,verts,faces,color);o.data.materials.append(self.mat('coralDark'))
  for i,p in enumerate(o.data.polygons):
   if i>6*n:p.material_index=1

 def branch(self,name,points,radii,color):
  n=9;verts=[]
  for j,point in enumerate(points):
   p=Vector(point);tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
   tangent.normalize();side=tangent.cross(Vector((0,1,0)))
   if side.length<.001:side=tangent.cross(Vector((1,0,0)))
   side.normalize();up=tangent.cross(side).normalized()
   for i in range(n):verts.append(tuple(p+radii[j]*(side*math.cos(i*math.tau/n)+up*math.sin(i*math.tau/n))))
  faces=[tuple(reversed(range(n)))]+[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(points)-1) for i in range(n)]+[tuple(range((len(points)-1)*n,len(points)*n))]
  self.mesh(name,verts,faces,color)

 def fan(self,name,x,y,z,color):
  self.branch(name+' trunk',[(x,y,z),(x-.01,y,z+.12),(x+.01,y,z+.25),(x,y,z+.38)],[.045,.048,.039,.023],color)
  for i,sign in enumerate([-1,1]):
   self.branch(name+' lower arm '+str(i),[(x,y,z+.10),(x+sign*.08,y,z+.17),(x+sign*.12,y,z+.28)],[.039,.033,.018],color)
   self.branch(name+' upper arm '+str(i),[(x,y,z+.22),(x+sign*.065,y+.01,z+.29),(x+sign*.085,y+.005,z+.41)],[.032,.027,.016],color)
 def leaf(self,name,x,y,z,h,w,lean,phase):
  verts=[];n=8;angle=phase*.63
  for i in range(n):
   t=i/(n-1);ww=w*(.42+.58*math.sin(t*math.pi))*(.08 if i==n-1 else 1)
   xx=x+lean*t+.035*math.sin(t*math.pi*2+phase)*math.sin(t*math.pi)
   yy=y+.025*math.sin(t*math.pi+phase)
   for dx,dy in ((-ww/2,0),(0,-ww*.28),(ww/2,0),(0,ww*.28)):
    verts.append((xx+dx*math.cos(angle)-dy*math.sin(angle),yy+dx*math.sin(angle)+dy*math.cos(angle),z+h*t))
  faces=[(3,2,1,0),tuple(range((n-1)*4,n*4))]
  for i in range(n-1):
   for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
  o=self.mesh(name,verts,faces,'kelp');o.data.materials.append(self.mat('kelpLight'));o.data.materials.append(self.mat('kelpDark'))
  for i,p in enumerate(o.data.polygons):p.material_index=1 if (i-2)%4==0 else 2 if (i-2)%4==2 else 0
 def floor(self,variant):
  # Matching boundary color; subtle interior facets cannot form repeated wave stripes.
  edge=[(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]
  verts=[(x,y,0) for x,y in edge]+[(-.18+.06*variant,-.1,0),(.17,.16-.05*variant,0)]
  o=self.mesh('ocean bed',verts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5),(4,5,3)],'sand')
  # One matte color on the boundary and interior avoids baked checker seams.
  return o
 def ledge(self,name,x,y,w,d,top,seed):
  # Unequal shoulders, bulges and offset layers; no long straight cut column sides.
  outline=[(-.5,-.35),(-.34,-.5),(.31,-.5),(.5,-.28),(.5,.38),(.32,.5),(-.36,.5),(-.5,.29)]
  verts=[];profile=[(0,1),(.19,.97),(.44,.80),(.68,.94),(.86,.73),(1,.79)]
  for ring,(fraction,scale) in enumerate(profile):
   dx=min(.065,(1-scale)*.46)*math.sin(seed+ring*1.7);dy=min(.055,(1-scale)*.46)*math.cos(seed+ring*1.3)
   for i,(xx,yy) in enumerate(outline):
    radial=1 if ring==0 else 1-.08*(.5+.5*math.sin(i*2.1+seed+ring))
    zz=top*fraction
    if ring not in (0,len(profile)-1):zz+=min(.15,top*.10)*math.sin(i*1.8+seed+ring)
    if ring==len(profile)-1:zz-=min(.17,top*.15)*(.5+.5*math.sin(i*1.6+seed))
    verts.append((x+(xx*scale*radial+dx)*w,y+(yy*scale*radial+dy)*d,max(0,zz)))
  last=(len(profile)-1)*8;verts.append((x-.03*w,y+.02*d,top-min(.075,top*.075)));centre=len(verts)-1
  faces=[tuple(reversed(range(8)))];matids=[0]
  for ring in range(len(profile)-1):
   for i in range(8):
    a=ring*8+i;b=ring*8+(i+1)%8;c=(ring+1)*8+(i+1)%8;dd=(ring+1)*8+i
    faces.extend([(a,b,dd),(b,c,dd)]);matids.extend([(ring+i+seed)%3,(ring+i+seed+1)%3])
  for i in range(8):faces.append((last+i,last+(i+1)%8,centre));matids.append(1 if i%3 else 0)
  o=self.mesh(name,verts,faces,'rock');o.data.materials.append(self.mat('rockLight'));o.data.materials.append(self.mat('rockDark'))
  for i,face in enumerate(o.data.polygons):face.material_index=matids[i]
  self.rock_parts.append(o)

 def surface(self,x,y):
  heights=[]
  for obj in self.rock_parts:
   for face in obj.data.polygons:
    if len(face.vertices)!=3:continue
    a,b,c=[obj.data.vertices[i].co for i in face.vertices]
    den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
    if abs(den)<1e-8:continue
    u=((b.y-c.y)*(x-c.x)+(c.x-b.x)*(y-c.y))/den;v=((c.y-a.y)*(x-c.x)+(a.x-c.x)*(y-c.y))/den
    if min(u,v,1-u-v)>=-1e-6:heights.append(u*a.z+v*b.z+(1-u-v)*c.z)
  assert heights,(self.id,x,y)
  return max(heights)

 def growth(self,kind,band,x,y,index,color='coral'):
  z=self.surface(x,y)
  if kind=='kelp':
   for j,(dx,dy,h,w) in enumerate([(-.045,0,.48,.13),(.04,.018,.70,.16),(0,-.035,.60,.15)]):
    zz=self.surface(x+dx,y+dy)
    self.leaf(f'{band} kelp {index}-{j}',x+dx,y+dy,zz,h,w,.035*math.sin(index+j),index*.8+j)
  else:
   if index%2:
    self.fan(f'{band} branching coral {index}',x,y,z,color)
   else:
    for j,(dx,dy,h,r) in enumerate([(-.065,.02,.22,.082),(.055,0,.31,.10)]):
     zz=self.surface(x+dx,y+dy)
     self.tube(f'{band} flared sponge {index}-{j}',x+dx,y+dy,zz,h,r,color,lean=.012*math.sin(index+j))
  self.decorations.append({'kind':kind,'band':band,'position':[x,y,z],'color':color if kind!='kelp' else 'green','form':'kelp' if kind=='kelp' else 'branching' if index%2 else 'flared-sponge'})

 def build(self):
  self.rock_parts=[];self.decorations=[];self.preserved=[];self.base_height=0
  if self.id.startswith('bed-'):self.floor(0);return
  seed={'low-rock':1,'coral':3,'kelp':5,'spire':7,'column':9}[self.id]
  top=PROJECTED_HEIGHTS[self.id]/HEIGHT-({'low-rock':.36,'coral':.39,'kelp':.70,'spire':.48,'column':.83}[self.id])
  self.base_height=top
  self.ledge('back crag',-.06,.12,.88,.76,top,seed)
  self.ledge('middle ledge',.29,-.20,.42,.60,top*(.48 if self.id in ('kelp','spire') else .58),seed+2)
  self.ledge('front shelf',-.18,-.32,.64,.36,min(.30,top*.24),seed+4)
  top_kind='kelp' if self.id in ('kelp','spire') else 'coral'
  palette={'low-rock':('purple','blueCoral'),'coral':('coral','orangeCoral'),'kelp':('purple','blueCoral'),'spire':('blueCoral','coralLight'),'column':('orangeCoral','purple')}[self.id]
  self.growth('kelp','bottom',-.22,-.35,seed)
  self.growth('coral','bottom',-.02,-.35,seed+1,palette[1])
  self.growth('coral' if self.id in ('coral','column') else 'kelp','middle',.27,-.28,seed+2,palette[0])
  if self.id=='column':
   z=self.surface(-.11,.17)
   self.rock('original-size pale ruin',-.11,.17,.43,.40,.65,'stone',z=z,seed=4)
   self.growth('kelp','top',.17,.30,seed+3)
  else:
   self.growth(top_kind,'top',-.10,.22,seed+3,palette[0])
   self.growth('coral','top',.19,.28,seed+4,palette[1])

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
   vv=[list(ev.matrix_world@v.co) for v in me.vertices];allv+=vv;out.append({'name':o.name,'vertices':vv,'faces':[list(f.vertices) for f in me.polygons]})
  finally:ev.to_mesh_clear()
 lo=[min(v[i] for v in allv) for i in range(3)];hi=[max(v[i] for v in allv) for i in range(3)]
 return {'objects':out,'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}
def pose(man,ident,direction):
 for item in man['objects']:
  c=bpy.data.collections[item['collection']];c.hide_render=item['id']!=ident;c.hide_viewport=item['id']!=ident
  r=bpy.data.objects[item['rootObject']];r.rotation_euler.z=DIRS[direction] if item['id']==ident else 0
 bpy.context.view_layer.update()
def create(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 assert not (out/'decoration-study.blend').exists()
 prefix='S33 decor '+uuid.uuid4().hex[:8];scene=bpy.data.scenes.new(prefix);man={'schemaVersion':1,'scene':scene.name,'cellSize':CELL,'frameSize':FRAME,'root':ROOT,'sourceScale':SCALE,'heightRatio':HEIGHT,'directions':list(DIRS),'nativeProject':'decoration-study.blend','sourceHash':sha(__file__),'objects':[],'status':'authored','scope':'Static native geometry/coverage study, not final reskinned art; production library unchanged.'}
 with active(scene):
  settings(scene);c=bpy.data.objects.new(prefix+' camera',bpy.data.cameras.new(prefix+' camera'));scene.collection.objects.link(c);scene.camera=c
  scene.world=bpy.data.worlds.new(prefix+' world');scene.world.use_nodes=True
  bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.65,.8,1,1);bg.inputs['Strength'].default_value=0
  for name,pos,energy,size in []:
   data=bpy.data.lights.new(prefix+name,'AREA');o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();data.energy=energy;data.shape='DISK';data.size=size
  names={'bed-0':('Ocean bed','ground'),'low-rock':('Blue coral shelf','low'),'coral':('Pink and amber reef','medium'),'kelp':('Kelp terrace','tall'),'spire':('Decorated cobalt crag','tall'),'column':('Ruin garden','medium')}
  for ident,(name,band) in names.items():
   model=Piece(scene,prefix,ident);model.build();man['objects'].append({'id':ident,'name':name,'heightBand':band,'collection':model.col.name,'rootObject':model.root.name,'images':{},'receipts':{},'baseHeight':model.base_height,'decorations':model.decorations})
  man['camera']=camera(scene)
  for item in man['objects']:
   pose(man,item['id'],'S');g=geometry(bpy.data.collections[item['collection']]);item['bounds']={k:g[k] for k in ('min','max','dimensions')};item['height']=g['max'][2]
   assert item['height']*math.cos(math.radians(35))<3,(item['id'],item['height'])
   if item['id'] in PROJECTED_HEIGHTS:
    item['intendedHeightBand']=PROJECTED_HEIGHTS[item['id']]
   projected=[-v[1]-.7*v[2] for part in g['objects'] for v in part['vertices']]
   item['baselineSilhouetteHeight']=max(projected)-min(projected)
   assert min(g['min'][:2])>=-.501 and max(g['max'][:2])<=.501,(item['id'],item['bounds'])
   write(out/('geometry/'+item['id']+'.json'),g)
   item['geometry']='geometry/'+item['id']+'.json';item['geometrySHA256']=sha(out/item['geometry'])
  pose(man,'coral','S');camera(scene)
  bpy.data.libraries.write(str(out/man['nativeProject']),{scene},fake_user=True,compress=True)
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
