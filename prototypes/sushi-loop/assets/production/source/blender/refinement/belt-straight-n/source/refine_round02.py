import bpy,json,pathlib,math
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'source'/'round-01.blend'));s=bpy.context.scene;OUT=P/'candidates'/'round-02';OUT.mkdir(parents=True,exist_ok=True)
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.world.node_tree.nodes['Background'].inputs[1].default_value=.32
for o in s.objects:
 if o.type=='LIGHT':o.data.energy=85 if o.name.startswith('Centered') else 30
s.cycles.samples=96

def srgb(h):
 h=h.lstrip('#');v=[int(h[i:i+2],16)/255 for i in (0,2,4)];return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)+(1,)
def node(nt,typ):return nt.nodes.new(typ)
def ramp(nt,inp,colors):
 n=node(nt,'ShaderNodeValToRGB');n.color_ramp.interpolation='EASE'
 for i,(pos,col) in enumerate(colors):
  el=n.color_ramp.elements[i] if i<2 else n.color_ramp.elements.new(pos);el.position=pos;el.color=srgb(col)
 nt.links.new(inp,n.inputs[0]);return n.outputs[0]
def mathn(nt,op,a,b=None):
 n=node(nt,'ShaderNodeMath');n.operation=op
 for inp,v in zip(n.inputs,[a,b]):
  if v is None:continue
  if hasattr(v,'node'):nt.links.new(v,inp)
  else:inp.default_value=v
 return n.outputs[0]
# Camera radiance field is a native object-coordinate rail material. BSDF remains active for non-camera transport.
m=bpy.data.materials['WarmSoft_CoralRail'];nt=m.node_tree;n=nt.nodes;l=nt.links;sh=n.get('Principled BSDF');out=n.get('Material Output');tex=node(nt,'ShaderNodeTexCoord');sep=node(nt,'ShaderNodeSeparateXYZ');l.new(tex.outputs['Object'],sep.inputs[0]);a=mathn(nt,'DIVIDE',mathn(nt,'ABSOLUTE',sep.outputs['X']),.065)
top=ramp(nt,a,[(0,'D17B59'),(.5,'D27C59'),(.72,'EDAA78'),(.87,'D77C56'),(1,'A9523D')]);zz=mathn(nt,'DIVIDE',mathn(nt,'ADD',sep.outputs['Z'],.095),.19);side=ramp(nt,zz,[(0,'84452F'),(.25,'A5583C'),(.78,'C77150'),(1,'DD956B')]);geo=node(nt,'ShaderNodeNewGeometry');sp=node(nt,'ShaderNodeSeparateXYZ');l.new(geo.outputs['True Normal'],sp.inputs[0]);f=mathn(nt,'GREATER_THAN',sp.outputs['Z'],.5);mx=node(nt,'ShaderNodeMixRGB');l.new(f,mx.inputs[0]);l.new(side,mx.inputs[1]);l.new(top,mx.inputs[2]);em=node(nt,'ShaderNodeEmission');l.new(mx.outputs[0],em.inputs[0]);em.inputs[1].default_value=1
lp=node(nt,'ShaderNodeLightPath');mix=node(nt,'ShaderNodeMixShader');l.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);l.new(sh.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
# Deck retains original phase and native UV; radiance is smoothly shouldered and phase-periodic, blended with real BSDF.
m=next(m for m in bpy.data.materials if 'moving_deck' in m.name);nt=m.node_tree;n=nt.nodes;l=nt.links;sh=n.get('Principled BSDF');out=n.get('Material Output');r=n.get('Soft_slat_shoulders');cols=['263440','263440','60778A','4C6376','455B6E','4B6275','2D3D4B','263440']
for el,col in zip(sorted(r.color_ramp.elements,key=lambda e:e.position),cols):el.color=srgb(col)
em=node(nt,'ShaderNodeEmission');l.new(r.outputs[0],em.inputs[0]);mix=node(nt,'ShaderNodeMixShader');mix.inputs[0].default_value=.65;l.new(sh.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
# Artifact-free stable world material on supports; broad native lighting plus subtle emission lift avoids black underside.
for name in ['WarmSoft_HoneyWood','WarmSoft_WoodFoot']:
 m=bpy.data.materials[name];nt=m.node_tree;n=nt.nodes;l=nt.links;sh=n.get('Principled BSDF');out=n.get('Material Output');em=node(nt,'ShaderNodeEmission')
 if sh.inputs['Base Color'].is_linked:l.new(sh.inputs['Base Color'].links[0].from_socket,em.inputs[0])
 else:em.inputs[0].default_value=sh.inputs['Base Color'].default_value
 mix=node(nt,'ShaderNodeMixShader');mix.inputs[0].default_value=.22;l.new(sh.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
root=next(o for o in s.objects if '__root.' in o.name);root.rotation_euler.z=math.pi;s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'source'/'round-02.blend'))
for direction,rot in [('N',math.pi),('E',math.pi/2)]:
 root.rotation_euler.z=rot;bpy.context.view_layer.update();s.render.filepath=str(OUT/('hero-'+direction+'.png'));bpy.ops.render.render(write_still=True)
recipe=json.load(open(P/'source'/'round-01-recipe.json'));recipe.update(round=2,project=str(P/'source'/'round-02.blend'),method=recipe['method']+' Native object-coordinate camera radiance on rectangular rails keeps an uninterrupted rounded light shoulder at open ends. Deck mixes65% native periodic emission with35% BSDF. Supports22% common emission lift. No external raster textures; Standard view; broad85W overhead,4x30W fills and uniform.32 world.');(P/'source'/'round-02-recipe.json').write_text(json.dumps(recipe,indent=2))
