import bpy,json,math,pathlib
from mathutils import Vector
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
bpy.ops.wm.open_mainfile(filepath=str(P/'source/round-01.blend'))
s=bpy.context.scene;c=bpy.data.collections['S33_FB_belt-straight-w.001'];c.hide_render=False;c.hide_viewport=False
def unhide(l):
 l.exclude=False;l.hide_viewport=False
 for x in l.children:unhide(x)
unhide(bpy.context.view_layer.layer_collection)
for o in c.all_objects:o.hide_set(False);o.hide_viewport=False;o.hide_render=False
root=next(o for o in c.objects if '__root.' in o.name);orient=next(o for o in c.objects if '__orientation.' in o.name);deck=next(o for o in c.objects if 'connected_straight_deck' in o.name)
root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();bpy.context.evaluated_depsgraph_get().update()
records=[]
for o in c.objects:
 if o.type!='MESH':continue
 pts=[v.co for v in o.data.vertices]
 bounds=[[min(v[k] for v in pts),max(v[k] for v in pts)] for k in range(3)]
 records.append({'name':o.name,'parent':o.parent.name,'objectLocalBoundsXYZ':bounds,'matrixLocal':[list(r) for r in o.matrix_local],'matrixWorld':[list(r) for r in o.matrix_world],'generatedCoordinateBasis':'Blender default per-mesh native Object coordinates, local units rather than normalized Generated bounds; no named object reference.','coordinateNodes':[{'material':m.name,'node':n.name,'type':n.bl_idname,'object':n.object.name if n.object else None,'linkedOutputs':[l.from_socket.name for l in m.node_tree.links if l.from_node==n]} for m in o.data.materials for n in m.node_tree.nodes if n.type=='TEX_COORD']})
rails=[r for r in records if 'stationary_rail' in r['name']]
checks={'WIntrinsicRotationMinus90':abs(orient.rotation_euler.z+math.pi/2)<1e-6,'nativeRailTransverseXPlusMinus065':all(abs(r['objectLocalBoundsXYZ'][0][0]+.065)<1e-6 and abs(r['objectLocalBoundsXYZ'][0][1]-.065)<1e-6 for r in rails),'nativeRailLocalZPlusMinus095':all(abs(r['objectLocalBoundsXYZ'][2][0]+.095)<1e-6 and abs(r['objectLocalBoundsXYZ'][2][1]-.095)<1e-6 for r in rails),'nativeRailLongitudinalYPlusMinusHalf':all(abs(r['objectLocalBoundsXYZ'][1][0]+.5)<1e-6 and abs(r['objectLocalBoundsXYZ'][1][1]-.5)<1e-6 for r in rails),'allPerMeshCoordinatesUnboundFromExternalObjects':all(n['object'] is None for r in records for n in r['coordinateNodes'])}
uv=[{'localVertex':list(deck.data.vertices[l.vertex_index].co),'worldVertex':list(deck.matrix_world@deck.data.vertices[l.vertex_index].co),'uv':list(deck.data.uv_layers.active.data[l.index].uv)} for l in deck.data.loops]
out={'asset':'belt-straight-w','source':'source/round-01.blend reopened in Blender5.2.2; all hide/exclude flags cleared and depsgraph evaluated','root':root.name,'orientation':orient.name,'intrinsicRotationRadians':orient.rotation_euler.z,'perMeshBasis':records,'deckUVVertexAssociations':uv,'checks':checks,'meaning':'These actual candidate local axes/bounds and hierarchy establish the common procedural coordinate basis. Graph equivalence is independently recorded by native-audit.json. No view-specific transforms/material corrections are used.'}
(O/'coordinate-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(checks)
