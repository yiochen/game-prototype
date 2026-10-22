from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,hashlib
P=Path(__file__).resolve().parents[2]
write=lambda name,j:(P/name).write_text(json.dumps(j,indent=2)+'\n')
def pixelstats(a,b):
 a=Image.open(a).convert('RGBA') if not isinstance(a,Image.Image) else a.convert('RGBA');b=Image.open(b).convert('RGBA') if not isinstance(b,Image.Image) else b.convert('RGBA')
 assert a.size==b.size
 pairs=list(zip(a.get_flattened_data(),b.get_flattened_data()));d=[tuple(abs(x-y) for x,y in zip(p,q)) for p,q in pairs]
 return {'size':list(a.size),'rgbaDifferencePixels':sum(any(z) for z in d),'alphaDifferencePixels':sum(z[3]>0 for z in d),'maxRGBAChannelDelta':[max(z[k] for z in d) for k in range(4)],'rgbDifferenceWhereBothAlphaZero':sum(p[3]==q[3]==0 and p[:3]!=q[:3] for p,q in pairs),'rgbDifferenceWhereEitherAlphaNonzero':sum((p[3]>0 or q[3]>0) and p[:3]!=q[:3] for p,q in pairs)}
hi=Image.open(P/'baseline/historical-original4-S.png').convert('RGBA');lo=hi.resize((384,704),Image.Resampling.LANCZOS);ori=Image.open(P/'resources/object/inputs/original.png').convert('RGBA');hist=pixelstats(ori,lo);hist.update({'scope':'Historical raw4 replay and whole-frame LANCZOS normalization, not canonical capture','native4Frame':list(hi.size),'replayFrame':list(lo.size),'equality':ori.tobytes()==lo.tobytes(),'originalAlphaBBox':list(ori.getbbox()),'replayAlphaBBox':list(lo.getbbox()),'interpretation':'Honest replay difference retained. No pixel correction, camera fit or original replacement; registered matrices and source hash remain measured authority.'});write('historical-replay-comparison-v2.json',hist)
res=json.loads((P/'consumer-baseline-v2/results.json').read_text());out={'browserRuns':[],'crossMode':[],'independentVersusNative':[],'scope':'untouched end source beside approved middle02 and edge02; intentional old source fields differ; no candidate approval'}
for c in res['cases']:
 out['browserRuns'].append({'mode':c['mode'],'case':c['id'],'version':c['browserVersion'],'launch':c['launch'],'viewport':c['viewport'],'DPR':c['deviceScaleFactor'],'errors':c['errors'],'nativeNearestAfterResize':all(f['nativeNearestRestoredAfterResize'] for f in c['evidence']['fixtures'])})
 for d in 'NESW':
  stem=c['mode']+'-'+c['id']+'-'+d;st=pixelstats(P/'consumer-baseline-v2'/(stem+'-independent.png'),P/'consumer-baseline-v2'/(stem+'-native-control.png'));out['independentVersusNative'].append({'mode':c['mode'],'case':c['id'],'direction':d,**st})
for case in ['logical128-integer','logical128-fractional','phone32-integer','phone32-fractional']:
 for suffix in ['css']+[d+'-'+s for d in 'NESW' for s in ['independent','native-control']]:
  st=pixelstats(P/'consumer-baseline-v2'/('full-chromium-'+case+'-'+suffix+'.png'),P/'consumer-baseline-v2'/('bundled-headless-shell-'+case+'-'+suffix+'.png'));out['crossMode'].append({'case':case,'evidence':suffix,**st})
write('consumer-comparison.json',out)
# Exact full-frame logical sheets for own singles and native true chain, every facing at 128 and 32 cell sizes.
for scale,label in [(0.5,'logical128'),(.125,'phone32')]:
 sizes=[]
 for d in 'NESW':
  for kind in ['original-canonical-rig','mixed-native']:
   im=Image.open(P/'baseline-v2'/kind/(d+'.png')).convert('RGBA');sizes.append((d,kind,im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)))
 width=max(im.width for _,_,im in sizes);height=sum(im.height+20 for _,_,im in sizes)
 sheet=Image.new('RGB',(width*3,height),'#808080');dr=ImageDraw.Draw(sheet);y=0
 for d,kind,im in sizes:
  for k,(bg,c) in enumerate([('light','#eeeeee'),('gray','#808080'),('dark','#151923')]):
   dr.rectangle((k*width,y,(k+1)*width-1,y+im.height+19),fill=c);dr.text((k*width+2,y+2),d+' '+kind+' '+bg,fill='white' if bg=='dark' else 'black');sheet.paste(im,(k*width,y+20),im)
  y+=im.height+20
 sheet.save(P/('native-use-'+label+'.png'))
print('historical',hist)
print('crossmode mismatches',[(r['case'],r['evidence'],r['rgbaDifferencePixels']) for r in out['crossMode'] if r['rgbaDifferencePixels']])
