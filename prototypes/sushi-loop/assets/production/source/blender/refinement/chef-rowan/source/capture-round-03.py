"""Saved/reopened native audit and fixed capture; --preview or --full."""
import bpy,sys,json,math,hashlib,importlib.util
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).parent;OBJ=HERE.parent
OUT=OBJ/'candidates/round-03';OUT.mkdir(parents=True,exist_ok=True)
mode='full' if '--full' in sys.argv else 'preview'
rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
brief=json.loads((OBJ/'brief-v4-food-occlusion.json').read_text())
original=json.loads((HERE/'inspection-v1/native-action-audit.json').read_text())
root=bpy.data.objects[rig['groundRootObject']];arm=bpy.data.objects[rig['armatures'][0]['object']]
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001'];scene=bpy.context.scene
nativepath=HERE/'resources/original-native-actions.py'
spec=importlib.util.spec_from_file_location('original_native_actions',nativepath);native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
col.hide_viewport=False;col.hide_render=False
def unhide(lc):
 lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
 for c in lc.children:unhide(c)
unhide(bpy.context.view_layer.layer_collection)
arm.hide_viewport=False;arm.hide_set(False)
bpy.context.view_layer.update()
asset=dict(root=root,collection=col,armature=arm)
saved_root_matrix=[list(r) for r in root.matrix_world]
food=bpy.data.objects[root.name+'__held_dish-salmon'];plane=bpy.data.objects[food.name+'__image_plane'];utensil=bpy.data.objects[root.name+'__utensil']
def h(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bounds(o,dg):
 eo=o.evaluated_get(dg);m=eo.to_mesh();vs=[eo.matrix_world@v.co for v in m.vertices];eo.to_mesh_clear()
 return [[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]
frames=[];checks=[];original_by={(f['clip'],f['direction'],f['frame']):f for f in original['frames']}
for clip in rig['clips']:
 for direction in ['S','E','N','W']:
  for frame in range(1,13):
   native.apply_clip(asset,rig,clip,frame=frame,direction=direction,scene=scene)
   bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ea=arm.evaluated_get(dg)
   obs={o.name:bounds(o,dg) for o in col.objects if o.type=='MESH' and not o.hide_render}
   body=[b for n,b in obs.items() if '__held_dish-' not in n and '__knife_' not in n]
   env=[[min(b[0][i] for b in body) for i in range(3)],[max(b[1][i] for b in body) for i in range(3)]]
   contacts={}
   for s in ['L','R']:
    pb=ea.pose.bones['hand_'+s];rb=ea.data.bones['hand_'+s]
    contacts['palm_'+s]=list(ea.matrix_world@pb.matrix@rb.matrix_local.inverted()@(rb.head_local+Vector((0,-.002,-.046))))
    contacts['foot_'+s]=list(ea.matrix_world@ea.pose.bones['foot_'+s].head)
   f=dict(clip=clip,direction=direction,frame=frame,index=len(frames),bounds=env,contacts=contacts,
          food_socket=list(food.evaluated_get(dg).matrix_world.translation),food_plane_visible=not plane.hide_render,
          utensil_socket=list(utensil.evaluated_get(dg).matrix_world.translation),knife_visible=not bpy.data.objects[root.name+'__knife_blade'].hide_render,
          object_bounds=obs,
          evaluatedTopology={o.name:[len(o.evaluated_get(dg).data.vertices),len(o.evaluated_get(dg).data.polygons)] for o in col.objects if o.type=='MESH'})
   old=original_by[(clip,direction,frame)]
   f['sourceContactMaximumError']=max(abs(a-b) for k in contacts for a,b in zip(contacts[k],old['contacts'][k]))
   f['sourceFoodRootMaximumError']=max(abs(a-b) for a,b in zip(f['food_socket'],old['food_socket']))
   f['sourceUtensilRootMaximumError']=max(abs(a-b) for a,b in zip(f['utensil_socket'],old['utensil_socket']))
   f['sourceEnvelopeDifference']=[[env[j][i]-old['bounds'][j][i] for i in range(3)] for j in range(2)]
   frames.append(f)
cam=scene.camera
textures=[]
for im in bpy.data.images:
 if im.source in ['FILE','TILED']:
  textures.append(dict(name=im.name,size=list(im.size),packed=bool(im.packed_file),sha256=hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,filepath=im.filepath))
uvs=[list(v.uv) for v in plane.data.uv_layers.active.data]
xs=[v.co.x for v in plane.data.vertices];ys=[v.co.y for v in plane.data.vertices]
food_audit=dict(representation='Exact canonical packed2D raster, not modeled sushi',textures=textures,fullUV=uvs,
                localPlaneWidth=max(xs)-min(xs),localPlaneHeight=max(ys)-min(ys),
                worldDisplayWidth=(max(xs)-min(xs))*root.scale.x,
                worldDisplayHeight=(max(ys)-min(ys))*root.scale.x,
                planeBottomLocalY=min(ys),planeLocation=list(plane.location),planeRotation=list(plane.rotation_euler),
                depthPolicy=brief['foodOcclusionPolicy'],depthProvenance=plane.get('camera_ray_depth_bias_world_cells'),
                oldSourceSHA256='5de7475813a133bb643fa9de09adbef104c7bd20a572514a297cba54846ceafe',newDependency=brief['foodDependency'])
loop_closure=[]
def snapshot():
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ea=arm.evaluated_get(dg)
 return [v for b in ea.pose.bones for row in b.matrix for v in row]+[v for o in [food,plane,utensil] for row in o.evaluated_get(dg).matrix_world for v in row]
for clip,rc in rig['clips'].items():
 native.apply_clip(asset,rig,clip,1,'S',scene);first=snapshot()
 endpoint=13 if rc['loop'] else 12
 native.apply_clip(asset,rig,clip,endpoint,'S',scene);last=snapshot()
 loop_closure.append(dict(clip=clip,loop=rc['loop'],first=1,checkedEndpoint=endpoint,maximumMatrixError=max(abs(a-b) for a,b in zip(first,last)),policy='Duplicate closing key13 excluded from 12-frame loop atlas' if rc['loop'] else 'Original out-and-back equal endpoints retained; playback nonlooping'))
actions={a.name:dict(slots=[s.identifier for s in a.slots],frameRange=list(a.frame_range),
                    keyframeHash=h([dict(path=f.data_path,index=f.array_index,keys=[dict(co=list(k.co),interpolation=k.interpolation) for k in f.keyframe_points]) for f in native._fcurves(a)])) for a in bpy.data.actions}
rest=[dict(name=b.name,parent=b.parent.name if b.parent else None,head=list(b.head_local),tail=list(b.tail_local),deform=b.use_deform) for b in arm.data.bones]
foreign=[];materials=[]
for o in col.objects:
 if o.parent and o.parent not in col.objects[:]:foreign.append(o.name+' parent '+o.parent.name)
 for m in o.modifiers:
  target=getattr(m,'object',None)
  if target and target not in col.objects[:]:foreign.append(o.name+' modifier '+target.name)
 for c in o.constraints:
  if getattr(c,'target',None) and c.target not in col.objects[:]:foreign.append(o.name+' constraint '+c.target.name)
 if o.type=='MESH':materials.append(dict(object=o.name,materials=[m.name for m in o.data.materials],faceMaterialIndices=sorted(set(p.material_index for p in o.data.polygons)),valid=all(p.material_index<len(o.data.materials) for p in o.data.polygons)))
checks=[dict(name='192 indexed native frame records',passed=len(frames)==192),
        dict(name='registered camera unchanged',passed=[list(r) for r in cam.matrix_world]==original['source']['camera']['matrix'] and cam.data.ortho_scale==original['source']['camera']['ortho_scale'] and cam.data.shift_y==original['source']['camera']['shift_y']),
        dict(name='all native loop and load endpoints retained',passed=all(c['maximumMatrixError']<1e-6 for c in loop_closure)),
        dict(name='all original action slots and keyframes retained',passed=actions==json.loads((HERE/'inspection-v1/original-action-identity.json').read_text())),
        dict(name='all source foot/palm contacts unchanged',passed=max(f['sourceContactMaximumError'] for f in frames)<1e-6),
        dict(name='all food-root/utensil paths unchanged',passed=max(max(f['sourceFoodRootMaximumError'],f['sourceUtensilRootMaximumError']) for f in frames)<1e-6),
        dict(name='one-cell physical body envelope',passed=all(max(abs(f['bounds'][j][i]) for j in range(2) for i in range(2))<.5 for f in frames)),
        dict(name='source phase-specific height envelope',passed=all(f['bounds'][1][2]<=original_by[(f['clip'],f['direction'],f['frame'])]['bounds'][1][2]+1e-6 for f in frames)),
        dict(name='source phase-specific physical body clearance',passed=all(max(-f['sourceEnvelopeDifference'][0][i],f['sourceEnvelopeDifference'][1][i])<1e-6 for f in frames for i in range(3))),
        dict(name='stable evaluated mesh topology in all 192 poses',passed=all(f['evaluatedTopology']==frames[0]['evaluatedTopology'] for f in frames)),
        dict(name='nominal authored height retained',passed=abs(float(root['anatomy_height'])-1.3968749344348907)<1e-8),
        dict(name='original rest skeleton retained',passed=rest==original['bones']),
        dict(name='exact canonical food packed and no stale texture',passed=len(textures)==1 and textures[0]['sha256']==brief['foodDependency']['sha256'] and textures[0]['size']==[731,505]),
        dict(name='full source UV and bottom anchor',passed=sorted(uvs)==sorted([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]) and abs(min(ys))<1e-9 and abs(food_audit['worldDisplayWidth']-.35)<1e-7 and abs(food_audit['worldDisplayHeight']-.35*505/731)<1e-7),
        dict(name='visibility matches original',passed=all(f['food_plane_visible']==original_by[(f['clip'],f['direction'],f['frame'])]['food_plane_visible'] and f['knife_visible']==original_by[(f['clip'],f['direction'],f['frame'])]['knife_visible'] for f in frames)),
        dict(name='material assignments valid',passed=all(m['valid'] for m in materials)),
        dict(name='no foreign rig dependency',passed=not foreign)]
audit=dict(activeBrief='brief-v4-food-occlusion.json',sourceProject=bpy.data.filepath,sourceProjectSHA256=hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),
           savedReopenedSource=True,blender=bpy.app.version_string,camera=dict(matrix=[list(r) for r in cam.matrix_world],orthoScale=cam.data.ortho_scale,shiftY=cam.data.shift_y,shiftX=cam.data.shift_x),
           root=dict(savedMatrix=saved_root_matrix,scale=list(root.scale),nominalHeight=float(root['anatomy_height'])),
           logicalFrame=[192,320],logicalRoot=[96,248],nativeFrame=[384,640],sourceScale=2,fps=12,
           yaws=dict(S=0,E=90,N=180,W=-90),clips={k:{x:c[x] for x in ['frames','fps','loop','closingKeyFrame']} for k,c in rig['clips'].items()},
           restSkeleton=rest,actions=actions,loopClosure=loop_closure,food=food_audit,materials=materials,foreignDependencies=foreign,
           checks=checks,allChecksPassed=all(c['passed'] for c in checks),frames=frames)
(OUT/'native-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('AUDIT',json.dumps(checks),flush=True)
if not audit['allChecksPassed']:raise RuntimeError('Native audit failed; inspect before full capture.')
render_dir=OUT/('frames' if mode=='full' else 'preflight');render_dir.mkdir(exist_ok=True)
todo=frames if mode=='full' else [f for f in frames if f['frame']==1 or (f['clip']=='load' and f['frame']==6)]
for f in todo:
 native.apply_clip(asset,rig,f['clip'],frame=f['frame'],direction=f['direction'],scene=scene)
 scene.render.filepath=str(render_dir/f"{f['clip']}-{f['direction']}-{f['frame']-1:02d}.png")
 bpy.ops.render.render(write_still=True)
 print('CAPTURE',f['clip'],f['direction'],f['frame'],flush=True)
