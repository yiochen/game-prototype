import bpy,math,json,pathlib,bmesh
P=pathlib.Path(__file__).resolve().parents[1];R=P/'source/resources';O=P/'candidates/round-01';O.mkdir(parents=True,exist_ok=True);asset=P.name
bpy.ops.wm.open_mainfile(filepath=str(R/'approved-family.blend'));s=bpy.context.scene;family=bpy.data.collections['S33_FB_belt-straight-n.001']
with bpy.data.libraries.load(str(R/'original-library.blend'),link=False) as (a,b):
 b.collections=['S33_FB_'+asset+'.001'];b.actions=['S33_NATIVE__belt-end-w__running__Shader_Nodetree.001']
c=b.collections[0];s.collection.children.link(c);s.collection.children.unlink(family);c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
root=next(o for o in c.all_objects if '__root.' in o.name);orient=next(o for o in c.all_objects if '__orientation.' in o.name);deck=next(o for o in c.all_objects if 'connected_' in o.name);cap=next(o for o in c.all_objects if '_cap.' in o.name)
originalUV=[list(v.uv) for v in deck.data.uv_layers.active.data];familydeck=next(o for o in family.all_objects if 'connected_straight_deck' in o.name);m=familydeck.data.materials[0].copy();m.name='WarmSoft_NativeDirectedDeck';m.node_tree.animation_data_create();m.node_tree.animation_data.action=b.actions[0];m.node_tree.animation_data.action_slot=b.actions[0].slots[0]
for t in m.node_tree.animation_data.nla_tracks:t.mute=True
deck.data.materials.clear();deck.data.materials.append(m)
for o in list(c.objects):
 if o.type=='MESH' and o not in [deck,cap]:bpy.data.objects.remove(o,do_unlink=True)
for o in family.all_objects:
 if o.type!='MESH' or 'connected_' in o.name:continue
 q=o.copy();q.data=o.data.copy();q.name=o.name.replace('belt-straight-n',asset);c.objects.link(q);q.parent=orient
capmat=bpy.data.materials['WarmSoft_CoralRail'].copy();capmat.name='WarmSoft_CoralClosedTerminal';nt=capmat.node_tree;at=nt.nodes.new('ShaderNodeAttribute');at.attribute_name='RailSection';at.name='Native_cap_equivalent_section'
for n in list(nt.nodes):
 if n.type=='TEX_COORD':
  for l in list(nt.links):
   if l.from_node==n and l.from_socket.name=='Object':nt.links.new(at.outputs['Vector'],l.to_socket)
cap.data.materials.clear();cap.data.materials.append(capmat);section=cap.data.attributes.new('RailSection','FLOAT_VECTOR','POINT')
for v,d in zip(cap.data.vertices,section.data):d.vector=(v.co.y*.13/.08,0,v.co.z)
be=cap.modifiers.new('Family_terminal_soft_edges','BEVEL');be.width=.012;be.segments=4;be.harden_normals=True;wn=cap.modifiers.new('Family_terminal_weighted_normals','WEIGHTED_NORMAL');wn.keep_sharp=True
s.name='Registered_Native_Conveyor';s['asset_id']=asset;s['source_project_sha256']='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6';s['authored_child_orientation_radians']=float(orient.rotation_euler.z);s['native_phase_function']='-7*(frame-1)/24';s['nativeCaptureScale']=2;s['publishedSourceScale']=2
root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();assert originalUV==[list(x.uv) for x in deck.data.uv_layers.active.data]
keep=set(c.all_objects)|set(family.all_objects)|set(s.objects)
for sc in list(bpy.data.scenes):
 if sc!=s:bpy.data.scenes.remove(sc)
for o in list(bpy.data.objects):
 if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
for im in list(bpy.data.images):
 if im.users==0:bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'source/round-01.blend'))
recipe={'schemaVersion':1,'asset':asset,'method':'recipe-reuse','independentReview':False,'executable':'source/build-round01.py','nativeProject':'source/round-01.blend','portableInputs':['source/resources/original-library.blend','source/resources/approved-family.blend'],'methodDetail':'Exact approved straight family rail/support geometry,materials,camera,light,deterministic capture. Original4vertex deck/UV/native stored25key action and intrinsic preserved. Original functional terminal cap retained within native bounds; minor native edge softening and equivalent section mapping only.','nativeCaptureScale':2,'publishedSourceScale':2,'frame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,248],'nominalFunctionalHeight':.695,'physicalCapTop':.71939999,'footprint':[1,1]}
(P/'source/recipe-round01.json').write_text(json.dumps(recipe,indent=2));print(asset,'NATIVE_BUILD_READY')
