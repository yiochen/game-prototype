import bpy,math,json,hashlib,os
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parent.parent
ROUND=P/'candidates/round-03';ROUND.mkdir(parents=True,exist_ok=True)
# Source is loaded externally and never saved in place. Keep the entrance and a matching wall context only.
sc=bpy.context.scene
keepcols={'S33_PROP_uniform35-gate','S33_PROP_uniform35-wall-plain'}
keep=set()
for cn in keepcols:keep.update(bpy.data.collections[cn].all_objects)
keep.add(sc.camera)
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for c in list(bpy.data.collections):
 if c.name not in keepcols:bpy.data.collections.remove(c)
for c in bpy.data.collections:
 if c.name not in sc.collection.children:sc.collection.children.link(c)
for lc in sc.view_layers[0].layer_collection.children:lc.exclude=False;lc.hide_viewport=False
G=bpy.data.collections['S33_PROP_uniform35-gate'];W=bpy.data.collections['S33_PROP_uniform35-wall-plain']
for o in G.objects:o.hide_render=False;o.hide_viewport=False
for o in W.objects:o.hide_render=True;o.hide_viewport=False
root=bpy.data.objects['uniform35-gate__root'];wr=bpy.data.objects['uniform35-wall-plain__root']
root.rotation_euler=(0,0,0);root.location=(0,0,0);wr.rotation_euler=(0,0,0);wr.location=(0,0,0)
# Keep source camera transform and frame exactly, including its front-contact registration.
camera=sc.camera
camera.matrix_world=Matrix(json.loads((P/'inputs/source-assetRecord.json').read_text())['camera']['camera']['worldMatrix'])
camera.data.type='ORTHO';camera.data.ortho_scale=4.5;camera.data.shift_x=0;camera.data.shift_y=0.2696022093296051
sc.render.resolution_x=1728;sc.render.resolution_y=1344;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=1;sc.render.pixel_aspect_y=1;sc.render.film_transparent=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
sc.render.engine='CYCLES';sc.cycles.samples=96;sc.cycles.use_denoising=True
sc.cycles.transparent_max_bounces=8
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.refresh_devices()
 for d in pref.devices:d.use=(d.type=='METAL')
 sc.cycles.device='GPU'
except Exception:sc.cycles.device='CPU'
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
# An infinite, z-only environment and x-neutral sun have no module-width falloff.
world=bpy.data.worlds.new('Warm Soft Facade Family World');sc.world=world;world.use_nodes=True
n=world.node_tree.nodes;n.clear();ln=world.node_tree.links
out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');ramp=n.new('ShaderNodeValToRGB')
ln.new(tc.outputs['Normal'],sep.inputs[0]);ln.new(sep.outputs['Z'],ramp.inputs[0]);ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(.5,.53,.58,1);ramp.color_ramp.elements[1].position=1;ramp.color_ramp.elements[1].color=(1,.94,.84,1)
bg.inputs['Strength'].default_value=.65;ln.new(ramp.outputs['Color'],bg.inputs['Color']);ln.new(bg.outputs[0],out.inputs['Surface'])
sun_data=bpy.data.lights.new('Facade infinite soft overhead','SUN');sun=bpy.data.objects.new('Facade infinite soft overhead',sun_data);sc.collection.objects.link(sun)
sun.rotation_euler=Vector((0,-.55,1)).to_track_quat('Z','Y').to_euler();sun_data.energy=2.5;sun_data.angle=math.radians(35);sun_data.color=(1,.96,.88);sun_data.use_shadow=False
# Rebuild the existing palette as real surface shaders. Shader bevel is restricted near outer X join planes.
material_settings={}
for mat in bpy.data.materials:
 col=list(mat.diffuse_color);mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();nodes=nt.nodes;links=nt.links
 out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=col;bs.inputs['Roughness'].default_value=.48;bs.inputs['Specular IOR Level'].default_value=.26
 if 'blue' in mat.name:bs.inputs['Roughness'].default_value=.31;bs.inputs['Coat Weight'].default_value=.22;bs.inputs['Coat Roughness'].default_value=.28
 elif 'red' in mat.name:bs.inputs['Roughness'].default_value=.66;bs.inputs['Sheen Weight'].default_value=.2
 elif 'metal' in mat.name:bs.inputs['Roughness'].default_value=.38;bs.inputs['Metallic'].default_value=.15
 elif 'brass' in mat.name:bs.inputs['Roughness'].default_value=.39;bs.inputs['Metallic'].default_value=.18
 elif 'paper' in mat.name:
  bs.inputs['Roughness'].default_value=.62;bs.inputs['Subsurface Weight'].default_value=.05;bs.inputs['Emission Color'].default_value=col;bs.inputs['Emission Strength'].default_value=.22
 elif 'door' in mat.name:bs.inputs['Roughness'].default_value=.85;bs.inputs['Specular IOR Level'].default_value=.12
 else:bs.inputs['Roughness'].default_value=.47;bs.inputs['Coat Weight'].default_value=.08
 if 'blue_dark' in mat.name:bs.inputs['Specular IOR Level'].default_value=.04;bs.inputs['Coat Weight'].default_value=0;bs.inputs['Roughness'].default_value=.4
 if 'paper' in mat.name:
  lp=nodes.new('ShaderNodeLightPath');mul=nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=.22;links.new(lp.outputs['Is Camera Ray'],mul.inputs[0]);links.new(mul.outputs[0],bs.inputs['Emission Strength'])
 # Real ray-traced bevel normals give shared beams soft edge reflections without changing protected join geometry.
 bevel=nodes.new('ShaderNodeBevel');bevel.inputs['Radius'].default_value=.012;bevel.samples=4;links.new(bevel.outputs['Normal'],bs.inputs['Normal'])
 links.new(bs.outputs[0],out.inputs['Surface'])
 material_settings[mat.name]={'baseColor':col,'roughness':bs.inputs['Roughness'].default_value,'specularIORLevel':bs.inputs['Specular IOR Level'].default_value,'coat':bs.inputs['Coat Weight'].default_value,'bevelShaderRadius':.012}
# Preserve each shared profile mesh and its original modifiers at both protected join planes.
protected=[];geometric_edits=[]
for c,bound in [(G,2.0),(W,.5)]:
 for o in c.objects:
  if o.type!='MESH':continue
  coords=[o.matrix_world@v.co for v in o.data.vertices]
  shared=any(abs(abs(v.x)-bound)<1e-5 for v in coords)
  if shared:protected.append(o.name);continue
  if 'noren_panel' in o.name or 'paper_lantern' in o.name:continue
  for m in list(o.modifiers):
   if m.type=='BEVEL':m.segments=4;m.harden_normals=True
  if 'flat_roof_tile' in o.name:
   m=o.modifiers.new('Soft ceramic tile edges','BEVEL');m.width=.008;m.segments=4;m.affect='EDGES';m.harden_normals=True
  elif not any(m.type=='BEVEL' for m in o.modifiers) and not ('fish_eye' in o.name or 'threshold_center_joint' in o.name):
   m=o.modifiers.new('Soft native edges','BEVEL');m.width=.008 if 'band_' in o.name else .012;m.segments=4;m.harden_normals=True
  for poly in o.data.polygons:poly.use_smooth=True
  m=o.modifiers.new('Planar face normals','WEIGHTED_NORMAL');m.keep_sharp=True;m.weight=50
  geometric_edits.append(o.name)
# Smooth native lantern lathes, retaining all authored ring heights/radii and maximum envelope.
for o in G.objects:
 if o.type=='MESH' and 'paper_lantern' in o.name:
  cx=-1.56 if 'left' in o.name else 1.56;cy=-.76
  rings=[(1.19,.11),(1.25,.19),(1.35,.22),(1.82,.22),(1.94,.17),(1.99,.11)]
  dense=[]
  for i in range(len(rings)-1):
   z0,r0=rings[i];z1,r1=rings[i+1]
   for k in range(6):
    t=k/6;s=t*t*(3-2*t);dense.append((z0+(z1-z0)*t,r0+(r1-r0)*s))
  dense.append(rings[-1]);verts=[];faces=[];radial=64
  for z,r in dense:
   for j in range(radial):a=j*2*math.pi/radial;verts.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
  for k in range(len(dense)-1):
   for j in range(radial):faces.append((k*radial+j,k*radial+(j+1)%radial,(k+1)*radial+(j+1)%radial,(k+1)*radial+j))
  faces += [tuple(reversed(range(radial))),tuple((len(dense)-1)*radial+j for j in range(radial))]
  mats=list(o.data.materials);me=bpy.data.meshes.new(o.name+' smooth lathe');me.from_pydata(verts,[],faces);me.update();o.data=me
  for m in mats:me.materials.append(m)
  for f in me.polygons:f.use_smooth=len(f.vertices)==4
  geometric_edits.append(o.name)
# Smooth matching original three lantern bands to prevent faceted chords intersecting the paper.
for o in G.objects:
 if o.type=='MESH' and '_band_' in o.name:
  for m in list(o.modifiers):o.modifiers.remove(m)
  old=o.data;zs=[v.co.z for v in old.vertices];zlo=min(zs);zhi=max(zs);rad=.223;nn=64;vv=[];ff=[]
  for zz in [zlo,zhi]:
   for j in range(nn):a=j*2*math.pi/nn;vv.append((rad*math.cos(a),rad*math.sin(a),zz))
  for j in range(nn):ff.append((j,(j+1)%nn,nn+(j+1)%nn,nn+j))
  ff += [tuple(reversed(range(nn))),tuple(nn+j for j in range(nn))]
  ma=list(old.materials);me=bpy.data.meshes.new(o.name+' smooth band');me.from_pydata(vv,[],ff);me.update();o.data=me
  for m in ma:me.materials.append(m)
  for f in me.polygons:f.use_smooth=len(f.vertices)==4
  b=o.modifiers.new('Soft band rim','BEVEL');b.width=.003;b.segments=3;b.harden_normals=True
  no=o.modifiers.new('Band normals','WEIGHTED_NORMAL');no.keep_sharp=True
# Three native cloth surfaces with soft cross-section folds and the same silhouettes/attachment row.
for o in G.objects:
 if o.type=='MESH' and 'noren_panel' in o.name:
  idx=int(o.name.rsplit('_',1)[1]);cx=(idx-1)*.66;verts=[];faces=[];nx=40;nz=24
  for j in range(nz+1):
   v=j/nz
   for i in range(nx+1):
    u=i/nx;x=cx-.31+.62*u;bottom=1.32+.035*abs(2*u-1)**4;z=2.3+(bottom-2.3)*v
    y=-.47+.025*math.cos(4*math.pi*u)*(0.8+0.2*math.sin(math.pi*v))
    verts.append((x,y,z))
  for j in range(nz):
   for i in range(nx):a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
  me=bpy.data.meshes.new(o.name+' soft cloth');me.from_pydata(verts,[],faces);me.materials.append(bpy.data.materials['S33_uniform35_red']);me.update();o.data=me
  for f in me.polygons:f.use_smooth=True
  for m in o.modifiers:
   if m.type=='SOLIDIFY':m.thickness=.015;m.offset=-1
  b=o.modifiers.new('Soft cloth edge','BEVEL');b.width=.004;b.segments=3
  geometric_edits.append(o.name)
for o in G.objects:
 if o.type=='CURVE':o.data.bevel_resolution=4;o.data.resolution_u=16
# Family recipe is a reusable native technical context, independent of review opinions.
recipe={'schemaVersion':1,'asset':'backdrop-entrance','round':'round-03','sourceSha256':hashlib.sha256((P/'../../../production/source/backdrop/restaurant-backdrop-35.blend').resolve().read_bytes()).hexdigest(),'blender':bpy.app.version_string,'camera':{'matrix':[list(r) for r in camera.matrix_world],'type':'ORTHO','orthoScale':4.5,'shift':[0,camera.data.shift_y],'elevationDegrees':35,'frame':[1728,1344],'pixelAspect':[1,1],'sourceScale':3,'logicalFrame':[576,448],'logicalRoot':[288,416],'frontContactPoint':[0,-.5,0]},'renderer':{'engine':'CYCLES','device':sc.cycles.device,'samples':96,'denoising':True,'viewTransform':'Standard','look':'None','exposure':0},'lighting':{'world':'z-only warm sky gradient; no X/Y coordinate dependency','worldStrength':.65,'sun':{'energy':2.5,'direction':[0,-.55,1],'angleDegrees':35,'color':[1,.96,.88],'useShadow':False},'groundObject':None,'horizontalGlobalGradient':False,'paperEmission':'camera rays only; zero emission for diffuse/glossy illumination rays; no local wall light falloff'},'materials':material_settings,'protectedProfileObjects':protected,'nativeGeometricEdits':geometric_edits,'wallContext':'S33_PROP_uniform35-wall-plain, hidden in entrance hero; context only, not wall production approval','sourcePhase':'S root rotation Z 0 radians, original publisher single player-facing facade'}
(P/'source/round-03-recipe.json').write_text(json.dumps(recipe,indent=2))
(P/'source/family-context.json').write_text(json.dumps({'schemaVersion':1,'nativeLibrary':'round-03.blend','materials':material_settings,'world':world.name,'light':sun.name,'recipe':'round-03-recipe.json','protectedProfiles':protected,'camera':recipe['camera'],'usage':'Append family materials, world and infinite light from this library. Preserve original wall geometry/join planes and use wall camera frame 576x1344 at 384px per world unit. No prior art verdict is included.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-03.blend'))
sc.render.filepath=str(ROUND/'static-S-000.png');bpy.ops.render.render(write_still=True)
print('ROUND03_RENDERED')
