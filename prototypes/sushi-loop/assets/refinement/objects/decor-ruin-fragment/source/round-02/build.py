"""Self-contained native ruin reconstruction, Blender 5.x. No raster materials."""
import bpy, math, random, json, sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
OUT=HERE.parent.parent/'candidates'/'round-02'
OUT.mkdir(parents=True,exist_ok=True)
random.seed(317)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Ruin fragment warm native round 02'
col=bpy.data.collections.new('decor-ruin-fragment');sc.collection.children.link(col)
root=bpy.data.objects.new('decor-ruin-fragment__ground_root',None);col.objects.link(root)
root['assetId']='decor-ruin-fragment';root['nominalHeight']=2.18;root['squareFooting']=True;root['footingTransitionHeight']=.42
root['lineage']='Native reconstruction of S33 production concept reef-face from source SHA b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def rgba(h):return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))+(1,)
def material(name,h,rough=.82,noise=.02):
 m=bpy.data.materials.new(name);m.use_nodes=True;t=m.node_tree;n=t.nodes;l=t.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=rough;p.inputs['Specular IOR Level'].default_value=.16;l.new(p.outputs['BSDF'],out.inputs['Surface'])
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=15;tex.inputs['Detail'].default_value=2
 geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0]);l.new(geo.outputs['Position'],tex.inputs['Vector'])
 ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1.8;ramp.inputs['To Min'].default_value=.71;ramp.inputs['To Max'].default_value=1.0;ramp.clamp=True;l.new(sep.outputs['Z'],ramp.inputs[0])
 base=n.new('ShaderNodeRGB');base.outputs[0].default_value=rgba(h)
 mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(base.outputs[0],mul.inputs[1]);l.new(ramp.outputs[0],mul.inputs[2])
 varying=n.new('ShaderNodeMapRange');varying.inputs['From Min'].default_value=0;varying.inputs['From Max'].default_value=1;varying.inputs['To Min'].default_value=1-noise;varying.inputs['To Max'].default_value=1+noise;l.new(tex.outputs['Fac'],varying.inputs[0])
 grain=n.new('ShaderNodeMixRGB');grain.blend_type='MULTIPLY';grain.inputs[0].default_value=1;l.new(mul.outputs[0],grain.inputs[1]);l.new(varying.outputs[0],grain.inputs[2]);l.new(grain.outputs[0],p.inputs['Base Color'])
 if noise:
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.14;bump.inputs['Distance'].default_value=.006;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
 return m
stone=material('Warm ivory stone','D6D3BF',.88,.035)
stoneSide=material('Stone worn edges','CBCAB8',.9,.035)
stoneChip=material('Fresh pale chipped stone','DCD8C5',.9,.025)
recess=material('Blue gray carved recess','3E6470',.94,.015)
crack=material('Subtle weathered fracture','6E8581',.96,.01)
blue=[material('Cobalt reef facet '+str(i),h,.9,.025) for i,h in enumerate(['125692','1B689D','154879','237AA6','164F84','1B5B8C'])]
moss=material('Fresh olive green moss','698D25',.76,.045);mossLight=material('Moss tender tips','88A33A',.73,.035);leafmat=material('Thick reef sprouts','3E7944',.7,.025)
def finish(o,name,mat):
 o.name=name
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.parent=root
 o.data.materials.append(mat)
 return o
def block(name,loc,size,mat,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=finish(bpy.context.object,name,mat);o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  b=o.modifiers.new('Worn rounded stone edges','BEVEL');b.width=bevel;b.segments=1;b.affect='EDGES';b.profile=.58
  b=o.modifiers.new('Weighted broad stone planes','WEIGHTED_NORMAL');b.keep_sharp=True;b.weight=40
 return o
def ellipsoid(name,loc,scale,mat,seg=14,rings=8):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc);o=finish(bpy.context.object,name,mat);o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 return o
def mesh(name,verts,faces,mat):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;me.materials.append(mat);return o
def fracture(name,pts,r=.003):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=0;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,co in zip(sp.points,pts):p.co=(*co,1)
 o=bpy.data.objects.new(name,cu);col.objects.link(o);o.parent=root;cu.materials.append(crack)
 # Convert to native mesh so capture-time lower deformation treats all geometry equally.
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
 return o
# Broad full-cell reef footing with deliberately irregular side facets.
outline=[(-.5,-.33),(-.33,-.5),(.31,-.5),(.5,-.33),(.5,.32),(.31,.5),(-.32,.5),(-.5,.32)]
verts=[(x,y,0) for x,y in outline]+[(x,y,.135+random.uniform(-.025,.025)) for x,y in outline]+[(x*.98,y*.98,.27+random.uniform(-.02,.02)) for x,y in outline]+[(0,0,.30)]
faces=[tuple(reversed(range(8)))]
for j in range(2):
 for i in range(8):
  a=j*8+i;b=j*8+(i+1)%8;c=(j+1)*8+(i+1)%8;d=(j+1)*8+i
  faces.extend([(a,b,d),(b,c,d)])
for i in range(8):faces.append((16+i,16+(i+1)%8,24))
base=mesh('Broad cobalt faceted footing',verts,faces,blue[0])
for m in blue[1:]:base.data.materials.append(m)
for p in base.data.polygons:p.material_index=(0 if p.normal.z<.05 else 1) if p.index%7 else 4
# Continuous core with inset eyes. Broad planar stone, real rounded silhouette.
body=block('Carved head solid mass',(0,.015,.94),(.69,.58,1.33),stone,.055)
# Apply bevel before boolean eye niches.
bpy.context.view_layer.objects.active=body
for mod in list(body.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
for x in [-.185,.185]:
 cut=block('Eye socket cutter',(x,-.285,1.17),(.195,.15,.22),stone, .027)
 bpy.context.view_layer.objects.active=cut
 for mod in list(cut.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
 mod=body.modifiers.new('Actual carved eye niche','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cut
 bpy.context.view_layer.objects.active=body;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
 block('Inset blue stone eye',(x,-.223,1.17),(.160,.018,.183),recess,.020)
block('Upper forehead weathered block',(0,.025,1.735),(.755,.61,.405),stone,.041)
block('Forehead narrow base step',(0,-.264,1.540),(.58,.16,.080),stoneSide,.021)
block('Broad worn brow ledge',(0,-.327,1.420),(.835,.202,.190),stoneChip,.039)
# Face has projection and thick long nose but avoids detached bar relationships.
block('Long carved nose bridge',(0,-.323,1.055),(.170,.245,.480),stone,.029)
block('Nose rounded end',(0,-.363,.824),(.242,.249,.137),stoneSide,.028)
block('Mouth shallow carved groove',(0,-.284,.667),(.318,.022,.035),recess,.009)
block('Soft lower lip ledge',(0,-.311,.617),(.348,.108,.097),stoneChip,.023)
for x in [-.383,.383]:
 block('Substantial weathered side ear',(x,.028,1.382),(.134,.26,.375),stoneSide,.044)
# Three broken crown teeth with varied scale and intentional worn cuts.
for i,(x,y,z,sz) in enumerate([(-.205,.045,2.000,(.208,.240,.205)),(.125,.070,2.036,(.247,.263,.275)),(.295,-.010,1.945,(.115,.152,.140))]):
 block('Crown broken stone '+str(i),(x,y,z),sz,stoneChip,.034)
# Selected sparse cracks follow stone planes; no repeated noisy speckle.
fracture('Forehead split',[(.145,-.282,1.92),(.095,-.282,1.80),(.119,-.282,1.72),(.070,-.282,1.61)],.0035)
fracture('Left cheek age crack',[(-.343,-.225,.81),(-.29,-.278,.74),(-.312,-.278,.60),(-.255,-.278,.48)],.003)
fracture('Right lower diagonal fracture',[(.339,-.237,.74),(.31,-.279,.62),(.265,-.279,.54),(.29,-.279,.43)],.0032)
fracture('Brow worn seam',[(.242,-.429,1.50),(.19,-.429,1.45),(.216,-.429,1.38)],.0028)
fracture('Rear long quiet split',[(-.15,.321,1.85),(-.11,.321,1.67),(-.17,.309,1.53),(-.18,.307,1.31)],.003)
fracture('Side old chip',[(.346,.20,.91),(.346,.13,.81),(.346,.16,.65)],.003)
# Moss forms are flattened coherent islands/lobes actually on stone surfaces.
def moss_patch(label,center,scale,count=5,mat=moss):
 x,y,z=center;sx,sy,sz=scale
 ellipsoid(label+' cushion',center,scale,mat)
 for j in range(count):
  ang=j*2.4+.5;rad=.55+random.random()*.25
  ellipsoid(label+' attached lobe '+str(j),(x+sx*math.cos(ang)*rad,y+sy*math.sin(ang)*rad,z+sz*random.uniform(-.1,.2)),(sx*.46,sy*.44,sz*.7),mossLight if j%4==0 else mat,12,7)
# Crown moss crowns and spill tongues; each connected to a horizontal island.
for i,(c,s) in enumerate([((-.205,.04,2.105),(.112,.13,.025)),((.125,.07,2.173),(.135,.14,.007)),((.294,-.01,2.016),(.070,.080,.021)),((.245,-.10,1.94),(.105,.15,.023)),((-.26,-.13,1.94),(.1,.16,.02))]):moss_patch('Crown moss '+str(i),c,s,4)
for i,(c,s) in enumerate([((-.228,-.082,2.041),(.106,.025,.07)),((.204,-.071,2.07),(.06,.025,.09)),((.315,-.029,1.91),(.026,.063,.09))]):moss_patch('Crown moss spill '+str(i),c,s,4)
# Less moss on front feature planes; small meaningful seam growth.
for i,(c,s) in enumerate([((-.28,-.26,1.529),(.085,.10,.018)),((.24,-.20,1.52),(.065,.11,.017)),((.10,-.283,.72),(.058,.022,.095)),((.13,-.30,.60),(.055,.06,.025)),((-.30,-.22,.31),(.12,.12,.025)),((.31,.18,.32),(.12,.13,.03)),((.28,.31,1.68),(.08,.025,.14)),((-.22,.315,1.08),(.10,.022,.12))]):moss_patch('Attached aged moss '+str(i),c,s,4)
# Thick little reef sprouts around footing, motivated by target vegetation.
for k,(x,y,h) in enumerate([(-.39,-.22,.33),(-.34,-.31,.25),(.40,.18,.48),(.39,.28,.33),(-.38,.27,.32)]):
 for j in range(2):
  o=ellipsoid('Rooted thick reef leaf '+str(k)+' '+str(j),(x+(j-.5)*.045,y,.30+h*.40),(.030,.054,h*.48),leafmat)
  o.rotation_euler=(.16*(j-.5),(-.18 if x<0 else .18)+j*.08,(j-.5)*.3)
 moss_patch('Root moss '+str(k),(x,y,.29),(.055,.072,.022),3)
# Small broad stone rubble, never floating dust.
for i,(x,y,z,s) in enumerate([(-.27,-.33,.312,.11),(.32,-.33,.291,.065),(.23,.34,.29,.082),(-.34,.33,.30,.07)]):
 o=block('Footing stone rubble '+str(i),(x,y,z+s*.3),(s,s*.8,s*.70),stoneSide,s*.20);o.rotation_euler=(.06,-.1,i*.55)
# A few asymmetrical planar chips interrupt otherwise uniform cuboid edges.
def chip(target_name,label,loc,size,rot):
 target=bpy.data.objects[target_name]
 bpy.context.view_layer.objects.active=target
 for md in list(target.modifiers):bpy.ops.object.modifier_apply(modifier=md.name)
 cutter=block(label+' cutter',loc,size,stone,0);cutter.rotation_euler=rot
 bpy.context.view_layer.update();md=target.modifiers.new(label,'BOOLEAN');md.operation='DIFFERENCE';md.object=cutter
 bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=md.name);bpy.data.objects.remove(cutter,do_unlink=True)
 target.data.materials.append(stoneChip)
 for face in target.data.polygons:
  if face.select:face.material_index=0
chip('Upper forehead weathered block','Upper right stone chip',(.258,-.272,1.934),(.13,.095,.052),(.3,.3,.24))
chip('Upper forehead weathered block','Upper left stone chip',(-.326,-.258,1.918),(.09,.10,.052),(.2,-.24,-.35))
chip('Upper forehead weathered block','Forehead side missing corner',(.376,.196,1.83),(.08,.085,.115),(.3,.5,.35))
chip('Broad worn brow ledge','Brow right edge wear',(.30,-.425,1.511),(.085,.07,.036),(.3,-.2,.45))
chip('Broad worn brow ledge','Brow left weathered corner',(-.377,-.42,1.345),(.12,.10,.07),(.2,.3,-.30))
chip('Carved head solid mass','Lower left broken plane',(-.306,-.265,.31),(.16,.12,.10),(.3,-.35,.4))
chip('Carved head solid mass','Lower right broken plane',(.320,-.26,.40),(.08,.09,.16),(.24,.35,.2))
chip('Carved head solid mass','Rear shoulder old chip',(-.317,.29,1.36),(.09,.09,.16),(.15,.3,.2))

# Capture configuration: fixed object camera, source4/publication2, root at96,384.
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
sc.render.resolution_x=768;sc.render.resolution_y=1920;sc.render.resolution_percentage=100
sc.render.pixel_aspect_x=sc.render.pixel_aspect_y=1;sc.render.film_transparent=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.dither_intensity=0;sc.render.fps=12
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0;sc.view_settings.gamma=1
cam=bpy.data.objects.new('Registered ruin camera 35deg',bpy.data.cameras.new('Registered ruin camera 35deg'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.sensor_fit='HORIZONTAL';cam.data.ortho_scale=1.5;cam.data.shift_x=0;cam.data.shift_y=.75
ang=math.radians(35);cam.location=(0,-10*math.cos(ang),10*math.sin(ang));cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler()
world=bpy.data.worlds.new('Balanced neutral ambient');world.use_nodes=True;sc.world=world
bg=world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.7,.78,.85,1);bg.inputs['Strength'].default_value=.16
lights=[]
def light(name,loc,power,size,color):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(name,d);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler();lights.append(o)
light('Soft centered overhead',(0,0,4.5),110,3.5,(1,.94,.83))
for a in (0,90,180,270):
 t=math.radians(a);light('Equal cardinal fill '+str(a),(3*math.cos(t),3*math.sin(t),2.0),72,4,(1,.98,.94))
# Source scene compositing is intentionally explicit, no copied scene node references.
nt=bpy.data.node_groups.new('Ruin own-scene RGBA passthrough','CompositorNodeTree');nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');rl=nt.nodes.new('CompositorNodeRLayers');rl.scene=sc;out=nt.nodes.new('NodeGroupOutput');nt.links.new(rl.outputs['Image'],out.inputs['Image']);sc.compositing_node_group=nt;sc.render.use_compositing=True
bpy.context.view_layer.update();root.rotation_euler=(0,0,0);sc.frame_set(1)
# Save native undeformed scene before separate capture process; no external dependencies.
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'project.blend'),compress=True)
(HERE/'settings.json').write_text(json.dumps({'asset':'decor-ruin-fragment','round':'round-02','engine':sc.render.engine,'samples':sc.cycles.samples,'seed':317,'camera':{'elevation':35,'ortho':1.5,'shift':[0,.75],'logicalFrame':[192,480],'logicalRoot':[96,384],'nativeScale':4,'publicationScale':2},'lightRig':[{ 'name':o.name,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'location':list(o.location)} for o in lights],'worldStrength':.16,'lowerTone':'Native world-height factor .71 to1.0 overZ0..1.8','compositor':'Explicit own-scene render layer passthrough preserving native RGBA','nominalHeight':2.18,'footingTransition':.42,'rebuild':'Full native geometry rebuild with chamfered stone, eye niche booleans, attached organic moss, thick leaves and sparse fracture meshes'},indent=2)+'\n')
print('SAVED',HERE/'project.blend')
