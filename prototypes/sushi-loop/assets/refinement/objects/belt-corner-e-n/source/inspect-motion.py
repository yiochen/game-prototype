import bpy,json,pathlib
p=pathlib.Path(__file__).parent;c=bpy.data.collections['S33_FB_belt-corner-e-n.001'];d=next(o for o in c.objects if 'connected_turn_deck' in o.name);m=d.data.materials[0]
def anim(a):
 if not a:return None
 return {'action':a.action.name if a.action else None,'tracks':[(t.name,[(s.name,s.action.name if s.action else None) for s in t.strips]) for t in a.nla_tracks]}
out={'deck':d.name,'material':m.name,'nodeAnim':anim(m.node_tree.animation_data),'materialAnim':anim(m.animation_data),'nodes':[(n.name,n.type,n.label) for n in m.node_tree.nodes],'actions':[(a.name,len(a.slots)) for a in bpy.data.actions if 'corner-e-n' in a.name]}
print(json.dumps(out,indent=2));(p/'motion-inspection.json').write_text(json.dumps(out,indent=2))
