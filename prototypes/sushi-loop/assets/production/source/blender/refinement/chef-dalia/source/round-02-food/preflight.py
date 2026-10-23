import bpy,sys,json,math
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));sys.dont_write_bytecode=True
from common import *
rows_by_kind={}
for kind,path in [('source',P/'dependencies/approved-body.blend'),('candidate',BASE/'source/round-02.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));rows=[]
 for c in ['idle','work','hold','load']:
  for d in ['N','E','S','W']:
   for i in range(12):rows.append(phase(c,d,i))
 compact(OUT/f'{kind}-phases-preflight.json',rows);rows_by_kind[kind]=rows;print('PREFLIGHT_PHASES',kind,len(rows),flush=True)
compact(OUT/'source-phases.json',rows_by_kind['source'])
mp=json.loads((P/'dependencies/frozen-canonical-map.json').read_text());refs={(r['clip'],r['direction'],r['index']):r for r in mp['phaseMapping']}
def diff(a,b):
 if isinstance(a,list):return max((diff(x,y) for x,y in zip(a,b)),default=0)
 return abs(a-b)
errors=[];maxima={'cornerNative':0,'supportNative':0,'palmWorld':0,'boneWorld':0,'foodRootWorld':0};exact=0
for s,c in zip(rows_by_kind['source'],rows_by_kind['candidate']):
 ref=refs[c['clip'],c['direction'],c['index']];e={'cornerNative':diff(c['foodCornersNative'],ref['canonicalCornersProjectedNative']),'supportNative':diff(c['semanticSupportNative'],ref['semanticSupportProjectedNative']),'palmWorld':diff(c['palmMeanWorld'],s['palmMeanWorld']),'boneWorld':max(diff(c['boneMatricesWorld'][n],s['boneMatricesWorld'][n]) for n in c['boneMatricesWorld']),'foodRootWorld':diff(c['foodRootMatrix'],s['foodRootMatrix'])};physical=all(c['physicalGeometry'][n]['worldVerticesSHA256']==s['physicalGeometry'][n]['worldVerticesSHA256'] for n in c['physicalGeometry']);exact+=physical
 for k,v in e.items():maxima[k]=max(maxima[k],v)
 if not physical or any(v>(.001 if 'Native' in k else 1e-6) for k,v in e.items()) or s['visibility']!=c['visibility'] or not c['diagnosticVisibilityEvaluation']['allAuthoredVisibilityRestoredBeforeRender'] or not c['diagnosticVisibilityEvaluation']['allMuteStatesRestoredBeforeRender']:errors.append({'phase':[c['clip'],c['direction'],c['index']],'errors':e,'physicalExact':physical})
result={'ok':not errors,'phaseCount':192,'exactPhysicalPoseHashMatches':exact,'maxErrors':maxima,'errors':errors,'diagnosticPolicy':'Stable native owner list; authored visibility captured, only visibility curves temporarily muted and hidden owners tagged for data/time depsgraph evaluation. All mute states and authored visibility restored before captures. No source save or transform fitting.'};write(OUT/'mapping-preflight.json',result);print('PREFLIGHT_COMPLETE',result,flush=True)
assert result['ok'],result
