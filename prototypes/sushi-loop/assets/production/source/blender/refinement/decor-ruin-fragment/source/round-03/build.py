"""Self-contained native ruin reconstruction, Blender 5.x. No raster materials."""
import bpy, math, random, json, sys
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
OUT=HERE.parent.parent/'candidates'/'round-03'
OUT.mkdir(parents=True,exist_ok=True)
random.seed(317)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='Ruin fragment warm native round 03'
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
# Deliberately worn stone: irregular broad cross-sections, generous asymmetric
# edge planes and broken shoulders. The front center remains a carved face plane.
def wornstone(name,loc,size,mat,rows=None,top_offsets=None,cuts=(.12,.16,.15,.12),bevel=.012):
 x,y,z=loc;w,d,h=size
 rows=rows or [(0,1,0),(1,1,0)]
 outline=[(-.5+cuts[0],-.5),(.5-cuts[1],-.5),(.5,-.5+cuts[1]),(.5,.5-cuts[2]),(.5-cuts[2],.5),(-.5+cuts[3],.5),(-.5,.5-cuts[3]),(-.5,-.5+cuts[0])]
 verts=[]
 for j,(v,wide,shift) in enumerate(rows):
  for i,(xx,yy) in enumerate(outline):
   # Uneven radial shoulders give broad planes instead of noise texture.
   zz=z+h*(v-.5)+(top_offsets[i] if top_offsets and j==len(rows)-1 else 0)
   verts.append((x+xx*w*wide+shift,y+yy*d*(1-.018*math.sin(j*2+i)),zz))
 faces=[tuple(reversed(range(8)))]
 for j in range(len(rows)-1):
  for i in range(8):faces.append((j*8+i,j*8+(i+1)%8,(j+1)*8+(i+1)%8,(j+1)*8+i))
 faces.append(tuple((len(rows)-1)*8+i for i in range(8)))
 o=mesh(name,verts,faces,mat)
 if bevel:
  md=o.modifiers.new('Soft chipped stone transitions','BEVEL');md.width=bevel;md.segments=2;md.limit_method='ANGLE';md.angle_limit=.45
  md=o.modifiers.new('Broad worn stone normals','WEIGHTED_NORMAL');md.keep_sharp=True;md.weight=40
 return o
# Native reef boulder: different shoulder outline/height, broad worn facets,
# gently broken lower perimeter and a substantial full-cell ground footprint.
outline=[(-.5,-.28),(-.38,-.46),(-.18,-.5),(.19,-.5),(.43,-.42),(.5,-.19),(.5,.18),(.36,.45),(.13,.5),(-.21,.5),(-.46,.35),(-.5,.07)]
upper=[(-.445,-.26),(-.34,-.42),(-.17,-.455),(.18,-.46),(.40,-.36),(.455,-.17),(.46,.16),(.31,.41),(.10,.45),(-.19,.455),(-.40,.31),(-.455,.05)]
verts=[(x,y,0) for x,y in outline]
middle=[(-.49,-.28),(-.343,-.414),(-.19,-.48),(.15,-.465),(.425,-.40),(.475,-.18),(.48,.17),(.31,.42),(.12,.465),(-.18,.49),(-.43,.31),(-.48,.06)]
verts += [(x,y,z) for (x,y),z in zip(middle,[.12,.18,.12,.145,.18,.13,.17,.14,.165,.15,.18,.15])]
verts += [(x,y,z) for (x,y),z in zip(upper,[.27,.31,.32,.29,.33,.285,.30,.335,.28,.32,.29,.315])]
verts += [(0,0,.30)]
faces=[tuple(reversed(range(12)))]
for j in range(2):
 for i in range(12):
  a=j*12+i;b=j*12+(i+1)%12;c=(j+1)*12+(i+1)%12;d=j*12+12+i
  if (i+j)%4==1:faces.extend([(a,b,c),(a,c,d)])
  else:faces.append((a,b,c,d))
for i in range(12):faces.append((24+i,24+(i+1)%12,36))
base=mesh('Broad cobalt faceted footing',verts,faces,blue[0])
for m in blue[1:]:base.data.materials.append(m)
for p in base.data.polygons:
 p.material_index=1 if p.normal.z>.45 else (2 if p.normal.z<-.08 or p.index in (4,9,22) else 0)
md=base.modifiers.new('Worn natural reef edges','BEVEL');md.width=.010;md.segments=1;md.limit_method='ANGLE';md.angle_limit=.8
md=base.modifiers.new('Broad reef plane normals','WEIGHTED_NORMAL');md.keep_sharp=True;md.weight=30
body=wornstone('Carved head solid mass',(0,.015,.94),(.69,.58,1.33),stone,
 rows=[(0,.90,-.004),(.24,1,-.008),(.66,.98,.004),(1,.965,0)],
 top_offsets=[-.025,-.005,.012,-.012,-.024,.005,-.01,-.025],cuts=(.13,.18,.14,.13),bevel=.018)
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
wornstone('Upper forehead weathered block',(0,.025,1.735),(.755,.61,.405),stone,rows=[(0,.965,0),(.56,1,-.004),(1,.965,.006)],top_offsets=[-.015,.008,-.015,-.025,.012,-.008,-.027,-.004],cuts=(.17,.11,.18,.14),bevel=.014)
block('Forehead narrow base step',(0,-.264,1.540),(.58,.16,.080),stoneSide,.021)
wornstone('Broad worn brow ledge',(0,-.327,1.420),(.835,.202,.190),stoneChip,rows=[(0,.94,.006),(.38,1,0),(1,.965,-.004)],top_offsets=[-.020,.004,-.006,-.014,-.008,-.002,-.016,-.023],cuts=(.075,.14,.11,.08),bevel=.013)
# Face has projection and thick long nose but avoids detached bar relationships.
block('Long carved nose bridge',(0,-.323,1.055),(.170,.245,.480),stone,.029)
block('Nose rounded end',(0,-.363,.824),(.242,.249,.137),stoneSide,.028)
block('Mouth shallow carved groove',(0,-.284,.667),(.318,.022,.035),recess,.009)
block('Soft lower lip ledge',(0,-.311,.617),(.348,.108,.097),stoneChip,.023)
for x in [-.383,.383]:
 block('Substantial weathered side ear',(x,.028,1.382),(.134,.26,.375),stoneSide,.044)
# Two substantial broken crown teeth plus a small remaining shoulder.
# Lowered stone tips reserve real space for rounded moss volume within2.18.
for i,(x,y,z,sz) in enumerate([(-.205,.045,1.985,(.217,.245,.20)),(.125,.070,2.010,(.250,.265,.235)),(.296,-.004,1.942,(.120,.155,.13))]):
 wornstone('Crown broken stone '+str(i),(x,y,z),sz,stoneChip,rows=[(0,1,0),(.60,1.02,-.004),(1,.92,.004)],top_offsets=[-.01,.005,-.006,.008,-.014,.002,-.008,-.005],cuts=(.16,.20,.12,.17),bevel=.012)
# Sparse actual age traces are secondary to the broad worn silhouette planes.
fracture('Left cheek age crack',[(-.327,-.24,.81),(-.288,-.275,.74),(-.30,-.275,.62)],.0025)
fracture('Rear quiet old split',[(-.14,.312,1.84),(-.11,.312,1.72),(-.16,.309,1.62)],.0025)
# Thick organic growth is built as overlapping native volumes, fused into a
# continuous surface and relaxed. Explicit corner paths bridge top/side planes.
def moss_cluster(label,bulbs):
 parts=[]
 for c,s in bulbs:parts.append(ellipsoid(label+' growth volume',c,s,moss,20,12))
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=label
 md=o.modifiers.new('Native continuous moss union','REMESH');md.mode='VOXEL';md.voxel_size=.006;md.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=md.name)
 md=o.modifiers.new('Soft living moss transitions','SMOOTH');md.factor=.8;md.iterations=4;bpy.ops.object.modifier_apply(modifier=md.name)
 for p in o.data.polygons:p.use_smooth=True
 return o
# Crown1: a puffy irregular cap curls over its left side and meets the top slab.
moss_cluster('Left crown connected moss wrap',[
 ((-.210,.045,2.075),(.114,.135,.061)),((-.253,-.020,2.067),(.074,.093,.060)),
 ((-.287,-.020,2.010),(.050,.081,.090)),((-.302,-.018,1.960),(.052,.095,.061)),
 ((-.280,-.087,1.943),(.085,.120,.040)),((-.201,.081,2.104),(.075,.080,.042))])
# Crown2: thickness, a top mound and an uninterrupted front/right hanging lobe.
moss_cluster('Right crown connected moss wrap',[
 ((.126,.075,2.105),(.128,.140,.063)),((.166,.015,2.087),(.095,.105,.068)),
 ((.210,-.030,2.032),(.064,.064,.092)),((.221,-.044,1.968),(.069,.072,.066)),
 ((.252,-.075,1.938),(.090,.118,.040)),((.106,.113,2.126),(.078,.082,.046))])
# Right rear corner has one growth flow across the shoulder and down the back.
moss_cluster('Rear shoulder moss cascade',[
 ((.264,.243,1.944),(.105,.095,.047)),((.295,.288,1.909),(.077,.065,.074)),
 ((.302,.319,1.846),(.068,.042,.097)),((.277,.326,1.773),(.071,.033,.067)),
 ((.309,.270,1.794),(.052,.065,.075))])
moss_cluster('Small crown corner remnant',[
 ((.297,-.005,2.003),(.071,.086,.046)),((.331,-.013,1.968),(.042,.066,.062))])
# Localized seam growth curls across the brow step rather than sitting as a badge.
moss_cluster('Left brow seam moss',[
 ((-.285,-.246,1.526),(.083,.105,.034)),((-.315,-.280,1.496),(.055,.066,.053)),
 ((-.340,-.253,1.460),(.037,.064,.057))])
moss_cluster('Nose seam moss',[
 ((.099,-.276,.744),(.041,.035,.077)),((.124,-.297,.690),(.036,.045,.072)),
 ((.108,-.319,.636),(.052,.064,.036))])
# Rear edge growth follows a long corner/low stone contact; no circular badge.
moss_cluster('Rear edge rooted moss seam',[
 ((-.317,.240,.360),(.060,.100,.072)),((-.331,.275,.415),(.042,.064,.093)),
 ((-.323,.292,.487),(.036,.051,.091)),((-.328,.281,.548),(.030,.057,.069))])
def moss_patch(label,center,scale,count=5,mat=moss):
 # Root cushion with real thickness; rounded separate plants grow through it.
 x,y,z=center;sx,sy,sz=scale
 return moss_cluster(label,[((x,y,z),(sx,sy,max(sz,.032))),((x+sx*.35,y-sy*.25,z+.008),(sx*.65,sy*.72,max(sz*.9,.024)))])
moss_patch('Attached base left',(-.30,-.22,.31),(.12,.12,.034))
moss_patch('Attached base right',(.31,.18,.32),(.12,.13,.040))
# Thick little reef sprouts around footing, motivated by target vegetation.
for k,(x,y,h) in enumerate([(-.39,-.22,.33),(-.34,-.31,.25),(.40,.18,.48),(.39,.28,.33),(-.38,.27,.32)]):
 for j in range(2):
  o=ellipsoid('Rooted thick reef leaf '+str(k)+' '+str(j),(x+(j-.5)*.045,y,.30+h*.40),(.030,.054,h*.48),leafmat)
  o.rotation_euler=(.16*(j-.5),(-.18 if x<0 else .18)+j*.08,(j-.5)*.3)
 moss_patch('Root moss '+str(k),(x,y,.29),(.055,.072,.022),3)
# Small broad stone rubble, never floating dust.
for i,(x,y,z,s) in enumerate([(-.27,-.33,.312,.11),(.32,-.33,.291,.065),(.23,.34,.29,.082),(-.34,.33,.30,.07)]):
 o=block('Footing stone rubble '+str(i),(x,y,z+s*.3),(s,s*.8,s*.70),stoneSide,s*.20);o.rotation_euler=(.06,-.1,i*.55)
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
(HERE/'settings.json').write_text(json.dumps({'asset':'decor-ruin-fragment','round':'round-03','engine':sc.render.engine,'samples':sc.cycles.samples,'seed':317,'camera':{'elevation':35,'ortho':1.5,'shift':[0,.75],'logicalFrame':[192,480],'logicalRoot':[96,384],'nativeScale':4,'publicationScale':2},'lightRig':[{ 'name':o.name,'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color),'location':list(o.location)} for o in lights],'worldStrength':.16,'lowerTone':'Native world-height factor .71 to1.0 overZ0..1.8','compositor':'Explicit own-scene render layer passthrough preserving native RGBA','nominalHeight':2.18,'footingTransition':.42,'rebuild':'Round03: irregular broad stone profiles and natural reef shoulders; puffy voxel-unioned continuous moss with deliberate top-to-side wraps; inherited camera/palette/horizontal light' },indent=2)+'\n')
print('SAVED',HERE/'project.blend')
