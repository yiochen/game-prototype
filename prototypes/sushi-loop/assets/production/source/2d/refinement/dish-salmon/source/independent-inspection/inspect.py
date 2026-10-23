from pathlib import Path
import hashlib,json
from PIL import Image,ImageDraw
O=Path(__file__).resolve().parents[2]
D=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
records={}
frames={}
for key,rel in [('original','inputs/original.png'),('target','inputs/target.png')]:
 p=O/rel;im=Image.open(p).convert('RGBA');a=im.getchannel('A');bounds=a.point(lambda v:255 if v>8 else 0).getbbox();cut=im.crop(bounds)
 if key=='original':frame=im
 else:
  cut=cut.resize((132,round(cut.height/cut.width*132)),Image.Resampling.LANCZOS)
  frame=Image.new('RGBA',(384,640));frame.alpha_composite(cut,(round(192-cut.width/2),round(496-cut.height/2)))
 frames[key]=frame
 records[key]={'path':rel,'sha256':sha(p),'size':im.size,'boundsAlpha0':a.getbbox(),'boundsAlpha8':bounds,'normalizedBounds':frame.getchannel('A').getbbox(),'normalizedSize':frame.size}
 frame.save(D/f'{key}-registered.png')
canvas=Image.new('RGB',(800,418),(230,225,216));d=ImageDraw.Draw(canvas)
for r,(bgname,bg) in enumerate([('light',(246,241,229)),('gray',(125,126,129)),('dark',(30,33,39))]):
 d.text((8,r*138+4),bgname,fill=(0,0,0))
 for c,(key,f) in enumerate(frames.items()):
  cut=f.crop((112,438,272,554))
  pane=Image.new('RGBA',(160,116),bg+(255,));pane.alpha_composite(cut)
  canvas.paste(pane.convert('RGB'),(90+c*350,r*138+18))
  logical=cut.resize((80,58),Image.Resampling.LANCZOS);pane=Image.new('RGBA',(80,58),bg+(255,));pane.alpha_composite(logical)
  canvas.paste(pane.convert('RGB'),(258+c*350,r*138+47))
  d.text((90+c*350,r*138+4),key+' native132 / logical66',fill=(0,0,0))
canvas.save(D/'target-vs-original-actual-widths.png')
(D/'observations.json').write_text(json.dumps({'independent':True,'readBeforeJudgeOrCriteria':True,'records':records,'observations':['Target preserves salmon nigiri on round ivory saucer, coral-orange broad stripes and high oblique camera.','Target softens fish surfaces, warmer rice clusters and continuous ceramic edge.','Target raw alpha>0 includes low-opacity far-out pixels; alpha>8 crop once is authorized existing publisher operation.','No target role or camera conflict. Existing2D source and no Blender geometry.','Native132 and logical66 width previews retain large stripe/white rice/plate distinction.']},indent=2)+'\n')
