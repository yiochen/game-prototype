import sys
sys.dont_write_bytecode=True
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent;OBJ=HERE.parents[1];OUT=OBJ/'candidates/round-04';scene=bpy.context.scene;col=bpy.data.collections['S33_PROP_garbage-shelving'];root=bpy.data.objects['garbage-shelving__root'];carriers=[o for o in col.objects if o.type=='MESH'];RIG=json.loads((HERE/'resources/original-rig.json').read_text())
def pl(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if isinstance(x,dict):return {k:pl(v) for k,v in x.items()}
 return [pl(v) for v in x]
def apply(c,f):
 for r in RIG['clips'][c]['actions']:
  o=bpy.data.objects[r['ownerName']];a=bpy.data.actions[r['action']];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=next(s for s in a.slots if s.identifier==r['slotIdentifier'])
 root.rotation_euler=(0,0,0);scene.frame_set(f);bpy.context.view_layer.update()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
apply('idle',1);dg=bpy.context.evaluated_depsgraph_get();contact=[];meshes=[]
for o in carriers:
 eo=o.evaluated_get(dg);me=eo.to_mesh();vs=[eo.matrix_world@v.co for v in me.vertices];minimum=min(v.z for v in vs)
 minima=[v for v in vs if v.z<minimum+.002]
 if 'old_upright' in o.name or 'fallen_board' in o.name or 'loose_debris' in o.name:
  contact.append({'owner':o.name,'groundMinZ':minimum,'bandVerticesWorld':[list(v) for v in minima],'bandCentroid':[sum(v[i] for v in minima)/len(minima) for i in range(3)],'contactTolerance':.002,'withinIdleGroundBand':abs(minimum)<.002})
 meshes.append({'name':o.name,'localVertices':pl([v.co for v in o.data.vertices]),'polygons':[[*p.vertices] for p in o.data.polygons],'materialIndices':[p.material_index for p in o.data.polygons],'materialSlots':[m.name for m in o.data.materials],'evaluatedLocalVerticesSHA256':hashlib.sha256(json.dumps([list(v.co) for v in me.vertices]).encode()).hexdigest(),'evaluatedWorldVerticesSHA256':hashlib.sha256(json.dumps([list(v) for v in vs]).encode()).hexdigest(),'objectMatrix':pl(o.matrix_world),'parentInverse':pl(o.matrix_parent_inverse),'UVLayers':[u.name for u in o.data.uv_layers],'drivers':[d.data_path for d in o.animation_data.drivers] if o.animation_data else []});eo.to_mesh_clear()
dump(OUT/'contacts-and-native-meshes.json',{'projectSHA256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'idleContacts':contact,'meshes':meshes,'scene':scene.name,'sourceSavedNeverModifiedInInspection':True})
# These additional geometry diagnostics are explicitly outside the immutable registered export camera.
cam=scene.camera;originalMatrix=cam.matrix_world.copy();originalOrtho=cam.data.ortho_scale;originalShift=cam.data.shift_y
cam.data.shift_y=0;cam.data.ortho_scale=3.5
folder=OUT/'previews';folder.mkdir(exist_ok=True)
for name,pos,target in [('underside-diagnostic',(2.5,-4,-2),(0,0,.6)),('ground-contact-frontal-diagnostic',(0,-8,.7),(0,-.1,.7)),('rear-structure-diagnostic',(3,4,2.6),(0,0,.8))]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
 if name=='underside-diagnostic':
  d=bpy.data.lights.new('Diagnostic only underside soft fill','AREA');d.energy=120;d.size=4;lo=bpy.data.objects.new(d.name,d);scene.collection.objects.link(lo);lo.location=(0,-2,-3);lo.rotation_euler=(-lo.location).to_track_quat('-Z','Y').to_euler()
 scene.render.filepath=str(folder/f'{name}.png');bpy.ops.render.render(write_still=True)
 if name=='underside-diagnostic':bpy.data.objects.remove(lo,do_unlink=True)
cam.matrix_world=originalMatrix;cam.data.ortho_scale=originalOrtho;cam.data.shift_y=originalShift
print('SAVED_CONTACT_DIAGNOSTICS_DONE',flush=True)
