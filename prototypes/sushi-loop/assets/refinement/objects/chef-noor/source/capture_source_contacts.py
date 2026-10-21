import bpy,json,sys
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round01 as native
from audit_common_round01 import contacts
rig=json.loads((P/'rig-round01.json').read_text());root=bpy.data.objects[rig['groundRootObject']];coll=next(c for c in root.users_collection if 'CHARACTER' in c.name);arm=next(o for o in coll.all_objects if o.type=='ARMATURE');sc=bpy.data.scenes.new('Noor original contact audit');bpy.context.window.scene=sc;sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update();asset={'collection':coll,'root':root,'armature':arm};rows=[]
for c in rig['clips']:
 for d in ['N','E','S','W']:
  for i in range(12):
   native.apply_clip(asset,rig,c,i+1,d,sc);ct=contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get());ct.update(clip=c,direction=d,index=i);rows.append(ct)
(P/'source-contacts-round01.json').write_text(json.dumps(rows,separators=(',',':')));print('CONTACTS',len(rows))
