"""Native compositor proof of the selected browser contrast, without lighting changes.
Create through Blender MCP; capture the saved isolated scene through Blender CLI.
"""
import bpy,json,hashlib,sys,importlib.util
from pathlib import Path
SAMPLES={'cobalt-crags':'ordinary35','pink-coral':'oblique70','wood-planter':'oblique70','pale-column':'ordinary35'}
FACTOR=1.35
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def core(path):
 spec=importlib.util.spec_from_file_location('s33_contrast_core',str(path));m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def compositor(scene):
 ng=bpy.data.node_groups.new(scene.name+' sRGB Contrast 135','CompositorNodeTree');ng.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');nodes=ng.nodes;links=ng.links
 source=nodes.new('CompositorNodeRLayers');source.scene=scene;source.label='Unchanged materials and lighting';source.location=(-900,0)
 straight=nodes.new('CompositorNodePremulKey');straight.inputs['Type'].default_value='To Straight';straight.label='Unpremultiply before grading';straight.location=(-680,0);links.new(source.outputs['Image'],straight.inputs['Image'])
 encode=nodes.new('CompositorNodeConvertColorSpace');encode.from_color_space='scene_linear';encode.to_color_space='sRGB';encode.label='Match browser sRGB';encode.location=(-460,0);links.new(straight.outputs['Image'],encode.inputs['Image'])
 split=nodes.new('CompositorNodeSeparateColor');split.mode='RGB';split.location=(-240,0);links.new(encode.outputs['Image'],split.inputs['Image'])
 combine=nodes.new('CompositorNodeCombineColor');combine.mode='RGB';combine.location=(200,0)
 for i,channel in enumerate(['Red','Green','Blue']):
  grade=nodes.new('ShaderNodeMath');grade.operation='MULTIPLY_ADD';grade.use_clamp=True;grade.inputs[1].default_value=FACTOR;grade.inputs[2].default_value=.5-.5*FACTOR;grade.label=f'{channel}: clamp(1.35 × c − 0.175)';grade.location=(-10,-i*160)
  links.new(split.outputs[channel],grade.inputs[0]);links.new(grade.outputs[0],combine.inputs[channel])
 links.new(source.outputs['Alpha'],combine.inputs['Alpha'])
 decode=nodes.new('CompositorNodeConvertColorSpace');decode.from_color_space='sRGB';decode.to_color_space='scene_linear';decode.label='Return to working linear space';decode.location=(420,0);links.new(combine.outputs['Image'],decode.inputs['Image'])
 premul=nodes.new('CompositorNodePremulKey');premul.inputs['Type'].default_value='To Premultiplied';premul.location=(640,0);links.new(decode.outputs['Image'],premul.inputs['Image'])
 output=nodes.new('NodeGroupOutput');output.location=(860,0);links.new(premul.outputs['Image'],output.inputs['Image'])
 ng['contrastFactor']=FACTOR;ng['displayChannelFormula']='clamp((c - 0.5) * 1.35 + 0.5, 0, 1)';ng['alphaPolicy']='Render Layers alpha bypasses RGB grading'
 scene.compositing_node_group=ng;scene.render.use_compositing=True;return ng

def create(out,core_path):
 out=Path(out);assert not out.exists();out.mkdir(parents=True)
 m=core(core_path);m.create(out/'authored')
 man=json.loads((out/'authored/study.json').read_text());scene=bpy.data.scenes[man['scene']]
 ng=compositor(scene);scene['contrast135']='Native sRGB compositor pass; no light/material changes'
 # Independent library snapshot; never save over the user's active project.
 bpy.data.libraries.write(str(out/'native-contrast.blend'),{scene},fake_user=True,compress=True)
 proof={'schemaVersion':1,'scene':scene.name,'nodeGroup':ng.name,'contrastFactor':FACTOR,'sourceHash':sha(__file__),'coreSourceSHA256':sha(core_path),'nativeProject':'native-contrast.blend','nativeProjectSHA256':sha(out/'native-contrast.blend'),'frameSize':m.FRAME,'root':m.ROOT,'sourceScale':m.SCALE,'cellSize':m.CELL,'samples':SAMPLES,'authoredManifest':'authored/study.json','captures':[]}
 (out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n');return {'scene':scene.name,'samples':len(SAMPLES),'project':str(out/'native-contrast.blend')}

def capture(out,core_path):
 out=Path(out);proof=json.loads((out/'proof.json').read_text());assert sha(out/proof['nativeProject'])==proof['nativeProjectSHA256'];assert sha(core_path)==proof['coreSourceSHA256']
 m=core(core_path);man=json.loads((out/proof['authoredManifest']).read_text());scene=bpy.data.scenes[proof['scene']];ng=bpy.data.node_groups[proof['nodeGroup']]
 with m.active(scene):
  m.settings(scene)
  for ident,profile in SAMPLES.items():
   item=next(o for o in man['objects'] if o['id']==ident)
   for facing in m.DIRS:
    m.pose(man,ident,facing);camera=m.camera(scene,profile)
    with m.capture_projection(bpy.data.collections[item['collection']],profile):
     geom=m.geometry(bpy.data.collections[item['collection']]);geometry_hash=hashlib.sha256(json.dumps(geom,sort_keys=True).encode()).hexdigest()
     images={}
     for grade in ['original','native135']:
      scene.compositing_node_group=ng if grade=='native135' else None
      path=f'sprites/{ident}/{facing}-{grade}.png';target=out/path;target.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(target);bpy.ops.render.render(write_still=True,scene=scene.name)
      images[grade]={'image':path,'sha256':sha(target)}
     proof['captures'].append({'id':ident,'facing':facing,'profile':profile,'camera':camera,'captureGeometrySHA256':geometry_hash,'images':images})
    print('CONTRAST_PROOF '+ident+'/'+facing,flush=True)
  scene.compositing_node_group=ng
 proof['status']='captured';(out/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
if __name__=='__main__' and '--capture' in sys.argv:
 i=sys.argv.index('--capture');capture(sys.argv[i+1],sys.argv[i+2])
