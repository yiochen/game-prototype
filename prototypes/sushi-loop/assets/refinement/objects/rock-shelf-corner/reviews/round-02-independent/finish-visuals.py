import pathlib,json,sys
sys.dont_write_bytecode=True
from PIL import Image,ImageDraw,ImageChops
P=pathlib.Path(__file__).resolve().parent;C=P.parents[1]/'candidates/round-02';O=P/'analysis'
def rgba(p):return Image.open(p).convert('RGBA')
def bg(im):
 a=Image.new('RGBA',im.size,(144,144,144,255));a.alpha_composite(im);return a.convert('RGB')
for mode in ['chromium','headless-shell']:
 for fixture in ['L','W','N']:
  sheet=Image.new('RGB',(416*4,624*3),'#909090');dr=ImageDraw.Draw(sheet)
  for j,back in enumerate(['light','gray','dark']):
   for i,d in enumerate('NESW'):
    a=rgba(P/f'browser/{mode}/{fixture}-{d}-128-{back}-integer.png').crop((16,128,432,584)).convert('RGB');sheet.paste(a,(i*416,j*624+14));phone=rgba(P/f'browser/{mode}/{fixture}-{d}-32-{back}-integer.png');sheet.paste(phone.convert('RGB'),(i*416+152,j*624+470));dr.text((i*416+5,j*624),f'{mode} {fixture} {d}: actual cell128 / cell32',fill='#102335')
  sheet.save(O/f'{mode}-{fixture}-review-sheet.png')
sheet=Image.new('RGB',(900,760),'#909090');dr=ImageDraw.Draw(sheet)
for i,d in enumerate(['S','W']):
 im=rgba(C/f'frames/static/{d}/000.png');a=bg(im);crop=a.crop((60,498,324,628));sheet.paste(crop,(i*450,30));sheet.paste(crop.resize((396,195),Image.Resampling.NEAREST),(i*450,190));sheet.paste(bg(im.resize((192,352),Image.Resampling.BOX)),(i*450+20,400));sheet.paste(bg(im.resize((48,88),Image.Resampling.BOX)),(i*450+240,500));dr.text((i*450+6,6),f'{d}: 2x side / nearest zoom / logical128 / phone32',fill='white')
sheet.save(O/'exposed-side-evidence.png')
# Honest cross-browser sample location; do not infer complete pixel parity.
a=rgba(P/'browser/chromium/L-N-128-light-mixed.png');b=rgba(P/'browser/headless-shell/L-N-128-light-mixed.png');ds=list(ImageChops.difference(a,b).getdata());k=max(range(len(ds)),key=lambda k:max(ds[k]));x,y=k%a.width,k//a.width;r={'case':'L-N-128-light-mixed','maximumDifferencePoint':[x,y],'chromiumRGBA':a.getpixel((x,y)),'headlessRGBA':b.getpixel((x,y)),'maxRGBA':ds[k],'interpretation':'Source native canvases are exact across configurations; ordinary final CSS filtering differs. All per-case screenshot comparisons are retained. Inspect actual contours/joins rather than treating global max as a seam gate.'};(P/'browser-residual-example.json').write_text(json.dumps(r,indent=2)+'\n')
# Supplemental mixed phase at normal logical scale for each browser and facing.
for mode in ['chromium','headless-shell']:
 sheet=Image.new('RGB',(416*4,456*2),'#909090');dr=ImageDraw.Draw(sheet)
 for j,back in enumerate(['light','dark']):
  for i,d in enumerate('NESW'):
   a=rgba(P/f'browser/{mode}/L-{d}-128-{back}-mixed.png').crop((16,128,432,584)).convert('RGB');sheet.paste(a,(i*416,j*456))
 sheet.save(O/f'{mode}-mixed-review-sheet.png')
print(json.dumps(r,indent=2))
sheet=Image.new('RGB',(1024,1024),'#909090')
for row,(port,mode) in enumerate([(p,m) for p in ['W','N'] for m in ['albedo','normal']]):
 for col,role in enumerate(['reference','candidate']):sheet.paste(bg(rgba(P/f'cap-controls/{port}-{mode}-{role}.png')),(col*512,row*256))
sheet.save(O/'cap-independent-review-sheet.png')
