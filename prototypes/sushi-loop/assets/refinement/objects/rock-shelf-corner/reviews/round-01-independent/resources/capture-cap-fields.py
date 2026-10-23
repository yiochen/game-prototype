import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'candidates/round-01/evidence/cap-fields';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'round-01.blend'));s=bpy.context.scene;core=next(o for o in s.objects if 'continuous_rounded' in o.name)
with bpy.data.libraries.load(str(BASE/'dependencies/canonical-middle.blend'),link=False) as (fr,to):to.objects=['rock-shelf-middle__sculpted_core']
ref=to.objects[0];s.collection.objects.link(ref)
for o in s.objects:o.hide_render=True
cam=s.camera;cam.hide_render=False;s.use_nodes=False;s.render.resolution_x=512;s.render.resolution_y=512;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;s.render.film_transparent=True;s.render.filter_size=.5;cam.data.ortho_scale=1.05;cam.data.shift_x=cam.data.shift_y=0
results=[]
for port,axis,value,refx in [('W',0,-.5,-.5),('N',1,.5,.5)]:
 for role,source in [('reference',ref),('candidate',core)]:
  m=source.data;p=next(p for p in m.polygons if p.material_index and all(abs(m.vertices[i].co[0 if role=='reference' else axis]-(refx if role=='reference' else value))<1e-6 for i in p.vertices));vs=[tuple(m.vertices[i].co) for i in p.vertices]
  mesh=bpy.data.meshes.new('field actual cap');mesh.from_pydata(vs,[],[list(range(len(vs)))]);mesh.update();ob=bpy.data.objects.new('field '+port+role,mesh);s.collection.objects.link(ob)
  if port=='N' and role=='candidate':ob.rotation_euler.z=-math.pi/2
  mat=m.materials[p.material_index].copy();mesh.materials.append(mat);n=mat.node_tree.nodes;l=mat.node_tree.links;bs=next(n for n in n if n.type=='BSDF_PRINCIPLED');out=next(n for n in n if n.type=='OUTPUT_MATERIAL');albedo=bs.inputs['Base Color'].links[0].from_socket;normal=bs.inputs['Normal'].links[0].from_socket if bs.inputs['Normal'].is_linked else None
  for mode in ['albedo','normal']:
   emit=n.new('ShaderNodeEmission');emit.inputs['Strength'].default_value=1
   if mode=='albedo':l.new(albedo,emit.inputs['Color'])
   else:
    norm=normal
    if norm is None:geo=n.new('ShaderNodeNewGeometry');norm=geo.outputs['Normal']
    mult=n.new('ShaderNodeVectorMath');mult.operation='SCALE';mult.inputs[3].default_value=.5;l.new(norm,mult.inputs[0]);add=n.new('ShaderNodeVectorMath');add.operation='ADD';add.inputs[1].default_value=(.5,.5,.5);l.new(mult.outputs[0],add.inputs[0]);l.new(add.outputs[0],emit.inputs['Color'])
   l.new(emit.outputs[0],out.inputs['Surface']);cam.location=(refx+(-2 if refx<0 else 2),0,.215);target=Vector((refx,0,.215));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();s.render.filepath=str(OUT/f'{port}-{role}-{mode}.png');bpy.ops.render.render(write_still=True);results.append({'port':port,'role':role,'mode':mode,'path':f'evidence/cap-fields/{port}-{role}-{mode}.png','objectMatrix':[list(r) for r in ob.matrix_world],'sourceMaterial':m.materials[p.material_index].name,'sourcePolygon':p.index})
  ob.hide_render=True
(OUT.parent.parent/'cap-field-captures.json').write_text(json.dumps(results,indent=2)+'\n')
print('CAP FIELD COMPLETE')
