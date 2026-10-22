from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,shutil,hashlib
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'evidence'/'historical-adapter-replay';ROOT=BASE.parents[2]
sheet=Image.new('RGB',(960,1280),'#d8ddd7');draw=ImageDraw.Draw(sheet)
for row,direction in enumerate(['S','E','N','W']):
 for col,frame in enumerate([1,4,7,10,13]):
  im=Image.open(OUT/'native'/direction/f'{frame:02d}.png').convert('RGBA').resize((120,300),Image.Resampling.LANCZOS);sheet.paste(im,(col*192+36,row*320+18),im);draw.text((col*192+10,row*320+4),f'{direction} native {frame}'+(' closure'if frame==13 else ''),fill='black')
sheet.save(OUT/'native-phase-sheet.png')
# Original published input and honest current-version replay comparison.
orig=Image.open(BASE/'object/inputs/original.png').convert('RGBA');replay=Image.open(OUT/'native/S/01.png').convert('RGBA').resize(orig.size,Image.Resampling.LANCZOS);replay.save(OUT/'replay-published-S01.png')
diff=ImageChops.difference(orig,replay); pixels=list(diff.getdata());visible=[p for p in pixels if any(p)];(OUT/'replay-comparison.json').write_text(json.dumps({'method':'Complete native4x canvas reduced uniformly to published2x with Pillow LANCZOS; no fitting/repair','originalSize':orig.size,'replaySize':replay.size,'RGBAmaxDifference':max(max(p)for p in pixels),'differentPixels':len(visible),'totalPixels':len(pixels),'alphaMaxDifference':max(p[3]for p in pixels),'limits':'Current Blender5.2.2 + 32 EEVEE samples replay may differ from historical version/sample settings; report visible differences rather than claim byte parity.'},indent=2)+'\n')
comp=Image.new('RGB',(768,960),'#d8ddd7');comp.paste(orig,(0,0),orig);comp.paste(replay,(384,0),replay);comp.save(OUT/'original-vs-replay.png')
