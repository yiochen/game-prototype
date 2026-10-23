from pathlib import Path
import json
from PIL import Image,ImageDraw
R=Path(__file__).parent;x=json.loads((R/'video-review-complete.json').read_text());rows=[]
for v in x['videos']:
 ims=[Image.open(R/f['path']).convert('RGB') for f in v['frames']];name=Path(v['declaredPath']).stem
 if name.startswith('all4'):
  # Native encoded all4 video already has four logical192x352 frames in one row.
  sh=Image.new('RGB',(768*2,398*((len(ims)+1)//2)),(156,167,172));dr=ImageDraw.Draw(sh)
  for i,im in enumerate(ims):sh.paste(im,(i%2*768,i//2*398));dr.text((i%2*768+3,i//2*398+378),f'Actual MP4 mediaTime {v["frames"][i]["mediaTime"]}',fill='black')
  # Split by six frames so every pixel remains inspectable in bounded sheets.
  for block in range(2):sh.crop((0,block*3*398,1536,(block+1)*3*398)).save(R/'sheets'/f'video-all4-part{block+1}.png')
 else:
  sh=Image.new('RGB',(6*192,2*372),(156,167,172));dr=ImageDraw.Draw(sh)
  for i,im in enumerate(ims):im=im.resize((192,352),Image.Resampling.LANCZOS);xy=(i%6*192,i//6*372);sh.paste(im,xy);dr.text((xy[0]+2,xy[1]+353),f'{name} f{i+1}',fill='black')
  sh.save(R/'sheets'/f'video-{name}.png')
 rows.append({'declaredPath':v['declaredPath'],'decodedFrames':len(v['frames']),'duration':v['duration'],'playbackRate':v['playbackRate'],'elapsedMs':v['elapsed'],'quality':v['quality'],'mediaTimes':[f['mediaTime'] for f in v['frames']],'callbackDeltaMs':[v['frames'][i]['callbackNow']-v['frames'][i-1]['callbackNow'] for i in range(2,len(v['frames']))]})
(R/'video-coverage.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
