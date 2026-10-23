"""Portable helpers for Omar canonical-food v3; never imports production code."""
from pathlib import Path
import bpy,json,math,hashlib,sys,re
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));import native_actions_round02 as native
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def config(runtime=False):return json.loads((P/('runtime-config-round02.json' if runtime else 'config-round02.json')).read_text())
def setup(c):
 sc=bpy.data.scenes[c['scene']];bpy.context.window.scene=sc;bpy.context.window.view_layer=sc.view_layers[0]
 co=bpy.data.collections[c['collection']];co.hide_render=False;co.hide_viewport=False
 root=bpy.data.objects[c['root']];arm=bpy.data.objects[c['armature']];bpy.context.view_layer.update()
 rig=json.loads((P/c['rig']).read_text());asset={'root':root,'collection':co,'armature':arm}
 plane=next(o for o in co.all_objects if '__image_plane' in o.name)
 return sc,co,root,arm,rig,asset,plane
def px(sc,v):
 v=world_to_camera_view(sc,sc.camera,Vector(v));return np.array([v.x*sc.render.resolution_x,(1-v.y)*sc.render.resolution_y],dtype=np.float64)
def ray(sc):return (sc.camera.matrix_world.to_3x3()@Vector((0,0,1))).normalized()
def coeffs(plane,root):
 fc=next(f for f in plane.animation_data.drivers if f.data_path=='location' and f.array_index==0)
 coefficient=float(re.findall(r'[0-9]+\.[0-9]+',fc.driver.expression)[-1]);z=float(plane.location.z)
 scale=float(root.scale.x);return coefficient,z,math.hypot(coefficient,z)*scale
def image_node(plane):return next(n for n in plane.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE')
def canonicalize(c,plane):
 path=P/c['canonical'];assert sha(path)==c['canonicalSHA256']
 node=image_node(plane);old=node.image;im=bpy.data.images.load(str(path),check_existing=False)
 im.alpha_mode=old.alpha_mode;im.colorspace_settings.name=old.colorspace_settings.name
 im.pack();im.filepath='//round-02-resources/'+path.name;node.image=im
 width=float(plane.data.vertices[1].co.x-plane.data.vertices[0].co.x);height=width*c['canonicalSize'][1]/c['canonicalSize'][0]
 for v,co in zip(plane.data.vertices,[(-width/2,0,0),(width/2,0,0),(width/2,height,0),(-width/2,height,0)]):v.co=co
 uv=plane.data.uv_layers.active
 for poly in plane.data.polygons:
  for i in poly.loop_indices:uv.data[i].uv=[(0,0),(1,0),(1,1),(0,1)][plane.data.loops[i].vertex_index]
 plane.data.update();return width,height,im
def install_law(plane,root,dmin,coefficient,z,d0):
 ratio=f'(1-(1-{dmin:.17g}/{d0:.17g})*max(0,-cos(facing))**2)'
 expressions=[f'-sin(facing)*{coefficient:.17g}*{ratio}',f'-cos(facing)*{coefficient:.17g}*{ratio}',f'{z:.17g}*{ratio}']
 for axis,expression in enumerate(expressions):
  fc=next((f for f in plane.animation_data.drivers if f.data_path=='location' and f.array_index==axis),None)
  if fc is None:
   fc=plane.driver_add('location',axis);v=fc.driver.variables.new();v.name='facing';v.type='SINGLE_PROP';v.targets[0].id=root;v.targets[0].data_path='rotation_euler[2]'
  fc.driver.expression=expression
  while fc.keyframe_points:fc.keyframe_points.remove(fc.keyframe_points[0],fast=True)
  for m in list(fc.modifiers):fc.modifiers.remove(m)
  m=fc.modifiers.new('GENERATOR');m.mode='POLYNOMIAL';m.poly_order=1;m.coefficients=(0,1);m.use_additive=False
  fc.extrapolation='LINEAR'
 bpy.context.view_layer.update();return expressions
def enable_saved_device(sc):
 # Device preference selection only; saved scene renderer/settings remain untouched.
 if sc.render.engine=='CYCLES' and sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.refresh_devices()
  for d in prefs.devices:d.use=d.type=='METAL'
def save_library(path,sc,rig):
 ids={sc}|{bpy.data.actions[t['action']] for r in rig['clips'].values() for t in r['actions']}
 bpy.data.libraries.write(str(path),ids,fake_user=True,compress=True)
def quad_state(sc,plane):
 e=plane.evaluated_get(bpy.context.evaluated_depsgraph_get());corners=[e.matrix_world@v.co for v in e.data.vertices]
 bottom=(corners[0]+corners[1])*.5
 return {'world':np.array(corners,dtype=np.float64),'projected':np.array([px(sc,v) for v in corners]),'bottomWorld':np.array(bottom,dtype=np.float64),'bottomPixel':px(sc,bottom),'matrix':np.array(e.matrix_world,dtype=np.float64),'location':np.array(e.location,dtype=np.float64),'visible':not plane.hide_render}
def evaluated_food_transform(sc,plane,sampler=None):
 # Native idle/work keys cull the plane from the viewport as well as the render.
 # Temporarily evaluate its transform in the viewport, never changing render visibility,
 # controllers, saved bytes or native render state. Restore before any rendering.
 viewport=plane.hide_viewport;hidden=plane.hide_get()
 if viewport or hidden:
  plane.hide_viewport=False;plane.hide_set(False);plane.update_tag();bpy.context.view_layer.update()
 q=sampler() if sampler else quad_state(sc,plane)
 if viewport or hidden:
  plane.hide_viewport=viewport;plane.hide_set(hidden);plane.update_tag();bpy.context.view_layer.update()
 q['viewportEvaluationForced']=viewport or hidden
 return q
