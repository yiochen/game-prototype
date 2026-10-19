"""Shared approved native art treatment, issue 33, 2026-10-19.
No world light direction: height-driven lower tone and camera-symmetric form.
The native sRGB contrast group grades RGB only and preserves alpha.
"""
import bpy, math, importlib.util
from pathlib import Path

REVISION='art-2026-10-19'

def ensure_compositor(scene):
    existing=scene.compositing_node_group
    if existing and existing.get('contrastFactor')==1.35:
        owners=[n.scene for n in existing.nodes if n.type=='R_LAYERS']
        if owners and all(owner==scene for owner in owners):return existing
        group=existing.copy()
        for node in group.nodes:
            if node.type=='R_LAYERS':node.scene=scene
        scene.compositing_node_group=group;scene.render.use_compositing=True;return group
    group=_compositor(scene)
    group.name='S33 approved sRGB contrast 135 '+scene.name
    return group

def _compositor(scene):
 ng=bpy.data.node_groups.new(scene.name+' sRGB Contrast 135','CompositorNodeTree');ng.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');nodes=ng.nodes;links=ng.links
 source=nodes.new('CompositorNodeRLayers');source.scene=scene;source.label='Unchanged materials and lighting';source.location=(-900,0)
 straight=nodes.new('CompositorNodePremulKey');straight.inputs['Type'].default_value='To Straight';straight.label='Unpremultiply before grading';straight.location=(-680,0);links.new(source.outputs['Image'],straight.inputs['Image'])
 encode=nodes.new('CompositorNodeConvertColorSpace');encode.from_color_space='scene_linear';encode.to_color_space='sRGB';encode.label='Match browser sRGB';encode.location=(-460,0);links.new(straight.outputs['Image'],encode.inputs['Image'])
 split=nodes.new('CompositorNodeSeparateColor');split.mode='RGB';split.location=(-240,0);links.new(encode.outputs['Image'],split.inputs['Image'])
 combine=nodes.new('CompositorNodeCombineColor');combine.mode='RGB';combine.location=(200,0)
 for i,channel in enumerate(['Red','Green','Blue']):
  grade=nodes.new('ShaderNodeMath');grade.operation='MULTIPLY_ADD';grade.use_clamp=True;grade.inputs[1].default_value=1.35;grade.inputs[2].default_value=.5-.5*1.35;grade.label=f'{channel}: clamp(1.35 × c − 0.175)';grade.location=(-10,-i*160)
  links.new(split.outputs[channel],grade.inputs[0]);links.new(grade.outputs[0],combine.inputs[channel])
 links.new(source.outputs['Alpha'],combine.inputs['Alpha'])
 decode=nodes.new('CompositorNodeConvertColorSpace');decode.from_color_space='sRGB';decode.to_color_space='scene_linear';decode.label='Return to working linear space';decode.location=(420,0);links.new(combine.outputs['Image'],decode.inputs['Image'])
 premul=nodes.new('CompositorNodePremulKey');premul.inputs['Type'].default_value='To Premultiplied';premul.location=(640,0);links.new(decode.outputs['Image'],premul.inputs['Image'])
 output=nodes.new('NodeGroupOutput');output.location=(860,0);links.new(premul.outputs['Image'],output.inputs['Image'])
 ng['contrastFactor']=1.35;ng['displayChannelFormula']='clamp((c - 0.5) * 1.35 + 0.5, 0, 1)';ng['alphaPolicy']='Render Layers alpha bypasses RGB grading'
 scene.compositing_node_group=ng;scene.render.use_compositing=True;return ng


def lower_material(material,asset_id,height,rock=False,floor=False):
    """Preserve procedural base-color graphs, including animated belt phases."""
    if material.get('s33ArtRevision')==REVISION:return material
    # Deck nodes carry animation recipe references; these materials are already
    # unique to an asset, so retain their identity. Other palette slots are copied.
    unique=asset_id in material.name
    m=material if unique else material.copy()
    if not unique:m.name=asset_id+' approved '+material.name
    m['s33ArtRevision']=REVISION;m['lowerTone']='world-Z ramp, no light direction'
    nodes=m.node_tree.nodes;links=m.node_tree.links
    output=next((n for n in nodes if n.type=='OUTPUT_MATERIAL'),None)
    if output is None:return m
    surface=output.inputs['Surface']
    source=surface.links[0].from_node if surface.is_linked else None
    if source and source.type=='EMISSION':
        # Concept assemblies already have the verified lower ramp and symmetric
        # normal treatment. They still receive the shared compositor grade.
        return m
    shader=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
    if shader is None:return m
    base=shader.inputs['Base Color']
    color=base.links[0].from_socket if base.is_linked else None
    constant=tuple(base.default_value)
    emit=nodes.new('ShaderNodeEmission');emit.label='Direction-free approved surface'
    links.new(emit.outputs[0],surface)
    alpha=shader.inputs.get('Alpha')
    if alpha and (alpha.is_linked or alpha.default_value<.999):
        transparent=nodes.new('ShaderNodeBsdfTransparent');blend=nodes.new('ShaderNodeMixShader')
        if alpha.is_linked:links.new(alpha.links[0].from_socket,blend.inputs[0])
        else:blend.inputs[0].default_value=alpha.default_value
        links.new(transparent.outputs[0],blend.inputs[1]);links.new(emit.outputs[0],blend.inputs[2]);links.new(blend.outputs[0],surface)
    if floor:
        if color:links.new(color,emit.inputs['Color'])
        else:emit.inputs['Color'].default_value=constant
        return m
    geom=nodes.new('ShaderNodeNewGeometry')
    xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(geom.outputs['Position'],xyz.inputs[0])
    span=nodes.new('ShaderNodeMapRange');span.clamp=True
    span.inputs['From Min'].default_value=0
    span.inputs['From Max'].default_value=max(.25,height)
    links.new(xyz.outputs['Z'],span.inputs['Value'])
    ramp=nodes.new('ShaderNodeValToRGB');ramp.label='Dark lower half → bright crown'
    low=.21 if rock else .42 if asset_id.startswith(('chef-','customer-')) else .37
    ramp.color_ramp.elements[0].color=(low,low*1.04,low*1.10,1)
    ramp.color_ramp.elements[1].position=.90
    ramp.color_ramp.elements[1].color=(1,1,1,1)
    links.new(span.outputs['Result'],ramp.inputs[0])
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
    if color:links.new(color,mix.inputs[1])
    else:mix.inputs[1].default_value=constant
    links.new(ramp.outputs['Color'],mix.inputs[2])
    dot=nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
    links.new(geom.outputs['Normal'],dot.inputs[0]);links.new(geom.outputs['Incoming'],dot.inputs[1])
    absolute=nodes.new('ShaderNodeMath');absolute.operation='ABSOLUTE';links.new(dot.outputs['Value'],absolute.inputs[0])
    gain=nodes.new('ShaderNodeMath');gain.operation='MULTIPLY_ADD';gain.inputs[1].default_value=.20;gain.inputs[2].default_value=.80;links.new(absolute.outputs[0],gain.inputs[0])
    tone=nodes.new('ShaderNodeMixRGB');tone.blend_type='MULTIPLY';tone.inputs[0].default_value=1
    links.new(mix.outputs[0],tone.inputs[1]);links.new(gain.outputs[0],tone.inputs[2]);links.new(tone.outputs[0],emit.inputs['Color'])
    return m

def apply(asset,aid):
    floor=aid.startswith('floor-') or aid=='dock-floor'
    rock=('rock' in aid or aid.startswith(('reef-','column-','slate-')))
    cache={}
    for obj in asset['collection'].all_objects:
        if obj.type!='MESH':continue
        for slot in obj.material_slots:
            if slot.material is None:continue
            old=slot.material
            if old.name not in cache:cache[old.name]=lower_material(old,aid,asset['height'],rock,floor)
            slot.material=cache[old.name]
    # Keep the original moving-deck phase node alive for the callback/baker.
    asset['artStyle']={'revision':REVISION,'contrast':1.35,'environmentHeightRatio':.7,'lowerTone':'native material height ramp','worldLighting':False}
    asset['root']['artStyle']=REVISION
    return asset
