"""Approved native Faceted finish, 2026-10-19.
Keep native geometry, height ramps, procedural/animated colors and alpha routing.
ImageGen held-food planes remain unlit 2D artwork. Materials are edited in place
so baked shader-action targets retain their exact material/node-tree identities.
"""
import bpy, math
from mathutils import Vector
REVISION='faceted-approved-2026-10-19'
WOOD_MULTIPLIER=.42
RAIL_SRGB='#966B60'
FLOOR_MULTIPLIER=.42 # Compensate diffuse floor brightness; preserve cream/wave/checker colors.
ROLES=[('overhead',(0,0,4.5),140,3.5)]+[(f'fill-{i}',p,100,4) for i,p in enumerate(((3,0,1.8),(0,3,1.8),(-3,0,1.8),(0,-3,1.8)))]
def linear_hex(color):
 values=[int(color[i:i+2],16)/255 for i in (1,3,5)]
 return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]+[1]
def ensure_lights(scene):
 # Only scene-level capture lights; never alter a model's own objects.
 for obj in scene.collection.objects:
  if obj.type=='LIGHT' and obj.name.startswith('S33 '):obj.data.energy=0
 for role,position,power,size in ROLES:
  obj=next((o for o in scene.collection.objects if o.type=='LIGHT' and o.get('s33FacetedRole')==role),None)
  if obj is None:
   data=bpy.data.lights.new('S33 Faceted '+role,'AREA');obj=bpy.data.objects.new('S33 Faceted '+role,data);scene.collection.objects.link(obj);obj['s33FacetedRole']=role
  obj.data.energy=power;obj.data.shape='DISK';obj.data.size=size;obj.data.color=(1,1,1);obj.location=position
  obj.rotation_euler=(Vector((0,0,.8))-obj.location).to_track_quat('-Z','Y').to_euler()
 scene.world=scene.world or bpy.data.worlds.new('S33 Faceted World');scene.world.use_nodes=True
 background=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');background.inputs['Strength'].default_value=0
 scene['s33Lighting']=REVISION
 return {'treatment':'Faceted','overheadWatts':140,'overheadPosition':[0,0,4.5],'overheadSize':3.5,'fillWattsEach':100,'fillSize':4,'fillRadius':3,'fillZ':1.8,'horizontalSymmetry':4,'worldStrength':0}
def lower_color(material):
 return next((n for n in material.node_tree.nodes if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY' and n.inputs[2].is_linked and n.inputs[2].links[0].from_node.type=='VALTORGB'),None)
def calibrate_floor(material,aid):
 if not(aid.startswith('floor-') or aid=='dock-floor') or material.get('s33FloorCalibrated'):return
 nodes=material.node_tree.nodes;links=material.node_tree.links;output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
 shader=output.inputs['Surface'].links[0].from_node
 if shader.type!='BSDF_PRINCIPLED':raise RuntimeError('Expected matte floor surface')
 base=shader.inputs['Base Color']
 if base.is_linked:
  upstream=base.links[0].from_socket;scale=nodes.new('ShaderNodeMixRGB');scale.blend_type='MULTIPLY';scale.inputs[0].default_value=1;scale.inputs[2].default_value=(FLOOR_MULTIPLIER,)*3+(1,);scale.label='Floor diffuse palette calibration'
  links.new(upstream,scale.inputs[1]);links.new(scale.outputs[0],base)
 else:base.default_value=tuple(c*FLOOR_MULTIPLIER for c in base.default_value[:3])+(base.default_value[3],)
 material['s33FloorCalibrated']=FLOOR_MULTIPLIER
 material['s33MaterialRefinement']='floor linear albedo × 0.42; retain readable approved floor palette under actual light'
def finish(material,aid):
 if material.get('s33FacetedRevision')==REVISION:
  calibrate_floor(material,aid);return material
 if material.get('sprite_source'):
  material['s33FacetedException']='approved ImageGen screen-space food; preserve original unlit color and alpha';return material
 nodes=material.node_tree.nodes;links=material.node_tree.links
 output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
 # Follow only active surface links, retaining transparent MixShader structure.
 active=[];seen=set()
 def walk(node):
  if node.as_pointer() in seen:return
  seen.add(node.as_pointer())
  if node.type in ('EMISSION','BSDF_PRINCIPLED'):active.append(node);return
  for inp in node.inputs:
   if inp.type=='SHADER' and inp.is_linked:walk(inp.links[0].from_node)
 if output.inputs['Surface'].is_linked:walk(output.inputs['Surface'].links[0].from_node)
 if len(active)!=1:raise RuntimeError('Expected one native active color surface: '+aid+' '+material.name)
 old=active[0];base=old.inputs['Color'] if old.type=='EMISSION' else old.inputs['Base Color']
 lower=lower_color(material)
 shader=nodes.new('ShaderNodeBsdfPrincipled');shader.label='Approved Faceted matte surface'
 shader.inputs['Roughness'].default_value=.85;shader.inputs['Specular IOR Level'].default_value=.03
 shader.inputs['Metallic'].default_value=0;shader.inputs['IOR'].default_value=1.45;shader.inputs['Emission Strength'].default_value=0
 if lower:links.new(lower.outputs[0],shader.inputs['Base Color'])
 elif base.is_linked:links.new(base.links[0].from_socket,shader.inputs['Base Color'])
 else:shader.inputs['Base Color'].default_value=base.default_value
 if old.type=='BSDF_PRINCIPLED':
  alpha=old.inputs.get('Alpha')
  if alpha:
   if alpha.is_linked:links.new(alpha.links[0].from_socket,shader.inputs['Alpha'])
   else:shader.inputs['Alpha'].default_value=alpha.default_value
 outgoing=[l.to_socket for l in links if l.from_node==old and l.from_socket.type=='SHADER']
 for target in outgoing:links.new(shader.outputs['BSDF'],target)
 if aid=='crate-wood' and 'wood' in material.name.lower():
  if lower is None or lower.inputs[1].is_linked:raise RuntimeError('Expected editable native crate albedo')
  before=list(lower.inputs[1].default_value);lower.inputs[1].default_value=[c*WOOD_MULTIPLIER for c in before[:3]]+[before[3]]
  shader.inputs['Roughness'].default_value=1;shader.inputs['Specular IOR Level'].default_value=0
  material['s33MaterialRefinement']='crate wood linear RGB × 0.42; matte'
 elif aid.startswith('belt-') and 'S33_FB_red' in material.name:
  if lower is None or lower.inputs[1].is_linked:raise RuntimeError('Expected editable native rail color')
  lower.inputs[1].default_value=linear_hex(RAIL_SRGB);shader.inputs['Roughness'].default_value=1;shader.inputs['Specular IOR Level'].default_value=0
  material['s33MaterialRefinement']='muted clay '+RAIL_SRGB+'; matte'
 calibrate_floor(material,aid)
 material['s33FacetedRevision']=REVISION;material['s33Lighting']='actual centered overhead plus symmetric cardinal fills; old view-tone bypassed'
 return material
def apply(asset,aid):
 materials={slot.material for obj in asset['collection'].all_objects if obj.type=='MESH' for slot in obj.material_slots if slot.material}
 for mat in materials:finish(mat,aid)
 asset['artStyle']={'revision':REVISION,'contrast':1.35,'contrastSpace':'sRGB','environmentHeightRatio':.7,'lowerTone':'native world-height material ramp','worldLighting':True,'lighting':'Faceted 140 W overhead plus four equal 100 W cardinal fills','roughness':.85,'specularIORLevel':.03,'woodRefinement':'crate only: linear albedo × 0.42, roughness 1, specular 0','beltRailColor':RAIL_SRGB,'floorAlbedoCalibration':FLOOR_MULTIPLIER}
 asset['root']['artStyle']=REVISION
 return asset
