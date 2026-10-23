import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
sys.dont_write_bytecode=True
RES=Path(__file__).resolve().parent;BASE=RES.parent;OUT=BASE.parent/'candidates/round-02';E=OUT/'evidence/collar-shader-controls';E.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-02.blend'));s=bpy.context.scene;core=next(o for o in s.objects if 'continuous_rounded' in o.name);root=core.parent
with bpy.data.libraries.load(str(BASE/'dependencies/canonical-middle.blend'),link=False) as (fr,to):to.objects=['rock-shelf-middle__sculpted_core']
ref=to.objects[0];s.collection.objects.link(ref);ref.parent=None
for o in s.objects:o.hide_render=True
cam=s.camera;cam.hide_render=False;s.use_nodes=False;s.render.resolution_x=s.render.resolution_y=128;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;cam.data.ortho_scale=.04;cam.data.shift_x=cam.data.shift_y=0
originals={role:[m for m in ob.data.materials] for role,ob in [('candidate',core),('reference',ref)]};ledger=[]
def field_material(original,mode):
 m=original.copy();ns=m.node_tree.nodes;ls=m.node_tree.links;bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED');out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');emit=ns.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=1
 if mode=='albedo':ls.new(bs.inputs['Base Color'].links[0].from_socket,emit.inputs['Color'])
 else:
  if bs.inputs['Normal'].is_linked:normal=bs.inputs['Normal'].links[0].from_socket
  else:normal=ns.new('ShaderNodeNewGeometry').outputs['Normal']
  mult=ns.new('ShaderNodeVectorMath');mult.operation='SCALE';mult.inputs[3].default_value=.5;ls.new(normal,mult.inputs[0]);add=ns.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5);ls.new(mult.outputs[0],add.inputs[0]);ls.new(add.outputs[0],emit.inputs['Color'])
 ls.new(emit.outputs[0],out.inputs['Surface']);return m
transparent=bpy.data.materials.new('field-control transparent unselected surface');transparent.use_nodes=True;ns=transparent.node_tree.nodes;ls=transparent.node_tree.links;ns.clear();out=ns.new('ShaderNodeOutputMaterial');tr=ns.new('ShaderNodeBsdfTransparent');ls.new(tr.outputs[0],out.inputs['Surface'])
profile=[(-.45,0),(.45,0),(.45,.28),(.39,.43),(-.39,.43),(-.45,.28)]
angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}
# The same fixed .04 world square is used for every cross-section center. Full
# profile endpoint/intermediate coverage is supplied by collar-fields.json; these
# actual shader-output controls verify graph evaluation and all world transforms.
for port in ['W','N']:
 for d,angle in angles.items():
  rotation=Matrix.Rotation(angle,4,'Z');extra=Matrix.Identity(4) if port=='W' else Matrix.Rotation(math.pi/2,4,'Z');ref.rotation_euler.z=angle+(0 if port=='W' else math.pi/2);root.rotation_euler.z=angle
  for edge in [1,2,3,4,5]:
   a=Vector((0,*profile[edge]));b=Vector((0,*profile[(edge+1)%6]));tangent=(b-a).normalized();normal=Vector((0,tangent.z,-tangent.y));center=(a+b)*.5;center.x=-.4875 if port=='W' else .4875;target=rotation@(extra@center);worldnormal=(rotation@extra).to_3x3()@normal;cam.location=target+worldnormal*2;cam.rotation_euler=(-worldnormal).to_track_quat('-Z','Y').to_euler()
   for mode in ['albedo','normal']:
    for role,ob in [('reference',ref),('candidate',core)]:
     core.hide_render=role!='candidate';ref.hide_render=role!='reference';selected=0 if role=='reference' else 3
     for i,original in enumerate(originals[role]):ob.data.materials[i]=field_material(original,mode) if i==selected else transparent
     bpy.context.view_layer.update();path=E/f'{port}-{d}-edge{edge}-{role}-{mode}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);ledger.append({'port':port,'direction':d,'edge':edge,'role':role,'mode':mode,'path':path.relative_to(OUT).as_posix(),'actualObjectMatrix':[list(r) for r in ob.matrix_world],'cameraMatrix':[list(r) for r in cam.matrix_world],'sourceProjectSHA256':hashlib.sha256((BASE/'round-02.blend').read_bytes()).hexdigest(),'canonicalSHA256':hashlib.sha256((BASE/'dependencies/canonical-middle.blend').read_bytes()).hexdigest()})
(OUT/'collar-shader-control-captures.json').write_text(json.dumps({'method':'Actual native shader output, same .04 world square on each of five exposed profile segments, W/N and every root rotation. Emission reads actual linked post-interpolation normalized Normal; canonical unlinked BSDF uses actual Geometry.Normal. Actual per-point full collar fields are recorded separately. Only control surfaces are isolated; candidate art unchanged.','captures':ledger},indent=2)+'\n');print('SHADER CONTROLS COMPLETE')
