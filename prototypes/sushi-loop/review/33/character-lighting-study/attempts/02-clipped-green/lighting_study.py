"""Issue33: actual Blender-lighting study on one frozen C125 chef.

Author via Blender MCP: build_from_live_rollout(repo).
Recapture the saved, isolated study with Blender --background source/noor-lighting.blend
 --python source/lighting_study.py -- --render ROOT.
No production meshes, materials, cameras, actions or PNGs are replaced.
"""
import bpy, hashlib, importlib.util, json, math, sys
from pathlib import Path
from mathutils import Vector

VARIANTS=[
 {'id':'baseline','name':'Current production','description':'Current emission materials. Height-based lower shading, with little separation between upward and vertical faces.','settings':{'shader':'emission','topWatts':0,'fillWattsEach':0,'topSize':0}},
 {'id':'soft','name':'Soft overhead','description':'Broad overhead key and even fill. A gentle brighter crown with readable side planes.','settings':{'shader':'matte-principled','topWatts':180,'fillWattsEach':100,'topSize':3.5}},
 {'id':'faceted','name':'Faceted overhead','description':'Stronger overhead key with the same even fill; the green hat facets read as distinct surfaces.','settings':{'shader':'matte-principled','topWatts':280,'fillWattsEach':100,'topSize':3.0}},
 {'id':'crisp','name':'Crisp overhead','description':'A stronger, smaller overhead key increases the separation while preserving the same face fill.','settings':{'shader':'matte-principled','topWatts':400,'fillWattsEach':100,'topSize':2.5}},
]
DIRECTIONS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):Path(path).write_text(json.dumps(data,indent=2)+'\n')

def mesh_hash(objects):
 h=hashlib.sha256()
 for o in sorted(objects,key=lambda o:o.get('sourceObject','')):
  h.update(o.get('sourceObject',o.name).encode())
  h.update(json.dumps([[round(x,7) for x in v.co] for v in o.data.vertices]).encode())
  h.update(json.dumps([list(p.vertices) for p in o.data.polygons]).encode())
 return h.hexdigest()

def matte_copy(original,variant):
 m=original.copy();m.name='S33 lighting '+variant+' '+original.name
 if variant=='baseline':return m
 nodes=m.node_tree.nodes;links=m.node_tree.links
 output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
 # Reuse the approved base-color × world-height ramp, excluding the old
 # abs(normal·view) multiplier. Actual illumination now supplies facet shading.
 lower=next((n for n in nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY' and n.inputs[2].is_linked and n.inputs[2].links[0].from_node.type=='VALTORGB'),None)
 if lower is None:raise RuntimeError('Expected approved lower-tone graph: '+original.name)
 shader=nodes.new('ShaderNodeBsdfPrincipled');shader.label='Matte surface responding to actual study lamps'
 shader.inputs['Roughness'].default_value=.85
 shader.inputs['Metallic'].default_value=0
 shader.inputs['IOR'].default_value=1.45
 shader.inputs['Specular IOR Level'].default_value=.03
 shader.inputs['Emission Strength'].default_value=0
 links.new(lower.outputs[0],shader.inputs['Base Color']);links.new(shader.outputs['BSDF'],output.inputs['Surface'])
 m['lightingStudy']='matte-principled; approved lower ramp retained; old view-tone bypassed'
 return m

def area(scene,name,position,target,power,size):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=(1,1,1)
 obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=position
 obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
 return obj

def configure(scene,repo):
 runtime=load('s33_lighting_camera_'+scene.name.replace(' ','_'),repo/'prototypes/sushi-loop/assets/production/source/blender/capture_runtime.py')
 runtime.scene=lambda:scene
 camera=runtime.configure_camera('character-orthographic',(192,320),(96,248),4,35)
 scene.eevee.taa_render_samples=64
 scene.render.image_settings.compression=100;scene.render.dither_intensity=0
 scene.world=scene.world.copy();scene.world.name=scene.name+' world'
 return camera

def build_from_live_rollout(repo):
 repo=Path(repo);folder=repo/'prototypes/sushi-loop/assets/character-lighting-study';folder.mkdir(parents=True,exist_ok=True)
 previous=bpy.context.window.scene
 state=sys.modules['s33_full_art_rollout'].state;a=state['runtime'].assets['chef-noor'];native=state['native'];sc=state['scene']
 visibility={c:(c.hide_render,c.hide_viewport) for c in sc.collection.children};oldframe=sc.frame_current;oldrot=a['root'].rotation_euler.copy()
 try:
  bpy.context.window.scene=sc
  for c in sc.collection.children:c.hide_render=c!=a['collection'];c.hide_viewport=c!=a['collection']
  native.apply_clip(a,state['records']['chef-noor'],'idle',frame=4,direction='S',scene=sc)
  bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
  frozen=[]
  for obj in a['collection'].all_objects:
   if obj.type!='MESH' or obj.hide_render:continue
   mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
   mesh.transform(obj.matrix_world);mesh.update()
   frozen.append((obj.name,mesh))
  scenes=[];manifest={'version':1,'character':{'id':'chef-noor','name':'Noor · green beret'},'cellSize':128,'frame':[192,320],'root':[96,248],'captureScale':4,'fps':12,'directions':list(DIRECTIONS),'pose':{'clip':'idle','frame':4,'animated':False},'variants':[],'productionUnchanged':True,'status':'lighting-experiment-awaiting-user-review','conceptReference':{'image':'../design/art-directions/restaurant-concept.png'},'source':{'blend':'source/noor-lighting.blend','recipe':'source/lighting_study.py','productionBlendSHA256':sha(repo/'prototypes/sushi-loop/assets/production/source/blender/sushi-loop-world-library.blend')}}
  for spec in VARIANTS:
   scene=bpy.data.scenes.new('S33 Noor lighting '+spec['id']);scene['lightingStudyVariant']=spec['id'];bpy.context.window.scene=scene
   root=bpy.data.objects.new('Noor '+spec['id']+' ground root',None);scene.collection.objects.link(root);scene['studyRoot']=root.name
   mats={};objects=[]
   for name,mesh in frozen:
    obj=bpy.data.objects.new('Noor '+spec['id']+' '+name,mesh.copy());obj['sourceObject']=name;obj.parent=root;scene.collection.objects.link(obj);objects.append(obj)
    for slot in obj.material_slots:
     old=slot.material
     if old:
      if old.name not in mats:mats[old.name]=matte_copy(old,spec['id'])
      slot.material=mats[old.name]
   camera=configure(scene,repo)
   settings=spec['settings']
   if spec['id']!='baseline':
    area(scene,'Noor '+spec['id']+' overhead',(0,0,4.5),(0,0,.8),settings['topWatts'],settings['topSize'])
    for i,(x,y) in enumerate(((3,0),(0,3),(-3,0),(0,-3))):area(scene,'Noor '+spec['id']+' even fill '+str(i),(x,y,1.8),(0,0,.8),settings['fillWattsEach'],4.0)
   scene['studyGeometrySHA256']=mesh_hash(objects)
   scene['studySourcePose']='chef-noor idle unique frame4; C125 anatomy; no mesh reshaping'
   value={**spec,'scene':scene.name,'geometrySHA256':scene['studyGeometrySHA256'],'camera':camera,'captures':{d:{'image':'sprites/'+spec['id']+'-'+d+'.png'} for d in DIRECTIONS}}
   manifest['variants'].append(value);scenes.append(scene)
  # Independent classification pass: top and side regions are defined by the
  # actual frozen hat polygon normals, not guessed image rectangles.
  source=scenes[0];mask=bpy.data.scenes.new('S33 Noor lighting hat mask');mask['lightingStudyVariant']='mask';bpy.context.window.scene=mask
  root=bpy.data.objects.new('Noor mask ground root',None);mask.collection.objects.link(root);mask['studyRoot']=root.name
  colors=[(0,0,0,1),(1,0,0,1),(0,0,1,1)];materials=[]
  for i,color in enumerate(colors):
   mat=bpy.data.materials.new('Noor hat classification '+str(i));mat.use_nodes=True
   output=next(n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL');emit=mat.node_tree.nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=color;mat.node_tree.links.new(emit.outputs[0],output.inputs['Surface']);materials.append(mat)
  for name,mesh in frozen:
   obj=bpy.data.objects.new('Noor mask '+name,mesh.copy());obj.parent=root;mask.collection.objects.link(obj);obj.data.materials.clear()
   for mat in materials:obj.data.materials.append(mat)
   for poly in obj.data.polygons:poly.material_index=1 if 'beret_' in name and poly.normal.z>=.65 else 2 if 'beret_' in name and poly.normal.z<=.35 else 0
  camera=configure(mask,repo);mask.render.use_compositing=False;scenes.append(mask)
  manifest['hatMasks']={d:'validation/hat-mask-'+d+'.png' for d in DIRECTIONS}
  # Hat bounds use the native projection and are shared by every candidate.
  from bpy_extras.object_utils import world_to_camera_view
  points=[v.co for name,mesh in frozen if 'beret_' in name for v in mesh.vertices]
  all_bounds=[]
  for d,angle in DIRECTIONS.items():
   from mathutils import Matrix
   rotation=Matrix.Rotation(angle,4,'Z')
   px=[world_to_camera_view(mask,mask.camera,rotation@p) for p in points]
   all_bounds.extend([(p.x*192,(1-p.y)*320) for p in px])
  x0=min(p[0] for p in all_bounds)-6;y0=min(p[1] for p in all_bounds)-6;x1=max(p[0] for p in all_bounds)+6;y1=max(p[1] for p in all_bounds)+6
  manifest['hatCrop']=[math.floor(x0),math.floor(y0),math.ceil(x1-x0),math.ceil(y1-y0)]
  bpy.context.window.scene=scenes[2]
  path=folder/'source/noor-lighting.blend';bpy.data.libraries.write(str(path),set(scenes),fake_user=True,compress=True)
  manifest['source']['sha256']=sha(path);manifest['source']['recipeSHA256']=sha(Path(__file__))
  write(folder/'manifest.json',manifest)
  return {'path':str(path),'variants':len(VARIANTS),'meshesPerVariant':len(frozen),'hatCrop':manifest['hatCrop'],'sourceSHA256':manifest['source']['sha256']}
 finally:
  a['root'].rotation_euler=oldrot;sc.frame_set(oldframe)
  for c,(r,v) in visibility.items():c.hide_render=r;c.hide_viewport=v
  bpy.context.window.scene=previous

def render(folder,variant=None):
 folder=Path(folder);manifest=json.loads((folder/'manifest.json').read_text());records=[]
 for item in manifest['variants']+[{'id':'mask','scene':'S33 Noor lighting hat mask','captures':{d:{'image':manifest['hatMasks'][d]} for d in DIRECTIONS}}]:
  if variant and item['id'] not in variant:continue
  scene=bpy.data.scenes[item['scene']];bpy.context.window.scene=scene;root=bpy.data.objects[scene['studyRoot']]
  for d,angle in DIRECTIONS.items():
   root.rotation_euler.z=angle;scene.view_layers[0].update();path=folder/item['captures'][d]['image'];path.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(path)
   bpy.ops.render.render(write_still=True,scene=scene.name)
   records.append({'variant':item['id'],'direction':d,'image':str(path.relative_to(folder)),'sha256':sha(path),'geometrySHA256':scene.get('studyGeometrySHA256'),'camera':manifest['variants'][0]['camera']})
   write(folder/'capture-status.json',{'state':'rendering','done':len(records),'current':[item['id'],d]})
 write(folder/'captures.json',{'records':records,'sourceSHA256':sha(folder/'source/noor-lighting.blend')})
 write(folder/'capture-status.json',{'state':'complete','done':len(records)})

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--render',type=Path);p.add_argument('--variants',nargs='*');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if args.render:render(args.render,args.variants)
