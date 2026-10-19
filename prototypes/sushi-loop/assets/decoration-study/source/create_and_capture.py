"""Isolated native decoration coverage study. Author with Blender MCP, capture via CLI.
No production scene mutations. Static shape/layout study, not final reskinned art.
"""
import bpy, math, json, hashlib, sys, argparse, uuid, contextlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
CELL=128; FRAME=[192,768]; ROOT=[96,688]; SCALE=4; HEIGHT=.7
PROJECTED_HEIGHTS={'low-rock':1.0,'coral':1.8,'column':2.5,'kelp':3.0,'spire':4.0}
DIRS={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
COLORS={'rock':'285A88','rockLight':'376F9E','rockDark':'20486D','sand':'2AADC0','coral':'E94781','coralLight':'F66E99','coralDark':'972D67','purple':'8754CF','kelp':'43A447','kelpLight':'76C942','kelpDark':'237746','stone':'CADBD8','stoneSide':'9ABCBF'}
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
  p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.9
  if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.12
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
  n=10;verts=[]
  for zz,rad,shift in ((z,r*.70,0),(z+h*.72,r*.92,lean*.7),(z+h,r,lean),(z+h-.018,r*.62,lean),(z+h-.11,r*.54,lean*.95)):
   verts += [(x+rad*math.cos(i*math.tau/n)+shift,y+rad*math.sin(i*math.tau/n),zz) for i in range(n)]
  faces=[tuple(reversed(range(n)))]+[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(4) for i in range(n)]+[tuple(range(4*n,5*n))]
  o=self.mesh(name,verts,faces,color);o.data.materials.append(self.mat('coralDark'))
  for i,p in enumerate(o.data.polygons):
   if i>3*n:p.material_index=1
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
 def build(self):
  if self.id.startswith('bed-'):self.floor(int(self.id[-1]));return
  self.rock('left ground stone',-.18,-.15,.64,.70,.17,seed=1)
  self.rock('rear ground stone',.12,.20,.76,.60,.22,seed=3)
  self.rock('right ground stone',.34,-.21,.32,.58,.13,seed=5)
  if self.id=='low-rock':
   self.rock('wide low shelf',-.07,.07,.80,.77,.23,z=.13,seed=2)
   self.rock('front fragment',.26,-.29,.38,.38,.16,z=.04,seed=4)
   self.rock('edge fragment',-.34,-.31,.27,.29,.13,z=.04,seed=1)
  elif self.id=='coral':
   for i,(x,y,h,r) in enumerate([(-.12,.21,.67,.17),(-.34,-.10,.48,.12),(.27,.25,.51,.15),(.19,-.04,.72,.13),(-.22,-.30,.25,.16),(.15,-.31,.39,.15),(-.35,.32,.35,.11),(.34,-.28,.25,.10)]):
    self.tube('coral tube '+str(i),x,y,.12,h,r,'coralLight' if i%3==0 else 'purple' if i in (1,4,6) else 'coral',lean=.025*math.sin(i))
  elif self.id=='kelp':
   for i,(x,y,h,w) in enumerate([(-.33,.29,.88,.19),(-.06,.30,1.12,.21),(.28,.30,.94,.20),(-.31,.01,.70,.22),(.02,.02,.92,.24),(.31,-.03,.73,.22),(-.29,-.31,.48,.23),(.02,-.29,.60,.25),(.29,-.31,.46,.22)]):
    self.leaf('kelp blade '+str(i),x,y,.12,h,w,.055*math.sin(i*2),i*.8)
   self.rock('kelp toe rock',.34,-.30,.31,.34,.21,z=.03,seed=4)
  elif self.id=='spire':
   self.rock('tall asymmetric peak',-.16,.14,.64,.69,1.18,z=.12,seed=3)
   self.rock('secondary peak',.28,-.12,.43,.65,.66,z=.10,seed=1)
   self.rock('front skirt',-.18,-.31,.58,.36,.31,z=.04,seed=2)
  elif self.id=='column':
   self.rock('broken pale shaft',-.10,.17,.61,.61,.83,'stone',z=.12,seed=4)
   self.rock('fallen column chunk',.12,-.28,.74,.35,.36,'stoneSide',z=.10,seed=2)
   self.leaf('column growth',.30,.25,.14,.49,.18,.02,1)
   self.leaf('column growth small',.32,.05,.13,.31,.15,.02,2)

 def raise_canopy(self):
  # Remodel native vertex heights around each part's attachment point. Keep the
  # broad ground stones shallow and preserve every X/Y coordinate and tile root.
  if self.id not in PROJECTED_HEIGHTS:return
  upper=[o for o in self.parts if 'ground stone' not in o.name]
  tallest=max(upper,key=lambda o:max(v.co.z for v in o.data.vertices))
  base=min(v.co.z for v in tallest.data.vertices)
  top=max(v.co.z for v in tallest.data.vertices)
  factor=(PROJECTED_HEIGHTS[self.id]/HEIGHT-base)/(top-base)
  for obj in upper:
   attachment=min(v.co.z for v in obj.data.vertices)
   for v in obj.data.vertices:v.co.z=attachment+(v.co.z-attachment)*factor
   obj.data.update()

def camera(scene):
 c=scene.camera;scene.render.resolution_x=FRAME[0]*SCALE;scene.render.resolution_y=FRAME[1]*SCALE
 scene.render.pixel_aspect_x=math.sqrt(1+HEIGHT*HEIGHT);scene.render.pixel_aspect_y=1
 a=math.atan(1/HEIGHT);c.data.type='ORTHO';c.data.sensor_fit='HORIZONTAL';c.data.ortho_scale=FRAME[0]/CELL
 c.location=(0,-10*math.cos(a),10*math.sin(a));c.rotation_euler=(-c.location).to_track_quat('-Z','Y').to_euler();c.data.shift_x=c.data.shift_y=0
 def px(p):
  v=world_to_camera_view(scene,c,Vector(p));return Vector((v.x*FRAME[0]*SCALE,(1-v.y)*FRAME[1]*SCALE))
 bpy.context.view_layer.update();o=px((0,0,0));c.data.shift_x=1;bpy.context.view_layer.update();dx=px((0,0,0)).x-o.x;c.data.shift_x=(ROOT[0]*SCALE-o.x)/dx
 c.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-o.y;c.data.shift_y=(ROOT[1]*SCALE-o.y)/dy;bpy.context.view_layer.update()
 origin=px((0,0,0));vectors=[px(p)-origin for p in [(1,0,0),(0,-1,0),(0,0,1)]]
 assert (origin-Vector([v*SCALE for v in ROOT])).length<.05
 for actual,expected in zip(vectors,[(CELL*SCALE,0),(0,CELL*SCALE),(0,-CELL*SCALE*HEIGHT)]):assert (actual-Vector(expected)).length<.05
 matrix=c.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=FRAME[0]*SCALE,y=FRAME[1]*SCALE,scale_x=scene.render.pixel_aspect_x,scale_y=1)
 return {'worldMatrix':rows(c.matrix_world),'projectionMatrix':rows(matrix),'heightRatio':HEIGHT,'elevationDegrees':math.degrees(a),'pixelAspect':[scene.render.pixel_aspect_x,1],'calibration':{'root':list(origin/SCALE),'x':list(vectors[0]/SCALE),'depth':list(vectors[1]/SCALE),'height':list(vectors[2]/SCALE)}}
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
  bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.65,.8,1,1);bg.inputs['Strength'].default_value=.7
  for name,pos,energy,size in [('key',(-3,-4,7),450,5),('fill',(4,-1,3),180,4)]:
   data=bpy.data.lights.new(prefix+name,'AREA');o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();data.energy=energy;data.shape='DISK';data.size=size
  names={'bed-0':('Ocean bed','ground'),'low-rock':('Rock shelf','low'),'coral':('Full coral tile','medium'),'kelp':('Kelp grove','tall'),'spire':('Cobalt peaks','tall'),'column':('Broken column','medium')}
  for ident,(name,band) in names.items():
   model=Piece(scene,prefix,ident);model.build();model.raise_canopy();man['objects'].append({'id':ident,'name':name,'heightBand':band,'collection':model.col.name,'rootObject':model.root.name,'images':{},'receipts':{}})
  man['camera']=camera(scene)
  for item in man['objects']:
   pose(man,item['id'],'S');g=geometry(bpy.data.collections[item['collection']]);item['bounds']={k:g[k] for k in ('min','max','dimensions')};item['height']=g['max'][2]
   if item['id'] in PROJECTED_HEIGHTS:
    item['targetProjectedHeight']=PROJECTED_HEIGHTS[item['id']]
    assert abs(item['height']*HEIGHT-item['targetProjectedHeight'])<1e-5
   assert min(g['min'][:2])>=-.501 and max(g['max'][:2])<=.501,(item['id'],item['bounds'])
   write(out/('geometry/'+item['id']+'.json'),g)
   item['geometry']='geometry/'+item['id']+'.json';item['geometrySHA256']=sha(out/item['geometry'])
  pose(man,'coral','S');camera(scene)
  bpy.data.libraries.write(str(out/man['nativeProject']),{scene},fake_user=True,compress=True)
 man['nativeProjectSHA256']=sha(out/man['nativeProject']);write(out/'study.json',man);return {'scene':scene.name,'objects':len(man['objects']),'manifest':str(out/'study.json')}
def capture(out):
 out=Path(out);man=json.loads((out/'study.json').read_text());assert sha(out/man['nativeProject'])==man['nativeProjectSHA256'];scene=bpy.data.scenes[man['scene']]
 with active(scene):
  settings(scene)
  for item in man['objects']:
   for facing in (['S'] if item['heightBand']=='ground' else DIRS):
    pose(man,item['id'],facing);cam=camera(scene);g=geometry(bpy.data.collections[item['collection']]);assert min(g['min'][:2])>=-.501 and max(g['max'][:2])<=.501
    img='sprites/'+item['id']+'/'+facing+'.png';target=out/img;target.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(target);bpy.ops.render.render(write_still=True,scene=scene.name)
    rec={'id':item['id'],'facing':facing,'bounds':{k:g[k] for k in ('min','max','dimensions')},'camera':cam,'frameSize':FRAME,'root':ROOT,'sourceScale':SCALE,'nativeProjectSHA256':man['nativeProjectSHA256'],'image':img,'imageSHA256':sha(target),'rootMatrix':rows(bpy.data.objects[item['rootObject']].matrix_world)}
    path='cameras/'+item['id']+'/'+facing+'.json';write(out/path,rec);item['images'][facing]=img;item['receipts'][facing]=path
    print('DECOR_CAPTURE '+item['id']+'/'+facing,flush=True)
 man['status']='captured';write(out/'study.json',man)
if __name__=='__main__' and '--capture' in sys.argv:capture(sys.argv[sys.argv.index('--capture')+1])
