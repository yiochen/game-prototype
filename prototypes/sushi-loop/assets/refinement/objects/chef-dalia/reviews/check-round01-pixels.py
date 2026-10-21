from PIL import Image,ImageDraw
import json,pathlib,hashlib,subprocess
b=pathlib.Path(__file__).resolve().parents[1];p=b/'candidates/round-01';out=b/'reviews/round01-inspection';out.mkdir(exist_ok=True)
packet=json.loads((p/'packet.json').read_text());validation={'packetSHA256':hashlib.sha256((p/'packet.json').read_bytes()).hexdigest(),'allHashFailures':[],'rawFrameCount':0,'atlasChecks':[],'sheetChecks':[],'composites':[]}
for section in ['files','candidateRenders','previews']:
 for name,item in packet[section].items():
  f=p/item['path']
  if hashlib.sha256(f.read_bytes()).hexdigest()!=item['sha256']:validation['allHashFailures'].append([section,name])
frames=json.loads((p/'native-frames.json').read_text());validation['rawFrameCount']=len(frames)
for f in frames:
 z=b/f['path'];assert hashlib.sha256(z.read_bytes()).hexdigest()==f['sha256']
 assert Image.open(z).size==(384,640)
cat=json.loads((b/'inputs/catalog-object.json').read_text());BG={'light':'#f3f0e7','gray':'#8a8d8b','dark':'#242c30'}
def flat(im,c):
 bg=Image.new('RGBA',im.size,c);bg.alpha_composite(im);return bg.convert('RGB')
for c in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  raw=[Image.open(p/'frames'/f'{c}-{d}'/f'{i:03d}.png').convert('RGBA') for i in range(12)]
  atpath=p/'atlases'/f'{c}-{d}.png';atlas=Image.open(atpath).convert('RGBA');rec=next(z for z in cat['clips'] if z['id']==c)['directions'][d]
  assert atlas.size==tuple(rec['atlasSize'])
  for i,r in enumerate(rec['rects']):
   x,y,w,h=r;assert atlas.crop((x,y,x+w,y+h)).tobytes()==raw[i].tobytes()
  validation['atlasChecks'].append({'path':str(atpath.relative_to(p)),'all12CellsPixelExact':True,'originalLayout':True})
  # Review-only assembly takes exact non-background portions of all six supplied sheets.
  # No interpolation or image edits; intended/native material pixels retained at their sheet scale.
  canvas=Image.new('RGB',(2304,3*790),'#c0c0c0');dr=ImageDraw.Draw(canvas)
  for bi,(bg,color) in enumerate(BG.items()):
   dr.text((6,bi*790+2),f'{c}-{d} {bg}: all12 native384x640 left; all12 logical192x320 right; fixed crops only',fill='black')
   for disp,scale in [('logical',1),('enlarged',2)]:
    sp=p/'sheets'/f'{c}-{d}-{bg}-{disp}.png';sheet=Image.open(sp).convert('RGB');fw,fh,head=192*scale,320*scale,24*scale
    for i,im in enumerate(raw):
     x=i%6*fw;y=i//6*(fh+head)+head;shown=im if scale==2 else im.resize((192,320),Image.Resampling.LANCZOS)
     assert sheet.crop((x,y,x+fw,y+fh)).tobytes()==flat(shown,color).tobytes()
     crop=(64,160,320,536) if scale==2 else (32,80,160,268)
     cx0,cy0,cx1,cy1=crop;pix=sheet.crop((x+cx0,y+cy0,x+cx1,y+cy1))
     dx=(i%6)*pix.width+(0 if scale==2 else 1536);dy=bi*790+30+(i//6)*pix.height;canvas.paste(pix,(dx,dy))
    validation['sheetChecks'].append({'path':str(sp.relative_to(p)),'all12CellsPixelExact':True,'scale':scale})
  cp=out/f'all-six-{c}-{d}.png';canvas.save(cp);validation['composites'].append({'path':str(cp.relative_to(b/'reviews')),'suppliedSheets':[f'sheets/{c}-{d}-{bg}-{disp}.png' for bg in BG for disp in ['logical','enlarged']]})
(b/'reviews/round01-pixel-checks.json').write_text(json.dumps(validation,indent=2)+'\n');print('Verified',len(frames),'raw frames,',len(validation['atlasChecks']),'atlases,',len(validation['sheetChecks']),'sheets, hash failures',validation['allHashFailures'])
