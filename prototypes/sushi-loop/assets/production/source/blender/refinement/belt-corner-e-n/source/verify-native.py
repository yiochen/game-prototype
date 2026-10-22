import bpy,pathlib,json,hashlib,math
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01';bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'));s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-corner-e-n.001'];deck=next(o for o in c.objects if 'connected_turn_deck' in o.name)
candidateUV=[list(x.uv) for x in deck.data.uv_layers.active.data];candidateVertices=[list(x.co) for x in deck.data.vertices]
act=deck.data.materials[0].node_tree.animation_data.action;actionName=act.name;owner={'material':deck.data.materials[0].name,'nodeTree':deck.data.materials[0].node_tree.name,'slot':deck.data.materials[0].node_tree.animation_data.action_slot.identifier};curves=[]
for layer in act.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for f in bag.fcurves:curves.append({'dataPath':f.data_path,'keys':[{'frame':k.co.x,'value':k.co.y,'interpolation':k.interpolation} for k in f.keyframe_points]})
root=next(o for o in c.objects if '__root.' in o.name);root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();centers=[]
for i in range(49):centers.append((deck.data.vertices[2*i].co+deck.data.vertices[2*i+1].co)/2)
finite={'incoming':list((centers[-2]-centers[-1]).normalized()),'outgoing':list((centers[0]-centers[1]).normalized())}
# Inspect original source in an independent reopened file, without resaving it.
bpy.ops.wm.open_mainfile(filepath=str(P/'source/resources/original-library.blend'));orig=bpy.data.collections['S33_FB_belt-corner-e-n.001'];od=next(o for o in orig.objects if 'connected_turn_deck' in o.name)
uv=[list(x.uv) for x in od.data.uv_layers.active.data];vs=[list(x.co) for x in od.data.vertices]
report={'asset':'belt-corner-e-n','originalSourceSHA256':hashlib.sha256((P/'source/resources/original-library.blend').read_bytes()).hexdigest(),'candidateProjectSHA256':hashlib.sha256((P/'source/round-01.blend').read_bytes()).hexdigest(),'deckVerticesExactlyEqual':candidateVertices==vs,'curvedUVExactlyEqual':candidateUV==uv,'nativeAction':actionName,'actualActionOwner':owner,'originalSourceActionState':'Stored native action exists but original material has no bound action or NLA. Candidate binds that exact original action to the copied approved family deck material.','curves':curves,'centerlineDiscreteEndpointTangents':finite,'tangentInterpretation':'Measured polygon centerline chords deviate by0.9375degrees because48segments sample a true quarter circle; both original/candidate native mesh are exactly equal. Analytic original endpoint tangent incoming(-1,0),outgoing(0,1).','originalAngularLaw':'u=1-[q*pi/4+(1-pi/4)*(3*q*q-2*q*q*q)], angular q0 outgoing1 q1 incoming0; E-to-N; du/ds=1 at centerline endpoints. Deck radial compression preserved.','phaseSamples':curves[0]['keys'],'originalUVSHA256':hashlib.sha256(json.dumps(uv).encode()).hexdigest(),'candidateUVSHA256':hashlib.sha256(json.dumps(candidateUV).encode()).hexdigest(),'nativeTextureInventory':[],'nativeLibraryInventory':[]}
(O/'source-contract.json').write_text(json.dumps(report,indent=2));assert report['deckVerticesExactlyEqual'] and report['curvedUVExactlyEqual'];print('NATIVE_CONTRACT_READY')
