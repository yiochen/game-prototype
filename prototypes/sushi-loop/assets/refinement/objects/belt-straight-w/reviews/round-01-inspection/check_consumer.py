import json,time,hashlib
from pathlib import Path
from collections import defaultdict
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parent;EXP=OUT.parents[1];C=EXP/'candidates/round-01'
start=time.time();report={'groups':{},'failures':[]};domains={}
for name in ('consumer-metrics.json','floor-consumer-metrics.json'):
    d=json.loads((C/name).read_text());summary={};covered=defaultdict(set);closures={};unique=defaultdict(set)
    for row in d['pairs']:
        a=np.array(Image.open(EXP/row['current']).convert('RGBA'),dtype=np.int16);b=np.array(Image.open(EXP/row['reference']).convert('RGBA'),dtype=np.int16);delta=np.abs(a-b)
        mx=delta.max(axis=(0,1)).tolist();mask=delta[:,:,:3].max(axis=2)>1;ys,xs=np.where(mask);bounds=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)] if len(xs) else None
        for field,value in [('fullMaxRGBA',mx),('fullResidualPixelsOver1',int(mask.sum())),('fullResidualBoundsOver1',bounds)]:
            if row[field]!=value:report['failures'].append({'context':(name,row['pattern'],row['direction'],row['index'],row['pitch'],row['context'],row['background']),'field':field,'actual':value,'expected':row[field]})
        key=str(row['pitch']);s=summary.setdefault(key,{'pairs':0,'fullMaxRGBA':[0,0,0,0],'joinMaxRGBA':[0,0,0,0],'joinAlphaDifferentPixels':0,'joinRGBOver1Pixels':0,'fullRGBOver1Pixels':0});s['pairs']+=1;s['fullMaxRGBA']=np.maximum(s['fullMaxRGBA'],mx).tolist();s['fullRGBOver1Pixels']+=int(mask.sum())
        for jo in row['joins']:
            x,y,w,h=jo['rect'];dd=delta[y:y+h,x:x+w];jm=dd.max(axis=(0,1)).tolist();ja=int((dd[:,:,3]>0).sum());jr=int((dd[:,:,:3].max(axis=2)>1).sum())
            if jm!=jo['maxRGBA'] or ja!=jo['differentAlphaPixels'] or jr!=jo['differentRGBOver1Pixels']:report['failures'].append({'type':'joinMetricMismatch','row':row['current']})
            s['joinMaxRGBA']=np.maximum(s['joinMaxRGBA'],jm).tolist();s['joinAlphaDifferentPixels']+=ja;s['joinRGBOver1Pixels']+=jr
        ctx=(row['pattern'],row['direction'],row['pitch'],row['context'],row['background']);covered[ctx].add(row['index'])
        ah=hashlib.sha256(a.tobytes()).hexdigest();bh=hashlib.sha256(b.tobytes()).hexdigest()
        if row['index']<24:unique[ctx].add(ah)
        if row['index'] in (0,24):closures.setdefault(ctx,{})[row['index']]=(ah,bh)
    badclosure=[list(k) for k,v in closures.items() if v.get(0)!=v.get(24)]
    fullPatterns={str(k):sorted(v) for k,v in covered.items() if k[0] in ('WWW','WNW','NWN') and k[3] in (0,1) and v!=set(range(25))}
    report['groups'][name]={'pairsRecomputed':len(d['pairs']),'summary':summary,'closureContextCount':len(closures),'closureFailures':badclosure,'full25PhaseMatrixFailures':fullPatterns,'fullPatternUnique24Failures':[{'context':list(k),'unique':len(v)} for k,v in unique.items() if k[0] in ('WWW','WNW','NWN') and k[3] in (0,1) and len(v)!=24],'coverageContexts':len(covered)}
report['elapsedSeconds']=time.time()-start
(OUT/'independent-consumer-metrics.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
