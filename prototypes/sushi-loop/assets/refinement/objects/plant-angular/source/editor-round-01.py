"""Native plant candidate, immutable round 01. Run in isolated background Blender.
blender --background --python source/editor-round-01.py
Uses only the editable input blend; no reference raster enters the scene.
"""
import bpy, bmesh, hashlib, json, math, struct, time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'inputs/plant-tuned.blend'
OUT=ROOT/'candidates/round-01'
BLEND=ROOT/'source/round-01.blend'
BRIEF=json.loads((ROOT/'brief.json').read_text())
DIRECTIONS={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}
assert BRIEF['qualityCriteria'], 'Await frozen criteria'
assert not OUT.exists(), 'Immutable candidate already exists'
assert not BLEND.exists(), 'Immutable source already exists'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):
 Path(path).parent.mkdir(parents=True,exist_ok=True)
 Path(path).write_text(json.dumps(data,indent=2)+'\n')
def rel(path):return str(Path(path).relative_to(ROOT))
def registration():
 def px(p):
  q=world_to_camera_view(scene,scene.camera,Vector(p))
  return [q.x*scene.render.resolution_x,(1-q.y)*scene.render.resolution_y]
 return {'frame':[scene.render.resolution_x,scene.render.resolution_y],'root':px((0,0,0)),
         'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'unitHeight':px((0,0,1)),
         'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],
         'cameraMatrix':[list(r) for r in scene.camera.matrix_world],
         'orthoScale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y]}
def curves(action):
 for layer in action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    yield from bag.fcurves
def assign(owner,action):
 owner.animation_data_create();owner.animation_data.action=action
 if action and len(action.slots)==1:owner.animation_data.action_slot=action.slots[0]
def points(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 v=[ev.matrix_world@x.co for x in me.vertices];ev.to_mesh_clear();return v
def digest(v):
 return hashlib.sha256(b''.join(struct.pack('<3f',*p) for p in v)).hexdigest()
def geometry():
 records={}
 for o in meshes:
  v=points(o)
  records[o.name]={'min':[min(p[i] for p in v) for i in range(3)],
                   'max':[max(p[i] for p in v) for i in range(3)],'evaluatedVertices':len(v),'sha256':digest(v)}
 mn=[min(d['min'][i] for d in records.values()) for i in range(3)]
 mx=[max(d['max'][i] for d in records.values()) for i in range(3)]
 assert all(mn[i]>=[-.48,-.48,.015][i]-1e-6 for i in range(3)),mn
 assert all(mx[i]<=[.48,.48,1.48][i]+1e-6 for i in range(3)),mx
 return {'min':mn,'max':mx,'objects':records}
def topology(obj):
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 bm=bmesh.new();bm.from_mesh(me)
 d={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),
    'boundaryEdges':sum(e.is_boundary for e in bm.edges),
    'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),
    'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces)}
 bm.free();ev.to_mesh_clear();return d
def set_clip(clip):
 for o in leaves:assign(o.data.shape_keys,actions[o.name][clip])
 scene.frame_start=1;scene.frame_end=12 if clip=='idle' else 1
 scene['activeClip']=clip;scene.frame_set(1);bpy.context.view_layer.update()
def action_record(owner,action):
 return {'ownerType':'Key','ownerName':owner.name,'action':action.name,
         'slotIdentifier':action.slots[0].identifier,
         'fcurves':[{'path':f.data_path,'keyframes':[[p.co.x,p.co.y] for p in f.keyframe_points],
                     'interpolation':[p.interpolation for p in f.keyframe_points],
                     'modifiers':[m.type for m in f.modifiers]} for f in curves(action)]}

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
original_registration=registration()
root=bpy.data.objects[scene['studyRoot']]
root.name='plant-angular__root';scene['studyRoot']=root.name
scene.camera.name='plant-angular__camera'
scene.name='plant-angular__warm_refinement_round_01'
scene.render.film_transparent=True
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='8'
scene.render.fps=12;scene.render.fps_base=1
scene.cycles.samples=72;scene.cycles.use_denoising=True
scene.cycles.seed=213;scene.cycles.use_animated_seed=False
scene.render.use_persistent_data=True
root.rotation_euler=(0,0,0)
leaves=sorted([o for o in scene.objects if o.name.startswith('Folded thick blade')],key=lambda o:o.name)
assert len(leaves)==12
pot=bpy.data.objects['Planter continuous watertight shell'];pot.name='plant-angular__planter_shell'
soil=bpy.data.objects['Recessed soil'];soil.name='plant-angular__recessed_soil'
for i,o in enumerate(leaves):o.name='plant-angular__folded_leaf_%02d'%i
meshes=[o for o in scene.objects if o.type=='MESH']

# Two real shape keys bend each leaf progressively from its unmoving crown.
# The nearly shared phase gives one calm crown sway, with restrained leaf lag.
actions={}
for i,o in enumerate(leaves):
 basis=o.shape_key_add(name='Basis')
 sx=o.shape_key_add(name='Breeze X')
 sy=o.shape_key_add(name='Breeze depth')
 progress=o.data.attributes['leaf_progress']
 for j,p in enumerate(basis.data):
  t=float(progress.data[j].value);bend=t**1.85
  sx.data[j].co=p.co+Vector((.009*bend,0,.0012*math.sin(math.pi*t)))
  sy.data[j].co=p.co+Vector((0,.007*bend,.0008*math.sin(math.pi*t)))
 for key in [sx,sy]:key.slider_min=-1;key.slider_max=1
 keys=o.data.shape_keys;keys.name='plant-angular__leaf_%02d__shape_keys'%i
 keys.animation_data_create()
 actions[o.name]={}
 for clip in ['idle','static']:
  act=bpy.data.actions.new('WARM_NATIVE__plant-angular__%s__leaf_%02d'%(clip,i))
  act.use_fake_user=True;act['asset_id']='plant-angular';act['clip_id']=clip;act['fps']=12
  assign(keys,act)
  phase=.11*math.sin(i*1.73)
  for f in range(1,14) if clip=='idle' else [1]:
   t=2*math.pi*((f-1)%12)/12
   sx.value=math.sin(t+phase) if clip=='idle' else 0
   sy.value=.92*math.cos(t+phase) if clip=='idle' else 0
   sx.keyframe_insert(data_path='value',frame=f,group='Crown-anchored breeze')
   sy.keyframe_insert(data_path='value',frame=f,group='Crown-anchored breeze')
  for fc in curves(act):
   for kp in fc.keyframe_points:kp.interpolation='LINEAR'
   if clip=='idle':fc.modifiers.new('CYCLES')
  actions[o.name][clip]=act

# Remove unused study materials and geometry; all active nodes remain native.
bpy.data.orphans_purge(do_recursive=True)
set_clip('idle')
assert registration()==original_registration
assert registration()['root']==[192,576]
assert len([o for o in scene.objects if o.type=='LIGHT'])==1
light=next(o for o in scene.objects if o.type=='LIGHT')
assert light.data.type=='SUN' and list(light.rotation_euler)==[0,0,0]
assert len(bpy.data.images)==0
scene['refinementRound']=1
scene['recipe']='source/editor-round-01.py'
scene['sourceInputSHA256']=sha(SOURCE)
scene['captureContract']=json.dumps(BRIEF['constraints']['judgeMeasuredRequirements'],sort_keys=True)
scene['clipGuide']='candidates/round-01/records/rig.json'
scene['noGroundPlane']=True
scene['lightingSymmetry']='Axially symmetric world (absolute normal Z), vertical sun'
scene['idleDescription']='Crown-anchored two-axis leaf shape-key bend; fixed pot and root; frames1-12 unique,13 closure'
OUT.mkdir(parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)

validation={'asset':'plant-angular','round':1,'status':'awaiting-independent-review',
 'nativeSource':{'path':rel(BLEND),'sha256':sha(BLEND),'input':rel(SOURCE),'inputSHA256':sha(SOURCE),
                 'recipe':rel(__file__),'recipeSHA256':sha(__file__),'blender':bpy.app.version_string,
                 'scene':scene.name,'rootObject':root.name,'externalImages':[],'externalLibraries':[x.filepath for x in bpy.data.libraries]},
 'briefSHA256':sha(ROOT/'brief.json'),'capture':registration(),'originalCapture':original_registration,
 'fps':12,'logicalFrame':[192,384],'logicalRoot':[96,288],'sourceScale':2,'cellSize':128,
 'projection':'top-down-oblique-square-grid','footprint':[1,1],'geometryEnvelope':BRIEF['constraints']['geometryEnvelope'],
 'renderSettings':{'engine':scene.render.engine,'samples':scene.cycles.samples,'denoising':True,'seed':213,
                   'animatedSeed':False,'RGBA':True,'transparentFilm':True,'perViewFit':False,'perViewRecolor':False,
                   'postprocess':'none; native compositor retained from editable input','pixelFormat':'8-bit RGBA PNG'},
 'lighting':{'worldShader':'absolute world normal Z only; horizontally invariant','worldDiffuseStrength':.66,
             'worldReflectionStrength':1.35,'sunType':light.data.type,'sunRotation':list(light.rotation_euler),
             'sunEnergy':light.data.energy,'sunAngle':light.data.angle,'groundPlane':False,'receiverMeshCount':0},
 'topology':{o.name:topology(o) for o in meshes},'static':{},'idle':{},'renders':[],
 'notes':['All raw frames are unmodified native Cycles RGBA renders.',
          'One common root rotates the real meshes for each direction.',
          'Static is the neutral shape-key pose; idle is fully editable native geometry animation.',
          'No target image, camera-facing image card, image warp, mirrored capture, painted export, or ground plane.']}
rig={'assetId':'plant-angular','fps':12,'projection':'top-down-oblique-square-grid','footprint':[1,1],
     'groundRootObject':root.name,'sockets':{},'armatures':[],'clips':{}}
for clip in ['static','idle']:
 set_clip(clip)
 rig['clips'][clip]={'frames':12 if clip=='idle' else 1,'fps':12,'loop':clip=='idle','static':clip=='static',
                    'firstFrame':1,'lastUniqueFrame':12 if clip=='idle' else 1,
                    'closingKeyFrame':13 if clip=='idle' else None,
                    'actions':[action_record(o.data.shape_keys,actions[o.name][clip]) for o in leaves],
                    'geometryOwners':[o.name for o in leaves]}
for clip in ['static','idle']:
 set_clip(clip)
 for direction,angle in DIRECTIONS.items():
  root.rotation_euler.z=angle
  frames=[]
  for index in range(12 if clip=='idle' else 1):
   scene.frame_set(index+1);bpy.context.view_layer.update()
   current=geometry()
   capture=OUT/'raw'/('%s-%s'%(clip,direction))/('%03d.png'%index)
   capture.parent.mkdir(parents=True,exist_ok=True)
   scene.render.filepath=str(capture)
   start=time.monotonic();bpy.ops.render.render(write_still=True,scene=scene.name)
   record={'clip':clip,'direction':direction,'index':index,'blenderFrame':index+1,
           'path':rel(capture),'sha256':sha(capture),'seconds':round(time.monotonic()-start,4),
           'rootRotationZ':angle,'geometry':current}
   frames.append(record);validation['renders'].append(record)
   write(OUT/'native-validation.json',validation)
   print('PLANT_CAPTURE',clip,direction,index,record['seconds'],flush=True)
  validation[clip][direction]={'count':len(frames),'frames':[{'path':f['path'],'sha256':f['sha256']} for f in frames]}

# Prove unique native motion and closure using evaluated mesh coordinates.
set_clip('idle');root.rotation_euler.z=0
poses=[]
for f in range(1,14):
 scene.frame_set(f);bpy.context.view_layer.update();poses.append({o.name:points(o) for o in meshes})
motion={'frame1To13MaxDelta':0,'fixedPotMaxDelta':0,'leaves':{},'all12EvaluatedPosesUnique':False,
        'rootObjectTransform':{'location':list(root.location),'rotation':list(root.rotation_euler),'scale':list(root.scale)}}
all_signatures=[]
for index,pose in enumerate(poses):
 all_signatures.append(hashlib.sha256(''.join(digest(pose[o.name]) for o in leaves).encode()).hexdigest())
for o in meshes:
 close=max((a-b).length for a,b in zip(poses[0][o.name],poses[12][o.name]))
 motion['frame1To13MaxDelta']=max(motion['frame1To13MaxDelta'],close)
 if o in [pot,soil]:
  motion['fixedPotMaxDelta']=max(motion['fixedPotMaxDelta'],max(max((a-b).length for a,b in zip(poses[0][o.name],p[o.name])) for p in poses))
 if o in leaves:
  steps=[max((a-b).length for a,b in zip(poses[i][o.name],poses[(i+1)%12][o.name])) for i in range(12)]
  motion['leaves'][o.name]={'uniqueEvaluatedPoses':len(set(digest(p[o.name]) for p in poses[:12])),
                          'maximumAdjacentStep':max(steps),'loopBoundaryStep':steps[11],
                          'loopToLargestStepRatio':steps[11]/max(steps),
                          'maximumTipExcursion':max(max((a-b).length for a,b in zip(poses[0][o.name],p[o.name])) for p in poses[:12])}
motion['all12EvaluatedPosesUnique']=len(set(all_signatures[:12]))==12
motion['poseHashes']=all_signatures
assert motion['all12EvaluatedPosesUnique']
assert motion['frame1To13MaxDelta']<1e-7
assert motion['fixedPotMaxDelta']==0
validation['motion']=motion
validation['nativeContractPassed']=True
write(OUT/'native-validation.json',validation)
write(OUT/'records/rig.json',rig)
camera=json.loads((ROOT/'inputs/source-camera.json').read_text())
camera.update({'frame':[192,384],'anchor':[96,288],'captureScale':2,'fps':12,
               'nativeFrame':[384,768],'nativeRoot':[192,576],'nativeRegistration':registration()})
write(OUT/'records/camera.json',camera)
asset=json.loads((ROOT/'inputs/source-asset.json').read_text())
asset.update({'scale':2,'sourceScale':2,'nativeFrame':[384,768],
              'artStyle':{'style':BRIEF['style'],'renderer':'Cycles','nativeSource':rel(BLEND),'round':1}})
write(OUT/'records/asset.json',asset)
print('PLANT_NATIVE_READY',str(OUT),flush=True)
