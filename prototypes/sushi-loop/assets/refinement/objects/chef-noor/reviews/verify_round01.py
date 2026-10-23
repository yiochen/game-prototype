from PIL import Image,ImageDraw,ImageChops
from pathlib import Path
import hashlib,json,subprocess
b=Path('prototypes/sushi-loop/assets/refinement/objects/chef-noor');c=b/'candidates/round-01';out=b/'reviews';p=json.loads((c/'packet.json').read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
report={'packetSHA256':sha(c/'packet.json'),'hashMismatches':[],'hashedFileCount':0,'atlasFrameMismatches':[],'sheetCellMismatches':[],'videoProbes':[],'judgeMontages':[]}
for group in ['files','candidateRenders','previews']:
 for name,rec in p[group].items():
  f=(c/rec['path']).resolve();report['hashedFileCount']+=1
  if not f.exists() or sha(f)!=rec['sha256']:report['hashMismatches'].append([group,name,rec['path']])
raw=json.loads((c/'native-frames.json').read_text());look={(r['clip'],r['direction'],r['index']):r for r in raw}
for r in raw:
 f=b/r['path']
 if sha(f)!=r['sha256']:report['hashMismatches'].append(['nativeFrame',r['path']])
for atlas in json.loads((c/'atlas-manifest.json').read_text()):
 ai=Image.open(b/atlas['path']).convert('RGBA');assert ai.size==(2304,1280)
 for r in atlas['frames']:
  x,y,w,h=r['rect'];fi=Image.open(b/r['nativeFrame']).convert('RGBA')
  if ai.crop((x,y,x+w,y+h)).tobytes()!=fi.tobytes():report['atlasFrameMismatches'].append(r['nativeFrame'])
colors={'light':'#EFEBE1','gray':'#7C7C7C','dark':'#191D24'}
for clip in ['idle','work','hold','load']:
 for bg,col in colors.items():
  montage=Image.new('RGB',(1920,960),col);dr=ImageDraw.Draw(montage)
  covered=[]
  for row,d in enumerate(['N','E','S','W']):
   f=c/'sheets'/f'{clip}-{d}-{bg}.png';im=Image.open(f).convert('RGB');assert im.size==(1152,688);covered.append(str(f.relative_to(c)))
   for i in range(12):
    x=(i%6)*192;y=(i//6)*344+24
    cell=im.crop((x,y,x+192,y+320))
    native=Image.open(b/look[(clip,d,i)]['path']).convert('RGBA').resize((192,320),Image.Resampling.LANCZOS)
    flat=Image.new('RGBA',(192,320),col);flat.alpha_composite(native)
    if cell.tobytes()!=flat.convert('RGB').tobytes():report['sheetCellMismatches'].append([clip,d,bg,i])
    montage.paste(cell.crop((16,56,176,272)),(i*160,row*240+24))
    dr.text((i*160+4,row*240+4),f'{clip} {d} {i}',fill='#EDE9DD' if bg=='dark' else '#1D2430')
  mf=out/f'round01-{clip}-{bg}-verified.png';montage.save(mf);report['judgeMontages'].append({'path':str(mf.relative_to(b)),'covers':covered,'sheetCellsPixelExact':True,'display':'constant crop from original logical size, no per-frame fit or recolor'})
for name,r in p['previews'].items():
 if not r['path'].endswith('.mp4'):continue
 f=c/r['path'];pr=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,avg_frame_rate,r_frame_rate,nb_read_frames,duration','-of','json',str(f)]))
 report['videoProbes'].append({'path':r['path'],'probe':pr})
(out/'round01-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('hash entries',report['hashedFileCount'],'mismatches',report['hashMismatches'])
print('atlas mismatches',report['atlasFrameMismatches'],'sheet mismatches',report['sheetCellMismatches'])
print('probed videos',len(report['videoProbes']),'montages',len(report['judgeMontages']))
