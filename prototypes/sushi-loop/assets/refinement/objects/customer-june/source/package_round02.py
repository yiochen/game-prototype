"""Create exact whole-canvas atlases, 1/12s APNG playback, sheets and registered context from native captures."""
from pathlib import Path
import json,hashlib,struct,binascii,math
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-02';PROD=OBJ.parents[2]/'production'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def chunks(raw):
    i=8
    while i<len(raw):
        n=struct.unpack('>I',raw[i:i+4])[0];yield raw[i+4:i+8],raw[i+8:i+8+n];i+=n+12
def chunk(t,d):return struct.pack('>I',len(d))+t+d+struct.pack('>I',binascii.crc32(t+d)&0xffffffff)
def apng(paths,dest,loop):
    # Full native frame PNG IDAT streams, no frame deduplication or fitted crops.
    png=[list(chunks(p.read_bytes())) for p in paths];ihdr=next(d for t,d in png[0] if t==b'IHDR');w,h=struct.unpack('>II',ihdr[:8]);out=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',ihdr)
    for t,d in png[0]:
        if t not in [b'IHDR',b'IDAT',b'IEND']:out+=chunk(t,d)
    out+=chunk(b'acTL',struct.pack('>II',len(paths),0 if loop else 1));seq=0
    for i,ch in enumerate(png):
        out+=chunk(b'fcTL',struct.pack('>IIIIIHHBB',seq,w,h,0,0,1,12,0,0));seq+=1
        for t,d in ch:
            if t==b'IDAT':
                if i==0:out+=chunk(b'IDAT',d)
                else:out+=chunk(b'fdAT',struct.pack('>I',seq)+d);seq+=1
    out+=chunk(b'IEND',b'');dest.write_bytes(out)
    check=Image.open(dest);assert check.n_frames==12
    for i,path in enumerate(paths):check.seek(i);assert check.convert('RGBA').tobytes()==Image.open(path).convert('RGBA').tobytes()
    return {'fps':12,'loop':loop,'frameOrder':list(range(12)),'nativeFrame':[384,640],'delayNumerator':1,'delayDenominator':12,'frames':12,'durationSeconds':1,'encoding':'APNG full canvas, one exact native frame per fcTL, no image-space edits'}
library=json.loads((PROD/'library.json').read_text());stool=next(o for o in library['objects'] if o['id']=='stool-wood');context_sources=[]
stools={d:Image.open(PROD/stool['clips'][0]['directions'][d]['image']).convert('RGBA') for d in ['S','E','N','W']}
for d in stools:
    p=PROD/stool['clips'][0]['directions'][d]['image'];context_sources.append({'path':str(p.relative_to(OBJ)) if p.is_relative_to(OBJ) else __import__('os').path.relpath(p,OBJ),'sha256':sha(p),'role':'Approved registered whole-canvas stool context only'})
all_atlases={};all_frames={};previews={};all_phases=[];playbacks=[];image_metrics=[]
backgrounds={'light':(246,239,223),'gray':(166,164,159),'dark':(30,35,45)}
for mode in ['main','runtime']:
    rows=json.loads((OUT/(mode+'-phases-000-1000.json')).read_text());all_phases+=rows;all_frames[mode]=[{k:r[k] for k in ['clip','direction','index','path','sha256']} for r in rows];groups={}
    for r in rows:groups.setdefault((r['clip'],r['direction']),[]).append(r)
    all_atlases[mode]=[]
    for (clip,d),frames in groups.items():
        frames.sort(key=lambda r:r['index']);assert [r['index'] for r in frames]==list(range(12));paths=[OBJ/r['path'] for r in frames]
        imgs=[Image.open(p).convert('RGBA') for p in paths];assert all(im.size==(384,640) for im in imgs)
        atlas=Image.new('RGBA',(2304,1280));rects=[]
        for i,im in enumerate(imgs):x=i%6*384;y=i//6*640;atlas.paste(im,(x,y));rects.append([x,y,384,640]);assert atlas.crop((x,y,x+384,y+640)).tobytes()==im.tobytes()
        dest=OUT/mode/'atlases'/(clip+'-'+d+'.png');dest.parent.mkdir(exist_ok=True);atlas.save(dest)
        loop=clip not in ['sit-down','stand-up','happy'];a={'clip':clip,'direction':d,'path':str(dest.relative_to(OBJ)),'sha256':sha(dest),'columns':6,'rows':2,'size':[2304,1280],'rects':rects,'fps':12,'loop':loop,'frameOrder':list(range(12))};all_atlases[mode].append(a)
        dest=OUT/'playback'/(clip+'-'+d+'.png');dest.parent.mkdir(exist_ok=True);pb=apng(paths,dest,loop);pb.update(clip=clip,direction=d,path=str(dest.relative_to(OBJ)),sha256=sha(dest));playbacks.append(pb);previews[clip+'-'+d]=pb['path']
        for i,im in enumerate(imgs):
            alpha=im.getchannel('A');bbox=alpha.point(lambda x:255 if x>=128 else 0).getbbox();edge=any(alpha.getpixel((x,y)) for x in range(384) for y in [0,639]) or any(alpha.getpixel((x,y)) for y in range(640) for x in [0,383]);image_metrics.append({'clip':clip,'direction':d,'index':i,'bboxAlpha128':bbox,'canvasEdgeHasAlpha':edge,'sha256':frames[i]['sha256']})
    clips=list(dict.fromkeys(r['clip'] for r in rows))
    for clip in clips:
        for bgname,bg in backgrounds.items():
            sheet=Image.new('RGB',(6*192,8*340),bg);dr=ImageDraw.Draw(sheet)
            for di,d in enumerate(['S','E','N','W']):
                for i,r in enumerate(sorted(groups[clip,d],key=lambda r:r['index'])):
                    im=Image.open(OBJ/r['path']).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);x=i%6*192;y=(di*2+i//6)*340;sheet.paste(im,(x,y+20),im);dr.text((x+6,y+3),f'{clip} {d} {i}',fill=(225,225,225) if bgname=='dark' else (20,20,20))
            dest=OUT/'sheets'/(clip+'-'+bgname+'.png');dest.parent.mkdir(exist_ok=True);sheet.save(dest);previews['sheet:'+clip+':'+bgname]=str(dest.relative_to(OBJ))
        # Runtime-style composition with exact approved stool sprite under unchanged actor frame.
        if clip in ['seated-wait','eat','sit-down','stand-up','eat-salmon','seated-wait-empty']:
            canv=Image.new('RGB',(4*240,3*360),backgrounds['light']);dr=ImageDraw.Draw(canv)
            for di,d in enumerate(['S','E','N','W']):
                for fi,i in enumerate([0,6,11]):
                    st=stools[d].resize((192,352),Image.Resampling.LANCZOS);fr=Image.open(OBJ/groups[clip,d][i]['path']).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);x=di*240+24;y=fi*360+20;canv.paste(st,(x,y),st);canv.paste(fr,(x,y),fr);dr.text((di*240+8,fi*360+3),f'{clip} {d} frame {i}',fill=(25,25,25))
            dest=OUT/'contexts'/(clip+'-stool.png');dest.parent.mkdir(exist_ok=True);canv.save(dest);previews['context:'+clip]=str(dest.relative_to(OBJ))
heroes={d:next(r['path'] for r in all_frames['main'] if r['clip']=='stand' and r['direction']==d and r['index']==0) for d in ['S','E','N','W']}
sheet=Image.new('RGB',(4*192,352),backgrounds['gray']);dr=ImageDraw.Draw(sheet)
for i,d in enumerate(heroes):im=Image.open(OBJ/heroes[d]).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);sheet.paste(im,(i*192,24),im);dr.text((i*192+8,5),d,fill='black')
p=OUT/'four-view-sheet.png';sheet.save(p);previews['four-view-sheet']=str(p.relative_to(OBJ))
sheet=Image.new('RGB',(4*192,2*344),backgrounds['gray']);dr=ImageDraw.Draw(sheet)
for i,d in enumerate(['S','E','N','W']):
    for j,p in enumerate([OBJ/heroes[d],OUT/'repeat'/('main-'+d+'.png')]):
        im=Image.open(p).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);sheet.paste(im,(i*192,j*344+24),im);dr.text((i*192+6,j*344+4),('capture ' if j==0 else 'reopened repeat ')+d,fill='black')
p=OUT/'repeated.png';sheet.save(p);previews['repeated']=str(p.relative_to(OBJ))
# Phone-width illustrative registration context. No game/Godot state is altered.
phone=Image.new('RGB',(390,844),(246,239,222));dr=ImageDraw.Draw(phone);dr.rounded_rectangle((12,12,378,832),radius=26,fill=(224,212,183));dr.rectangle((20,80,370,760),fill=(240,227,195));dr.text((30,35),'June native sprite / phone-width context',fill=(42,38,31));dr.text((30,780),'Exact registered frames, uniform 0.75 scale',fill=(42,38,31))
for x in range(20,371,96):dr.line((x,80,x,760),fill=(220,204,173),width=1)
for y in range(88,761,96):dr.line((20,y,370,y),fill=(220,204,173),width=1)
def place(im,root_at,scale=.75):
    # Each source uses native root192,496 and native scale2; no independent X/Y fitting.
    size=(round(im.width*scale/2),round(im.height*scale/2));im=im.resize(size,Image.Resampling.LANCZOS);xy=(round(root_at[0]-192*scale/2),round(root_at[1]-496*scale/2));phone.paste(im,xy,im)
placements=[('main','eat','S',6,(119,445),True),('runtime','eat-salmon','E',6,(276,515),True),('main','walk','W',3,(120,670),False)]
for mode,clip,d,i,rt,with_stool in placements:
    if with_stool:place(stools[d],rt)
    fr=next(r for r in all_frames[mode] if r['clip']==clip and r['direction']==d and r['index']==i);place(Image.open(OBJ/fr['path']).convert('RGBA'),rt)
p=OUT/'contexts/phone-390.png';phone.save(p);previews['phone-context']=str(p.relative_to(OBJ))
html='''<!doctype html><meta charset="utf-8"><title>June native 12 fps review</title><style>body{font:14px system-ui;background:#a6a49f;color:#171717;margin:20px}section{display:grid;grid-template-columns:repeat(4,192px);gap:8px;margin-bottom:22px}figure{margin:0;background:#f6efdf}img{width:192px;height:320px;display:block}figcaption{padding:6px}h2{font-size:16px}</style><h1>June native review · 48 clips · 12 fps</h1><p>APNG delays are exactly 1/12 second. Nonloop states play once. Each frame is the full unchanged native 384×640 canvas. Reload to restart nonloop clips.</p>'''
for clip in dict.fromkeys(p['clip'] for p in playbacks):
    html+='<h2>'+clip+'</h2><section>'
    for d in ['S','E','N','W']:
        p=next(p for p in playbacks if p['clip']==clip and p['direction']==d);href=__import__('os').path.relpath(OBJ/p['path'],OUT);html+='<figure><img src="'+href+'"><figcaption>'+d+' · '+('loop' if p['loop'] else 'one play')+'</figcaption></figure>'
    html+='</section>'
(OUT/'playback.html').write_text(html);previews['playback-review-page']=str((OUT/'playback.html').relative_to(OBJ))
write(OUT/'package.json',{'rawFrames':all_frames,'atlases':all_atlases,'heroes':heroes,'previews':previews,'playbacks':playbacks,'contextSources':context_sources,'imageMetrics':image_metrics,'phoneContext':{'size':[390,844],'uniformLogicalScale':.75,'placements':[{'mode':m,'clip':c,'direction':d,'index':i,'groundRoot':r,'stool':s} for m,c,d,i,r,s in placements],'scope':'Illustrative registered native sprite composition, not a Godot gameplay screenshot'},'stoolContext':{'sourceSocketLogical':stool['sockets']['S']['seat'],'actorAndStoolNativeRoot':[192,496],'independentCaptureProfiles':True,'noActorFitOrOffset':True}})
write(OUT/'candidate-phases.json',all_phases)
print('JUNE_PACKAGED',len(all_phases),'frames',sum(len(a) for a in all_atlases.values()),'atlases',len(playbacks),'playbacks',flush=True)
