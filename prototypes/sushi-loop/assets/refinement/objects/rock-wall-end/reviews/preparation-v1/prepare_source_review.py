from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import hashlib,json
OUT=Path(__file__).resolve().parent
comparisons={}
sheet=Image.new('RGB',(192*4,352*2+26*2),'#808080');draw=ImageDraw.Draw(sheet)
for i,f in enumerate('NESW'):
 native=Image.open(OUT/f'source-baseline/native-{f}.png').convert('RGBA')
 for filter in ['BOX','LANCZOS']:
  native.resize((384,704),getattr(Image.Resampling,filter)).save(OUT/f'source-baseline/published-{filter}-{f}.png')
 old=Image.open(OUT/f'resources/source-catalog/static-{f}.png').convert('RGBA')
 new=Image.open(OUT/f'source-baseline/published-LANCZOS-{f}.png').convert('RGBA')
 diff=ImageChops.difference(old,new)
 comparisons[f]={'legacySourceSHA256':hashlib.sha256((OUT/f'resources/source-catalog/static-{f}.png').read_bytes()).hexdigest(),'newNativeSHA256':hashlib.sha256((OUT/f'source-baseline/native-{f}.png').read_bytes()).hexdigest(),'exactLegacyRGBAReplay':old.tobytes()==new.tobytes(),'diffExtrema':diff.getextrema(),'reasonIfDifferent':'New source pipeline render is diagnostic; immutable legacy catalog bytes remain authority for original snapshot, and Blender5.2 may differ from historical capture runtime.'}
 for row,image in enumerate([old,new]):
  tile=image.resize((192,352),Image.Resampling.BOX)
  y=row*378+26;sheet.paste(tile,(i*192,y),tile)
  draw.text((i*192+8,row*378+8),f'{f} '+('historical catalog' if row==0 else 'new original replay'),fill='white')
sheet.save(OUT/'source-all4-comparison.png')
(OUT/'source-replay-comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n')
