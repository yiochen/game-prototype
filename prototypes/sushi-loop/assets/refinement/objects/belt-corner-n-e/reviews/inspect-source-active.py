import bpy,json,pathlib,sys,math
from mathutils import Vector
out=pathlib.Path(__file__).parent
sys.path.insert(0,str(out.parents[5]/'production/source/blender'))
# Source helpers are read as native action evaluators only; the library is never saved.
sys.path.insert(0,str(pathlib.Path(bpy.data.filepath).parents[2]))
import native_actions
s=next(s for s in bpy.data.scenes if any(o.name.startswith('belt-corner-n-e__root') for o in s.objects))
c=bpy.data.collections['S33_FB_belt-corner-n-e.001']
s=bpy.data.scenes.new('Judge read-only native inspection')
s.collection.children.link(c)
bpy.context.window.scene=s
c.hide_viewport=False;c.hide_render=False
for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
for vl in s.view_layers:vl.update()
root=next(o for o in c.all_objects if '__root' in o.name)
record=json.loads((out.parent/'inputs/source-rig.json').read_text())
mat=bpy.data.materials['S33_belt-corner-n-e_moving_deck.001'];a=bpy.data.actions[record['clips']['running']['actions'][0]['action']]
curves=[{'path':f.data_path,'keys':[[float(k.co.x),float(k.co.y),k.interpolation] for k in f.keyframe_points],'evaluate':[float(f.evaluate(i)) for i in range(1,26)]} for f in native_actions._fcurves(a)]
native_actions._assign(mat.node_tree,a,record['clips']['running']['actions'][0]['slotIdentifier'])
res={'root':{'name':root.name,'matrix':[[float(v) for v in row] for row in root.matrix_world]},'objects':[],'phaseAction':{'name':a.name,'curves':curves},'phaseEvaluated':[]}
for o in c.all_objects:
 d={'name':o.name,'matrix':[[float(v) for v in row] for row in o.matrix_world],'localRotationZ':o.rotation_euler.z}
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices];d['worldBounds']=[[min(v[i] for v in pts) for i in range(3)],[max(v[i] for v in pts) for i in range(3)]]
 res['objects'].append(d)
for f in range(1,26):
 s.frame_set(f);bpy.context.view_layer.update();res['phaseEvaluated'].append({'frame':f,'value':mat.node_tree.nodes['Value'].outputs[0].default_value})
res['resourcesForThisObject']={'imageTextureNodes':[{'material':m.name,'node':n.name,'image':n.image.name if n.image else None} for o in c.all_objects if o.type=='MESH' for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE'],'linkedLibraries':[]}
(out/'native-source-active-inspection.json').write_text(json.dumps(res,indent=2))
print(json.dumps(res))
