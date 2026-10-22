import bpy,pathlib,sys,math,json
from mathutils import Vector
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;B=P.parents[1];O=P/'cap-controls';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-02.blend'));s=bpy.context.scene;core=next(o for o in s.objects if 'continuous_rounded' in o.name);root=core.parent
with bpy.data.libraries.load(str(B/'source/dependencies/canonical-middle.blend'),link=False) as (fr,to):to.objects=['rock-shelf-middle__sculpted_core']
ref=to.objects[0];s.collection.objects.link(ref);ref.parent=None;ref.location=(0,0,0);ref.rotation_euler=(0,0,0)
for o in s.objects:o.hide_render=True
cam=s.camera;cam.hide_render=False;s.render.use_compositing=False;s.render.resolution_x=512;s.render.resolution_y=256;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=.98;cam.data.shift_x=cam.data.shift_y=0
originals={o.name:list(o.data.materials) for o in [core,ref]}
tr=bpy.data.materials.new('judge unselected transparent');tr.use_nodes=True;ns=tr.node_tree.nodes;ls=tr.node_tree.links;ns.clear();oo=ns.new('ShaderNodeOutputMaterial');tt=ns.new('ShaderNodeBsdfTransparent');ls.new(tt.outputs[0],oo.inputs[0])
ledger=[]
for port in ['W','N']:
 root.rotation_euler.z=0 if port=='W' else -math.pi/2;outward=Vector((-1,0,0) if port=='W' else (1,0,0));target=Vector((-.5 if port=='W' else .5,0,.215));cam.location=target+outward*3;cam.rotation_euler=(-outward).to_track_quat('-Z','Y').to_euler()
 for mode in ['albedo','normal']:
  for role,ob,index in [('candidate',core,1 if port=='W' else 2),('reference',ref,1)]:
   core.hide_render=role!='candidate';ref.hide_render=role!='reference';orig=originals[ob.name][index];m=orig.copy();ns=m.node_tree.nodes;ls=m.node_tree.links;bs=next(n for n in ns if n.type=='BSDF_PRINCIPLED');out=next(n for n in ns if n.type=='OUTPUT_MATERIAL');em=ns.new('ShaderNodeEmission');em.inputs['Strength'].default_value=1
   field=bs.inputs['Base Color'].links[0].from_socket if mode=='albedo' else bs.inputs['Normal'].links[0].from_socket
   if mode=='normal':
    scale=ns.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs[3].default_value=.5;ls.new(field,scale.inputs[0]);add=ns.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5);ls.new(scale.outputs[0],add.inputs[0]);field=add.outputs[0]
   ls.new(field,em.inputs['Color']);ls.new(em.outputs[0],out.inputs['Surface'])
   for j in range(len(ob.data.materials)):ob.data.materials[j]=m if j==index else tr
   bpy.context.view_layer.update();s.render.filepath=str(O/f'{port}-{mode}-{role}.png');bpy.ops.render.render(write_still=True);ledger.append({'port':port,'mode':mode,'role':role,'objectMatrix':[list(r) for r in ob.matrix_world],'cameraMatrix':[list(r) for r in cam.matrix_world]})
(P/'cap-review-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');print('INDEPENDENT NATIVE CAP FIELD CAPTURES COMPLETE')
