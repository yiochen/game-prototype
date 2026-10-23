import sys
sys.dont_write_bytecode=True
from PIL import Image,ImageChops,ImageDraw
from pathlib import Path
import json,hashlib,PIL
B=Path(__file__).resolve().parents[1];E=B/'evidence/source-replay';findings=[]
bgs=[('light',(246,246,242,255)),('gray',(128,128,128,255)),('dark',(24,30,38,255))]
# Full registered frame crops here are review media only. Native PNGs remain untouched.
sheet=Image.new('RGB',(4*320,2*398),(128,128,128));dr=ImageDraw.Draw(sheet)
use=Image.new('RGB',(4*300,3*250),(246,246,242));du=ImageDraw.Draw(use)
for col,d in enumerate(['N','E','S','W']):
 raw=Image.open(E/('historical4x-filter1.5-'+d+'.png')).convert('RGBA');hist=raw.resize((384,704),Image.Resampling.LANCZOS);hist.save(E/('historical-published2x-'+d+'.png'))
 direct=Image.open(E/('direct2x-filter.01-control-'+d+'.png')).convert('RGBA')
 diff=ImageChops.difference(hist,direct);n=sum(any(x) for x in diff.getdata());maxs=[ch.getextrema()[1] for ch in diff.split()]
 findings.append({'direction':d,'historicalNativeSize':list(raw.size),'historicalPublishedSize':list(hist.size),'directNativeSize':list(direct.size),'historicalVsDirectDifferingPixels':n,'maximumRGBAChannelDifferences':maxs,'logicalRegistration':'fixed192x352/root96,248/cell128; native2x root192,496','historicalReduction':'Pillow12.3.0 Image.Resampling.LANCZOS; baseline review only'})
 for row,im in enumerate([hist,direct]):
  # Fixed frame viewport, identical in both policies: no art fit/candidate modification.
  crop=im.crop((32,256,352,640));bg=Image.new('RGBA',crop.size,(128,128,128,255));bg.alpha_composite(crop);sheet.paste(bg.convert('RGB'),(col*320,row*398+14));dr.text((col*320+4,row*398+1),('historical4x→2x ' if row==0 else 'direct2x source control ')+d,fill=(255,255,255))
 for row,(bn,bgcolor) in enumerate(bgs):
  x=col*300;y=row*250;panel=Image.new('RGBA',(300,250),bgcolor);p=Image.new('RGBA',(192,352),(0,0,0,0));p.alpha_composite(direct.resize((192,352),Image.Resampling.LANCZOS));p=p.crop((0,128,192,320));panel.alpha_composite(p,(4,32));phone=direct.resize((48,88),Image.Resampling.LANCZOS);panel.alpha_composite(phone,(232,80));use.paste(panel.convert('RGB'),(x,y));du.text((x+4,y+4),d+' / '+bn+' / cell128 + phone32',fill=(50,50,50) if bn!='dark' else (235,235,235))
orig=Image.open(B/'resources/original.png').convert('RGBA');histS=Image.open(E/'historical-published2x-S.png').convert('RGBA');delta=ImageChops.difference(orig,histS);df=[ch.getextrema()[1] for ch in delta.split()]
report={'stage':'Source replay/control only; no art or seam approval','pillow':PIL.__version__,'policies':findings,'originalSnapshotComparisonS':{'decodedRGBAExact':all(v==0 for v in df),'maximumRGBAChannelDifferences':df,'differingPixels':sum(any(x) for x in delta.getdata())},'sheetPolicy':'Comparison sheets use fixed registered crop and Pillow scaling for visual inspection only. Raw native PNGs never edited or overwritten. These are not actual browser CSS screenshots.','inspectionMedia':['evidence/source-replay-policy-sheet.png','evidence/source-replay-use-size-sheet.png'],'limits':['Historical replay validates bounded registration/source identity. Its ring sampling and native sparse source aesthetics are not approved.','Direct2x original source remains historical material/light; final derivative must adopt exact canonical field/light recipe after root freeze.']}
(B/'evidence/source-replay-policy-sheet.png').parent.mkdir(exist_ok=True);sheet.save(B/'evidence/source-replay-policy-sheet.png');use.save(B/'evidence/source-replay-use-size-sheet.png');(B/'source-replay-findings.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
