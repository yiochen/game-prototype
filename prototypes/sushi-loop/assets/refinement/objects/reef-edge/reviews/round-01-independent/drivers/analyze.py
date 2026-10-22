import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageChops
B=Path(__file__).resolve().parents[1];O=B.parents[1];C=O/'candidates/round-01';E=B/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
heroes=[]
for d in ['N','E','S','W']:
 p=E/('reopened-'+d+'.png');orig=C/f'frames/static/{d}/000.png';a=Image.open(p).convert('RGBA');b=Image.open(orig).convert('RGBA');diff=ImageChops.difference(a,b);hist=[diff.getchannel(i).histogram() for i in range(4)];heroes.append({'facing':d,'packetPath':str(orig.relative_to(C)),'reopenedPath':str(p.relative_to(B)),'exactDecodedRGBA':all(sum(h[1:])==0 for h in hist),'channelDifferentPixels':[sum(h[1:]) for h in hist],'byteExact':sha(p)==sha(orig)})
write(E/'hero-replay-comparison.json',heroes)
coverage=[]
packet=json.loads((C/'packet.json').read_text())
for group in ['candidateRenders','previews']:
 for alias,r in packet[group].items():coverage.append({'alias':alias,'group':group,'path':r['path'],'sha256':sha(C/r['path']),'inspection':'direct image view','note':'Alias repeated maps to the same hash/path as native-primary-all4 and reuses that actual inspection.' if alias=='repeated' else 'Large preview sheets additionally supported by independently replayed CSS/native detail sheets.'})
write(B/'inspection-coverage.json',{'candidatePacketSHA256':sha(C/'packet.json'),'candidateHeroCount':4,'previewAliasCount':19,'uniquePreviewPaths':18,'requiredPathsComplete':True,'records':coverage})
reports=[];crops=[]
for backend in ['full-chromium','headless-shell']:
 report=json.loads((E/'consumer'/(backend+'-report.json')).read_text());reports.append({'backend':backend,'version':report['browserVersion'],'options':report['options'],'cases':len(report['records']),'errors':report['errors'],'maximumMetrics':{k:max(r['metrics'][k] for r in report['records']) for k in report['records'][0]['metrics']}})
 for d in ['N','E','S','W']:
  rows=[]
  for size in [128,32]:
   for phase in ['r0-p0','r0.25-p0.75']:
    folder=E/'consumer'/backend/(d+'-'+str(size)+'-'+phase)
    native=Image.open(folder/'native.png').convert('RGBA');independent=Image.open(folder/'independent.png').convert('RGBA');box=ImageChops.lighter(native.getchannel('A'),independent.getchannel('A')).getbbox();box=(max(0,box[0]-3),max(0,box[1]-3),min(native.width,box[2]+3),min(native.height,box[3]+3));w=box[2]-box[0];h=box[3]-box[1]
    for bg in ['light','gray','dark']:
     source=folder/('css-'+bg+'.png');im=Image.open(source).convert('RGB');row=Image.new('RGB',(w*2+16,h+22),'#e8e8e8');draw=ImageDraw.Draw(row);draw.text((3,3),f'{backend} {d} cell{size} {phase} {bg}: native | independent',fill='black');row.paste(im.crop(box),(0,22));second=(box[0]+native.width+16,box[1],box[2]+native.width+16,box[3]);row.paste(im.crop(second),(w+16,22));rows.append(row);crops.append({'source':str(source.relative_to(O)),'nativeBox':list(box),'independentBox':list(second),'scale':1,'role':'Review-only exact-pixel CSS detail crop; full actual screenshots retained, runtime/source unchanged'})
  width=max(im.width for im in rows);height=sum(im.height+8 for im in rows);sheet=Image.new('RGB',(width,height),'#e8e8e8');y=0
  for im in rows:sheet.paste(im,(0,y));y+=im.height+8
  # Long vertical direction layouts are split into meaningful exact-pixel pages.
  if height>1900:
   pages=[];start=0;cy=0
   for im in rows:
    if cy+im.height+8-start>1850:
     pages.append((start,cy));start=cy
    cy+=im.height+8
   pages.append((start,cy))
  else:pages=[(0,height)]
  for i,(top,bottom) in enumerate(pages):sheet.crop((0,top,width,bottom)).save(E/f'detail-{backend}-{d}-{i}.png')
write(E/'consumer-independent-summary.json',{'candidatePacketSHA256':sha(C/'packet.json'),'primaryHardFixtureOnly':True,'cases':sum(r['cases'] for r in reports),'reports':reports,'limits':'Bounded independent replay at baseline and root.25/pan.75. Complete packet matrix remains independently hash-verified and directly inspected via all declared sheets. No new source-extent control or policy study run; actual raw unequal-extent outputs and finite native light RGB residuals retained. No whole-frame equality claim.'})
write(E/'detail-crop-map.json',crops)
print('HERO_REPLAY',heroes);print('CONSUMER_SUMMARY',reports)
