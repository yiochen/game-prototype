import bpy,json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;OUT=P.parent/'candidates/round-05';sys.path.insert(0,str(P));from semantic_round05 import props,compare,PLANE
plane=bpy.data.objects[PLANE];me=plane.data
report={'properties':props(me),'attributes':{a.name:{'props':props(a),'data':[props(v) for v in a.data]} for a in me.attributes},'vertices':[list(v.co) for v in me.vertices],'uv':[list(x.uv) for x in me.uv_layers.active.data]}
if '--baseline' in sys.argv:(OUT/'approved04-plane-details.json').write_text(json.dumps(report,separators=(',',':')))
else:
 baseline=json.loads((OUT/'approved04-plane-details.json').read_text());delta=compare(baseline,report);allowed=['/properties/texspace_location/1','/properties/texspace_size/1','/vertices/2/1','/vertices/3/1','/uv/','/attributes/position/data/2/vector/1','/attributes/position/data/3/vector/1','/attributes/'+me.uv_layers.active.name+'/data/'];unexpected=[x for x in delta if not any(x[0].startswith(y) for y in allowed)];assert not unexpected,unexpected
 (OUT/'food-plane-allowed-delta.json').write_text(json.dumps({'ok':True,'baseline':baseline,'candidate':report,'delta':delta,'unexpected':unexpected,'interpretation':'Exactly top two vertices height, fullUV and generated position/UV attributes plus automatic texture-space Y midpoint/extent. Lower edge and X/Z stay identical.'},indent=2))
 print('EXPLICIT_PLANE_DELTA',len(delta),'allowed',flush=True)
