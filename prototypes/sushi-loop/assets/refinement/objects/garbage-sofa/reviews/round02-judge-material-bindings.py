import bpy,json,pathlib,hashlib
O=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-sofa');R=O/'reviews';P=pathlib.Path(bpy.data.filepath)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
start=sha(P);c=bpy.data.collections['S33_PROP_garbage-sofa'];rows=[]
for ob in c.all_objects:
 if ob.type not in ('MESH','CURVE'):continue
 rows.append({'object':ob.name,'parent':ob.parent.name if ob.parent else None,'materialSlots':[{'material':slot.material.name,'coordinates':[{'node':n.name,'type':n.type,'object':n.object.name if n.object else None}for n in slot.material.node_tree.nodes if n.type=='TEX_COORD'],'principledAlpha':[float(n.inputs['Alpha'].default_value)for n in slot.material.node_tree.nodes if n.type=='BSDF_PRINCIPLED']}for slot in ob.material_slots if slot.material and slot.material.use_nodes]})
out={'project':str(P.relative_to(O)),'projectSHA256':start,'packetSHA256':sha(O/'candidates/round-02/packet.json'),'geometryMaterialBindings':rows,'sceneObjectsOutsideAsset':[{'name':ob.name,'type':ob.type,'hideRender':ob.hide_render}for ob in bpy.context.scene.objects if ob not in set(c.all_objects)],'sourceUnchanged':sha(P)==start}
(R/'round02-judge-material-bindings.json').write_text(json.dumps(out,indent=2)+'\n');print('MATERIAL_BINDINGS',len(rows),'unchanged',out['sourceUnchanged'])
