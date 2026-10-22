"""Read-only exact food semantic field details using the portable audit definitions."""
from pathlib import Path
import json
P=Path(__file__).parent;script=P/'semantic_audit_round03.py';ns={'__file__':str(script),'__name__':'food_static_definitions'};exec(compile(script.read_text().split('start=time.time();sourcepath=')[0],str(script),'exec'),ns);rows={}
for rd in ['02','03']:
 sc,co,root,arm,asset=ns['select'](P/f'round-{rd}.blend');s=ns['semantic'](sc,co,root,arm);rows[rd]={'foodPlane':s['objects'][ns['FOOD']],'rootCustom':s['objects'][root.name]['custom'],'foodMaterial':s['materials'][ns['bpy'].data.objects[ns['FOOD']].data.materials[0].name]}
def diff(a,b,path=''):
 if type(a)!=type(b):return [{'field':path,'source':a,'candidate':b}]
 if isinstance(a,dict):return [z for k in set(a)|set(b) for z in (diff(a.get(k),b.get(k),path+'.'+k))]
 if isinstance(a,list):
  if a==b:return []
  return [{'field':path,'source':a,'candidate':b}]
 return [] if a==b else [{'field':path,'source':a,'candidate':b}]
report={'source':rows['02'],'candidate':rows['03'],'exactFieldChanges':diff(rows['02'],rows['03']),'notes':'Mesh automatic texture-space location/size derive from the authorized two top vertices; no explicit texture-space setting was assigned. Food material comparison excludes only image binding; exact image provenance is separately packed/SHA-verified.'};(P.parent/'candidates/round-03/food-native-records.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['exactFieldChanges'],indent=2))
