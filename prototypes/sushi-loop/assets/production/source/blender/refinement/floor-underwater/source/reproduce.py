"""Editable, texture-free native underwater material and exact registered capture.
Run: blender -b --python source/reproduce.py -- --mode build|capture|patch|probe --out candidates/round-01
Every phase is driven by scene.frame_current; no frame image swapping or pixel repair.
"""
import bpy,math,json,sys,argparse,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
OBJ=Path(__file__).resolve().parents[1]
TAU=math.tau
SEEDS=[(.04,.07),(.40,.09),(.75,.045),(.20,.265),(.55,.29),(.91,.24),(.045,.46),(.36,.43),(.73,.475),(.17,.65),(.52,.63),(.88,.675),(.07,.85),(.43,.87),(.77,.84)]
PALETTE={'deep':'009fbd','body':'25cad4','halo':'44d7d6','caustic':'c8f0d1'}
ROT={'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2}
def write(p,d):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def col(h):
 vals=[int(h[i:i+2],16)/255 for i in (0,2,4)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals)+(1,)
def nodegraph(mat):
 mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links
 def node(kind,name):q=n.new(kind);q.name=name;q.label=name;return q
 def op(kind,a,b=None,name=None):
  q=node('ShaderNodeMath',name or kind);q.operation=kind
  for i,v in enumerate((a,b) if b is not None else (a,)):
   if hasattr(v,'node'):links.new(v,q.inputs[i])
   else:q.inputs[i].default_value=v
  return q.outputs[0]
 def add(a,b):return op('ADD',a,b)
 def mul(a,b):return op('MULTIPLY',a,b)
 def sin(a):return op('SINE',a)
 def cos(a):return op('COSINE',a)
 def mix(a,b,f,name):
  q=node('ShaderNodeMixRGB',name);q.blend_type='MIX'
  links.new(f,q.inputs[0]);q.inputs[1].default_value=col(a) if isinstance(a,str) else a if not hasattr(a,'node') else (0,0,0,1)
  q.inputs[2].default_value=col(b) if isinstance(b,str) else b if not hasattr(b,'node') else (0,0,0,1)
  if hasattr(a,'node'):links.new(a,q.inputs[1])
  if hasattr(b,'node'):links.new(b,q.inputs[2])
  return q.outputs[0]
 uv=node('ShaderNodeTexCoord','Exact local unit-square UV');sep=node('ShaderNodeSeparateXYZ','Periodic unit coordinates');links.new(uv.outputs['UV'],sep.inputs[0]);u,v=sep.outputs['X'],sep.outputs['Y']
 phase=node('ShaderNodeValue','Global one-second loop phase');phase.outputs[0].default_value=0
 phase.outputs[0].driver_add('default_value').driver.expression='((frame - 1) % 12) / 12'
 t=mul(phase.outputs[0],TAU)
 # Periodic two-axis domain warping; no unbounded texture coordinates or per-tile shading.
 U=add(u,add(mul(sin(add(mul(add(u,v),TAU),add(mul(sin(t),.24),.8))),.071),mul(sin(add(mul(add(mul(v,2),mul(u,-1)),TAU),mul(cos(t),.18))),.026)))
 V=add(v,add(mul(sin(add(mul(add(v,mul(u,-1)),TAU),add(mul(cos(t),.22),1.7))),.064),mul(sin(add(mul(add(mul(u,2),v),TAU),mul(sin(t),.17))),.026)))
 ds=[]
 for i,(x,y) in enumerate(SEEDS):
  sx=add(x,mul(sin(add(t,i*2.39996323)),.009))
  sy=add(y,mul(cos(add(t,i*1.819031)),.009))
  dx=mul(op('SUBTRACT',U,sx),TAU);dy=mul(op('SUBTRACT',V,sy),TAU)
  d=op('SQRT',op('MAXIMUM',op('SUBTRACT',op('SUBTRACT',2,cos(dx)),cos(dy)),0),name='Seed%02d toroidal distance'%i)
  ds.append(d)
 a=op('MINIMUM',ds[0],ds[1]);b=op('MAXIMUM',ds[0],ds[1])
 for d in ds[2:]:
  b=op('MINIMUM',b,op('MAXIMUM',a,d));a=op('MINIMUM',a,d)
 gap=op('SUBTRACT',b,a,name='Connected distance to caustic edge')
 def band(width):return op('EXPONENT',mul(op('POWER',op('DIVIDE',gap,width),2),-1))
 width=add(.027,mul(a,.045));core=band(width);halo=band(.16)
 broad=sin(add(mul(add(mul(u,2),v),TAU),mul(sin(t),.15)))
 volume=op('MINIMUM',op('MAXIMUM',add(mul(op('POWER',a,2),4.7),add(.02,mul(broad,.10))),0),1,name='Broad optical water volume')
 body=mix(PALETTE['deep'],PALETTE['body'],volume,'Aqua optical body')
 body=mix(body,PALETTE['halo'],mul(halo,.34),'Soft connected light halo')
 result=mix(body,PALETTE['caustic'],mul(core,.68),'Restrained pale warm caustic')
 em=node('ShaderNodeEmission','Water optical radiance / horizontal symmetry');links.new(result,em.inputs['Color']);em.inputs['Strength'].default_value=1
 out=node('ShaderNodeOutputMaterial','Native surface');links.new(em.outputs[0],out.inputs['Surface'])
 # Organize exact math as editable graph in automatic columns.
 for i,q in enumerate(n):q.location=((i//18)*230,-(i%18)*125)
 mat.diffuse_color=col(PALETTE['body']);mat['periodicity']='All U/V occur only inside integer-period sin/cos before toroidal seed distances; time is a shared12-frame periodic phase.'
 return mat

def configure(scene,frame=(128,128),root=(64,64),scale=4,top=False):
 scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=frame[0]*scale;scene.render.resolution_y=frame[1]*scale;scene.render.resolution_percentage=100
 scene.render.pixel_aspect_x=1 if top else math.sqrt(1+.7*.7);scene.render.pixel_aspect_y=1
 cam=scene.camera
 if cam is None:cam=bpy.data.objects.new('Registered water capture',bpy.data.cameras.new('Registered water capture'));scene.collection.objects.link(cam);scene.camera=cam
 cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=frame[0]/128
 elev=math.pi/2 if top else math.atan(1/.7)
 cam.location=(0,-10*math.cos(elev),10*math.sin(elev));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
 def px(v):q=world_to_camera_view(scene,cam,Vector(v));return Vector((q.x*scene.render.resolution_x,(1-q.y)*scene.render.resolution_y))
 base=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0)).y-base.y
 cam.data.shift_y=(root[1]*scale-base.y)/dy;cam.data.shift_x=(frame[0]/2-root[0])/frame[0];bpy.context.view_layer.update()
 scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=30
 scene.render.filter_size=.5;scene.render.dither_intensity=0;scene.render.fps=12;scene.render.fps_base=1;scene.render.use_persistent_data=True
 scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
 scene.world=scene.world or bpy.data.worlds.new('Unbiased water environment');scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=0
 if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=32
 return {'projection':'top-down-oblique-square-grid' if not top else 'material-probe','frame':list(frame),'anchor':list(root),'cellSize':128,'captureScale':scale,'fps':12,'camera':{'type':'orthographic','worldMatrix':[list(r) for r in cam.matrix_world],'projectionMatrix':[list(r) for r in cam.calc_matrix_camera(bpy.context.evaluated_depsgraph_get(),x=scene.render.resolution_x,y=scene.render.resolution_y,scale_x=scene.render.pixel_aspect_x,scale_y=scene.render.pixel_aspect_y)],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'worldUnitsPerCell':1,'elevationDegrees':math.degrees(elev)},'calibration':{'root':list(px((0,0,0))),'unitX':list(px((1,0,0))-px((0,0,0))),'unitDepth':list(px((0,-1,0))-px((0,0,0))),'unitHeight':list(px((0,0,1))-px((0,0,0)))},'filterSize':scene.render.filter_size,'nativeFrame':[scene.render.resolution_x,scene.render.resolution_y]}

def build():
 bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene;scene.name='Floor Underwater Native Round01'
 root=bpy.data.objects.new('floor-underwater__root',None);scene.collection.objects.link(root)
 me=bpy.data.meshes.new('Exact complete upward unit-square base');me.from_pydata([(-.5,-.5,0),(.5,-.5,0),(.5,.5,0),(-.5,.5,0)],[],[(0,1,2,3)]);me.update()
 uv=me.uv_layers.new(name='Periodic unit square');
 for l in me.loops:co=me.vertices[l.vertex_index].co;uv.data[l.index].uv=(co.x+.5,co.y+.5)
 floor=bpy.data.objects.new('floor-underwater__continuous_water',me);scene.collection.objects.link(floor);floor.parent=root
 floor.data.materials.append(nodegraph(bpy.data.materials.new('Warm soft periodic aqua caustics')))
 root['asset']='floor-underwater';root['ground_root']='exact local origin';scene.frame_start=1;scene.frame_end=12
 scene['clip']='scroll';scene['loopClosingKey']=13;scene['nativeContractSHA256']='ceca86fd22114e1bb0f5406c353cf8be4969d22329d8a806d1e05331780ddcd3';scene['briefSHA256']='3fbe0de8986b1ab07a6a9064773b0fa59bbfcedf8d0e1cdb171422edcfd3bca6'
 configure(scene);scene.frame_set(1);bpy.context.view_layer.update()
 return scene,root,floor

def measured(scene,root,floor,direction,index,camera):
 deps=bpy.context.evaluated_depsgraph_get();ev=floor.evaluated_get(deps);me=ev.to_mesh();coords=[list(ev.matrix_world@v.co) for v in me.vertices]
 r={'direction':direction,'clip':'scroll','index':index,'nativeFrameNumber':scene.frame_current,'subframe':scene.frame_subframe,'actualPhase':bpy.data.materials['Warm soft periodic aqua caustics'].node_tree.nodes['Global one-second loop phase'].outputs[0].default_value,'rootRotationZ':root.rotation_euler.z,'rootMatrix':[list(a) for a in root.matrix_world],'camera':camera,'geometry':{'localCoordinates':[list(v.co) for v in me.vertices],'worldCoordinates':coords,'worldBounds':[[min(v[a] for v in coords),max(v[a] for v in coords)] for a in range(3)],'area':sum(p.area for p in me.polygons),'normalZ':[p.normal.z for p in me.polygons],'uv':[list(u.uv) for u in me.uv_layers.active.data]}}
 ev.to_mesh_clear();return r

def main():
 pa=argparse.ArgumentParser();pa.add_argument('--mode',choices=['build','draft','capture','patch','probe'],default='build');pa.add_argument('--out',default='candidates/round-01');a=pa.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 out=(OBJ/a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 if a.mode in ['build','draft']:
  scene,root,floor=build();project=OBJ/'source/round-01.blend' if a.mode=='build' else OBJ/'source/exploration-v4.blend'
  bpy.ops.wm.save_as_mainfile(filepath=str(project),check_existing=False)
  if a.mode=='build':return
 else:
  bpy.ops.wm.open_mainfile(filepath=str(OBJ/'source/round-01.blend'));scene=bpy.context.scene;root=bpy.data.objects['floor-underwater__root'];floor=bpy.data.objects['floor-underwater__continuous_water']
 records=[]
 if a.mode in ['draft','capture']:
  camera=configure(scene);write(out/'native-camera.json',camera)
  for direction in ('S' if a.mode=='draft' else 'NESW'):
   root.rotation_euler.z=ROT[direction]
   for index in ([0] if a.mode=='draft' else range(13)):
    scene.frame_set(index+1);bpy.context.view_layer.update();p=out/'native/scroll'/direction/('%03d.png'%index);p.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);r=measured(scene,root,floor,direction,index,camera);r.update(path=p.relative_to(OBJ).as_posix(),sha256=sha(p));records.append(r)
 elif a.mode=='patch':
  # Actual native nine-piece assembly, all objects share the same material/UV and global time.
  owned=[]
  for x,y in [(x,y) for y in (-1,0,1) for x in (-1,0,1) if x or y]:
   rr=root.copy();scene.collection.objects.link(rr);rr.location=(x,y,0);cp=floor.copy();scene.collection.objects.link(cp);cp.parent=rr;owned.append(rr)
  camera=configure(scene,(384,384),(192,192),4);write(out/'native-patch-camera.json',camera)
  for direction in 'NESW':
   for rr in [root]+owned:rr.rotation_euler.z=ROT[direction]
   for index in range(13):
    scene.frame_set(index+1);bpy.context.view_layer.update();p=out/'native-patch'/direction/('%03d.png'%index);p.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);r=measured(scene,root,floor,direction,index,camera);r.update(path=p.relative_to(OBJ).as_posix(),sha256=sha(p),placements=[[x,y,0] for y in (-1,0,1) for x in (-1,0,1)],actualPatchRoots=[{'matrix':[list(q) for q in rr.matrix_world],'rotationZ':rr.rotation_euler.z} for rr in [root]+owned]);records.append(r)
 elif a.mode=='probe':
  floor.hide_render=True;mat=floor.data.materials[0];N=257;h=1/256
  # Pixel centers sample each exact opposing boundary and ±h; x and y independent.
  specs=[(axis,c) for axis in ['X','Y'] for c in [0,1,-h,1-h,h,1+h]]
  for j,(axis,c) in enumerate(specs):
   verts=[(-.5,-.5+j/12,0),(.5,-.5+j/12,0),(.5,-.5+(j+1)/12,0),(-.5,-.5+(j+1)/12,0)]
   me=bpy.data.meshes.new('probe');me.from_pydata(verts,[],[(0,1,2,3)]);me.update();uv=me.uv_layers.new()
   for lo in me.loops:
    x=me.vertices[lo.vertex_index].co.x;v=(x+.5)*(N/(N-1))-.5/(N-1);uv.data[lo.index].uv=(c,v) if axis=='X' else (v,c)
   o=bpy.data.objects.new('Actual shader boundary probe %02d'%j,me);scene.collection.objects.link(o);o.data.materials.append(mat)
  cam=configure(scene,(128,128),(64,64),4,True);scene.render.resolution_x=N;scene.render.resolution_y=12;scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=N/12;scene.camera.data.ortho_scale=1;bpy.context.view_layer.update()
  for frame in list(range(1,14))+[1.5,7.5,12.5]:
   scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update();p=out/'material-probes'/('frame-%04.1f.png'%frame);p.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'frame':frame,'path':p.relative_to(OBJ).as_posix(),'sha256':sha(p),'rowsBottomToTop':specs,'h':h,'samples':N})
 write(out/('native-capture-records.json' if a.mode=='capture' else a.mode+'-records.json'),{'mode':a.mode,'projectSHA256':sha(OBJ/'source/round-01.blend') if (OBJ/'source/round-01.blend').exists() else None,'blender':bpy.app.version_string,'views':records})
if __name__=='__main__':main()
