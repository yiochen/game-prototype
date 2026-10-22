"""Registered previous/current full-canvas comparison with zero-visible-discard context."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops
P=Path(__file__).resolve().parents[1];O=P/'candidates/round-04'
canvas=Image.new('RGB',(832,948),(220,227,229));dr=ImageDraw.Draw(canvas)
for row,r in enumerate(['round-03','round-04']):
 for col,d in enumerate('NESW'):
  im=Image.open(P/f'candidates/{r}/frames/static/{d}/000.png').convert('RGBA').resize((192,352),Image.Resampling.BOX);bg=Image.new('RGBA',(192,352),(239,239,229,255));bg.alpha_composite(im);canvas.paste(bg.convert('RGB'),(col*208+8,row*382+24));dr.text((col*208+8,row*382+6),f'{r} / {d} / cell128',fill=(10,20,30))
images=[Image.open(P/f'candidates/{r}/joins/native-S-published.png').convert('RGBA') for r in ['round-03','round-04']]
a,b=[im.getchannel('A').getbbox() for im in images];bbox=(min(a[0],b[0])-8,min(a[1],b[1])-8,max(a[2],b[2])+8,max(a[3],b[3])+8)
# Choose even integer bounds so the same whole comparison reduction preserves2x->1x density.
bbox=tuple((v//2)*2 if i<2 else ((v+1)//2)*2 for i,v in enumerate(bbox));records=[]
for col,(r,im) in enumerate(zip(['round-03','round-04'],images)):
 crop=im.crop(bbox);restored=Image.new('RGBA',im.size);restored.paste(crop,bbox[:2]);diff=ImageChops.difference(im,restored)
 equal=all(e==(0,0) for e in diff.getextrema());assert equal,'Comparison-only padding removal discarded decoded pixels'
 small=crop.resize((crop.width//2,crop.height//2),Image.Resampling.BOX);bg=Image.new('RGBA',small.size,(122,137,148,255));bg.alpha_composite(small);canvas.paste(bg.convert('RGB'),(col*416+8,794));dr.text((col*416+8,774),f'{r} / full visible native S run / cell128',fill=(10,20,30))
 records.append({'round':r,'source':f'candidates/{r}/joins/native-S-published.png','sourceSHA256':hashlib.sha256((P/f'candidates/{r}/joins/native-S-published.png').read_bytes()).hexdigest(),'sameExactIntegerCrop':list(bbox),'sourceSize':list(im.size),'comparisonReduction':'Uniform BOX2x->1x; same density in both panels','decodedRGBAExactlyRestoredAtIntegerOffset':equal,'visibleDiscard':0,'scope':'Comparison-only transparent padding removal, no candidate or runtime art edit.'})
canvas.save(O/'round-comparison.png');(O/'round-comparison-record.json').write_text(json.dumps({'records':records,'logicalRootInComparisonCrop':[(448-bbox[0])/2,(768-bbox[1])/2],'method':'All4 upper panels retain complete authored frames. Lower registered S runs contain every actual visible pixel of the connected wall; exact integer restoration verified. No fitting or local pixel changes.'},indent=2)+'\n')
