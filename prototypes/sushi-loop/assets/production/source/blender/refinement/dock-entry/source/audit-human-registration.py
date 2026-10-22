"""Resolve visible source humanoid foot contact separately from hidden attachments."""
import bpy,json,re,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1];original=B/'source/resources/original-library.blend';bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene
with bpy.data.libraries.load(str(original),link=False) as (a,b):b.collections=['S33_CHARACTER_customer_rosa.001'];b.actions=[n for n in a.actions if 'customer-rosa' in n]
c=bpy.data.collections['S33_CHARACTER_customer_rosa.001'];sc.collection.children.link(c);c.hide_viewport=False;c.hide_render=False
for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
def lookup(data,name):return data.get(name) or data.get(name+'.001') or next((o for o in data if re.sub(r'\.\d+$','',o.name)==re.sub(r'\.\d+$','',name)),None)
r=json.loads((B/'source/resources/frozen-neighbors/customer-rosa-rig.json').read_text())
for o in c.all_objects:
 if o.animation_data:
  o.animation_data.action=None
  for tr in o.animation_data.nla_tracks:tr.mute=True
for t in r['clips']['stand']['actions']:
 if t['ownerType']=='Object':owner=lookup(bpy.data.objects,t['ownerName'])
 elif t['ownerType']=='Key':owner=lookup(bpy.data.shape_keys,t['ownerName'])
 else:raise RuntimeError(t)
 act=lookup(bpy.data.actions,t['action']);owner.animation_data_create();owner.animation_data.action=act;slots=list(act.slots);slot=next((s for s in slots if s.identifier==t.get('slotIdentifier')),slots[0] if len(slots)==1 else None)
 if slot:owner.animation_data.action_slot=slot
root=next(o for o in c.objects if o.type=='EMPTY' and o.parent is None);root.location=(0,0,0);root.rotation_euler.z=0;sc.frame_set(12);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();out=[]
for o in c.all_objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(dg);m=e.to_mesh();vs=[e.matrix_world@v.co for v in m.vertices]
 out.append({'name':o.name,'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'visibleRenderMesh':not o.hide_render,'bounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]]});e.to_mesh_clear()
feet=[o for o in out if 'minimal_foot' in o['name']]
record={'sourceSHA256':hashlib.sha256(original.read_bytes()).hexdigest(),'cohort':'customer-rosa/stand','frame':12,'groundRoot':[0,0,0],'objects':out,'visibleFeet':feet,'actualSoleMinimumZ':min(o['bounds'][0][2] for o in feet),'actualFootWidthX':[min(o['bounds'][0][0] for o in feet),max(o['bounds'][1][0] for o in feet)],'actualFootDepthY':[min(o['bounds'][0][1] for o in feet),max(o['bounds'][1][1] for o in feet)],'correction':'Earlier aggregate minimum-.01875 came from a hidden knife_handle attachment with unevaluated identity transform, not a visible sole. Visible source Rosa foot contacts are exact nearZ0. Do not repeat the superseded sole-overlap diagnostic. All previous rendered images remain unchanged.','pathRegistration':'Human ground root translated to exact0/.0733333333/.1466666667/.22/.22 support values; same scale/all4facing transforms. This standing source is a scale/path reference; approved browser walking gait is separate.'}
(B/'candidates/round-05/human-registration-visibility-audit.json').write_text(json.dumps(record,indent=2));print(record['actualSoleMinimumZ'],record['actualFootWidthX'],record['actualFootDepthY'])
