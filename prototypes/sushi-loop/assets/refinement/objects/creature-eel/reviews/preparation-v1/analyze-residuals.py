from pathlib import Path
from PIL import Image,ImageStat,ImageChops
import json,hashlib
P=Path(__file__).resolve().parent
p=P/'replay-published-residuals.json';d=json.loads(p.read_text())
for r in d['records']:
 if r['branch']!='untouched':continue
 im=Image.open(P/r['reducedPath']).convert('RGBA');at=Image.open(P/'resources/published'/r['publishedAtlas']).convert('RGBA');x,y,w,h=r['publishedRect'];ori=at.crop((x,y,x+w,y+h));di=ImageChops.difference(im,ori);visible=ImageChops.lighter(im.getchannel('A'),ori.getchannel('A')).point(lambda v:255 if v>=16 else 0);opaque=ImageChops.darker(im.getchannel('A'),ori.getchannel('A')).point(lambda v:255 if v>=250 else 0);r['visibleUnionMAE']=ImageStat.Stat(di,visible).mean;r['opaqueIntersectionMAE']=ImageStat.Stat(di,opaque).mean;r['sameAlphaBounds']=r['originalAlphaBounds']==r['replayAlphaBounds']
p.write_text(json.dumps(d,indent=2)+'\n')
# Browser decoded-pixel comparisons (videos record actual rAF playback, inspected still/timeline evidence is explicit).
bs={}
for mode in ['all','logical','phone','attachments','playback-0','playback-0_5','playback-0_9166666666666666','playback-1','playback-2']:
 a=P/'browser/chromium'/f'{mode}.png';b=P/'browser/shell'/f'{mode}.png'
 if a.exists() and b.exists():
  x=Image.open(a).convert('RGBA');y=Image.open(b).convert('RGBA');dd=ImageChops.difference(x,y);bs[mode]={'size':list(x.size),'decodedPixelsEqual':not dd.getbbox(alpha_only=False),'channelMAE':ImageStat.Stat(dd).mean,'channelMax':[e[1] for e in dd.getextrema()]}
(P/'browser-comparison.json').write_text(json.dumps(bs,indent=2)+'\n')
rr=[r for r in d['records'] if r['branch']=='untouched'];summary={'untouchedComparisons':len(rr),'exactDecodedMatches':sum(r['pixelExact'] for r in rr),'sameAlphaBounds':sum(r['sameAlphaBounds'] for r in rr),'maxWholeFrameMAE':[max(r['channelMAE'][i] for r in rr) for i in range(4)],'maxVisibleUnionMAE':[max(r['visibleUnionMAE'][i] for r in rr) for i in range(4)],'maxOpaqueIntersectionMAE':[max(r['opaqueIntersectionMAE'][i] for r in rr) for i in range(4)],'maxAlphaChannelDelta':max(r['channelMax'][3] for r in rr),'interpretation':'Reconstructed source4x camera and whole-frame LANCZOS agree in registration and visible appearance; they are not byte/pixel identical. Small renderer/filter residuals persist; transparent RGB can have large maxima without visible alpha. Do not call this an exact source replay.'}
(P/'replay-residual-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary);print(bs)
