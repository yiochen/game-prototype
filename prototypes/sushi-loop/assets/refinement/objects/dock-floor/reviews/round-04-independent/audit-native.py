import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
R=Path(__file__).resolve().parent;O=R.parents[1];C=O/'candidates/round-04';F=O/'source/round-04.blend';E=O/'inputs/paired-native/dock-entry-round-06.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def plain(x):
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 try:return list(x)
 except:return str(x)
def capture_state():
 s=bpy.context.scene;c=s.camera
 return {'scene':s.name,'cameraName':c.name,'worldMatrix':[list(x) for x in c.matrix_world],'orthoScale':c.data.ortho_scale,'shift':[c.data.shift_x,c.data.shift_y],'renderFrame':[s.render.resolution_x,s.render.resolution_y],'resolutionPercentage':s.render.resolution_percentage,'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'filterSize':s.render.filter_size,'engine':s.render.engine,'samples':s.eevee.taa_render_samples,'fps':s.render.fps,'fpsBase':s.render.fps_base,'frameRange':[s.frame_start,s.frame_end],'filmTransparent':s.render.film_transparent,'colorMode':s.render.image_settings.color_mode,'viewTransform':s.view_settings.view_transform,'compositor':s.compositing_node_group.name if s.compositing_node_group else None}
def inspect(col,root):
 dg=bpy.context.evaluated_depsgraph_get();objs=[];materials={}
 for o in col.all_objects:
  r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'hideRender':o.hide_render,'matrixWorld':[list(x) for x in o.matrix_world],'scale':list(o.scale),'constraints':[c.type for c in o.constraints],'modifiers':[m.type for m in o.modifiers],'actions':o.animation_data.action.name if o.animation_data and o.animation_data.action else None,'materials':[s.material.name if s.material else None for s in o.material_slots]}
  if o.type=='MESH':
   e=o.evaluated_get(dg);m=e.to_mesh();v=[e.matrix_world@x.co for x in m.vertices];r.update(vertices=[list(x) for x in v],polygons=[{'vertices':list(p.vertices),'normal':list((e.matrix_world.to_3x3().inverted().transposed()@p.normal).normalized()),'materialIndex':p.material_index} for p in m.polygons],bounds=[[min(x[i] for x in v) for i in range(3)],[max(x[i] for x in v) for i in range(3)]]);e.to_mesh_clear()
  objs.append(r)
  for sl in o.material_slots:
   m=sl.material
   if not m or m.name in materials:continue
   materials[m.name]={'nodes':[{'name':n.name,'type':n.type,'image':n.image.name if hasattr(n,'image') and n.image else None,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')},'inputLinks':{i.name:[{'node':l.from_node.name,'socket':l.from_socket.name} for l in i.links] for i in n.inputs if i.is_linked}} for n in m.node_tree.nodes] if m.node_tree else []}
 v=[p for o in objs if o['type']=='MESH' and not o['hideRender'] for p in o['vertices']]
 return {'root':root.name,'rootMatrix':[list(x) for x in root.matrix_world],'rootProperties':{k:plain(root[k]) for k in root.keys()},'collection':col.name,'objects':objs,'bounds':[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]],'materials':materials,'images':[{'name':i.name,'filepath':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images]}
report={'floorSourceSHA256':sha(F),'entrySourceSHA256':sha(E),'blender':bpy.app.version_string,'method':'Independent reopen source before companion append; full evaluated native geometry/materials and persisted capture state. No source saved. Direct standalone/pair renders retained in review output.'}
bpy.ops.wm.open_mainfile(filepath=str(E));sc=bpy.context.scene;er=bpy.data.objects['dock-entry__root'];er.rotation_euler=(0,0,0);bpy.context.view_layer.update();report['entryStandaloneCaptureState']=capture_state();report['entryStandalone']=inspect(bpy.data.collections['S33_PROP_dock-entry'],er)
bpy.ops.wm.open_mainfile(filepath=str(F));sc=bpy.context.scene;fr=bpy.data.objects['dock-floor__root'];report['floorSavedCaptureState']=capture_state();report['floorSavedRootMatrix']=[list(x) for x in fr.matrix_world];fr.rotation_euler=(0,0,0);bpy.context.view_layer.update();report['floorStandalone']=inspect(bpy.data.collections['WarmSoft_dock-floor'],fr);report['lights']=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'position':list(o.matrix_world.translation),'color':list(o.data.color),'useShadow':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT']
def px(v):
 p=world_to_camera_view(sc,sc.camera,Vector(v));return[p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y]
base=px((0,0,0));report['calibrationNative']={'root':base,**{k:[a-b for a,b in zip(px(v),base)] for k,v in [('unitX',(1,0,0)),('unitDepth',(0,-1,0)),('unitHeight',(0,0,1))]}}
report['standaloneReplays']=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 fr.rotation_euler.z=a;bpy.context.view_layer.update();p=R/f'own-standalone-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);report['standaloneReplays'].append({'facing':d,'path':p.name,'sha256':sha(p),'candidateSHA256':sha(C/f'frames/static-{d}/000.png'),'byteIdentical':sha(p)==sha(C/f'frames/static-{d}/000.png'),'rootMatrix':[list(x) for x in fr.matrix_world]})
fr.rotation_euler=(0,0,0)
with bpy.data.libraries.load(str(E),link=False) as (src,dst):dst.collections=['S33_PROP_dock-entry']
ec=dst.collections[0];sc.collection.children.link(ec);ec.hide_render=False;ec.hide_viewport=False;er=bpy.data.objects['dock-entry__root'];er.rotation_euler=(0,0,0);er.location=(0,-1.5,0);bpy.context.view_layer.update();report['pairedEntry']=inspect(ec,er)
sc.render.resolution_x=1152;sc.render.resolution_y=1280;sc.camera.data.ortho_scale=576/128;sc.camera.data.shift_x=0;sc.camera.data.shift_y=0;bpy.context.view_layer.update();b=px((0,0,0));sc.camera.data.shift_y=1;bpy.context.view_layer.update();dy=px((0,0,0))[1]-b[1];sc.camera.data.shift_y=(704-b[1])/dy;bpy.context.view_layer.update();report['pairCaptureState']=capture_state();report['pairReplays']=[]
for d,a in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 fr.rotation_euler.z=a;er.rotation_euler.z=a;er.location=Matrix.Rotation(a,3,'Z')@Vector((0,-1.5,0));bpy.context.view_layer.update();p=R/f'own-native-pair-{d}.png';sc.render.filepath=str(p);bpy.ops.render.render(write_still=True);report['pairReplays'].append({'facing':d,'path':p.name,'sha256':sha(p),'candidateSHA256':sha(C/f'native-pair-{d}.png'),'byteIdentical':sha(p)==sha(C/f'native-pair-{d}.png'),'floorMatrix':[list(x) for x in fr.matrix_world],'entryMatrix':[list(x) for x in er.matrix_world]})
report['sourceBytesUnchanged']={'floor':sha(F)==report['floorSourceSHA256'],'entry':sha(E)==report['entrySourceSHA256']};(R/'own-native-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('OWN_AUDIT_COMPLETE',json.dumps({'standaloneIdentical':[x['byteIdentical'] for x in report['standaloneReplays']],'pairedIdentical':[x['byteIdentical'] for x in report['pairReplays']],'unchanged':report['sourceBytesUnchanged']}))
