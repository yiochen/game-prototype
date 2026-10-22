from pathlib import Path
import shutil,json
E=Path(__file__).resolve().parents[2];ROOT=E.parent;AUD=json.loads((E/'source/conveyor-equivalence-audit.json').read_text())
for kind in ['start','end']:
 for facing in ['n','e','s','w']:
  asset=f'belt-{kind}-{facing}';P=ROOT/asset;S=P/'source'
  if (P/'candidates/round-01/packet.json').exists():continue
  R=S/'resources';R.mkdir(parents=True,exist_ok=True)
  for f in ['original-library.blend','approved-family.blend']:shutil.copyfile(E/'source/resources'/f,R/f)
  for f in ['source-camera.json','source-assetRecord.json','source-rig.json','catalog-object.json','family-settings.json','family-approval.json']:shutil.copyfile(P/'inputs'/f,R/f)
  row=next(x for x in AUD['rows'] if x['asset']==asset);(R/'native-equivalence.json').write_text(json.dumps(row,indent=2))
  text='''import bpy,math,json,pathlib,bmesh
P=pathlib.Path(__file__).resolve().parents[1];R=P/'source/resources';O=P/'candidates/round-01';O.mkdir(parents=True,exist_ok=True);asset=P.name
bpy.ops.wm.open_mainfile(filepath=str(R/'approved-family.blend'));s=bpy.context.scene;family=bpy.data.collections['S33_FB_belt-straight-n.001']
with bpy.data.libraries.load(str(R/'original-library.blend'),link=False) as (a,b):
 b.collections=['S33_FB_'+asset+'.001'];b.actions=['ACTION_NAME']
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
'''.replace('ACTION_NAME',row['authoredPhaseCurves'][0]['action'])
  (S/'build-round01.py').write_text(text)
  # The measured-port generic corner capture only needs one active native port for a terminal.
  text=(ROOT/'belt-corner-n-w/source/capture-round01.py').read_text().replace('belt-corner-n-w',asset).replace("if 'connected_turn_deck' in o.name","if 'connected_' in o.name")
  text=text.replace("for name in ['incoming','outgoing']:","for name in ['outgoing']:\n" if kind=='start' else "for name in ['incoming']:\n")
  # Remove nonfunctional capped side from exported open-port records/profiles.
  text=text.replace("basePorts=measured_ports();moduleSpecs=[]", "basePorts=measured_ports();basePorts={k:v for k,v in basePorts.items() if k=='"+('outgoing' if kind=='start' else 'incoming')+"'};moduleSpecs=[]")
  text=text.replace("fam2,fr2=clone_collection(fam,'Outgoing_approved_family'); c.hide_render=False", "fam2,fr2=clone_collection(fam,'Unused_secondary_family');fam2.hide_render=True; c.hide_render=False")
  text=text.replace("for co in [c,fam,fam2]", "for co in [c,fam]")
  text=text.replace("'clearance':{'deckHeight':.64,", "'clearance':{'deckHeight':.64,'nativeCapTop':.71939999,'supportMaxZ':.54,")
  text=text.replace("railmat=next(o for o in c.objects if 'outside_rail' in o.name).data.materials[0]","railmat=next(o for o in c.objects if '_cap.' in o.name).data.materials[0]")
  (S/'capture-round01.py').write_text(text)
  for f in ['package-round01.py','playback-evidence.py','replay-source.py']:
   shutil.copyfile(ROOT/'belt-corner-n-w/source'/f,S/f)
  text=(ROOT/'belt-corner-n-w/source/consumer-bench.jsx').read_text().replace('belt-corner-n-w',asset);(S/'consumer-bench.jsx').write_text(text);shutil.copyfile(E/'source/consumer-bench.html',S/'consumer-bench.html');shutil.copyfile(E/'source/batch/verify_native_template.py',S/'verify-native.py');(S/'quick-consumer.mjs').write_text((E/'source/batch/quick-consumer-template.mjs').read_text().replace('ASSET_ID',asset))
  print(asset,'PREPARED')
