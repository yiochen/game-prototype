"""Focused material-only Stage1 v6 porthole refinement from exact immutable v5.
Blender5.2.2: blender -b --python build_glass.py [-- --study]
All geometry/normals/UVs, lights, camera, native actions and interfaces unchanged.
"""
import bpy,json,hashlib,sys,math
from pathlib import Path
H=Path(__file__).resolve().parent;B=H.parents[1];R=H/'resources';O=B/'candidates/stage1-v6';O.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256((R/'baseline-v5.blend').read_bytes()).hexdigest()=='87647d3167633d4f3a7c4cd4bf5a4af4e221a6a944d57cd06400df8df9d1ea94'
bpy.ops.wm.open_mainfile(filepath=str(R/'baseline-v5.blend'))
lens=bpy.data.objects['body__convex_blue_glass'];m=lens.data.materials[0].copy();m.name='Sub Native depth glass v6';m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
def node(kind,name,loc):
 n=nt.nodes.new(kind);n.name=name;n.label=name;n.location=loc;return n
def link(a,out,b,inp):nt.links.new(a.outputs[out],b.inputs[inp])
def ramp(name,loc,stops):
 n=node('ShaderNodeValToRGB',name,loc);cr=n.color_ramp;cr.interpolation='EASE'
 while len(cr.elements)>1:cr.elements.remove(cr.elements[-1])
 cr.elements[0].position=stops[0][0];cr.elements[0].color=(*stops[0][1],1)
 for x,c in stops[1:]:e=cr.elements.new(x);e.color=(*c,1)
 return n
out=node('ShaderNodeOutputMaterial','Native opaque glass output',(840,180))
p=node('ShaderNodeBsdfPrincipled','Polished blue optical surface',(590,180));p.inputs['Roughness'].default_value=.095;p.inputs['IOR'].default_value=1.46;p.inputs['Specular IOR Level'].default_value=.38;p.inputs['Metallic'].default_value=0;p.inputs['Coat Weight'].default_value=.70;p.inputs['Coat Roughness'].default_value=.065;p.inputs['Coat IOR'].default_value=1.46;p.inputs['Alpha'].default_value=1;p.inputs['Transmission Weight'].default_value=0
lw=node('ShaderNodeLayerWeight','Angle-dependent blue optical depth',(-850,370));lw.inputs['Blend'].default_value=.32
blue=ramp('Blue core to cyan edge value',(-610,370),[(0,(.003,.11,.43)),(.35,(.002,.19,.61)),(.72,(.01,.37,.85)),(1,(.06,.64,.95))]);link(lw,'Facing',blue,'Fac')
g=node('ShaderNodeNewGeometry','World shading vectors',(-1100,0))
neg=node('ShaderNodeVectorMath','Incoming ray toward environment',(-850,0));neg.operation='SCALE';neg.inputs['Scale'].default_value=-1;link(g,'Incoming',neg,0)
ref=node('ShaderNodeVectorMath','Native reflected viewing ray',(-620,0));ref.operation='REFLECT';link(neg,'Vector',ref,0);link(g,'Normal',ref,1)
xyz=node('ShaderNodeSeparateXYZ','Reflection elevation only',(-410,0));link(ref,'Vector',xyz,'Vector')
hi=ramp('Centered overhead reflection envelope',(-190,0),[(.50,(0,0,0)),(.78,(.10,.10,.10)),(.94,(.58,.58,.58)),(1,(.42,.42,.42))]);link(xyz,'Z',hi,'Fac')
mix=node('ShaderNodeMixRGB','Blue tinted broad reflection',(125,290));mix.blend_type='MIX';mix.inputs[2].default_value=(.28,.72,.94,1);link(hi,'Color',mix,0);link(blue,'Color',mix,1);link(mix,'Color',p,'Base Color')
p.inputs['Emission Color'].default_value=(.14,.48,.70,1)
em=node('ShaderNodeMath','Restrained reflected radiance',(130,-90));em.operation='MULTIPLY';em.inputs[1].default_value=.22;link(hi,'Color',em,0);link(em,'Value',p,'Emission Strength')
link(p,'BSDF',out,'Surface');lens.data.materials[0]=m
m['scope']='Only main porthole lens. Native static angle/reflection shading, no opacity/transmission/image/card/geometry/light/camera changes.';m['lightingLaw']='Reflection field uses only worldZ of reflected incoming ray; no preferred horizontal direction, no per-view settings.'
bpy.context.view_layer.update()
if '--study' in sys.argv:
 study=O/'glass-study-02';study.mkdir(exist_ok=True);filepath=H/'glass-study-02.blend'
else:study=O;filepath=H/'submarine-stage1.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(filepath),compress=True)
if '--study' in sys.argv:
 root=bpy.data.objects['submarine-yellow__root'];acts=json.loads(root['nativeActions']);s=bpy.context.scene
 for owner,name in acts['dock-ready'].items():
  o=bpy.data.objects[owner];o.animation_data_create();a=bpy.data.actions[name];o.animation_data.action=a
  if a.slots:o.animation_data.action_slot=a.slots[0]
 for d,a in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
  root.rotation_euler.z=a;s.frame_set(1);bpy.context.view_layer.update();s.render.filepath=str(study/('dock-ready-'+d+'.png'));bpy.ops.render.render(write_still=True)
print('SOURCE',str(filepath),hashlib.sha256(filepath.read_bytes()).hexdigest())
