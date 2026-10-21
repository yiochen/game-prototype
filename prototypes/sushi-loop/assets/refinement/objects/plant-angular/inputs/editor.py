"""Reproducible native Blender plant tuning. Run from background Blender.
blender --background --python editor.py -- --round 2
Exact prior rounds are preserved in source/editor-round-NN.py.
No image or reference pixels are loaded by this recipe.
"""
import argparse, hashlib, json, math, sys, time
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parents[4]
BRIEF=json.loads((ROOT/'brief.json').read_text())
SOURCE=Path(BRIEF['workspace'])/BRIEF['sourceStudy']
BASELINE=Path(BRIEF['workspace'])/BRIEF['untouchedSource']
DIRECTIONS={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
def lin(h):
 c=[int(h[i:i+2],16)/255 for i in (1,3,5)]
 return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)
def mesh(name,verts,faces,material):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
 o=bpy.data.objects.new(name,m);scene.collection.objects.link(o);o.parent=root
 o.data.materials.append(material);return o

def material(name,colors,roughness=.43,spec=.3,attribute=None,zrange=None,ao=.88,coat=.08):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');l.new(p.outputs['BSDF'],out.inputs['Surface'])
 p.inputs['Roughness'].default_value=roughness;p.inputs['Specular IOR Level'].default_value=spec;p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.4
 if attribute:
  a=n.new('ShaderNodeAttribute');a.attribute_name=attribute;fac=a.outputs['Fac']
 elif zrange:
  a=n.new('ShaderNodeNewGeometry');s=n.new('ShaderNodeSeparateXYZ');l.new(a.outputs['Position'],s.inputs[0]);r=n.new('ShaderNodeMapRange');r.inputs['From Min'].default_value=zrange[0];r.inputs['From Max'].default_value=zrange[1];l.new(s.outputs['Z'],r.inputs['Value']);fac=r.outputs[0]
 else:fac=None
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
 for e in list(ramp.color_ramp.elements)[2:]:ramp.color_ramp.elements.remove(e)
 for i,(pos,col) in enumerate(colors):
  e=ramp.color_ramp.elements[i] if i<2 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=lin(col)
 if fac:l.new(fac,ramp.inputs[0])
 else:ramp.inputs[0].default_value=.5
 a=n.new('ShaderNodeAmbientOcclusion');a.inputs['Distance'].default_value=.07;a.samples=16
 r=n.new('ShaderNodeMapRange');r.inputs['To Min'].default_value=ao;r.inputs['To Max'].default_value=1;l.new(a.outputs['AO'],r.inputs['Value'])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;l.new(ramp.outputs[0],mix.inputs[1]);l.new(r.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
 return m

def rounded_square(half,r,z,segments=8):
 pts=[]
 for x,y,a in [(half-r,half-r,0),(-half+r,half-r,90),(-half+r,-half+r,180),(half-r,-half+r,270)]:
  for i in range(segments+1):
   t=math.radians(a+90*i/segments);pts.append((x+r*math.cos(t),y+r*math.sin(t),z))
 return pts

def build_pot():
 # Single closed shell: continuous corners, rounded plan corners, real bevel.
 profile=[(.27,.023,.015),(.38,.032,.3925),(.4125,.038,.3925),(.4125,.038,.4675),(.343,.024,.4675),(.343,.024,.3975),(.23,.020,.105)]
 v=[p for half,r,z in profile for p in rounded_square(half,r,z)];c=36;f=[]
 for j in range(len(profile)-1):
  for i in range(c):f.append((j*c+i,j*c+(i+1)%c,(j+1)*c+(i+1)%c,(j+1)*c+i))
 f.append(tuple(reversed(range(c))));f.append(tuple((len(profile)-1)*c+i for i in range(c)))
 o=mesh('Planter continuous watertight shell',v,f,potmat);o.data.materials.append(rimmat)
 for p in o.data.polygons:
  if c<=p.index<c*5:p.material_index=1
 # Ensure outward orientation. Smooth then weighted normals keep broad panels clean.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for p in o.data.polygons:p.use_smooth=True
 be=o.modifiers.new('Physical softened edge','BEVEL');be.width=.008;be.segments=4;be.limit_method='ANGLE';be.angle_limit=.35
 no=o.modifiers.new('Weighted panel normals','WEIGHTED_NORMAL');no.keep_sharp=True;no.weight=40
 return o

def leaf(i,tip,halfwidth,basez):
 tip=Vector(tip);r=Vector((tip.x,tip.y,0)).normalized();w=Vector((-r.y,r.x,0))
 start=Vector((.025*r.x,.025*r.y,basez+.004*(i%3)))
 # Cross section spans a shallow folded blade. A raised central ridge remains readable.
 ts=[0,.09,.22,.38,.55,.72,.87,.96,1]
 ss=[-1,-.52,0,.52,1]
 v=[];prog=[]
 for t in ts:
  center=start+(tip-start)*t
  center.z+=.05*math.sin(math.pi*t)
  width=halfwidth*math.sin(math.pi*t)**.84*(.92+.08*t)
  # Slightly swept centre gives a broad organic blade rather than a flat triangle.
  center+=w*(.010*math.sin(math.pi*t)*(1 if i%2 else -1))
  for s in ss:
   p=center+w*(width*s)
   p.z+=.082*math.sin(math.pi*t)*(1-abs(s))
   v.append(tuple(p));prog.append(t)
 f=[]
 for j in range(len(ts)-1):
  for k in range(4):f.append((j*5+k,j*5+k+1,(j+1)*5+k+1,(j+1)*5+k))
 o=mesh('Folded thick blade %02d'%i,v,f,leafmats[i%3][0]);o.data.materials.append(leafmats[i%3][1])
 for face in o.data.polygons:face.material_index=0 if face.index%4<2 else 1
 a=o.data.attributes.new('leaf_progress','FLOAT','POINT')
 for j,x in enumerate(prog):a.data[j].value=x
 # Merge the coincident tip/root vertices; solidify produces a manifold leaf.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for p in o.data.polygons:p.use_smooth=True
 # Split shading along the actual raised central fold, while smoothing each broad side.
 sharp=o.data.attributes.new('sharp_edge','BOOLEAN','EDGE')
 for edge in o.data.edges:
  pts=[o.data.vertices[j].co for j in edge.vertices]
  if all(abs((pt-start).dot(w)-.010*math.sin(math.pi*min(1,max(0,(pt.z-basez)/(tip.z-basez))))*(1 if i%2 else -1))<.012 for pt in pts):sharp.data[edge.index].value=True
 so=o.modifiers.new('Real leaf thickness','SOLIDIFY');so.thickness=.009;so.offset=-1;so.use_even_offset=True
 be=o.modifiers.new('Soft blade edge','BEVEL');be.width=.002;be.segments=2;be.limit_method='ANGLE';be.angle_limit=.4
 return o

def setup_world():
 scene.world=bpy.data.worlds.new('Plant rotationally symmetric studio');scene.world.use_nodes=True;n=scene.world.node_tree.nodes;l=scene.world.node_tree.links;n.clear()
 out=n.new('ShaderNodeOutputWorld');bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.78,.75,.67,1);bg.inputs['Strength'].default_value=.66
 coord=n.new('ShaderNodeTexCoord');s=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs['Normal'],s.inputs[0]);a=n.new('ShaderNodeMath');a.operation='ABSOLUTE';l.new(s.outputs['Z'],a.inputs[0])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE';ramp.color_ramp.elements[0].color=(.30,.25,.18,1);ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[1].position=.85;ramp.color_ramp.elements[1].color=(1,.93,.76,1)
 glossy=n.new('ShaderNodeBackground');glossy.inputs['Strength'].default_value=1.35;l.new(a.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],glossy.inputs['Color'])
 path=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(path.outputs['Is Glossy Ray'],mix.inputs[0]);l.new(bg.outputs[0],mix.inputs[1]);l.new(glossy.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
 for o in list(scene.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 data=bpy.data.lights.new('Plant broad vertical sun','SUN');data.energy=1.8;data.angle=1.05;data.color=(1,.975,.91)
 o=bpy.data.objects.new(data.name,data);scene.collection.objects.link(o);o.location=(0,0,5);o.rotation_euler=(0,0,0)

def registration():
 def px(p):
  q=world_to_camera_view(scene,scene.camera,Vector(p));return [q.x*scene.render.resolution_x,(1-q.y)*scene.render.resolution_y]
 return {'frame':[scene.render.resolution_x,scene.render.resolution_y],'root':px((0,0,0)),'unitX':px((1,0,0)),'unitDepth':px((0,-1,0)),'pixelAspect':[scene.render.pixel_aspect_x,scene.render.pixel_aspect_y],'cameraMatrix':[list(r) for r in scene.camera.matrix_world],'orthoScale':scene.camera.data.ortho_scale,'shift':[scene.camera.data.shift_x,scene.camera.data.shift_y]}

def topology(obj):
 bm=bmesh.new();bm.from_mesh(obj.data);d={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'boundaryEdges':sum(e.is_boundary for e in bm.edges),'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-10 for f in bm.faces)};bm.free();return d

def bounds():
 deps=bpy.context.evaluated_depsgraph_get();records={}
 for o in scene.objects:
  if o.type!='MESH':continue
  ev=o.evaluated_get(deps);me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
  records[o.name]={'min':[min(v[i] for v in pts) for i in range(3)],'max':[max(v[i] for v in pts) for i in range(3)]}
 return records

p=argparse.ArgumentParser();p.add_argument('--round',type=int,default=2);args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
assert args.round>=2,'Use exact preserved recipe for earlier rounds'
assert not (ROOT/'candidates'/('round-%02d'%args.round)).exists(),'Refusing to overwrite immutable round'
assert sha(BASELINE)==BRIEF['untouchedSourceSHA256'],'Untouched baseline mismatch'
sourcehash=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.data.scenes[BRIEF['sourceScene']];bpy.context.window.scene=scene
source_registration=registration();root=bpy.data.objects[scene['studyRoot']]
# Keep one self-contained editable native scene and preserve the fixed source camera.
for s in list(bpy.data.scenes):
 if s!=scene:bpy.data.scenes.remove(s)
for o in list(scene.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
root.rotation_euler=(0,0,0);scene.name='Plant tuning round %02d'%args.round
potmat=material('Warm terracotta body',[(0,'#783000'),(.30,'#AA4A02'),(1,'#D67C0A')],.60,.045,zrange=(.015,.44),ao=.94,coat=0)
rimmat=material('Golden ceramic continuous rim',[(0,'#D67B14'),(.5,'#E99B22'),(1,'#FAC64A')],.31,.38,zrange=(.3925,.4675),ao=.92)
soilmat=material('Warm dark potting soil',[(0,'#4F270D'),(1,'#734119')],.84,.10,ao=.9)
leafmats=[]
for i,(lime,green) in enumerate([('#79D12C','#28A21B'),('#8AD72D','#35AD20'),('#71C925','#239A17')]):
 leafmats.append([material('Broad lime fold '+str(i),[(0,'#4DAA29'),(.22,'#61BE29'),(.57,lime),(1,'#B6E748')],.43,.24,attribute='leaf_progress',ao=.96,coat=.035),material('Rich green turning plane '+str(i),[(0,'#24851F'),(.22,'#309921'),(.57,green),(1,'#79CB29')],.46,.20,attribute='leaf_progress',ao=.96,coat=.035)])
pot=build_pot()
# Soil covers the bottom of the opening, held below the rounded inner lip.
soilverts=rounded_square(.341,.025,.415);soil=mesh('Recessed soil',soilverts,[tuple(range(len(soilverts)))],soilmat)
tips=[(-.46,-.14,.96),(-.31,-.45,1.03),(.12,-.465,.91),(.45,-.265,1.02),(.465,.13,1.13),(.23,.455,1.01),(-.20,.465,1.10),(-.455,.265,1.07),(-.235,-.05,1.33),(.215,-.115,1.39),(.15,.245,1.452),(-.17,.20,1.40)]
for i,t in enumerate(tips):leaf(i,t,.150 if i<8 else .125,.455 if i<8 else .49)
setup_world();scene.cycles.samples=72;scene.cycles.use_denoising=True;scene.cycles.seed=213;scene.cycles.use_animated_seed=False
scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=3;scene.cycles.glossy_bounces=3
# Preserve compositor grade: same source pipeline and same settings in every facing.
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.resolution_percentage=100
bpy.context.view_layer.update();base_bounds=bounds();reg=registration();assert reg==source_registration
mn=[min(d['min'][i] for d in base_bounds.values()) for i in range(3)];mx=[max(d['max'][i] for d in base_bounds.values()) for i in range(3)]
assert all(mn[i]>=(-.48,-.48,.015)[i]-1e-6 for i in range(3)),mn
assert all(mx[i]<=(.48,.48,1.46)[i]+1e-6 for i in range(3)),mx
outdir=ROOT/'candidates'/('round-%02d'%args.round);outdir.mkdir(parents=True,exist_ok=True)
blend=ROOT/'source'/('round-%02d.blend'%args.round)
scene['experiment']='native Blender plant tuning';scene['round']=args.round;scene['sourceSHA256']=sourcehash
scene['recipe']='source/editor.py';scene['noGroundPlane']=True
root.rotation_euler.z=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
val={'round':args.round,'status':'awaiting independent pixel review','blend':str(blend.relative_to(ROOT)),'blendSHA256':sha(blend),'sourceSHA256':sourcehash,'untouchedSourceSHA256':sha(BASELINE),'recipeSHA256':sha(__file__),'blenderVersion':bpy.app.version_string,'registration':reg,'sourceRegistration':source_registration,'assetBounds':{'min':mn,'max':mx},'objectBounds':base_bounds,'rimTopology':topology(pot),'lighting':{'symmetry':'Z axis; world shader depends only on absolute normal Z','sunRotation':[0,0,0],'sunAngle':1.05,'sunEnergy':1.8,'worldDiffuseStrength':.66,'worldReflectionStrength':1.35,'horizontalLightPositionFalloff':False,'groundPlane':False},'materials':{},'renders':{},'contract':BRIEF['contract'],'recipePath':'source/editor-round-%02d.py'%args.round,'notes':['Every PNG is an unmodified native Cycles RGBA render.','No external textures, no ground plane, no camera or per-view grade changes.','Single manifold planter shell replaces four intersecting rim rails.','Each leaf uses broad intrinsic fold materials; all facings rotate only the common root.']}
for m in [potmat,rimmat,soilmat]+[m for pair in leafmats for m in pair]:
 pr=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');val['materials'][m.name]={key:pr.inputs[key].default_value for key in ['Roughness','Specular IOR Level','Coat Weight','Coat Roughness']}
for d,a in DIRECTIONS.items():
 root.rotation_euler.z=a;bpy.context.view_layer.update();scene.render.filepath=str(outdir/(d+'.png'));t=time.monotonic();bpy.ops.render.render(write_still=True,scene=scene.name)
 # Inspect actual native PNG alpha via Blender, without changing any export pixels.
 im=bpy.data.images.load(scene.render.filepath,check_existing=False);w,h=im.size;pix=im.pixels[:];xs=[];ys=[];partial=0
 for y in range(h):
  for x in range(w):
   alpha=pix[(y*w+x)*4+3]
   if alpha>0:xs.append(x);ys.append(h-1-y)
   if 0<alpha<1:partial+=1
 bbox=[min(xs),min(ys),max(xs)+1,max(ys)+1];clipped=bbox[0]<=0 or bbox[1]<=0 or bbox[2]>=w or bbox[3]>=h
 val['renders'][d]={'path':str(Path(scene.render.filepath).relative_to(ROOT)),'sha256':sha(scene.render.filepath),'size':[w,h],'alphaBBox':bbox,'partiallyTransparentPixels':partial,'clearBorder':not clipped,'seconds':round(time.monotonic()-t,3),'rootRotationZ':a,'geometryBounds':bounds()}
 bpy.data.images.remove(im);assert not clipped,(d,bbox);write(outdir/'validation.json',val);print('PLANT_ROUND_FRAME',d,json.dumps(val['renders'][d]),flush=True)
root.rotation_euler.z=0
write(outdir/'validation.json',val)
print('PLANT_ROUND_READY',str(outdir),flush=True)
