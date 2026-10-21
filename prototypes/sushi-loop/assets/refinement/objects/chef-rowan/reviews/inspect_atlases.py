from PIL import Image,ImageDraw
import json,pathlib,hashlib
b=pathlib.Path('prototypes/sushi-loop/assets/refinement/objects/chef-rowan').resolve(); p=pathlib.Path('prototypes/sushi-loop/assets/production').resolve(); out=b/'reviews/original-atlas-evidence';out.mkdir(exist_ok=True)
c=json.loads((b/'inputs/catalog-object.json').read_text()); result=[]
for clip in c['clips']:
 for facing,rec in clip['directions'].items():
  path=p/rec['image']; a=Image.open(path).convert('RGBA'); frames=[]
  for ix,(x,y,w,h) in enumerate(rec['rects']):
   f=a.crop((x,y,x+w,y+h)); f.save(out/f'{clip["id"]}-{facing}-{ix:02}.png'); frames.append(f)
  logical=[f.resize((192,320),Image.Resampling.LANCZOS) for f in frames]
  # All12 full registered frames, scaled uniformly to logical use-size, plus labels.
  sheet=Image.new('RGB',(192*6,336*2),(112,118,124));d=ImageDraw.Draw(sheet)
  for ix,f in enumerate(logical):
   x=(ix%6)*192;y=(ix//6)*336;sheet.paste(f,(x,y+16),f);d.text((x+4,y+2),f'{clip["id"]}-{facing} {ix:02}',fill='white')
  sheet.save(out/f'all12-{clip["id"]}-{facing}.png')
  result.append({'clip':clip['id'],'facing':facing,'atlas':str(path),'atlasSHA256':hashlib.sha256(path.read_bytes()).hexdigest(),'dimensions':list(a.size),'frames':len(frames),'frameDimensions':list(frames[0].size),'alphaBounds':[f.getbbox() for f in frames]})
# Each facing at intended size, every frame cropped identically for readable sheet.
for facing in ['N','E','S','W']:
 sheet=Image.new('RGB',(6*128,8*216),(146,150,155));d=ImageDraw.Draw(sheet)
 for ci,clip in enumerate(['idle','work','hold','load']):
  for ix in range(12):
   im=Image.open(out/f'{clip}-{facing}-{ix:02}.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS).crop((32,64,160,264))
   x=(ix%6)*128;y=(ci*2+ix//6)*216;sheet.paste(im,(x,y+16),im);d.text((x+2,y+2),f'{clip} {facing} {ix:02}',fill=(25,30,35))
 sheet.save(out/f'all48-{facing}-logical-crops.png')
(out/'extraction.json').write_text(json.dumps({'method':'Lossless extraction from unchanged original native published atlases; full frames are384x640; contact sheets uniformly reduced to logical192x320. Guide source-capture hashes bind absent768x1280 raws and cannot equal these downsampled atlas crops. Atlas SHA256 recorded directly.','atlases':result},indent=2))
print(json.dumps({'atlases':len(result),'frames':sum(r['frames'] for r in result),'ranges':[{'clip':r['clip'],'facing':r['facing'],'bbox0':r['alphaBounds'][0]} for r in result]}))
