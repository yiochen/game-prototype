from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw,ImageChops,ImageStat
OBJ=Path(__file__).resolve().parent.parent;OUT=OBJ/'candidates/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=[]
for d in 'NESW':
 p=OUT/'native/static'/d/'000.png';im=Image.open(p).convert('RGBA');assert im.size==(768,1408)
 pub=im.resize((384,704),Image.Resampling.LANCZOS)
 f=OUT/'frames/static'/d/'000.png';f.parent.mkdir(parents=True,exist_ok=True);pub.save(f)
 atlas=OUT/'atlases'/('static-'+d+'.png');atlas.parent.mkdir(exist_ok=True);shutil.copyfile(f,atlas)
 consumer=OBJ/'source/round-01-resources/consumer/sprites/decor-background-rock'/('static-'+d+'.png');consumer.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(atlas,consumer)
 records.append({'direction':d,'native':str(p.relative_to(OBJ)),'nativeSHA256':sha(p),'nativeSize':list(im.size),'published':str(f.relative_to(OBJ)),'publishedSHA256':sha(f),'publishedSize':list(pub.size),'method':'Pillow uniform whole-canvas LANCZOS','noCropFitOrPixelRepair':True,'alphaBoundsNative':list(im.getbbox()),'alphaBoundsPublished':list(pub.getbbox()),'alphaDoesNotTouchCanvas':all([pub.getbbox()[0]>0,pub.getbbox()[1]>0,pub.getbbox()[2]<384,pub.getbbox()[3]<704])})
for layer,size in [('native',(768,1408)),('frames',(384,704))]:
 sheet=Image.new('RGBA',(size[0]*4,size[1]+32),(227,233,232,255));draw=ImageDraw.Draw(sheet)
 for i,d in enumerate('NESW'):
  im=Image.open(OUT/layer/'static'/d/'000.png').convert('RGBA');sheet.alpha_composite(im,(i*size[0],32));draw.text((i*size[0]+12,10),d,fill='#172B38')
 sheet.save(OUT/('four-view-'+('native' if layer=='native' else 'published')+'.png'))
# Registered full logical and64px-cell use; transparent full frame resized uniformly, never fit.
sheet=Image.new('RGB',(192*12,352+176+64),'#E9EFEC');draw=ImageDraw.Draw(sheet)
for bgidx,(label,col) in enumerate([('light','#F1F0E8'),('gray','#839097'),('dark','#132A37')]):
 for i,d in enumerate('NESW'):
  x=(bgidx*4+i)*192
  for y,size in [(32,(192,352)),(416,(96,176))]:
   tile=Image.new('RGBA',size,col);im=Image.open(OUT/'frames/static'/d/'000.png').convert('RGBA').resize(size,Image.Resampling.LANCZOS);tile.alpha_composite(im);sheet.paste(tile,(x,y))
  draw.text((x+6,8),label+' '+d,fill='#132A37');draw.text((x+6,392),'64px cell '+d,fill='#132A37')
sheet.save(OUT/'logical-and-small-neutral-backgrounds.png')
(OUT/'publication.json').write_text(json.dumps({'pathBase':'object root','publishedFrame':[384,704],'nativeFrame':[768,1408],'resampling':'LANCZOS','wholeFrameScale':.5,'records':records},indent=2)+'\n')
print('Published',len(records))
