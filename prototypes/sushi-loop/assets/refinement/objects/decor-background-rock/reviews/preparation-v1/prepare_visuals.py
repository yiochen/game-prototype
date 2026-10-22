from pathlib import Path
from PIL import Image, ImageDraw, ImageChops, ImageStat
import json
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent
OUT=HERE/'published';OUT.mkdir(exist_ok=True)
stats={}
for d in 'NESW':
    im=Image.open(HERE/'native'/d/'000.png').convert('RGBA');pub=im.resize((384,704),Image.Resampling.BOX);pub.save(OUT/f'{d}.png')
    original=Image.open(OBJ/'inputs'/'original.png').convert('RGBA') if d=='S' else Image.open(OBJ.parent.parent.parent/'production'/'sprites'/'decor-background-rock'/f'static-{d}.png').convert('RGBA')
    diff=ImageChops.difference(original,pub)
    stats[d]={'nativeSize':list(im.size),'publishedSize':list(pub.size),'originalBBox':original.getbbox(),'replayBBox':pub.getbbox(),'rgbaExact':diff.getbbox() is None,'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'maxChannelError':max(x[1] for x in diff.getextrema())}
sheet=Image.new('RGB',(4*384,744),'#a0a4a4');dr=ImageDraw.Draw(sheet)
for i,d in enumerate('NESW'):
    im=Image.open(OUT/f'{d}.png');sheet.paste(im,(i*384,40),im);dr.text((i*384+12,12),f'{d} native4x -> published2x BOX',fill='black')
sheet.save(HERE/'source-four-view-sheet.png')
compare=Image.new('RGB',(4*384,744),'#a0a4a4');dr=ImageDraw.Draw(compare)
for i,(title,p) in enumerate([('Original S',OBJ/'inputs/original.png'),('Fixed target (whole canvas)',OBJ/'inputs/target.png'),('GLOBAL style',OBJ.parent.parent/'style/warm-soft-reference.png'),('Source replay S',OUT/'S.png')]):
    im=Image.open(p).convert('RGBA').resize((384,704),Image.Resampling.LANCZOS if i in [1,2] else Image.Resampling.NEAREST)
    compare.paste(im,(i*384,40),im);dr.text((i*384+12,12),title,fill='black')
compare.save(HERE/'independent-comparison.png')
sizes=Image.new('RGB',(1100,780),'#223e55');dr=ImageDraw.Draw(sizes)
for row,(bg,label) in enumerate([('#223e55','dark ocean'),('#a0a4a4','gray'),('#eef2ed','light')]):
    dr.rectangle((0,row*260,1100,(row+1)*260),fill=bg);dr.text((10,row*260+10),label,fill='white' if row==0 else 'black')
    for col,d in enumerate('NESW'):
        im=Image.open(OUT/f'{d}.png');im=im.resize((96,176),Image.Resampling.BOX)
        x=90+col*250;sizes.paste(im,(x,row*260+36),im);dr.text((x,row*260+224),f'{d}: 0.5 logical / 64px cell',fill='white' if row==0 else 'black')
sizes.save(HERE/'source-small-backgrounds.png')
(HERE/'source-raster-comparison.json').write_text(json.dumps(stats,indent=2)+'\n')
