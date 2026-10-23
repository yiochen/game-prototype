"""Independent unedited-source sprite repeats; diagnostic alpha probes only."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
OUT=Path(__file__).resolve().parent
report={'scope':'Unedited original source, not a candidate; full-frame sampling only. No native connected reference or browser/Godot claim.',
 'cases':[], 'seamSampling':'S probe at source2x join x320 and source rows350,360,370,390,430,460,490,520; source fields are opaque at these interior points.'}
def composite(im,d):
    step=(256,0) if d in 'NS' else (0,256)
    canvas=Image.new('RGBA',(896,704) if d in 'NS' else (384,1216))
    for i in range(3):canvas.alpha_composite(im,(step[0]*i,step[1]*i))
    return canvas
sheet=Image.new('RGB',(4*448,4*500),(90,90,90));draw=ImageDraw.Draw(sheet)
for j,d in enumerate('NESW'):
    for i,(folder,name,filt) in enumerate([('historical-replay','old1.5-LANCZOS',Image.Resampling.LANCZOS),('narrow-filter-probe','narrow.01-LANCZOS',Image.Resampling.LANCZOS),('narrow-filter-probe','narrow.01-BOX',Image.Resampling.BOX),('native2-probe','native2.01-identity',None)]):
        raw=Image.open(OUT/folder/'native'/('static-'+d)/'000.png').convert('RGBA')
        im=raw.resize((384,704),filt) if filt is not None else raw
        dest=OUT/'narrow-filter-probe/published'/name/('static-'+d+'.png');dest.parent.mkdir(parents=True,exist_ok=True);im.save(dest)
        rep=composite(im,d);rpath=dest.parent/('repeat-'+d+'.png');rep.save(rpath)
        entry={'direction':d,'sampling':name,'repeated':str(rpath.relative_to(OUT))}
        alpha=np.asarray(im)[:,:,3]
        entry['partialAlphaPixelCount']=int(((alpha>0)&(alpha<255)).sum())
        if d=='S':entry['alphaAcrossInteriorJoin']={str(y):[rep.getpixel((x,y))[3] for x in range(315,326)] for y in [350,360,370,390,430,460,490,520]}
        report['cases'].append(entry)
        bg=Image.new('RGBA',rep.size,(90,90,90,255));bg.alpha_composite(rep)
        scale=min(448/rep.width,470/rep.height)
        reduced=bg.convert('RGB').resize((round(rep.width*scale),round(rep.height*scale)),Image.Resampling.LANCZOS)
        sheet.paste(reduced,(448*j,500*i+25));draw.text((448*j+8,500*i+8),d+' '+name,fill='white')
sheet.save(OUT/'narrow-filter-probe/repeat-sampling-sheet.png')
(OUT/'narrow-filter-probe/sampling-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([r for r in report['cases'] if r['direction']=='S'],indent=2))
