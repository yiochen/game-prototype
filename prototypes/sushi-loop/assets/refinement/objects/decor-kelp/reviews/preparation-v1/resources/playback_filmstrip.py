from pathlib import Path
from PIL import Image,ImageDraw,ImageSequence
import json
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'evidence';gif=Image.open(OUT/'historical-playback.gif');sheet=Image.new('RGB',(1152,960),'#d8ddd7');d=ImageDraw.Draw(sheet);mapping=[]
for i,frame in enumerate(ImageSequence.Iterator(gif)):
 im=frame.convert('RGB').resize((384,240),Image.Resampling.LANCZOS);x=i%3*384;y=i//3*240;sheet.paste(im,(x,y));d.text((x+4,y+4),f'published frame{i} S/E/N/W',fill='black');mapping.append({'gifFrame':i,'durationMs':frame.info.get('duration'),'atlasFrameIndex':i,'directions':['S','E','N','W']})
sheet.save(OUT/'historical-playback-filmstrip.png');(OUT/'playback-mapping.json').write_text(json.dumps({'source':'historical-playback.gif','method':'Every decoded GIF frame shown once, four facings; GIF is derived from exact own original published atlases at logical size; palette quantization is presentation only.','mapping':mapping},indent=2)+'\n')
