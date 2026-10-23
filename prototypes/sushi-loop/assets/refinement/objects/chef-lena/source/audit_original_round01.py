import bpy,json,sys
from pathlib import Path
P=Path(__file__).parent;sys.path.insert(0,str(P));import native_actions_round01 as native;from audit_common_round01 import contacts
coll=bpy.data.collections['S33_CHARACTER_chef_lena.002'];root=bpy.data.objects['chef_lena__ground_root.002'];arm=bpy.data.objects['chef_lena__armature.002'];rig=json.loads((P/'rig-round01.json').read_text());asset={'collection':coll,'root':root,'armature':arm}
sc=bpy.data.scenes.new('Lena original evaluated audit');bpy.context.window.scene=sc;sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update();rows=[]
for clip in rig['clips']:
 for d in ['N','E','S','W']:
  for f in range(1,13):
   native.apply_clip(asset,rig,clip,f,d,sc);rows.append({'clip':clip,'direction':d,'index':f-1,**contacts(coll,root,arm,bpy.context.evaluated_depsgraph_get())})
(P/'source-contacts-round01.json').write_text(json.dumps(rows,separators=(',',':')));print('ORIGINAL CONTACTS',len(rows))
