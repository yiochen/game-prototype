from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
import hashlib,json
B=Path(__file__).resolve().parents[2];obj=B.parents[1];O=B/'evidence';C=obj/'candidates/round-04';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((C/'round-comparison-record.json').read_text());rows=[]
canvas=Image.new('RGB',(832,948),(220,227,229));dr=ImageDraw.Draw(canvas)
for row,r in enumerate(['round-03','round-04']):
 for col,d in enumerate('NESW'):
  image=Image.open((B/'resources/comparison-inputs'/f'candidates/{r}/frames/static/{d}/000.png') if r!='round-04' else (obj/f'candidates/{r}/frames/static/{d}/000.png')).convert('RGBA').resize((192,352),Image.Resampling.BOX);bg=Image.new('RGBA',image.size,(239,239,229,255));bg.alpha_composite(image);canvas.paste(bg.convert('RGB'),(col*208+8,row*382+24));dr.text((col*208+8,row*382+6),f'{r} / {d} / cell128',fill=(10,20,30))
for col,r in enumerate(record['records']):
 p=(B/'resources/comparison-inputs'/r['source']) if r['round']!='round-04' else obj/r['source'];im=Image.open(p).convert('RGBA');box=r['sameExactIntegerCrop'];assert sha(p)==r['sourceSHA256'];assert all(type(v)==int for v in box)
 crop=im.crop(box);restored=Image.new('RGBA',im.size,(0,0,0,0));restored.paste(crop,box[:2]);exact=restored.tobytes()==im.tobytes();mask=Image.new('L',im.size,255);ImageDraw.Draw(mask).rectangle([box[0],box[1],box[2]-1,box[3]-1],fill=0)
 removed=sum(1 for a,m in zip(im.getchannel('A').getdata(),mask.getdata()) if a and m);assert exact and removed==0
 small=crop.resize((crop.width//2,crop.height//2),Image.Resampling.BOX);bg=Image.new('RGBA',small.size,(122,137,148,255));bg.alpha_composite(small);canvas.paste(bg.convert('RGB'),(col*416+8,794));dr.text((col*416+8,774),f"{r['round']} / full visible native S run / cell128",fill=(10,20,30))
 rows.append({'round':r['round'],'source':r['source'],'sourceSHA256':sha(p),'integerCrop':box,'exactRGBAIntegerRestoration':exact,'discardedVisiblePixels':removed,'fullSize':im.size,'scope':'Only lower comparison panels; published/native/consumer full sprites unchanged.'})
submitted=Image.open(C/'round-comparison.png').convert('RGB');assert canvas.size==submitted.size and canvas.tobytes()==submitted.tobytes()
canvas.save(O/'independent-round-comparison.png')
strips=[]
for mode in ['full-chromium','headless-shell']:
 for case in ['logical128-integer','logical128-fractional']:
  src=C/f'consumer/{mode}-{case}.png';im=Image.open(src);d=O/'desktop-strips'/f'{mode}-{case}';d.mkdir(parents=True,exist_ok=True)
  for i,y in enumerate(range(0,im.height,1600)):
   box=(0,y,im.width,min(y+1600,im.height));dst=d/f'{i}.png';im.crop(box).save(dst);strips.append({'source':str(src.relative_to(C)),'crop':box,'path':str(dst.relative_to(obj)),'noRescale':True})
(O/'comparison-padding-audit.json').write_text(json.dumps({'records':rows,'wholeComparisonDecodedRGBEqual':True,'comparisonSize':canvas.size,'desktopFullResolutionStrips':strips},indent=2)+'\n');print(json.dumps({'exactRestoration':all(x['exactRGBAIntegerRestoration'] for x in rows),'visibleDiscard':sum(x['discardedVisiblePixels'] for x in rows),'wholeComparisonEqual':True,'desktopStrips':len(strips)}))
