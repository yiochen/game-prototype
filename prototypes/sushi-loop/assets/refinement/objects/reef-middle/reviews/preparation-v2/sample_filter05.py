import sys
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image
b=Path(__file__).resolve().parent/'evidence/study-filter05'
for d in ['N','E','S','W']:
 for name in ['single','three-joined']:
  a=Image.open(b/'native'/(name+'-'+d+'.png')).convert('RGBA');p=b/'packed'/(name+'-'+d);p.mkdir(parents=True);a.resize((a.width//2,a.height//2),Image.Resampling.BOX).save(p/'sheet.png')
