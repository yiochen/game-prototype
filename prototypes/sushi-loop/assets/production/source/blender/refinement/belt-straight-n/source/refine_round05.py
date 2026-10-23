import bpy,pathlib,math,json
P=pathlib.Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-04.blend'));s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-straight-n.001'];orient=next(o for o in c.objects if '__orientation.' in o.name);root=next(o for o in c.objects if '__root.' in o.name)
s.cycles.samples=1;s.cycles.sampling_pattern='TABULATED_SOBOL';s.cycles.scrambling_distance=0;s.cycles.filter_width=1
# Deterministic native toon camera radiance: constant pixel sample is necessary for exact independent alpha tiling of the source zero-thickness deck.
for m in bpy.data.materials:
 if not m.node_tree:continue
 nt=m.node_tree;n=nt.nodes;l=nt.links;out=n.get('Material Output');sh=next((x for x in n if x.type=='BSDF_PRINCIPLED'),None)
 if not out or not sh:continue
 if m.name=='WarmSoft_CoralRail':continue # already native camera-ray radiance with broad continuous edge bands
 em=n.new('ShaderNodeEmission');em.name='Native_soft_toon_camera_radiance'
 if 'moving_deck' in m.name:
  l.new(n['Soft_slat_shoulders'].outputs['Color'],em.inputs['Color'])
 else:
  # Default per-mesh object coordinates repeat exactly across independently captured modules.
  for t in n:
   if t.type=='TEX_COORD':t.object=None
  color=sh.inputs['Base Color'].links[0].from_socket if sh.inputs['Base Color'].is_linked else None
  geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Normal'],sep.inputs[0]);absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(sep.outputs['Z'],absolute.inputs[0]);mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY_ADD';l.new(absolute.outputs[0],mul.inputs[0]);mul.inputs[1].default_value=.30;mul.inputs[2].default_value=.72
  shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=1
  if color:l.new(color,shade.inputs[1])
  else:shade.inputs[1].default_value=sh.inputs['Base Color'].default_value
  l.new(mul.outputs[0],shade.inputs[2]);l.new(shade.outputs[0],em.inputs['Color'])
 path=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(path.outputs['Is Camera Ray'],mix.inputs[0]);l.new(sh.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
# Reposition the useful fasteners onto readable outward leg faces below the deck.
for o in list(c.objects):
 if o.name.startswith('Brass_joinery_peg'):bpy.data.objects.remove(o,do_unlink=True)
brass=bpy.data.materials['WarmSoft_BrassFastener']
for axis in (0,1):
 for sign in [-1,1]:
  for p in [-.28,.28]:
   loc=[p,sign*.371,.34] if axis==1 else [sign*.371,p,.34]
   bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=loc);o=bpy.context.object
   for cc in list(o.users_collection):cc.objects.unlink(o)
   c.objects.link(o);o.parent=orient;o.name='Visible_brass_leg_joinery';o.scale=(.021,.010,.021) if axis==1 else (.010,.021,.021);o.data.materials.append(brass)
   for f in o.data.polygons:f.use_smooth=True
root.rotation_euler.z=math.pi;s.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-05.blend'))
recipe=json.load(open(P/'source/round-02-recipe.json'));recipe.update(round=5,project=str(P/'source/round-05.blend'),method=recipe['method']+' Deterministic native camera-ray toon radiance for exact RGB/alpha compositing of flat source deck: one TABULATED_SOBOL sample, scrambling_distance0, BOX1, denoisingOFF. Shaders use original UV phase, rail-local x/z, per-mesh wood coordinates and horizontally symmetric normal-Z response. BSDF transport remains for noncamera rays. Leg fasteners placed below deck to be visible.');recipe['render'].update(samples=1,pattern='TABULATED_SOBOL',scramblingDistance=0,denoising=False,filter='BOX',filterWidth=1,viewTransform='Standard',look='None');(P/'source/round-05-recipe.json').write_text(json.dumps(recipe,indent=2))
OUT=P/'candidates/round-05';OUT.mkdir(parents=True,exist_ok=True)
for d,rot in [('N',math.pi),('E',math.pi/2)]:
 root.rotation_euler.z=rot;bpy.context.view_layer.update();s.render.filepath=str(OUT/('hero-'+d+'.png'));bpy.ops.render.render(write_still=True)
original=list(c.objects);clones=[]
for i in [-1,1]:
 mapping={}
 for o in original:q=o.copy();c.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 clones.append((i,mapping[root]))
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
for d,rot in [('N',math.pi),('E',math.pi/2)]:
 root.rotation_euler.z=rot
 for i,q in clones:q.rotation_euler.z=rot;q.location=(0,i,0) if d=='N' else (i,0,0)
 bpy.context.view_layer.update();s.render.filepath=str(OUT/('native-'+d+'-00.png'));bpy.ops.render.render(write_still=True)
