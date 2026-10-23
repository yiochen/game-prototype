from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np,subprocess
b=Path(__file__).resolve().parents[1];c=b/'candidates/round-02';out=b/'reviews';p=json.loads((c/'packet.json').read_text());delivery=json.loads((c/'delivery.snapshot.json').read_text());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();r={'packetSHA256':sha(c/'packet.json'),'hashEntriesChecked':0,'hashMismatches':[],'atlasCellMismatches':[],'singleSheetCellMismatches':[],'pairedSheetCellMismatches':[],'phoneCellMismatches':[],'montages':[],'videoProbes':[],'hiddenFrameMaxRGBA':[0,0,0,0]}
for group in ['files','candidateRenders','previews']:
 for name,v in p[group].items():
  f=(c/v['path']).resolve();r['hashEntriesChecked']+=1
  if not f.exists() or sha(f)!=v['sha256']:r['hashMismatches'].append([group,name,v['path']])
raw=delivery['rawFrames'];look={(x['clip'],x['direction'],x['index']):x for x in raw};bg={'light':'#f3eee2','gray':'#858b8b','dark':'#202a31'}
def frame(clip,d,i,old=False):return Image.open(b/'candidates'/('round-01' if old else 'round-02')/'frames'/f'{clip}-{d}'/f'{i:03d}.png').convert('RGBA')
def flat(im,col):
 f=Image.new('RGBA',im.size,col);f.alpha_composite(im);return f.convert('RGB')
for a in delivery['atlases']:
 ai=Image.open(b/a['path']).convert('RGBA');assert ai.size==(2304,1280)
 for i,rect in enumerate(a['rects']):
  x,y,w,h=rect
  if ai.crop((x,y,x+w,y+h)).tobytes()!=frame(a['clip'],a['direction'],i).tobytes():r['atlasCellMismatches'].append([a['clip'],a['direction'],i])
for clip in ['idle','work','hold','load']:
 for name,col in bg.items():
  active=clip in ['hold','load'];montage=Image.new('RGB',(1920,1920 if active else 960),col);dr=ImageDraw.Draw(montage);covers=[]
  for di,d in enumerate(['N','E','S','W']):
   single=c/'contact-sheets'/f'{clip}-{d}-{name}.png';si=Image.open(single).convert('RGB');covers.append(str(single.relative_to(c)))
   pair=c/'contact-sheets'/f'{clip}-{d}-source-canonical-{name}.png';pi=Image.open(pair).convert('RGB') if active else None
   if active:covers.append(str(pair.relative_to(c)))
   for i in range(12):
    new=frame(clip,d,i);logical=flat(new.resize((192,320),Image.Resampling.LANCZOS),col);x=i%6*192;y=i//6*352+28;sc=si.crop((x,y,x+192,y+320))
    if logical.tobytes()!=sc.tobytes():r['singleSheetCellMismatches'].append([clip,d,name,i])
    versions=[False,True] if active else [True]
    for vi,isnew in enumerate(versions):
     cell=logical if isnew else flat(frame(clip,d,i,True).resize((192,320),Image.Resampling.LANCZOS),col)
     if active:
      px=i%6*384+vi*192;py=i//6*352+28;pc=pi.crop((px,py,px+192,py+320))
      if pc.tobytes()!=cell.tobytes():r['pairedSheetCellMismatches'].append([clip,d,name,i,vi])
      cell=pc
     row=di*2+vi if active else di;montage.paste(cell.crop((16,56,176,272)),(i*160,row*240+24));dr.text((i*160+3,row*240+4),f'{clip} {d} {i} '+('new' if isnew else 'source'),fill='#efefef' if name=='dark' else '#1d2430')
   if clip in ['idle','work']:
    for i in range(12):
     dif=np.abs(np.asarray(frame(clip,d,i)).astype(int)-np.asarray(frame(clip,d,i,True)).astype(int)).max(axis=(0,1));r['hiddenFrameMaxRGBA']=np.maximum(r['hiddenFrameMaxRGBA'],dif).tolist()
  mf=out/f'round02-{clip}-{name}-verified.png';montage.save(mf);r['montages'].append({'path':str(mf.relative_to(b)),'covers':covers,'method':'Every cell verified against original/new raw frames; constant logical crop[16,56,176,272], no fitting/recolor.'})
for name,v in p['previews'].items():
 if v['path'].endswith('.mp4'):
  probe=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,avg_frame_rate,r_frame_rate,nb_read_frames,duration','-of','json',str(c/v['path'])]));r['videoProbes'].append({'path':v['path'],'probe':probe})
for d in ['N','E','S','W']:
 ph=Image.open(c/'phone'/f'all24-source-canonical-{d}.png');assert ph.size==(390,844)
# Control outputs are independently compared below by their declared settings/paths; no old/new bodyRGB identity is assumed.
(out/'round02-verification.json').write_text(json.dumps(r,indent=2)+'\n');print('hash',r['hashEntriesChecked'],r['hashMismatches']);print('atlas/sheets',len(r['atlasCellMismatches']),len(r['singleSheetCellMismatches']),len(r['pairedSheetCellMismatches']));print('hiddenMax',r['hiddenFrameMaxRGBA'],'videos',len(r['videoProbes']))
