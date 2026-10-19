"""MCP-authored lighting experiment on existing production belt/crate meshes.
Build: build_from_live_rollout(REPO), through Blender MCP.
Render the saved project using --render STUDY --variants baseline soft, etc.
The production library is never written. Belt phase remains native -7f/24.
"""
import bpy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from mathutils import Matrix,Vector
DIRECTIONS={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
SUBJECTS=[
 {'id':'belt-straight','name':'Conveyor belt','description':'A full-width straight conveyor: charcoal moving deck, red rails and thick supporting legs.','frame':[192,352],'root':[96,248],'footprint':[1,1],'floorBounds':[-.5,-.5,1,1],'placements':[{'id':'belt-straight-e','offset':[0,0,0]}]},
 {'id':'crate-wood','name':'Wood crate','description':'Compare the wooden top, front boards, beveled frame and diagonal braces. Soft retains more color detail in the pale top boards; the stronger presets brighten them enough to lose detail.','frame':[192,352],'root':[96,248],'footprint':[1,1],'floorBounds':[-.5,-.5,1,1],'placements':[{'id':'crate-wood','offset':[0,0,0]}]},
 {'id':'belt-connected','name':'Connected conveyor','description':'A three-module L: downward straight into a north-to-east corner, followed by an eastward straight. South view plays the native 24-frame loop.','frame':[384,448],'root':[192,288],'footprint':[2,2],'floorBounds':[-1,-1,2,2],'placements':[{'id':'belt-corner-n-e','offset':[-.5,-.5,0]},{'id':'belt-straight-s','offset':[-.5,.5,0]},{'id':'belt-straight-e','offset':[.5,-.5,0]}]},
]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2)+'\n')
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def mesh_hash(objects):
 h=hashlib.sha256()
 for o in sorted(objects,key=lambda o:(o['sourceAssetId'],o['sourceObject'])):
  h.update((o['sourceAssetId']+o['sourceObject']).encode())
  h.update(json.dumps([[round(c,7) for c in v.co] for v in o.data.vertices]).encode())
  h.update(json.dumps([list(p.vertices) for p in o.data.polygons]).encode())
  h.update(json.dumps([[round(c,7) for c in uv.uv] for uv in o.data.uv_layers.active.data] if o.data.uv_layers.active else []).encode())
 return h.hexdigest()

def phase(scene,value):
 materials={s.material for o in scene.objects if o.type=='MESH' for s in o.material_slots if s.material}
 found=[]
 for mat in materials:
  for n in mat.node_tree.nodes:
   if n.type=='VALUE' and n.label=='Deck travel phase':n.outputs[0].default_value=value;found.append(mat.name)
 return found

def build_from_live_rollout(repo):
 repo=Path(repo);folder=repo/'prototypes/sushi-loop/assets/environment-lighting-study';previous=bpy.context.window.scene
 common_path=repo/'prototypes/sushi-loop/assets/character-lighting-study/source/lighting_study.py';common=load('s33_prop_light_common',common_path)
 state=sys.modules['s33_full_art_rollout'].state;sc=state['scene'];native=state['native'];visibility={c:(c.hide_render,c.hide_viewport) for c in sc.collection.children};oldframe=sc.frame_current
 ids={p['id'] for s in SUBJECTS for p in s['placements']};oldrots={aid:state['runtime'].assets[aid]['root'].rotation_euler.copy() for aid in ids}
 try:
  frozen={};bpy.context.window.scene=sc
  for aid in sorted(ids):
   a=state['runtime'].assets[aid]
   for c in sc.collection.children:c.hide_render=c!=a['collection'];c.hide_viewport=c!=a['collection']
   native.apply_clip(a,state['records'][aid],next(iter(a['clips'])),frame=1,direction='S',scene=sc)
   bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();parts=[]
   for obj in a['collection'].all_objects:
    if obj.type!='MESH' or obj.hide_render:continue
    mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps);mesh.transform(obj.matrix_world);mesh.update();parts.append((obj.name,mesh))
   frozen[aid]=parts
  manifest={'version':1,'cellSize':128,'captureScale':4,'fps':12,'directions':list(DIRECTIONS),'productionUnchanged':True,'status':'lighting-experiment-awaiting-user-review','subjects':[],'source':{'blend':'source/environment-lighting.blend','recipe':'source/lighting_study.py','productionBlendSHA256':sha(repo/'prototypes/sushi-loop/assets/production/source/blender/sushi-loop-world-library.blend'),'sharedLightingRecipe':'../character-lighting-study/source/lighting_study.py','sharedLightingRecipeSHA256':sha(common_path)}}
  scenes=[]
  def configure(scene,subject):
   bpy.context.window.scene=scene
   runtime=load('s33_prop_lighting_camera_'+scene.name,repo/'prototypes/sushi-loop/assets/production/source/blender/capture_runtime.py');runtime.scene=lambda:scene
   record=runtime.configure_camera('square-top-front-oblique',subject['frame'],subject['root'],4)
   scene.eevee.taa_render_samples=64;scene.render.dither_intensity=0;scene.render.image_settings.compression=100;scene.world=scene.world.copy();scene.world.name=scene.name+' world';return record
  for subject in SUBJECTS:
   entry={**subject,'cellSize':128,'captureScale':4,'fps':12,'directions':list(DIRECTIONS),'projection':'top-down-oblique-square-grid','environmentHeightRatio':.7,'variants':[]}
   for spec in common.VARIANTS:
    variant=spec['id'];scene=bpy.data.scenes.new('S33 prop lighting '+subject['id']+' '+variant);scenes.append(scene);bpy.context.window.scene=scene
    scene['lightingStudySubject']=subject['id'];scene['lightingStudyVariant']=variant
    root=bpy.data.objects.new(subject['id']+' '+variant+' ground root',None);scene.collection.objects.link(root);scene['studyRoot']=root.name
    mats={};objects=[]
    for placement in subject['placements']:
     for name,mesh in frozen[placement['id']]:
      obj=bpy.data.objects.new(subject['id']+' '+variant+' '+name,mesh.copy());obj.data.transform(Matrix.Translation(placement['offset']));obj.parent=root;scene.collection.objects.link(obj)
      obj['sourceObject']=name;obj['sourceAssetId']=placement['id'];obj['sourceOffset']=placement['offset'];objects.append(obj)
      for slot in obj.material_slots:
       old=slot.material
       if old:
        if old.name not in mats:
         mat=common.matte_copy(old,variant)
         if mat.node_tree.animation_data:mat.node_tree.animation_data_clear()
         mats[old.name]=mat
        slot.material=mats[old.name]
    camera=configure(scene,subject);settings=spec['settings'];phase(scene,0)
    if variant!='baseline':
     camera['artStyle']['lighting']='actual overhead area key plus four identical cardinal area fill lights';camera['artStyle']['lowerShading']='original height ramp; old camera-facing form multiplier bypassed'
     common.area(scene,scene.name+' overhead',(0,0,4.5),(0,0,.8),settings['topWatts'],settings['topSize'])
     for i,(x,y) in enumerate(((3,0),(0,3),(-3,0),(0,-3))):common.area(scene,scene.name+' fill '+str(i),(x,y,1.8),(0,0,.8),settings['fillWattsEach'],4)
    geometry=mesh_hash(objects);scene['studyGeometrySHA256']=geometry;scene['nativePlacements']=json.dumps(subject['placements'])
    captures={d:{'image':f'sprites/{subject["id"]}/{variant}-{d}.png'} for d in DIRECTIONS}
    if subject['id']=='belt-connected':captures['S'].update(fps=12,frames=[captures['S']['image']]+[f'frames/{subject["id"]}/{variant}-{f:03d}.png' for f in range(1,24)])
    desc='Original emission materials and procedural deck colors.' if variant=='baseline' else f'{settings["topWatts"]} W overhead key, with the same four 100 W fill lights and matte materials.'
    entry['variants'].append({'id':variant,'name':spec['name'],'description':desc,'settings':settings,'scene':scene.name,'geometrySHA256':geometry,'camera':camera,'captures':captures})
   # Shared per-subject detail crop, measured in the exact capture projection.
   from bpy_extras.object_utils import world_to_camera_view
   scene=bpy.data.scenes[entry['variants'][0]['scene']];bpy.context.window.scene=scene;scene.view_layers[0].update();points=[v.co for o in scene.objects if o.type=='MESH' for v in o.data.vertices];bounds=[]
   for angle in DIRECTIONS.values():
    rot=Matrix.Rotation(angle,4,'Z')
    for p in points:
     q=world_to_camera_view(scene,scene.camera,rot@p);bounds.append((q.x*subject['frame'][0],(1-q.y)*subject['frame'][1]))
   lo=[min(p[i] for p in bounds)-6 for i in (0,1)];hi=[max(p[i] for p in bounds)+6 for i in (0,1)]
   entry['detailCrop']=[math.floor(lo[0]),math.floor(lo[1]),math.ceil(hi[0]-lo[0]),math.ceil(hi[1]-lo[1])]
   # Classification surfaces are native ungraded emission masks. For belts:
   # red=rail top, blue=rail side, green=deck. For crate:red=top,blue=side.
   if subject['id']!='belt-connected':
    mask=bpy.data.scenes.new('S33 prop lighting '+subject['id']+' mask');scenes.append(mask);bpy.context.window.scene=mask;mask['lightingStudySubject']=subject['id'];mask['lightingStudyVariant']='mask'
    mr=bpy.data.objects.new(subject['id']+' mask root',None);mask.collection.objects.link(mr);mask['studyRoot']=mr.name
    materials=[]
    for i,color in enumerate(((0,0,0,1),(1,0,0,1),(0,0,1,1),(0,1,0,1))):
     m=bpy.data.materials.new(subject['id']+' region '+str(i));m.use_nodes=True;out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL');emit=m.node_tree.nodes.new('ShaderNodeEmission');emit.inputs['Color'].default_value=color;m.node_tree.links.new(emit.outputs[0],out.inputs['Surface']);materials.append(m)
    for obj in [o for o in scene.objects if o.type=='MESH']:
     copy=bpy.data.objects.new(subject['id']+' mask '+obj['sourceObject'],obj.data.copy());copy.parent=mr;mask.collection.objects.link(copy);copy.data.materials.clear()
     for m in materials:copy.data.materials.append(m)
     name=obj['sourceObject'];rail='rail' in name;deck='deck' in name
     for poly in copy.data.polygons:
      selected=subject['id']=='crate-wood' or rail
      poly.material_index=1 if selected and poly.normal.z>=.65 else 2 if selected and poly.normal.z<=.35 else 3 if deck else 0
    configure(mask,subject);mask.render.use_compositing=False
    entry['regionMasks']={d:f'validation/{subject["id"]}-{d}.png' for d in DIRECTIONS};entry['maskScene']=mask.name
   manifest['subjects'].append(entry)
  path=folder/'source/environment-lighting.blend';path.parent.mkdir(parents=True,exist_ok=True);bpy.data.libraries.write(str(path),set(scenes),fake_user=True,compress=True)
  manifest['source']['sha256']=sha(path);manifest['source']['recipeSHA256']=sha(__file__);write(folder/'manifest.json',manifest)
  return {'project':str(path),'sha256':manifest['source']['sha256'],'subjects':[(s['id'],s['detailCrop']) for s in manifest['subjects']],'scenes':len(scenes)}
 finally:
  for aid,rot in oldrots.items():state['runtime'].assets[aid]['root'].rotation_euler=rot
  sc.frame_set(oldframe)
  for c,(r,v) in visibility.items():c.hide_render=r;c.hide_viewport=v
  bpy.context.window.scene=previous

def render(folder,variants):
 folder=Path(folder);m=json.loads((folder/'manifest.json').read_text());records=[];tag='-'.join(variants)
 def capture(subject,item,d,frame,path):
  scene=bpy.data.scenes[item['scene']];bpy.context.window.scene=scene;bpy.data.objects[scene['studyRoot']].rotation_euler.z=DIRECTIONS[d]
  names=phase(scene,-7*frame/24);scene.view_layers[0].update();target=folder/path;target.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(target);bpy.ops.render.render(write_still=True,scene=scene.name)
  records.append({'subject':subject['id'],'variant':item['id'],'direction':d,'frame':frame,'phase':-7*frame/24,'phaseMaterials':names,'image':path,'sha256':sha(target),'geometrySHA256':scene.get('studyGeometrySHA256'),'camera':item.get('camera')})
  write(folder/f'capture-status-{tag}.json',{'state':'rendering','done':len(records),'current':[subject['id'],item['id'],d,frame]})
 for s in m['subjects']:
  for v in s['variants']:
   if v['id'] not in variants:continue
   for d,c in v['captures'].items():capture(s,v,d,0,c['image'])
   for f,path in enumerate(v['captures'].get('S',{}).get('frames',[])):
    if f:capture(s,v,'S',f,path)
  if 'baseline' in variants and s.get('maskScene'):
   item={'id':'mask','scene':s['maskScene']}
   for d,path in s['regionMasks'].items():capture(s,item,d,0,path)
 write(folder/f'captures-{tag}.json',{'sourceSHA256':m['source']['sha256'],'records':records});write(folder/f'capture-status-{tag}.json',{'state':'complete','done':len(records)})

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--render',type=Path);p.add_argument('--variants',nargs='+',default=['baseline','soft','faceted','crisp']);args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 if args.render:render(args.render,args.variants)
