from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,itertools,hashlib
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent
def area(poly):return sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))/2
def clip_convex(subject,clip):
    if area(clip)<0:clip=list(reversed(clip))
    out=subject
    for a,b in zip(clip,clip[1:]+clip[:1]):
        inp=out;out=[]
        if not inp:break
        def cross(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        prev=inp[-1];cp=cross(prev)
        for cur in inp:
            cc=cross(cur)
            if (cc>=-1e-12)!=(cp>=-1e-12):
                t=cp/(cp-cc);out.append([prev[0]+t*(cur[0]-prev[0]),prev[1]+t*(cur[1]-prev[1])])
            if cc>=-1e-12:out.append(cur)
            prev=cur;cp=cc
    return out
audit=json.loads((HERE/'source-audit.json').read_text());polys=[]
for name,g in audit['geometry'].items():
    for face in g['groundContactFaces']:
        poly=[[g['rawWorldVertices'][i][0],g['rawWorldVertices'][i][1]] for i in face];poly=list(reversed(poly)) if area(poly)<0 else poly;polys.append((name,poly))
union=0
for n in range(1,len(polys)+1):
    for combo in itertools.combinations(polys,n):
        q=combo[0][1]
        for _,poly in combo[1:]:q=clip_convex(q,poly)
        union+=(-1)**(n+1)*abs(area(q))
support={'method':'Actual authored Z0 polygon faces; convex polygon intersections and inclusion-exclusion; not AABB or alpha inference','groundZ':0,'basePolygons':[{'object':name,'verticesXY':poly,'area':abs(area(poly))} for name,poly in polys],'unionAreaWorldSquared':union,'nominalCellArea':1,'coverageFraction':union,'fullOpaqueSquareRequired':False,'finiteContact':'Four actual closed base caps at z0. No support sockets, join ports or gameplay stand surface.'}
(HERE/'finite-ground-support.json').write_text(json.dumps(support,indent=2)+'\n')
replay={}
for facing in 'NESW':
    source=Image.open(HERE/'native'/facing/'000.png').convert('RGBA');pub=source.resize((384,704),Image.Resampling.LANCZOS);original=Image.open(HERE/'resources/consumer/sprites/decor-background-rock'/f'static-{facing}.png').convert('RGBA');diff=ImageChops.difference(pub,original)
    folder=HERE/'historical-lanczos';folder.mkdir(exist_ok=True);pub.save(folder/f'{facing}.png')
    replay[facing]={'publishedReplayFilter':'whole-frame LANCZOS historical recipe','meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'exactDecodedPixels':pub.tobytes()==original.tobytes(),'maxChannelError':max(x[1] for x in diff.getextrema()),'replayBBox':pub.getbbox(),'historicalBBox':original.getbbox(),'historicalNativeMissing':True}
(HERE/'historical-replay-comparison.json').write_text(json.dumps(replay,indent=2)+'\n')
results=json.loads((HERE/'consumer/results.json').read_text());comparison=[]
for left,right in zip(results['modes'][0]['cases'],results['modes'][1]['cases']):
    rec={'case':left['config']['name']}
    for key in ['screenshot','nativeCanvas']:
        a=Image.open(OBJ/left[key]).convert('RGBA');b=Image.open(OBJ/right[key]).convert('RGBA');diff=ImageChops.difference(a,b)
        rec[key]={'sameSize':a.size==b.size,'exactDecodedPixels':a.tobytes()==b.tobytes(),'maxChannelError':max(x[1] for x in diff.getextrema()),'meanAbsoluteRGBA':ImageStat.Stat(diff).mean}
    comparison.append(rec)
(HERE/'consumer/two-mode-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
for mode in results['modes']:
    sheet=Image.new('RGB',(1800,1200),'#b0b5b5');dr=ImageDraw.Draw(sheet)
    mapping=[]
    for i,rec in enumerate(mode['cases']):
        im=Image.open(OBJ/rec['screenshot']).convert('RGB');im.thumbnail((580,560),Image.Resampling.LANCZOS);x=(i%3)*600;y=(i//3)*600;sheet.paste(im,(x,y+30));dr.text((x+6,y+8),rec['config']['name'],fill='black');mapping.append({'cell':[i//3,i%3],'path':rec['screenshot'],'screenshotSHA256':hashlib.sha256((OBJ/rec['screenshot']).read_bytes()).hexdigest()})
    sheet.save(HERE/'consumer'/f"{mode['mode']}-all-cases-sheet.png")
    (HERE/'consumer'/f"{mode['mode']}-sheet-map.json").write_text(json.dumps(mapping,indent=2)+'\n')
sheet=Image.new('RGB',(1280,1120),'#e9efec');dr=ImageDraw.Draw(sheet)
for row,(bg,label) in enumerate([('#223e55','dark ocean'),('#a0a4a4','gray'),('#eef2ed','light')]):
    y=row*370;dr.rectangle((0,y,1280,y+370),fill=bg);dr.text((10,y+10),label+' — original LANCZOS published sprites',fill='white' if row==0 else 'black')
    for i,d in enumerate('NESW'):
        original=Image.open(HERE/'resources/consumer/sprites/decor-background-rock'/f'static-{d}.png').convert('RGBA');logical=original.resize((192,352),Image.Resampling.LANCZOS);small=original.resize((96,176),Image.Resampling.LANCZOS);x=i*320;sheet.paste(logical,(x,y+18),logical);sheet.paste(small,(x+204,y+150),small);dr.text((x+205,y+332),d+' 64px cell',fill='white' if row==0 else 'black')
sheet.save(HERE/'source-original-logical-and-small.png')
print('EVIDENCE_SUMMARY',len(comparison),'cases','SUPPORT',union,'MODES_IDENTICAL',all(v[k]['exactDecodedPixels'] for v in comparison for k in ['screenshot','nativeCanvas']))
