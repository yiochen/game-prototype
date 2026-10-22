import bpy,json,pathlib,math,hashlib
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=pathlib.Path(__file__).resolve().parent.parent;R=B/'reviews';O=R/'round01-native-replay';O.mkdir(exist_ok=True)
s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-corner-n-e.001'];root=next(o for o in c.all_objects if '__root.' in o.name);orient=next(o for o in c.all_objects if '__orientation.' in o.name);deck=next(o for o in c.all_objects if 'connected_turn_deck' in o.name)
root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();mat=deck.data.materials[0];action=mat.node_tree.animation_data.action;uv=[list(x.uv) for x in deck.data.uv_layers.active.data];vs=[list(v.co) for v in deck.data.vertices]
report={'project':bpy.data.filepath,'projectSHA256':hashlib.sha256(pathlib.Path(bpy.data.filepath).read_bytes()).hexdigest(),'scene':s.name,'collection':c.name,'root':root.name,'intrinsicOrientation':orient.rotation_euler.z,'objects':[],'phase':[],'ports':{},'replay':[],'images':[i.filepath for i in bpy.data.images],'libraries':[l.filepath for l in bpy.data.libraries]}
cam=s.camera;report['camera']={'matrix':[[float(v) for v in r] for r in cam.matrix_world],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'frame':[s.render.resolution_x,s.render.resolution_y],'pixelAspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y]}
for o in c.all_objects:
 if o.type!='MESH':continue
 ev=o.evaluated_get(dep);me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices];row={'name':o.name,'evaluatedVertices':len(pts),'bounds':[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]],'imageNodes':[n.image.filepath if n.image else None for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']}
 if 'stationary_' in o.name or o==deck:
  row['profiles']={}
  for name,axis in [('incoming',1),('outgoing',0)]:row['profiles'][name]={'points':[list(v) for v in pts if abs(v[axis]-.5)<1e-6],'capFaces':[f.index for f in me.polygons if all(abs(pts[i][axis]-.5)<1e-6 for i in f.vertices)]}
 report['objects'].append(row);ev.to_mesh_clear()
for i in range(25):s.frame_set(i+1);bpy.context.view_layer.update();report['phase'].append(float(mat.node_tree.nodes['Value'].outputs[0].default_value))
for d,r in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=r;bpy.context.view_layer.update();report['ports'][d]={}
 for n,pt in [('incoming',(0,.5,.64)),('outgoing',(.5,0,.64)),('deck',(0,0,.64))]:
  w=root.matrix_world@Vector(pt);p=world_to_camera_view(s,cam,w);report['ports'][d][n]={'world':list(w),'logical':[p.x*192-96,(1-p.y)*352-248]}
 for i in [0,24] if d in ['N','S'] else [11]:
  s.frame_set(i+1);bpy.context.view_layer.update();s.render.filepath=str(O/f'{d}-{i:02}.png');bpy.ops.render.render(write_still=True);report['replay'].append({'direction':d,'index':i,'path':str(O/f'{d}-{i:02}.png')})
bpy.ops.wm.open_mainfile(filepath=str(B/'source/resources/original-library.blend'));od=next(o for o in bpy.data.collections['S33_FB_belt-corner-n-e.001'].all_objects if 'connected_turn_deck' in o.name);report['originalUVExactlyEqual']=uv==[list(x.uv) for x in od.data.uv_layers.active.data];report['originalDeckVerticesExactlyEqual']=vs==[list(v.co) for v in od.data.vertices]
(R/'round01-native-independent.json').write_text(json.dumps(report,indent=2)+'\n');print('INDEPENDENT_NATIVE_COMPLETE')
