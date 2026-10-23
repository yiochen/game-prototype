"""Portable native authoring/capture recipe. Run with Blender --background --python this.py.
Reads only sibling original-library.blend and ../inputs JSON contract; writes round-02.
Use --replay PROJECT OUTPUT to render an already saved candidate without rebuilding.
"""
import bpy, math, json, hashlib, sys, contextlib
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
BASE=Path(__file__).resolve().parent.parent
OUT=BASE/'candidates'/'round-02'; SRC=BASE/'source'
DIRS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
ROOT_NAME='S33 production concept cobalt-crags root'
COL_NAME='S33 production concept cobalt-crags'
SCENE='Boulder Underwater Refined Native'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def rows(m):return [[float(x) for x in r] for r in m]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lin(c):
 v=[int(c[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v)
def material(name,color,gain=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled')
 bs.inputs['Roughness'].default_value=.88;bs.inputs['Specular IOR Level'].default_value=.085;bs.inputs['IOR'].default_value=1.45
 geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Position'],sep.inputs[0])
 ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=2.325;ramp.inputs['To Min'].default_value=.82;ramp.inputs['To Max'].default_value=1.02;l.new(sep.outputs['Z'],ramp.inputs['Value'])
 mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[1].default_value=tuple(x*gain for x in lin(color))+(1,);l.new(ramp.outputs['Result'],mult.inputs[2]);l.new(mult.outputs[0],bs.inputs['Base Color'])
 # Modest blue fill is part of the native material, preventing crushed lower faces.
 l.new(mult.outputs[0],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.10
 l.new(bs.outputs[0],out.inputs['Surface']);m.diffuse_color=tuple(lin(color))+(1,)
 m['nativeSurface']='rough stone; broad height fill; no raster textures';return m

def rock(col,root,name,cx,cy,w,d,height,angle,variant):
 # Eight-sided hand-shaped stone with nonuniform crown and fractured shoulder bands.
 contours=[(-.49,-.29),(-.26,-.5),(.26,-.48),(.49,-.23),(.48,.26),(.21,.49),(-.28,.47),(-.5,.19)]
 # relative levels, width, depth, center shifts. Broad crown with asymmetric side break.
 rings=[(0,.89,.89,0,0),(.13,1,1,-.015,.005),(.39,.94,.96,.025,-.012),(.68,1.02,.94,-.020,.012),(.91,.95,.90,-.025,.020),(.985,.78,.77,-.031,.008),(1,.53,.56,-.033,.01)]
 verts=[]
 for j,(z,sx,sy,dx,dy) in enumerate(rings):
  for i,(x,y) in enumerate(contours):
   wiggle=[-.045,.085,-.065,.048,-.055,.075,.025,-.034][(i+variant)%8]
   zz=height*z+(0 if j==0 else wiggle*(.12 if j==6 else .2 if j==5 else .4 if j==1 else 1))
   organic=1+([-.06,.07,-.045,.04,-.07,.025,.055,-.03][(i+variant+j)%8] if j not in (0,6) else 0)
   xx=cx+w*(x*sx*organic+dx);yy=cy+d*(y*sy*organic+dy)
   xx,yy=cx+(xx-cx)*math.cos(angle)-(yy-cy)*math.sin(angle),cy+(xx-cx)*math.sin(angle)+(yy-cy)*math.cos(angle)
   verts.append((xx,yy,max(0,zz)))
 faces=[tuple(reversed(range(8)))];mids=[0]
 for j in range(len(rings)-1):
  for i in range(8):
   quad=(j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i)
   if j in (1,2,3) and (i+variant)%3==0:
    faces.extend([(quad[0],quad[1],quad[2]),(quad[0],quad[2],quad[3])]);mids.extend([0,3])
   else:
    faces.append(quad);mids.append(1 if j>=4 else (2 if (i+variant)%5==0 else (3 if (i+variant+j)%7==0 else 0)))
 faces.append(tuple(range((len(rings)-1)*8,len(rings)*8)));mids.append(1)
 me=bpy.data.meshes.new(name+' editable geology');me.from_pydata(verts,[],faces);me.update()
 ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.parent=root
 for m in MATS:me.materials.append(m)
 for p,mi in zip(me.polygons,mids):p.material_index=mi;p.use_smooth=False
 # Apply real edge geometry before capture deformation; preserve editable base mesh through saved recipe.
 bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 be=ob.modifiers.new('Worn stone edges — real volume','BEVEL');be.width=.038 if height>1.8 else .029;be.segments=4;be.limit_method='ANGLE';be.angle_limit=.11;be.affect='EDGES';be.harden_normals=True
 bpy.ops.object.modifier_apply(modifier=be.name)
 # Smooth bevel patches while keeping the broad native faces distinct.
 for p in ob.data.polygons:p.use_smooth=len(p.vertices)==4 and p.area<.010
 ob['role']='native volumetric stone';ob['construction']='hand-shaped crown/shoulder fractures with real 4-segment worn bevel';ob.select_set(False)
 return ob

def normalize_bounds(col):
 pts=[v.co for o in col.objects if o.type=='MESH' for v in o.data.vertices]
 lo=[min(p[i] for p in pts) for i in range(3)];hi=[max(p[i] for p in pts) for i in range(3)]
 for o in col.objects:
  if o.type!='MESH':continue
  for v in o.data.vertices:
   v.co.x=(v.co.x-lo[0])/(hi[0]-lo[0])-0.5;v.co.y=(v.co.y-lo[1])/(hi[1]-lo[1])-0.5;v.co.z=(v.co.z-lo[2])/(hi[2]-lo[2])*2.325000047683716
  o.data.update()

def build():
 global MATS
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name=SCENE
 col=bpy.data.collections.new(COL_NAME);sc.collection.children.link(col);root=bpy.data.objects.new(ROOT_NAME,None);col.objects.link(root)
 root['production_id']='boulder-underwater';root['sourceRoot']=ROOT_NAME;root['sourceProjectSHA256']=sha(SRC/'original-library.blend')
 root['native_action_record']=json.dumps({'source':'native_actions.py','assetId':'boulder-underwater','clips':{'static':[]}})
 MATS=[material('Blue stone body','216ED6'),material('Cyan blue crown','3A9FC7'),material('Blue stone secondary','2065C4'),material('Blue stone facet','2875D9')]
 # Main rock remains intentionally offset toward source rear. Secondary masses wrap all sides.
 rock(col,root,'Dominant broad crown',.035,.075,.83,.82,2.325,-.06,0)
 rock(col,root,'Rear left weathered shoulder',-.275,.255,.51,.51,1.55,.1,1)
 rock(col,root,'Front right shoulder',.285,-.19,.47,.54,1.42,-.14,2)
 rock(col,root,'Low front worn boulder',-.22,-.32,.55,.46,.89,.08,3)
 rock(col,root,'Back shoulder fracture',.25,.29,.48,.46,1.16,.02,4)
 rock(col,root,'Left middle stone',-.33,-.10,.42,.45,1.16,-.06,5)
 normalize_bounds(col)
 cam=bpy.data.objects.new('Registered 35 degree camera',bpy.data.cameras.new('Registered 35 degree camera'));sc.collection.objects.link(cam);sc.camera=cam
 configure(sc)
 # Horizontally symmetric broad soft illumination; no receiver plane or directional shadow.
 roles=[('Overhead',(0,0,5),115,4.5,(1,.95,.88))]
 for i in range(8):
  a=i*math.tau/8;roles.append(('Symmetric fill '+str(i),(3.5*math.cos(a),3.5*math.sin(a),2.3),44,5,(.90,.96,1)))
 for name,pos,power,size,color in roles:
  ld=bpy.data.lights.new(name,'AREA');ob=bpy.data.objects.new(name,ld);sc.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler();ld.energy=power;ld.shape='DISK';ld.size=size;ld.color=color
 sc.world=bpy.data.worlds.new('Balanced blue stone studio');sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.72,.80,1,1);bg.inputs['Strength'].default_value=.16
 sc['sourceCameraContract']='../inputs/source-camera.json';sc['squareFooting']=True;sc['footingTransitionHeight']=.42;sc['staticClip']='frame 1, 12fps, loop false'
 bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(SRC/'round-02.blend'),compress=True)
 return sc,col,root

def configure(sc):
 r=sc.render;r.engine='BLENDER_EEVEE';r.resolution_x=768;r.resolution_y=2048;r.resolution_percentage=100;r.pixel_aspect_x=r.pixel_aspect_y=1
 r.film_transparent=True;r.image_settings.file_format='PNG';r.image_settings.color_mode='RGBA';r.image_settings.color_depth='8';r.image_settings.compression=30;r.dither_intensity=0;r.fps=12;r.use_compositing=False;r.use_persistent_data=True
 sc.eevee.taa_render_samples=64
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
 cam=sc.camera;cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.clip_start=.1;cam.data.clip_end=1000
 # Exact per-asset source matrix, not unrelated active source camera frame.
 rec=json.loads((BASE/'inputs/source-camera.json').read_text());cam.matrix_world=Matrix(rec['camera']['worldMatrix']);cam.data.shift_x=0;cam.data.shift_y=1.6666641235351562
 # Source shift is derived from the exact root, avoiding a guessed saved-library shift.
 cam.data.shift_y=0;bpy.context.view_layer.update();o=world_to_camera_view(sc,cam,Vector((0,0,0)));base=(1-o.y)*2048
 cam.data.shift_y=1;bpy.context.view_layer.update();one=world_to_camera_view(sc,cam,Vector((0,0,0)));dy=(1-one.y)*2048-base
 cam.data.shift_y=(1664-base)/dy;bpy.context.view_layer.update();sc.frame_set(1)

def points(col,evaluated=False):
 pts=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in col.all_objects:
  if o.type!='MESH':continue
  if evaluated:
   ev=o.evaluated_get(dg);me=ev.to_mesh();pts += [ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
  else:pts += [o.matrix_world@v.co for v in o.data.vertices]
 return pts

def bounds(pts):return {'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
def camera_record(sc,scale):
 cam=sc.camera;dg=bpy.context.evaluated_depsgraph_get();root=world_to_camera_view(sc,cam,Vector((0,0,0)))
 return {'projection':'height-dependent-35-square-footing','frame':[192,512],'anchor':[96,416],'cellSize':128,'captureScale':scale,'fps':12,'axes':{'x':'X','depth':'-Y','height':'Z'},'camera':{'type':'orthographic','worldMatrix':rows(cam.matrix_world),'projectionMatrix':rows(cam.calc_matrix_camera(dg,x=768,y=2048,scale_x=1,scale_y=1)),'pixelAspect':[1,1],'worldUnitsPerCell':1,'elevationDegrees':35,'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y]},'calibration':{'root':[root.x*192*scale,(1-root.y)*512*scale]},'squareFooting':{'transitionHeight':.42,'formula':'world.y *= 1 + (1/sin(35deg)-1)*max(0,1-max(0,world.z)/.42)^2','appliedAfterFacingRotation':True},'nativeCaptureScale':4,'nativeResolution':[768,2048],'publishedResolution':[384,1024]}
@contextlib.contextmanager
def square_footing(col):
 saved=[]
 try:
  for ob in col.all_objects:
   if ob.type!='MESH':continue
   co=[v.co.copy() for v in ob.data.vertices];saved.append((ob,co));inv=ob.matrix_world.inverted()
   for v in ob.data.vertices:
    p=ob.matrix_world@v.co;b=max(0,1-max(0,p.z)/.42)**2;p.y*=1+(1/math.sin(math.radians(35))-1)*b;v.co=inv@p
   ob.data.update()
  bpy.context.view_layer.update();yield
 finally:
  for ob,co in saved:
   for v,c in zip(ob.data.vertices,co):v.co=c
   ob.data.update()
  bpy.context.view_layer.update()
def render(sc,col,root,out):
 out.mkdir(parents=True,exist_ok=True);physical=bounds(points(col));audits={}
 for direction,angle in DIRS.items():
  root.rotation_euler=(0,0,angle);bpy.context.view_layer.update()
  audit={'direction':direction,'nativeFrame':1,'rootMatrix':rows(root.matrix_world),'rootEuler':list(root.rotation_euler),'physicalBounds':bounds(points(col)),'evaluatedPhysicalBounds':bounds(points(col,True)),'camera':camera_record(sc,4)}
  with square_footing(col):
   audit['captureDeformedBounds']=bounds(points(col,True));sc.render.filepath=str(out/'raw'/f'static-{direction}'/'000.png');Path(sc.render.filepath).parent.mkdir(parents=True,exist_ok=True);bpy.ops.render.render(write_still=True)
  audits[direction]=audit
 root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
 write(out/'native-audit.json',{'asset':'boulder-underwater','scene':sc.name,'collection':col.name,'groundRootObject':root.name,'canonicalRootMatrix':rows(root.matrix_world),'physicalBounds':physical,'evaluatedPhysicalBounds':bounds(points(col,True)),'audit_directions':audits,'meshObjects':[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':[m.name for m in o.data.materials],'bounds':bounds([o.matrix_world@v.co for v in o.data.vertices])} for o in col.objects if o.type=='MESH'],'lights':[{'name':o.name,'type':o.data.type,'position':list(o.location),'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in sc.objects if o.type=='LIGHT'],'externalImages':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images if im.source=='FILE'],'armatures':[],'actions':[],'ports':{},'sockets':{},'footprint':[1,1],'nominalHeight':2.3,'occupiedCells':[[0,0]],'supportCells':[[0,0]],'rootCell':[.5,.5],'staticClip':{'frames':1,'frameOrder':[0],'nativeFrame':1,'fps':12,'static':True,'loop':False}})
 write(out/'records'/'camera-native.json',camera_record(sc,4));write(out/'records'/'camera.json',camera_record(sc,2))
 asset=json.loads((BASE/'inputs/source-assetRecord.json').read_text());asset.update(projection='height-dependent-35-square-footing',scale=2,nativeCaptureScale=4,artStyle={'revision':'warm-soft-cartoon-native-round01','lighting':'one broad overhead and eight equal horizontal fills','geometry':'six native weathered blue stone masses'},squareFooting=True)
 write(out/'records'/'asset.json',asset);write(out/'records'/'rig.json',json.loads((BASE/'inputs/source-rig.json').read_text()))
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
 if args and args[0]=='--replay':
  bpy.ops.wm.open_mainfile(filepath=str(Path(args[1]).resolve()));sc=bpy.data.scenes[SCENE];bpy.context.window.scene=sc;col=bpy.data.collections[COL_NAME];root=bpy.data.objects[ROOT_NAME];render(sc,col,root,Path(args[2]).resolve())
 else:
  sc,col,root=build();render(sc,col,root,OUT)
