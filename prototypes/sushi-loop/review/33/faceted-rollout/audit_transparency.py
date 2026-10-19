"""Read active saved-source graph snapshots to verify transparent mixing.
The linked shader changes, but transparent node colors, mixing factors and
connections into the Mix Shader must remain identical. No Blender mutation.
"""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=json.loads((HERE/'audit-native-baseline.json').read_text());new=json.loads((HERE/'audit-native-faceted.json').read_text());report={'projectSHA256':new['projectSHA256'],'materials':{},'issues':[]}
for name,m in old['materials'].items():
 if not any(t in m['surfaceTypes'] for t in ('MIX_SHADER','BSDF_TRANSPARENT')):continue
 candidate=new['materials'][name];types=('MIX_SHADER','BSDF_TRANSPARENT');before={n:v for n,v in m['activeGraph']['nodes'].items() if v['type'] in types};after={n:v for n,v in candidate['activeGraph']['nodes'].items() if v['type'] in types};equal=before==after
 report['materials'][name]={'flatImageGen':m['flatImageGen'],'transparentNodesAndMixFactorsUnchanged':equal,'wholeFlatGraphUnchanged':m['activeGraphSHA256']==candidate['activeGraphSHA256'] if m['flatImageGen'] else None}
 if not equal:report['issues'].append(name+': changed transparency mixing')
 if m['flatImageGen'] and m['activeGraphSHA256']!=candidate['activeGraphSHA256']:report['issues'].append(name+': changed ImageGen shader graph')
report['passed']=not report['issues'];(HERE/'audit-transparency.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':report['passed'],'materials':len(report['materials']),'issues':report['issues']}))
if not report['passed']:sys.exit(1)
