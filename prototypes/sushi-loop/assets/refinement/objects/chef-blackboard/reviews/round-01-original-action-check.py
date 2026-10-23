import bpy,json
from pathlib import Path
p=Path(__file__).resolve().parent.parent
def curves(action):
 for la in action.layers:
  for st in la.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:yield fc
observed={ac.name:[{'path':f.data_path,'index':f.array_index,'keys':[[float(x.co.x),float(x.co.y),x.interpolation] for x in f.keyframe_points]} for f in curves(ac)] for ac in bpy.data.actions if ac.name.startswith('S33_NATIVE__chef-blackboard__')}
ref=json.loads((p/'source/resources/original-actions.json').read_text());assert observed==ref
result={'originalBlend':bpy.data.filepath,'original30ActionsExactBoundResource':observed==ref,'actionCount':len(observed)}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
