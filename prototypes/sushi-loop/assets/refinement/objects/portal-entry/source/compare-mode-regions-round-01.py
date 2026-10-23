from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import json
H=Path(__file__).resolve().parent.parent/'candidates/round-01';r=json.loads((H/'consumer-report.json').read_text());records=[]
for a,b in zip(r['browserModes'][0]['screenshots'],r['browserModes'][1]['screenshots']):
    x=Image.open(H/'consumer'/a['file']).convert('RGBA');y=Image.open(H/'consumer'/b['file']).convert('RGBA');scale=a['evidence']['scale'];w=round(192*scale);h=round(384*scale);rows=list(range(12)) if 'all48' in a['file'] else [0,5,11];cells=[]
    for row,index in enumerate(rows):
        for col,d in enumerate('NESW'):
            rect=(col*w,row*(h+20)+20,(col+1)*w,row*(h+20)+20+h);diff=ImageChops.difference(x.crop(rect),y.crop(rect))
            cells.append({'direction':d,'index':index,'rect':list(rect),'maxRGBA':[v[1] for v in diff.getextrema()],'meanRGBA':ImageStat.Stat(diff).mean})
    records.append({'first':a['file'],'second':b['file'],'scope':'Only complete actual sprite viewport regions, excluding browser labels/margins; preserves native shared-canvas and CSS raster differences.','maxRGBA':[max(c['maxRGBA'][i] for c in cells) for i in range(4)],'cells':cells})
p=H/'consumer-mode-object-region-residuals.json';assert not p.exists();p.write_text(json.dumps({'asset':'portal-entry','records':records,'note':'Whole-page differences in consumer-analysis.json include label text rasterization; these values isolate object viewport pixels. No pixel identity assumed.'},indent=2)+'\n')
print([(x['first'],x['maxRGBA']) for x in records])
