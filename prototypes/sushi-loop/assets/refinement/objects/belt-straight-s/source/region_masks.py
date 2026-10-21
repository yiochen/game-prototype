import bpy,json,pathlib,math
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01/region-masks';O.mkdir(exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'));s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-straight-s.001'];root=next(o for o in c.objects if '__root.' in o.name)
colors={'deck':(0,0,1,1),'rail':(1,0,0,1),'honey-leg':(0,1,0,1),'honey-crossbeam':(0,1,1,1),'honey-sidebeam':(1,0,1,1),'foot-shoe':(1,1,0,1),'fastener':(1,1,1,1)};mats={}
for name,color in colors.items():
 m=bpy.data.materials.new('Diagnostic_'+name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=color;out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],out.inputs['Surface']);mats[name]=m
for o in c.objects:
 if o.type!='MESH':continue
 name=o.data.materials[0].name
 region='deck' if 'moving_deck' in name else 'rail' if 'CoralRail' in name else ('honey-crossbeam' if 'crossbeam' in o.name else 'honey-sidebeam' if 'sidebeam' in o.name else 'honey-leg') if 'HoneyWood' in name else 'foot-shoe' if 'WoodFoot' in name else 'fastener'
 o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(mats[region])
original=list(c.objects);groups=[]
for j in [-1,0,1]:
 if j==0:groups.append((j,root));continue
 mapping={}
 for o in original:q=o.copy();c.objects.link(q);mapping[o]=q
 for o,q in mapping.items():q.parent=mapping.get(o.parent,o.parent)
 groups.append((j,mapping[root]))
s.render.resolution_x=896;s.render.resolution_y=1216;s.camera.data.ortho_scale*=1216/704;s.camera.data.shift_y*=704/1216
records=[]
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 for j,r in groups:r.rotation_euler.z=angle;r.location=(0,-j,0) if d in ['N','S'] else (j,0,0)
 s.frame_set(1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update();p=O/f'native-material-regions-{d}.png';s.render.filepath=str(p);bpy.ops.render.render(write_still=True);records.append({'direction':d,'path':str(p)})
(O/'provenance.json').write_text(json.dumps({'method':'Native diagnostic material-ID render of actual candidate meshes, exact fixed sample/camera/geometry, assembled three-module route. Temporary flat emission categories only; never substituted for final art. Actual candidate graph unchanged on disk. All compatible N/E reference meshes share approved geometry, so same-flow region classes also label mixed triples.','colors':colors,'records':records},indent=2))
