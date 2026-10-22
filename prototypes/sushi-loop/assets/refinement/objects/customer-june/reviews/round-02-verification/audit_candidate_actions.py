import bpy,json,hashlib,importlib.util,sys
sys.dont_write_bytecode=True
from pathlib import Path
P=Path(__file__).parent;O=P.parents[1];RUNTIME='runtime' in bpy.data.filepath;mode='runtime' if RUNTIME else 'main';root=O.parents[5]
record=json.loads((O/('inputs/runtime-variants/export/source/customer-june/rig.json' if RUNTIME else 'inputs/source-rig.json')).read_text());path=O/'inputs/runtime-variants/external/assets/production/source/blender/native_actions.py' if RUNTIME else root/'prototypes/sushi-loop/assets/production/source/blender/native_actions.py'
spec=importlib.util.spec_from_file_location('n',path);n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
rows=[]
for clip,c in record['clips'].items():
 for target in c['actions']:
  a=bpy.data.actions[target['action']];owner=n._resolve_owner(target);curves=[{'path':f.data_path,'index':f.array_index,'extrapolation':f.extrapolation,'keys':[{'co':list(k.co),'interpolation':k.interpolation,'handleLeft':list(k.handle_left),'handleRight':list(k.handle_right),'handleLeftType':k.handle_left_type,'handleRightType':k.handle_right_type} for k in f.keyframe_points]} for f in n._fcurves(a)]
  payload=json.dumps(curves,sort_keys=True,separators=(',',':')).encode();rows.append({'clip':clip,'owner':owner.name,'action':a.name,'ownerType':target['ownerType'],'slot':target.get('slotIdentifier'),'curveCount':len(curves),'keyCount':sum(len(f['keys']) for f in curves),'sha256':hashlib.sha256(payload).hexdigest(),'curves':curves})
(P/(mode+'-native-action-baseline.json')).write_text(json.dumps(rows,separators=(',',':'))+'\n')
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE' and 'customer_june' in o.name)
(P/(mode+'-rig-constraint-baseline.json')).write_text(json.dumps({'armature':arm.name,'constraints':[{'bone':b.name,'constraints':[{'name':c.name,'type':c.type,'mute':c.mute,'influence':c.influence} for c in b.constraints]} for b in arm.pose.bones],'drivers':[{'owner':o.name,'path':f.data_path,'index':f.array_index,'expression':f.driver.expression} for o in bpy.data.objects if 'customer_june' in o.name and o.animation_data for f in o.animation_data.drivers]},indent=2)+'\n')
print(mode,'owners',len(rows),'curves',sum(x['curveCount'] for x in rows),'keys',sum(x['keyCount'] for x in rows))
