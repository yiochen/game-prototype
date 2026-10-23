import sys,pathlib,json,hashlib
sys.dont_write_bytecode=True
from PIL import Image,ImageChops,ImageDraw
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[7];PROD=ROOT/'prototypes/sushi-loop/assets/production';E=P/'evidence'
records={};sheet=Image.new('RGB',(384*4,704),(144,144,144))
for j,d in enumerate('NESW'):
 raw=Image.open(E/f'original-{d}-4x.png').convert('RGBA');replay=raw.resize((384,704),Image.Resampling.LANCZOS);out=E/f'original-{d}-2x.png';replay.save(out,compress_level=9)
 known=PROD/f'sprites/rock-shelf-corner/static-{d}.png';old=Image.open(known).convert('RGBA');diff=ImageChops.difference(old,replay);vals=list(diff.getdata());records[d]={'historicalPath':str(known),'historicalSHA256':hashlib.sha256(known.read_bytes()).hexdigest(),'replaySHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'equalRGBA':old.tobytes()==replay.tobytes(),'equalPNGBytes':known.read_bytes()==out.read_bytes(),'differentPixels':sum(any(p) for p in vals),'maxRGBA':[max(p[k] for p in vals) for k in range(4)]}
 bg=Image.new('RGBA',old.size,(144,144,144,255));bg.alpha_composite(replay);sheet.paste(bg.convert('RGB'),(384*j,0));ImageDraw.Draw(sheet).text((384*j+10,10),d,fill='white')
sheet.save(E/'historical-replay-all4.png');(E/'historical-replay-comparison.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
