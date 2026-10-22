"""Standalone cobalt stone reconstruction. Background Blender only. No external textures.
Run: blender --background --factory-startup --python THIS -- [--replay] [--output PATH]
The saved project is the portable editable source; this deterministic script rebuilds it.
"""
import bpy, bmesh, math, json, hashlib, sys, argparse
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
HERE=Path(__file__).resolve().parent
OBJ=HERE.parent
RES=HERE/'round-01-resources'
parser=argparse.ArgumentParser();parser.add_argument('--replay',action='store_true');parser.add_argument('--output',type=Path)
a=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=a.output.resolve() if a.output else OBJ/'candidates/round-01'
OUT.mkdir(parents=True,exist_ok=True)
PROJECT=HERE/'round-01.blend'
COLNAME='S33 production concept cobalt-shelf.001'
ROOTNAME='S33 production concept cobalt-shelf root.001'
def dump(p,data):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plain(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 return [plain(v) for v in x]
def bounds(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def linear(hex):
 cs=[int(hex[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in cs)+(1,)
def create_material(name,factor):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();l=m.node_tree.links
 out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 bs.inputs['Roughness'].default_value=.62;bs.inputs['Specular IOR Level'].default_value=.27;bs.inputs['Metallic'].default_value=0
 bs.inputs['Coat Weight'].default_value=.05;bs.inputs['Coat Roughness'].default_value=.48
 geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
 mp=n.new('ShaderNodeMapRange');mp.inputs['From Min'].default_value=0;mp.inputs['From Max'].default_value=1.075;l.new(sep.outputs['Z'],mp.inputs['Value'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
 colors=[(0,'16478D'),(.28,'1B5AAF'),(.70,'2371BF'),(1,'2A80C8')]
 for e in list(ramp.color_ramp.elements)[1:]:ramp.color_ramp.elements.remove(e)
 for idx,(pos,col) in enumerate(colors):
  e=ramp.color_ramp.elements[0] if idx==0 else ramp.color_ramp.elements.new(pos)
  e.position=pos;c=linear(col);e.color=tuple(v*factor for v in c[:3])+(1,)
 l.new(mp.outputs['Result'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Base Color']);m.diffuse_color=linear('1B5AAF')
 return m

def stone(name,cx,cy,rx,ry,z0,h,seed,material,rotation=0):
 n=9
 angles=[2*math.pi*i/n+rotation for i in range(n)]
 variation=[1+.065*math.sin(i*2.7+seed)+.035*math.cos(i*1.9+seed*.2) for i in range(n)]
 # Deliberately uneven coarse shoulders and nonparallel ridges; complete finite bottom.
 rings=[(0,.77),(.19,1),(.69,.96),(1,.67)]
 vs=[]
 for j,(z,radius) in enumerate(rings):
  for i,t in enumerate(angles):
   rr=radius*variation[i]*(1+.025*math.sin(i*2.1+j*1.8+seed))
   xx=cx+rx*rr*math.cos(t)+(.025*rx*math.sin(seed+j*1.8))
   yy=cy+ry*rr*math.sin(t)+(.035*ry*math.cos(seed+j*1.3))
   zz=z0+h*z
   if j in (1,2):zz+=h*.065*math.sin(i*1.7+seed+j)
   if j==3:zz-=h*.017*(.5+.5*math.sin(i*1.2+seed))
   vs.append((xx,yy,zz))
 fs=[tuple(reversed(range(n)))]
 for j in range(len(rings)-1):
  for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 fs.append(tuple((len(rings)-1)*n+i for i in range(n)))
 mesh=bpy.data.meshes.new(name+' mesh');mesh.from_pydata(vs,[],fs);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
 ob=bpy.data.objects.new(name,mesh);COL.objects.link(ob);ob.parent=ROOT;mesh.materials.append(material)
 return ob

def dimple(ob,origin,direction,radius):
 hit,loc,norm,_=ob.ray_cast(Vector(origin),Vector(direction).normalized())
 if not hit:raise RuntimeError('Dimple ray missed '+ob.name)
 # A shallow true subtractive depression. Cutter removed after application.
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=radius,location=ob.matrix_world@loc+norm*radius*.6)
 cutter=bpy.context.object;cutter.name='temporary native dimple cutter';cutter.scale=(1,1,1.18)
 mod=ob.modifiers.new('Shallow stone dimple','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.context.view_layer.objects.active=ob;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(cutter,do_unlink=True)

if not a.replay:
 bpy.ops.wm.read_factory_settings(use_empty=True)
 SC=bpy.context.scene;SC.name='Decor background rock round 01'
 COL=bpy.data.collections.new(COLNAME);SC.collection.children.link(COL)
 ROOT=bpy.data.objects.new(ROOTNAME,None);COL.objects.link(ROOT);ROOT['production_id']='decor-background-rock';ROOT['clip']='static';ROOT['ground_root']=[0.,0.,0.]
 mats=[create_material('Cobalt stone '+str(i+1),f) for i,f in enumerate([1,1.025,.97,1.02,1.01])]
 # Grounded basal body; crown overlaps its solid body. Four smaller projections preserve cluster identity.
 body=stone('Central deep body',.035,.075,.405,.37,0,.79,2.2,mats[0],.09)
 crown=stone('Broad softened crown',.045,.105,.405,.35,.49,.58,1.0,mats[1],.07)
 left=stone('Offset left shoulder',-.325,.165,.17,.315,0,.77,4.5,mats[2],-.12)
 low=stone('Low front boulder',-.22,-.306,.278,.19,0,.405,5.2,mats[3],.19)
 right=stone('Right front ledge',.32,-.22,.17,.274,0,.605,3.1,mats[4],-.07)
 bpy.context.view_layer.update()
 dimple(body,(.05,-1,.46),(0,1,0),.031)
 dimple(low,(-.29,-1,.22),(0,1,0),.025)
 dimple(crown,(1,.18,.87),(-1,0,0),.029)
 dimple(left,(-1,.20,.43),(1,0,0),.025)
 for ob in [body,crown,left,low,right]:
  # Authoring bounds fit inside the frozen placement budget by construction.
  for v in ob.data.vertices:
   v.co.x=max(-.5,min(.5,v.co.x));v.co.y=max(-.5,min(.5,v.co.y));v.co.z=max(0,min(1.075,v.co.z))
  for poly in ob.data.polygons:poly.use_smooth=True
  bevel=ob.modifiers.new('Soft finished stone edges','BEVEL');bevel.width=.022 if ob==crown else .018;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.13;bevel.harden_normals=True
  weighted=ob.modifiers.new('Broad face weighted normals','WEIGHTED_NORMAL');weighted.keep_sharp=True;weighted.weight=50
  ob['native_stone']=True
 world=bpy.data.worlds.new('Symmetric soft blue ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.72,.83,1,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.24;SC.world=world
 def area(name,pos,power,size):
  data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;ob=bpy.data.objects.new(name,data);SC.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,.45))-ob.location).to_track_quat('-Z','Y').to_euler();return ob
 area('Broad centered overhead',(0,0,4.5),260,4)
 for i in range(4):
  t=i*math.pi/2;area('Equal cardinal fill '+str(i),(3*math.cos(t),3*math.sin(t),1.8),115,4)
 cd=bpy.data.cameras.new('Registered rock camera');CAM=bpy.data.objects.new('Registered rock camera',cd);SC.collection.objects.link(CAM);SC.camera=CAM
 sourcecamera=json.loads((RES/'source-camera.json').read_text())
 CAM.matrix_world=Matrix(sourcecamera['camera']['worldMatrix']);CAM.data.type='ORTHO';CAM.data.sensor_fit='HORIZONTAL';CAM.data.ortho_scale=1.5;CAM.data.shift_x=0;CAM.data.shift_y=0;CAM.data.clip_start=.1;CAM.data.clip_end=1000
 SC.render.engine='BLENDER_EEVEE';SC.render.resolution_x=768;SC.render.resolution_y=1408;SC.render.resolution_percentage=100
 SC.render.pixel_aspect_x=sourcecamera['camera']['pixelAspect'][0];SC.render.pixel_aspect_y=sourcecamera['camera']['pixelAspect'][1]
 def px(p):
  q=world_to_camera_view(SC,CAM,Vector(p));return Vector((q.x*768,(1-q.y)*1408))
 bpy.context.view_layer.update();start=px((0,0,0));CAM.data.shift_y=1;bpy.context.view_layer.update();delta=px((0,0,0)).y-start.y;CAM.data.shift_y=(1024-start.y)/delta;bpy.context.view_layer.update()
 SC.render.film_transparent=True;SC.render.filter_size=1.5;SC.render.dither_intensity=0
 SC.render.image_settings.file_format='PNG';SC.render.image_settings.color_mode='RGBA';SC.render.image_settings.color_depth='8';SC.render.image_settings.compression=100
 SC.view_settings.view_transform='Standard';SC.view_settings.look='None';SC.view_settings.exposure=0;SC.view_settings.gamma=1
 SC.render.fps=12;SC.frame_start=1;SC.frame_end=1;SC.frame_set(1)
 bpy.ops.wm.save_as_mainfile(filepath=str(PROJECT))
else:
 bpy.ops.wm.open_mainfile(filepath=str(PROJECT));SC=bpy.context.scene;COL=bpy.data.collections[COLNAME];ROOT=bpy.data.objects[ROOTNAME];CAM=SC.camera

def px(p):
 q=world_to_camera_view(SC,CAM,Vector(p));return Vector((q.x*768,(1-q.y)*1408))
def temporal(owner):
 ad=getattr(owner,'animation_data',None)
 return {'action':ad.action.name if ad and ad.action else None,'nlaTracks':len(ad.nla_tracks) if ad else 0,'drivers':len(ad.drivers) if ad else 0}
def measure():
 dg=bpy.context.evaluated_depsgraph_get();dg.update();rows=[];allpoints=[]
 for ob in sorted(COL.all_objects,key=lambda ob:ob.name):
  rec={'name':ob.name,'type':ob.type,'parent':ob.parent.name if ob.parent else None,'matrixWorld':plain(ob.matrix_world),'animation':temporal(ob),'constraints':len(ob.constraints)}
  if ob.type=='MESH':
   ev=ob.evaluated_get(dg);mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];allpoints+=pts
   edgecounts={tuple(sorted(e.vertices)):0 for e in mesh.edges}
   for f in mesh.polygons:
    for e in f.edge_keys:edgecounts[tuple(sorted(e))]+=1
   rec.update(vertices=len(mesh.vertices),polygons=len(mesh.polygons),bounds=bounds(pts),boundaryEdges=sum(v==1 for v in edgecounts.values()),nonManifoldEdges=sum(v!=2 for v in edgecounts.values()),groundVertices=sum(abs(p.z)<1e-6 for p in pts),meshAnimation=temporal(ob.data),shapeKeys=bool(ob.data.shape_keys),materials=[m.name for m in ob.data.materials],modifiers=[{'type':m.type,'name':m.name} for m in ob.modifiers])
   ev.to_mesh_clear()
  rows.append(rec)
 return {'objects':rows,'bounds':bounds(allpoints)}
rootpx=px((0,0,0));cal={'root':plain(rootpx),'unitX':plain(px((1,0,0))-rootpx),'unitDepth':plain(px((0,-1,0))-rootpx),'unitHeight':plain(px((0,0,1))-rootpx)}
camera={'projection':'top-down-oblique-square-grid','frame':[192,352],'anchor':[96,256],'cellSize':128,'captureScale':4,'fps':12,'nativeFrame':[768,1408],'camera':{'type':'orthographic','worldMatrix':plain(CAM.matrix_world),'projectionMatrix':plain(CAM.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=768,y=1408,scale_x=SC.render.pixel_aspect_x,scale_y=SC.render.pixel_aspect_y)),'pixelAspect':[SC.render.pixel_aspect_x,SC.render.pixel_aspect_y],'orthoScale':CAM.data.ortho_scale,'shift':[CAM.data.shift_x,CAM.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':55.00797980144134},'calibration':cal,'filterSize':SC.render.filter_size,'sourceProjectSHA256':sha(PROJECT)}
records=[];measurements={};checks=[]
for direction,degrees in [('N',180),('E',90),('S',0),('W',-90)]:
 ROOT.rotation_euler.z=math.radians(degrees);SC.frame_set(1);bpy.context.view_layer.update();measurement=measure();measurements[direction]=[measurement]
 p=OUT/'native/static'/direction/'000.png';p.parent.mkdir(parents=True,exist_ok=True);SC.render.filepath=str(p)
 bpy.ops.render.render(write_still=True)
 rec={'direction':direction,'clip':'static','frameIndex':0,'nativeFrame':1,'rootRotationZ':ROOT.rotation_euler.z,'rootRotationDegrees':math.degrees(ROOT.rotation_euler.z),'actualRootMatrix':plain(ROOT.matrix_world),'path':str(p.relative_to(OBJ)),'sourceSHA256':sha(PROJECT),'camera':camera,'evaluatedBounds':measurement['bounds']}
 records.append(rec)
 b=measurement['bounds'];checks.append(all(v>=-.500001 for v in b['min'][:2]) and all(v<=.500001 for v in b['max'][:2]) and b['min'][2]>=-1e-6 and b['max'][2]<=1.075001)
 print('CAPTURED',direction,flush=True)
ROOT.rotation_euler.z=0;bpy.context.view_layer.update()
materials=list({m.name:m for ob in COL.all_objects if ob.type=='MESH' for m in ob.data.materials}.values())
owners=list(COL.all_objects)+[ob.data for ob in COL.all_objects if ob.data]+materials+[m.node_tree for m in materials]+[SC,SC.world,SC.world.node_tree,CAM,CAM.data]+[ob for ob in SC.objects if ob.type=='LIGHT']+[ob.data for ob in SC.objects if ob.type=='LIGHT']
tem=[{'name':owner.name,'type':owner.bl_rna.identifier,**temporal(owner)} for owner in owners]
static=all(not r['action'] and not r['nlaTracks'] and not r['drivers'] for r in tem)
closed=all(o.get('nonManifoldEdges',0)==0 for ms in measurements.values() for o in ms[0]['objects'])
validation={'asset':'decor-background-rock','round':'round-01','blender':bpy.app.version_string,'project':str(PROJECT.relative_to(OBJ)),'sourceSHA256':sha(PROJECT),'recipeSHA256':sha(__file__),'rootObject':ROOT.name,'camera':camera,'captureRecords':records,'nativeGeometryMeasurements':measurements,'staticTemporalOwners':tem,'effectiveOwnership':{'sceneObjects':[o.name for o in SC.objects],'ownCollectionObjects':[o.name for o in COL.all_objects],'libraries':[l.filepath for l in bpy.data.libraries],'imageTextures':[im.filepath for im in bpy.data.images if im.source=='FILE'],'externalResources':[]},'lighting':{'worldStrength':.24,'centeredPower':260,'centeredSize':4,'fourFillPowerEach':115,'fourFillSize':4,'fourFillRadius':3,'fourFillZ':1.8,'horizontalSymmetry':4,'groundPlane':False,'perViewChanges':False},'checks':{'all4Envelopes':all(checks),'closedManifoldMeshes':closed,'staticTemporalOwners':static,'frameRange':[SC.frame_start,SC.frame_end],'fps':SC.render.fps,'filterSize':SC.render.filter_size,'filmTransparent':SC.render.film_transparent},'allChecksPassed':all(checks) and closed and static,'scope':'Actual measured native frame captures; source at S saved once before captures; no source save after facing rotations.'}
dump(OUT/'native-validation.json',validation);dump(OUT/'native-camera.json',camera)
print('NATIVE_VALIDATION',validation['checks'],flush=True)
