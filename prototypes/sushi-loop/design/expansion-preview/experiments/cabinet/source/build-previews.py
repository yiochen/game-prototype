from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent.parent;p=E/'candidates/round-01';sheet=Image.new('RGB',(1600,800),'#344c59');d=ImageDraw.Draw(sheet);bounds={};report={};edges=Image.new('RGB',(1200,1100),'#fff1d3');ed=ImageDraw.Draw(edges)
for i,f in enumerate(['N','E','S','W']):
 im=Image.open(p/(f+'.png')).convert('RGBA');b=im.getbbox();bounds[f]=[b[0],b[1],b[2]-b[0],b[3]-b[1]]
 # Identical crop and uniform scale across four facings. Independent from export fitting.
 cr=im.crop((185,430,710,1125)).resize((368,487),Image.Resampling.LANCZOS);sheet.paste(cr,(i*400+16,35),cr);d.text((i*400+20,15),f,fill='white');sc=390/7/256;small=im.resize((round(896*sc),round(1344*sc)),Image.Resampling.LANCZOS);sheet.paste(small,(i*400+102,470),small);d.text((i*400+20,770),'390/7 px per cell',fill='white')
 x=i%2*600;y=i//2*550;edgecr=im.crop((185,430,710,1125));edgecr.thumbnail((560,500));edges.paste(edgecr,(x+20,y+30),edgecr);ed.text((x+20,y+10),f,fill='#4c3927')
 alpha=im.getchannel('A');report[f]={'sha256':hashlib.sha256((p/(f+'.png')).read_bytes()).hexdigest(),'frame':list(im.size),'alphaBBox':list(b),'edgeAlphaMax':max([alpha.crop((0,0,im.width,1)).getextrema()[1],alpha.crop((0,im.height-1,im.width,im.height)).getextrema()[1],alpha.crop((0,0,1,im.height)).getextrema()[1],alpha.crop((im.width-1,0,im.width,im.height)).getextrema()[1]]),'transparentPixelCount':sum(a==0 for a in alpha.get_flattened_data()),'opaquePixelCount':sum(a==255 for a in alpha.get_flattened_data())}
sheet.save(p/'four-view-sheet.png');edges.save(p/'alpha-edges.png');(p/'alpha-bounds.json').write_text(json.dumps(bounds,indent=2)+'\n');(p/'alpha-report.json').write_text(json.dumps(report,indent=2)+'\n')
