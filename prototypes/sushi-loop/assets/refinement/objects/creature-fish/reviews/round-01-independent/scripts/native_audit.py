import bpy,sys,json,math,hashlib,time
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1];O=P.parents[1];C=O/'candidates/round-01';SOURCE=Path(bpy.data.filepath)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mat(m):return [list(r) for r in m]
def bounds(v):return {'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)]}
def err(a,b):return max(abs(x-y) for r1,r2 in zip(a,b) for x,y in zip(r1,r2))
def write(n,d):p=P/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
assert sha(SOURCE)=='7e32d44911b1fd044fe7f64ef6033f9cfccd5d0ec1c23fc9a46c4497bbb63ae7'
rig=json.loads((C/'rig.json').read_text());coll=bpy.data.collections['S33_CFX_creature-fish.001'];root=bpy.data.objects['creature-fish__ground_root.001'];arm=bpy.data.objects['creature-fish__armature.001'];scene=next(s for s in bpy.data.scenes if coll.name in s.collection.children)
bpy.context.window.scene=scene;bpy.context.window.view_layer=scene.view_layers[0]
def show(lc):
 lc.exclude=False;lc.hide_viewport=False
 for child in lc.children:show(child)
show(bpy.context.view_layer.layer_collection)
for lc in bpy.context.view_layer.layer_collection.children:lc.exclude=lc.collection!=coll
for c in scene.collection.children:c.hide_render=c!=coll;c.hide_viewport=c!=coll
for o in coll.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
cam=scene.camera
camera={'type':cam.data.type,'orthoScale':cam.data.ortho_scale,'sensorFit':cam.data.sensor_fit,'shift':[cam.data.shift_x,cam.data.shift_y],'matrix':mat(cam.matrix_world),'frame':[scene.render.resolution_x,scene.render.resolution_y],'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'engine':scene.render.engine,'dither':scene.render.dither_intensity,'filmTransparent':scene.render.film_transparent,'colorMode':scene.render.image_settings.color_mode,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'compositing':scene.render.use_compositing,'filterSize':scene.render.filter_size}
materials={s.material for o in coll.all_objects if o.type=='MESH' for s in o.material_slots if s.material}
source={'projectSHA256':sha(SOURCE),'blender':bpy.app.version_string,'scene':scene.name,'collection':coll.name,'camera':camera,'boneModes':{b.name:b.rotation_mode for b in arm.pose.bones},'actions':[{'name':a.name,'fakeUser':a.use_fake_user,'range':list(a.frame_range)} for a in bpy.data.actions],'rootMetadata':{k:root[k] for k in root.keys() if isinstance(root[k],(str,int,float))},'owned':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'modifiers':[{'name':m.name,'type':m.type,'owner':getattr(getattr(m,'object',None),'name',None)} for m in o.modifiers]} for o in coll.all_objects],'usedImageTextures':[{'material':m.name,'path':n.image.filepath} for m in materials for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],'externalLibraries':[l.filepath for l in bpy.data.libraries],'lights':[{'name':o.name,'energy':o.data.energy,'color':list(o.data.color),'shape':o.data.shape,'size':o.data.size,'matrix':mat(o.matrix_world)} for o in scene.objects if o.type=='LIGHT']}
write('saved-source-inspection.json',source)
F={'N':math.pi,'E':math.pi/2,'S':0.,'W':-math.pi/2};records=[];boundary=[];response=[];captures=[];editor=json.loads((C/'geometry-ledger.json').read_text());lookup={(x['clip'],x['direction'],x['frame']):x for x in editor['views']};meshes=sorted([o for o in coll.all_objects if o.type=='MESH'],key=lambda o:o.name)
def apply(clip,frame,d):
 a=bpy.data.actions[f'S33_NATIVE__creature-fish__{clip}__creature-fish__armature.001'];arm.animation_data_create();arm.animation_data.action=a;arm.animation_data.action_slot=a.slots[0];root.rotation_euler=(0,0,F[d]);scene.frame_set(frame);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
def measure(clip,frame,d):
 apply(clip,frame,d);dg=bpy.context.evaluated_depsgraph_get();inv=arm.matrix_world.inverted();raw=[];pts=[];relative=[];attach=[]
 for o in meshes:
  raw.extend(o.matrix_world@v.co for v in o.data.vertices);e=o.evaluated_get(dg);m=e.to_mesh();q=[e.matrix_world@v.co for v in m.vertices];pts.extend(q);relative.extend(inv@v for v in q);e.to_mesh_clear()
  if any(n in o.name for n in ['eye','mouth','fin']):attach.append({'object':o.name,'parent':o.parent.name if o.parent else None,'sameArmature':any(m.type=='ARMATURE' and m.object==arm for m in o.modifiers),'normalizedWeights':all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in o.data.vertices)})
 pixel=[world_to_camera_view(scene,cam,v) for v in pts];row={'clip':clip,'direction':d,'frame':frame,'index':frame-1,'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'cameraMatrix':mat(cam.matrix_world),'rawAuthoredBounds':bounds(raw),'evaluatedBounds':bounds(pts),'boneMatrices':{b.name:mat(b.matrix) for b in arm.pose.bones},'armatureMatrix':mat(arm.matrix_world),'cameraBounds':{'min':[min(p[i] for p in pixel) for i in range(2)],'max':[max(p[i] for p in pixel) for i in range(2)]},'attachments':attach};return row,relative
for clip,recipe in rig['clips'].items():
 for d in F:
  rows=[];first=None;firstvs=None;last=None;lastvs=None
  for frame in range(1,13):
   row,vs=measure(clip,frame,d)
   if first is None:first=row;firstvs=vs
   if frame==12:last=row;lastvs=vs
   row['relativeVertexResponseFromFrame1']=max((a-b).length for a,b in zip(firstvs,vs));row['boneResponseFromFrame1']=max(err(first['boneMatrices'][n],m) for n,m in row['boneMatrices'].items());ex=lookup[(clip,d,frame)]
   row['editorLedgerMaxBoundResidual']=max(abs(row[k]['min'][i]-ex[e]['min'][i]) for k,e in [('rawAuthoredBounds','rawAuthoredBounds'),('evaluatedBounds','evaluatedModifierBounds')] for i in range(3))
   row['editorLedgerMaxBoundResidual']=max(row['editorLedgerMaxBoundResidual'],max(abs(row[k]['max'][i]-ex[e]['max'][i]) for k,e in [('rawAuthoredBounds','rawAuthoredBounds'),('evaluatedBounds','evaluatedModifierBounds')] for i in range(3)))
   box=row['evaluatedBounds'];assert all(box['min'][i]>=(-1.02 if i<2 else .02)-1e-5 and box['max'][i]<=(1.02 if i<2 else 1.18)+1e-5 for i in range(3));assert all(0<row['cameraBounds']['min'][i]<row['cameraBounds']['max'][i]<1 for i in range(2));assert all(abs(row['rootMatrix'][i][3])<1e-8 for i in range(3));records.append(row);rows.append(row)
  response.append({'clip':clip,'direction':d,'maxBoneResponse':max(r['boneResponseFromFrame1'] for r in rows),'maxRelativeVertexResponse':max(r['relativeVertexResponseFromFrame1'] for r in rows)})
  refs=[(13,first,firstvs)] if recipe['loop'] else [(13,last,lastvs),(24,last,lastvs)]
  for frame,ref,rv in refs:
   row,vs=measure(clip,frame,d);boundary.append({'clip':clip,'direction':d,'frame':frame,'relativeVertexResidual':max((a-b).length for a,b in zip(rv,vs)),'boneResidual':max(err(ref['boneMatrices'][n],m) for n,m in row['boneMatrices'].items()),'objectResidual':err(ref['armatureMatrix'],row['armatureMatrix'])})
  # Saved-source replay, each clip/facing at its largest evaluated relative-body phase.
  fi=max(rows,key=lambda r:r['relativeVertexResponseFromFrame1'])['frame'];apply(clip,fi,d);p=P/'native-replay'/clip/d/f'{fi-1:03d}.png';p.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True,scene=scene.name);captures.append({'clip':clip,'direction':d,'index':fi-1,'path':str(p.relative_to(O)),'candidateNative':f'candidates/round-01/native/{clip}/{d}/{fi-1:03d}.png','sha256':sha(p),'rootRotationZ':root.rotation_euler.z,'rootMatrix':mat(root.matrix_world),'cameraMatrix':mat(cam.matrix_world)})
  write('independent-native-evidence.json',{'packetSHA256':sha(C/'packet.json'),'sourceSHA256':sha(SOURCE),'camera':camera,'captureRecords':captures,'responses':response,'boundaryControls':boundary,'views':records,'scope':'All528 saved-source phases independently measured;44 required clip/facing maximum-relative-motion replay samples. No source/model/art changes or saves.'});print('JUDGE_NATIVE',clip,d,fi,flush=True)
assert sha(SOURCE)==source['projectSHA256'];print('JUDGE_NATIVE_COMPLETE',len(records),len(captures),flush=True)
