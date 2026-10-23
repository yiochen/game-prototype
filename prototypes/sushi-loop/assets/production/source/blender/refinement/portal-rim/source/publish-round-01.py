"""Whole-canvas uniform publication and full-registration inspection sheets."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import json,hashlib
S=Path(__file__).resolve().parent;C=S.parent/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
cat=json.loads((S/'round-01-resources/inputs/catalog-object.json').read_text())
frames=[];native=[];atlases=[];metrics={};allframes={}
(C/'evidence').mkdir(exist_ok=True);(C/'published').mkdir(exist_ok=True)
for facing in ['N','E','S','W']:
    atlas=Image.new('RGBA',(2304,1536));rows=[];images=[]
    sheet=Image.new('RGB',(1152,816),(128,128,128));draw=ImageDraw.Draw(sheet)
    for i in range(12):
        p=C/'raw/idle'/facing/f'{i:03d}.png';raw=Image.open(p).convert('RGBA');assert raw.size==(768,1536)
        published=raw.resize((384,768),Image.Resampling.LANCZOS)
        dest=C/'published/idle'/facing/f'{i:03d}.png';dest.parent.mkdir(parents=True,exist_ok=True);published.save(dest)
        rect=cat['clips'][0]['directions'][facing]['rects'][i];atlas.paste(published,tuple(rect[:2]));images.append(published)
        frames.append({'clip':'idle','direction':facing,'index':i,'path':str(dest.relative_to(S.parent)),'dimensions':[384,768],'sha256':sha(dest)})
        native.append({'clip':'idle','direction':facing,'index':i,'path':str(p.relative_to(S.parent)),'dimensions':[768,1536],'sha256':sha(p),'nativeCaptureScale':4})
        alpha=published.getchannel('A');box=alpha.getbbox();border=max(alpha.crop(r).getextrema()[1] for r in [(0,0,384,1),(0,767,384,768),(0,0,1,768),(383,0,384,768)])
        rawalpha=raw.getchannel('A');rawborder=max(rawalpha.crop(r).getextrema()[1] for r in [(0,0,768,1),(0,1535,768,1536),(0,0,1,1536),(767,0,768,1536)])
        rows.append({'index':i,'nativeAlphaBounds':rawalpha.getbbox(),'publishedAlphaBounds':box,'nativeBorderMaxAlpha':rawborder,'publishedBorderMaxAlpha':border,'decodedRGBA_SHA256':hashlib.sha256(published.tobytes()).hexdigest()})
        # Nearest reduction follows the common-canvas LANCZOS publication.
        logical=published.resize((192,384),Image.Resampling.NEAREST);x=(i%6)*192;y=(i//6)*408;sheet.paste(logical,(x,y),logical);draw.text((x+4,y+386),f'{facing} idle {i:02d}',fill='white')
        assert border==0 and rawborder==0
    atlaspath=C/'published'/f'idle-{facing}.png';atlas.save(atlaspath)
    atlases.append({'clip':'idle','direction':facing,'path':str(atlaspath.relative_to(S.parent)),'dimensions':[2304,1536],'columns':6,'rows':2,'rects':cat['clips'][0]['directions'][facing]['rects'],'sha256':sha(atlaspath)})
    # Every atlas cell must equal the separate exact published registered frame.
    for i,frame in enumerate(images):
        x,y,w,h=cat['clips'][0]['directions'][facing]['rects'][i];assert atlas.crop((x,y,x+w,y+h)).tobytes()==frame.tobytes()
    sheet.save(C/'evidence'/f'allframes-{facing}.png')
    # Real native-derived animation is retained; actual browser playback is separate.
    images[0].save(C/'evidence'/f'idle-{facing}.apng',save_all=True,append_images=images[1:],duration=[1000/12]*12,loop=0,disposal=0,blend=0)
    metrics[facing]={'frames':rows,'uniqueDecodedFrames':len(set(r['decodedRGBA_SHA256'] for r in rows)),'allBordersTransparent':all(r['nativeBorderMaxAlpha']==r['publishedBorderMaxAlpha']==0 for r in rows)}
    allframes[facing]=images
four=Image.new('RGB',(4*384,800),(128,128,128));draw=ImageDraw.Draw(four)
for j,f in enumerate(['N','E','S','W']):
    im=allframes[f][0];four.paste(im,(j*384,0),im);draw.text((j*384+12,774),f'{f} idle 00 | 384x768 published full canvas',fill='white')
four.save(C/'evidence/four-view-sheet.png')
# Support/contact and opening registered overlays are evidence only, never exports.
measure=json.loads((C/'native-measurements.json').read_text());maps=Image.new('RGB',(4*384,800),(128,128,128));d=ImageDraw.Draw(maps)
for j,f in enumerate(['N','E','S','W']):
    im=allframes[f][0];maps.paste(im,(j*384,0),im);r=measure['frames'][f][0];ex,ey=[v/2 for v in r['entryOpening']['nativePixel']];d.ellipse((j*384+ex-6,ey-6,j*384+ex+6,ey+6),outline='#ff5757',width=2);d.line((j*384,576,j*384+384,576),fill='#eeeeee',width=1);d.text((j*384+8,774),f'{f} red: entry center; white: root Z0 line',fill='white')
maps.save(C/'evidence/registration-entry-map.png')
write(C/'pixel-validation.json',{'nativeCaptureScale':4,'nativeDimensions':[768,1536],'sourceScale':2,'publishedDimensions':[384,768],'logicalFrame':[192,384],'logicalRoot':[96,288],'nativeRoot':[384,1152],'publishedRoot':[192,576],'publication':'Uniform complete native4x canvas to published2x LANCZOS; atlas insertion at original rects. No fitting, clipping, repositioning, RGB/alpha repair or recolor. Native logical sheets use NEAREST only after common-canvas publication; browser CSS has its own normal filtering.','PillowVersion':Image.__version__,'facings':metrics,'nativeFrames':native,'rawFrames':frames,'atlases':atlases,'allAtlasCellsExact':True,'minimumUniqueFrames6':all(v['uniqueDecodedFrames']>=6 for v in metrics.values())})
print(json.dumps({'frames':len(frames),'native':len(native),'atlases':len(atlases),'unique':{f:metrics[f]['uniqueDecodedFrames'] for f in metrics}}))
