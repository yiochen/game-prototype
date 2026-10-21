"""Rowan v2-food native reconstruction. Run against untouched b1765262 library."""
import bpy,bmesh,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Euler

HERE=Path(__file__).parent
OBJ=HERE.parent
brief=json.loads((OBJ/'brief-v2-food.json').read_text())
dep=brief['foodDependency']
assert bpy.data.filepath and hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest()==brief['source']['projectSHA256'], 'Reconstruction requires the untouched original b1765262 library; use capture-round-01.py to recapture the saved round blend.'
resources=HERE/'resources';resources.mkdir(exist_ok=True)
for label,key,hashkey in [('canonical-salmon.png','artwork','sha256'),('approved-salmon-packet.json','packet','packetSHA256'),('approved-salmon-review.json','review','reviewSHA256')]:
 local=resources/label
 if local.is_file():
  assert hashlib.sha256(local.read_bytes()).hexdigest()==dep[hashkey], 'Local approved dependency changed: '+label
 else:
  src=(OBJ/dep[key]).resolve();data=src.read_bytes();assert hashlib.sha256(data).hexdigest()==dep[hashkey]
  local.write_bytes(data)
foodpath=resources/'canonical-salmon.png'
source_scene=bpy.context.scene
col=bpy.data.collections['S33_CHARACTER_chef_rowan.001']
root=bpy.data.objects['chef_rowan__ground_root.001']
arm=bpy.data.objects['chef_rowan__armature.001']
cam=source_scene.camera.copy();cam.data=source_scene.camera.data.copy()
lights=[o.copy() for o in source_scene.objects if o.type=='LIGHT']
for o in lights:o.data=o.data.copy()
scene=bpy.data.scenes.new('Rowan warm soft native round01')
scene.collection.children.link(col)
scene.collection.objects.link(cam)
for o in lights:scene.collection.objects.link(o)
bpy.context.window.scene=scene
scene.camera=cam
col.hide_viewport=False;col.hide_render=False
for o in col.objects:o.hide_set(False)
bpy.context.view_layer.update()
original_objects=set(col.objects)

def linear(v):
 return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def mat(name,hexx,rough=.65,spec=.28,sub=0):
 m=bpy.data.materials.new('Rowan warm '+name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF')
 rgb=[linear(int(hexx[i:i+2],16)/255) for i in (0,2,4)]
 p.inputs['Base Color'].default_value=(*rgb,1)
 p.inputs['Roughness'].default_value=rough
 p.inputs['Specular IOR Level'].default_value=spec
 p.inputs['Subsurface Weight'].default_value=sub
 ao=m.node_tree.nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Color'].default_value=(*rgb,1);ao.inputs['Distance'].default_value=.045
 blend=m.node_tree.nodes.new('ShaderNodeMixRGB');blend.blend_type='MIX';blend.inputs[0].default_value=.28;blend.inputs[1].default_value=(*rgb,1)
 m.node_tree.links.new(ao.outputs['Color'],blend.inputs[2]);m.node_tree.links.new(blend.outputs[0],p.inputs['Base Color'])
 m.diffuse_color=(*rgb,1)
 return m
mats={
 'skin':mat('warm tan','F2B876',.67,.25,.035),
 'hair':mat('ginger','B64E14',.64,.27),
 'brow':mat('ginger brow','984212',.73,.2),
 'cap':mat('turquoise fabric','129FAE',.72,.25),
 'capedge':mat('turquoise bound edge','0CA4AD',.68,.26),
 'capseam':mat('turquoise raised seam','41C5C9',.72,.22),
 'ivory':mat('ivory cotton','FFF0D5',.78,.22),
 'collar':mat('ivory folded cotton','FFF5E1',.74,.25),
 'green':mat('green canvas','21813D',.76,.24),
 'belt':mat('green bound edges','196D34',.74,.24),
 'seam':mat('green pocket lip','3A9851',.78,.2),
 'tie':mat('teal kerchief','078899',.67,.27),
 'shoe':mat('dark leather','33291F',.61,.3),
 'eye':mat('eyes','190C05',.24,.5),
 'white':mat('eye glint','FFF7E4',.3,.35),
 'cheek':mat('warm blush','E4866A',.8,.18),
 'mouth':mat('mouth','6D300F',.75,.18),
 'steel':mat('knife steel','A6BDC1',.34,.42),
 'wood':mat('knife handle','65402B',.6,.25),
}

def source_obj(key):return next(o for o in original_objects if o.name==key or o.name.startswith('chef_rowan__'+key+'.') or o.name=='chef_rowan__'+key)
def clean_mesh(o,verts,faces,bone,material,smooth=True):
 for mod in list(o.modifiers):o.modifiers.remove(mod)
 o.vertex_groups.clear()
 mesh=bpy.data.meshes.new(o.name+' round01 geometry');mesh.from_pydata(verts,[],faces);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
 o.data=mesh
 for p in mesh.polygons:p.use_smooth=smooth
 mesh.materials.append(material)
 if bone:
  g=o.vertex_groups.new(name=bone);g.add(list(range(len(mesh.vertices))),1,'REPLACE')
 o['refinement']='Native rebuilt warm soft geometry, round01'
 return o
def add_obj(name):
 o=bpy.data.objects.new('chef_rowan__'+name,bpy.data.meshes.new('Rowan placeholder '+name));col.objects.link(o);o.parent=root
 return o
def deform(o):
 m=o.modifiers.new('Original native rig','ARMATURE');m.object=arm
 return o
def rounded(key,center,dims,r,bone,material,new=False,bend=None):
 o=add_obj(key) if new else source_obj(key)
 x,y,z=[d/2 for d in dims]
 verts=[(center[0]+a*x,center[1]+b*y,center[2]+c*z) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
 faces=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 clean_mesh(o,verts,faces,bone,material)
 bevel=o.modifiers.new('Crafted rounded edges','BEVEL');bevel.width=r;bevel.segments=8
 bevel.affect='EDGES'
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 bpy.ops.object.modifier_apply(modifier=bevel.name)
 if bend:
  for v in o.data.vertices:v.co=bend(v.co.copy())
 wn=o.modifiers.new('Broad surface normals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=35
 if bone:deform(o)
 return o
def ellipsoid(key,center,radius,bone,material,new=False,rot=(0,0,0)):
 o=add_obj(key) if new else source_obj(key)
 verts=[];faces=[];N=40;M=24;R=Euler(rot).to_matrix()
 for j in range(M+1):
  p=math.pi*j/M
  for i in range(N):
   t=math.tau*i/N
   v=R@Vector((radius[0]*math.sin(p)*math.cos(t),radius[1]*math.sin(p)*math.sin(t),radius[2]*math.cos(p)))+Vector(center)
   verts.append(tuple(v))
 for j in range(M):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 clean_mesh(o,verts,faces,bone,material)
 if bone:deform(o)
 return o
def ring(key,rings,bone,material,new=False):
 o=add_obj(key) if new else source_obj(key);verts=[];faces=[];N=64
 for z,rx,front,back in rings:
  for i in range(N):
   t=math.tau*i/N;c=math.cos(t);s=math.sin(t)
   x=rx*math.copysign(abs(c)**.42,c)
   y=(back if s>=0 else front)*math.copysign(abs(s)**.42,s)
   verts.append((x,y,z))
 for j in range(len(rings)-1):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 faces.extend([tuple(reversed(range(N))),tuple((len(rings)-1)*N+i for i in range(N))])
 clean_mesh(o,verts,faces,bone,material)
 sub=o.modifiers.new('Soft tailored transitions','SUBSURF');sub.levels=1;sub.render_levels=1
 if bone:deform(o)
 return o
def tube(name,points,r,bone,material):
 verts=[];faces=[];N=10
 for j,p in enumerate(points):
  tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  tangent.normalize();a=tangent.cross(Vector((0,0,1)))
  if a.length<.01:a=tangent.cross(Vector((0,1,0)))
  a.normalize();b=tangent.cross(a)
  for i in range(N):verts.append(tuple(Vector(p)+r*(math.cos(math.tau*i/N)*a+math.sin(math.tau*i/N)*b)))
 for j in range(len(points)-1):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 faces.extend([tuple(reversed(range(N))),tuple((len(points)-1)*N+i for i in range(N))])
 o=clean_mesh(add_obj(name),verts,faces,bone,material)
 if bone:deform(o)
 return o
def prism(key,outline,y,thickness,bone,material,r=.005):
 n=len(outline);verts=[(x,y+dy,z) for dy in [-thickness/2,thickness/2] for x,z in outline]
 faces=[tuple(reversed(range(n))),tuple(n+i for i in range(n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=clean_mesh(source_obj(key),verts,faces,bone,material)
 b=o.modifiers.new('Soft folded cloth edge','BEVEL');b.width=r;b.segments=5
 w=o.modifiers.new('Folded cloth normals','WEIGHTED_NORMAL');w.keep_sharp=True
 deform(o);return o

# Replace hard original material response on all native geometry, preserving
# original per-face material slots (notably ivory sleeve / skin transitions).
for o in original_objects:
 if o.type!='MESH' or '__held_dish-' in o.name:continue
 for i,m in enumerate(o.data.materials):
  name=m.name.lower()
  key='skin' if 'skin' in name else 'hair' if 'hair_' in name else 'ivory' if 'white' in name else 'green' if 'green' in name else 'tie' if 'teal' in name else 'shoe' if 'navy' in name else 'eye' if 'eye' in name else 'mouth' if 'mouth' in name else 'cheek' if 'cheek' in name else 'steel' if 'metal' in name else 'wood' if 'wood' in name else 'ivory'
  if 'glint' in o.name:key='white'
  if 'cap_' in o.name:key='cap'
  if 'brow' in o.name:key='brow'
  o.data.materials[i]=mats[key]
 for poly in o.data.polygons:poly.use_smooth=True
 for m in o.modifiers:
  if m.type=='BEVEL':m.segments=2 if 'cap_button' in o.name else 8

rounded('head',(0,.005,.67),(.56,.48,.48),.139,'head',mats['skin'])
for side,sign in [('-1',-1),('1',1)]:
 ellipsoid('ear_'+side,(sign*.293,.013,.65),(.029,.052,.0595),'head',mats['skin'])
 ellipsoid('eye_'+side,(sign*.103,-.246,.6892),(.025,.014,.039),'head',mats['eye'])
 ellipsoid('eye_glint_'+side,(sign*.103-.006,-.260,.704),(.007,.004,.009),'head',mats['white'])
 ellipsoid('cheek_'+side,(sign*.182,-.240,.5908),(.034,.009,.02),'head',mats['cheek'])
 ellipsoid('mustache_'+side,(sign*.050,-.265,.574),(.064,.025,.031),'head',mats['hair'],rot=(0,sign*.24,0))
rounded('nose',(0,-.255,.622),(.069,.052,.057),.023,'head',mats['skin'])

# Coherent swept locks stay below the visor rather than piercing its top face.
ellipsoid('rounded_crown',(0,.015,.857),(.286,.248,.16),'head',mats['hair'])
rounded('rounded_occiput',(0,.090,.780),(.568,.400,.390),.120,'head',mats['hair'])
for i,x in enumerate([-.208,-.074,.062,.194]):
 ellipsoid('wave_'+str(i),(x,-.211,.843+(0.004 if i in [1,2] else 0)),(.078,.065,.082),'head',mats['hair'],rot=(0,-.34,0))
for side,sign in [('-1',-1),('1',1)]:
 ellipsoid('wave_temple_'+side,(sign*.260,.005,.763),(.060,.160,.125),'head',mats['hair'],rot=(.08,sign*.10,0))
for i,x in enumerate([-.18,0,.18]):
 ellipsoid('wave_back_'+str(i),(x,.232,.733),(.097,.072,.132),'head',mats['hair'],rot=(0,(i-1)*.12,0))

rounded('cap_crown',(0,.030,.990),(.552,.468,.190),.073,'head',mats['cap'])
rounded('cap_brim',(0,-.198,.925),(.528,.180,.055),.024,'head',mats['cap'],
        bend=lambda v:Vector((v.x,v.y,v.z-.009*(v.x/.264)**2)))
# Retain the original top button's exact maximum height and head weights.
rounded('cap_front_badge',(0,-.204,.995),(.053,.015,.048),.009,'head',mats['capseam'],new=True)
pts=[]
for i in range(41):
 t=math.pi*i/40
 pts.append((.247*math.cos(t),-.211-.061*math.sin(t),.927-.007*math.cos(t)**2))
tube('visor_bound_stitch',pts,.0028,'head',mats['capseam'])
# Tidy panel seam on each side continues around the rear, below the crown.
pts=[]
for i in range(81):
 t=math.tau*i/80
 pts.append((.264*math.cos(t),.030+.226*math.sin(t),.941))
tube('cap_lower_bound_seam',pts,.0025,'head',mats['capedge'])

for o in [source_obj('tailored_tunic'),source_obj('arm_L'),source_obj('arm_R'),source_obj('leg_L'),source_obj('leg_R')]:
 sub=o.modifiers.new('Soft continuous garment anatomy','SUBSURF');sub.levels=2;sub.render_levels=2
 # Smooth the rest surface before the existing native deformation modifier.
 bpy.context.view_layer.objects.active=o
 while o.modifiers.find(sub.name)>0:bpy.ops.object.modifier_move_up(modifier=sub.name)
for side,sign in [('L',-1),('R',1)]:
 # Native cuff is weighted to the original upper arm. It follows every work pose.
 a=Vector((sign*.198,.004,.352));b=Vector((sign*.249,-.002,.247))
 axis=(b-a).normalized();n=axis.cross(Vector((0,1,0))).normalized();q=axis.cross(n)
 pts=[];verts=[];faces=[];N=40
 for t,r in [(0.70,.054),(0.72,.058),(0.91,.058),(0.94,.052)]:
  c=a+(b-a)*t
  for i in range(N):verts.append(tuple(c+r*(math.cos(math.tau*i/N)*n+math.sin(math.tau*i/N)*q)))
 for j in range(3):
  for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 faces.extend([tuple(reversed(range(N))),tuple(3*N+i for i in range(N))])
 cuff=clean_mesh(add_obj('rolled_cuff_'+side),verts,faces,'upper_arm_'+side,mats['collar']);deform(cuff)
 rounded('minimal_foot_'+side,(sign*.115,-.020,.029),(.148,.170,.058),.018,'foot_'+side,mats['shoe'])

for side,sign in [('-1',-1),('1',1)]:
 prism('collar_'+side,[(sign*.108,.412),(sign*.004,.390),(sign*.043,.339),(sign*.098,.358)],-.134,.026,'spine',mats['collar'],.009)
 prism('kerchief_tail_'+side,[(sign*.008,.330),(sign*.036,.327),(sign*.069,.255),(sign*.043,.243),(sign*.014,.282)],-.159,.027,'spine',mats['tie'],.006)
ring('apron_skirt',[(.082,.193,.163,.119),(.090,.205,.177,.127),(.195,.191,.164,.125),(.205,.186,.159,.122)],'pelvis',mats['green'])
rounded('apron_bib',(0,-.155,.277),(.260,.025,.145),.011,'spine',mats['green'])
ring('apron_waist',[(.181,.186,.176,.134),(.185,.196,.181,.142),(.212,.196,.181,.142),(.216,.187,.173,.134)],'pelvis',mats['belt'])
rounded('apron_pocket',(0,-.183,.147),(.186,.019,.066),.012,'pelvis',mats['green'])
pocket=source_obj('apron_pocket')
bm=bmesh.new();bm.from_mesh(pocket.data)
bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-7)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(pocket.data);bm.free();pocket.data.update()
rounded('pocket_bound_lip',(0,-.195,.175),(.168,.009,.011),.004,'pelvis',mats['seam'],new=True)
rounded('apron_belt_keeper',(.137,-.182,.198),(.041,.021,.045),.009,'pelvis',mats['green'],new=True)
for sign in [-1,1]:
 ellipsoid('apron_bib_button_'+str(sign),(sign*.105,-.174,.326),(.010,.007,.011),'spine',mats['seam'],new=True)
ellipsoid('back_apron_bow_knot',(0,.151,.197),(.023,.018,.019),'pelvis',mats['green'],new=True)
for side in ['-1','1']:
 o=source_obj('apron_back_tie_'+side)
 for m in o.modifiers:
  if m.type=='BEVEL':m.segments=8

# Exact new canonical food, full UV rectangle, fixed 0.35-cell width and bottom.
plane=bpy.data.objects[root.name+'__held_dish-salmon__image_plane']
local_width=.35/1.25;local_height=local_width*505/731
mesh=bpy.data.meshes.new('Exact canonical salmon full source UV')
mesh.from_pydata([(-local_width/2,0,0),(local_width/2,0,0),(local_width/2,local_height,0),(-local_width/2,local_height,0)],[],[(0,1,2,3)]);mesh.update()
uv=mesh.uv_layers.new(name='Canonical full source UV 0..1')
for li,value in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=value
plane.data=mesh
im=bpy.data.images.load(str(foodpath),check_existing=False);im.name='Rowan canonical salmon 4389d1e6 packed2D';im.pack()
material=bpy.data.materials.new('Exact approved canonical salmon packed 2D');material.use_nodes=True
nodes=material.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');transparent=nodes.new('ShaderNodeBsdfTransparent');emission=nodes.new('ShaderNodeEmission');tex=nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Linear'
links=material.node_tree.links;links.new(tex.outputs['Color'],emission.inputs['Color']);links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(emission.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
material.surface_render_method='DITHERED'
plane.data.materials.append(material)
plane['representation']='Exact approved packed 2D canonical salmon; not modeled sushi'
plane['source_sha256']=dep['sha256'];plane['source_image']=str(foodpath);plane['fixed_alpha_rectangle']=json.dumps([0,0,731,505]);plane['source_dimensions']=json.dumps([731,505]);plane['world_width_cells']=.35
plane['source_revision']='old5de74758 1254square croppedUV -> canonical4389d1e6 731x505 fullUV0..1; bottom anchor/actions/depth preserved'
root['held_food_source']=json.dumps(dep)
root['active_refinement_brief']='brief-v2-food.json'

# One fixed symmetric capture configuration. No ground plane or cast shadow.
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=384;scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.pixel_aspect_x=1;scene.render.pixel_aspect_y=1;scene.render.fps=12
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
scene.render.image_settings.compression=40
scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
scene.world=bpy.data.worlds.new('Rowan symmetric soft neutral world');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.82,.86,.90,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.22
for o in lights:
 o.data.energy=170 if 'overhead' in o.name else 95
 o.data.size=4.5
 o.data.color=(1,.96,.90)
scene.render.film_transparent=True
# Preserve only this asset, its native actions, lighting and packed dependencies.
keep=set(col.objects)|{cam}|set(lights)
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
for c in list(bpy.data.collections):
 if c!=col and not c.objects and not c.children:bpy.data.collections.remove(c)
for a in list(bpy.data.actions):
 if 'chef-rowan' not in a.name:bpy.data.actions.remove(a)
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
bpy.context.view_layer.update()
scene['activeBrief']='brief-v2-food.json'
scene['capture']='Original camera/root/yaws, 384x640, no fitting, symmetric broad native lighting'
bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'round-01.blend'))
recipe=dict(activeBrief='brief-v2-food.json',nativeSource='round-01.blend',sourceSHA256=brief['source']['projectSHA256'],targetSHA256=brief['target']['sha256'],foodDependency=dep,
            changes=['Rounded cap/curved visor and clean swept fringe overlap','Smooth native ginger locks/moustache and rounded face/ears/eyes','Soft continuous sleeve/tunic anatomy, rolled cuffs, shaped shoes','Thicker apron wrap/belt/pocket lip/bib buttons/back bow','Warm soft material response and fixed fourfold symmetric lighting'],
            rig='Original 25 bone rest, original 24 action cohorts, original root and child orientation unchanged',
            foodRevision='Exact approved 731x505 packed2D, fullUV0..1, .35world width; original plane bottom/local transform/actions unchanged',
            materials=[m.name for m in bpy.data.materials])
(HERE/'round-01-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
print('SAVED',HERE/'round-01.blend')
