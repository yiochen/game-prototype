import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parent.parent;D=P/'candidates/rgb-seam-diagnostics';D.mkdir(exist_ok=True)
s=bpy.context.scene;G=bpy.data.collections['S33_PROP_uniform35-gate'];W=bpy.data.collections['S33_PROP_uniform35-wall-plain']
for o in G.objects:o.hide_render=True
W.hide_render=False;W.hide_viewport=False
for o in W.objects:o.hide_render=False
s.render.resolution_x=576;s.render.resolution_y=1344;s.camera.data.ortho_scale=1.5;s.camera.data.shift_y=.2696022093296051*3
p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.refresh_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.view_layers[0].update()
# Isolate reconstruction: native materials/geometry, camera, seed, samples and alpha filter stay fixed.
s.cycles.use_denoising=False;s.render.filepath=str(D/'wall-no-denoise.png');bpy.ops.render.render(write_still=True)
# Isolate ray-bevel normals while retaining the original denoiser.
s.cycles.use_denoising=True
for m in bpy.data.materials:
 if not m.use_nodes:continue
 for n in m.node_tree.nodes:
  if n.type=='BEVEL':
   for l in list(n.inputs['Radius'].links):m.node_tree.links.remove(l)
   n.inputs['Radius'].default_value=0
s.render.filepath=str(D/'wall-no-ray-bevel.png');bpy.ops.render.render(write_still=True)
print('DIAGNOSTIC_CAPTURES_COMPLETE')
