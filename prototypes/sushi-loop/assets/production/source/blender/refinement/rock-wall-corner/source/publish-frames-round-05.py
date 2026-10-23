from pathlib import Path
from PIL import Image
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05'
for d in ['N','E','S','W']:
 im=Image.open(O/f'native-static-{d}.png').convert('RGBA');assert im.size==(768,1408);im.resize((384,704),Image.Resampling.BOX).save(O/f'published-static-{d}.png')
