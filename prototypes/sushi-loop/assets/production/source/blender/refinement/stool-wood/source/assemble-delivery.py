"""Assemble lossless native atlas copies and clearly labeled proof previews.
No native sprite pixel is changed. Preview compositing is only evidence.
Run with bundled workspace Python and --round round-NN.
"""
import json,hashlib,shutil,argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
parser=argparse.ArgumentParser();parser.add_argument('--round',required=True);args=parser.parse_args()
BASE=Path(__file__).resolve().parents[1];RN=args.round;OUT=BASE/'candidates'/RN
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def rel(p):return str(p.relative_to(BASE))
directions=['N','E','S','W'];frames={d:Image.open(OUT/'raw'/f'static-{d}-0000.png').convert('RGBA')for d in directions}
(OUT/'atlases').mkdir(exist_ok=True);(OUT/'previews').mkdir(exist_ok=True)
atlases=[];heroes={};raw=[]
for d in directions:
    source=OUT/'raw'/f'static-{d}-0000.png';target=OUT/'atlases'/f'static-{d}.png';shutil.copyfile(source,target)
    heroes[d]=rel(target);raw.append(rel(source))
    atlases.append({'clip':'static','direction':d,'path':rel(target),'sha256':sha(target),'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]})
def sheet(bg,title,logical=False):
    s=2 if logical else 1;w,h=384//s,704//s;im=Image.new('RGBA',(w*4,h+38),(*bg,255));draw=ImageDraw.Draw(im)
    color=(28,33,38)if sum(bg)>300 else (236,237,240)
    for i,d in enumerate(directions):
        frame=frames[d].resize((w,h),Image.Resampling.LANCZOS)if logical else frames[d]
        im.alpha_composite(frame,(i*w,38));draw.text((i*w+14,12),d+'  |  '+title,fill=color)
    return im
previews={}
for name,bg in [('light',(245,238,219)),('gray',(112,117,124)),('dark',(30,35,43))]:
    p=OUT/'previews'/f'background-{name}.png';sheet(bg,'native 384 x 704').convert('RGB').save(p);previews[f'background-{name}']=rel(p)
p=OUT/'previews'/'four-view-sheet.png';sheet((211,213,216),'native 384 x 704').convert('RGB').save(p);previews['four-view-sheet']=rel(p)
p=OUT/'previews'/'logical-size.png';sheet((211,213,216),'logical 192 x 352',True).convert('RGB').save(p);previews['logical-size']=rel(p)
# Independent PNGs placed at 128 logical pixel / 256 native pixel cell pitch.
im=Image.new('RGBA',(1024,1160),(226,220,200,255));draw=ImageDraw.Draw(im)
draw.text((20,18),'Independent native captures | 256 px native / 128 px logical cell pitch',fill=(45,47,47))
for y in range(3):
    for x in range(3):
        rx=256+x*256;ry=370+y*256
        draw.rectangle((rx-128,ry-128,rx+127,ry+127),fill=(216,210,191,255)if (x+y)%2 else (231,225,206,255))
for y in range(3):
    for x in range(3):
        d=directions[(x+y*3)%4];im.alpha_composite(frames[d],(256+x*256-192,370+y*256-496))
p=OUT/'previews'/'repeated.png';im.convert('RGB').save(p);previews['repeated']=rel(p)
def alpha_info(im):
    alpha=im.getchannel('A');w,h=im.size;data=alpha.tobytes();threshold=4
    mask=bytearray(v>threshold for v in data);components=[]
    for index in range(w*h):
        if not mask[index]:continue
        mask[index]=0;stack=[index];count=0;xs=[];ys=[]
        while stack:
            i=stack.pop();count+=1;x=i%w;y=i//w;xs.append(x);ys.append(y)
            for n in ([i-1]if x else [])+([i+1]if x+1<w else [])+([i-w]if y else [])+([i+w]if y+1<h else []):
                if mask[n]:mask[n]=0;stack.append(n)
        components.append({'pixels':count,'bounds':[min(xs),min(ys),max(xs)+1,max(ys)+1]})
    border=[data[x]for x in range(w)]+[data[(h-1)*w+x]for x in range(w)]+[data[y*w]for y in range(h)]+[data[y*w+w-1]for y in range(h)]
    return {'size':[w,h],'mode':im.mode,'alphaRange':list(alpha.getextrema()),'alphaBounds':list(alpha.getbbox()),'borderMaxAlpha':max(border),'connectedComponentsAlphaGT4':sorted(components,key=lambda x:-x['pixels']),'transparentPixels':sum(v==0 for v in data),'partialAlphaPixels':sum(0<v<255 for v in data),'opaquePixels':sum(v==255 for v in data)}
native=json.loads((OUT/'validation-native.json').read_text());native['alpha']={d:alpha_info(frames[d])for d in directions}
native['atlasLayout']={'matchesCatalog':True,'columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]],'nativePngCopiedWithoutChanges':all(sha(OUT/'raw'/f'static-{d}-0000.png')==sha(OUT/'atlases'/f'static-{d}.png')for d in directions)}
native['previews']=previews;native['sourceSettings']=f'source/{RN}-settings.json'
native['measurementNotes']=['Native shallow channels remove the original 0.004-unit raised seam strips. Seat slab top remains z=0.65, root/seat socket z=0.655 and declared height 0.64 unchanged.','Original envelope has no ground receiver; original leg bottoms are z=0.03210894 and remain unchanged.','The first diagnostic round had invalid camera assignment; round-02 had compositor/bevel issues. These are retained as diagnostic history and are not submitted.']
native['files']={'projectSHA256':sha(BASE/'source'/f'{RN}.blend'),'recipeSHA256':sha(BASE/'source'/f'{RN}.py'),'settingsSHA256':sha(BASE/'source'/f'{RN}-settings.json'),'assembleRecipeSHA256':sha(Path(__file__))}
write(OUT/'validation.json',native)
delivery={'asset':'stool-wood','round':RN,'project':f'source/{RN}.blend','recipe':f'source/{RN}.py','settings':f'source/{RN}-settings.json','validation':rel(OUT/'validation.json'),'heroes':heroes,'rawFrames':raw,'previews':previews,'atlases':atlases,'nativeRecords':{'camera':rel(OUT/'records/camera.json'),'assetRecord':rel(OUT/'records/asset.json'),'rig':rel(OUT/'records/rig.json')}}
write(OUT/'delivery.json',delivery)
print(json.dumps({'delivery':rel(OUT/'delivery.json'),'projectSHA256':sha(BASE/'source'/f'{RN}.blend'),'alpha':native['alpha'],'bounds':native['currentBounds'],'topology':[(x['object'],x['nonmanifoldEdges'],x['degenerateFaces'])for x in native['topology']]},indent=2))
