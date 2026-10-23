from PIL import Image,ImageChops
import pathlib,json,hashlib,struct
O=pathlib.Path(__file__).resolve().parents[1];P=O/'candidates/round-05';R=O/'reviews';d=json.loads((P/'packet.json').read_text());clips=[]
for ap in [P/v['path'] for v in d['previews'].values() if v['path'].endswith('.apng')]:
 base=ap.parent.parent;cid=ap.stem;im=Image.open(ap);atlas=Image.open(base/'atlases'/f'{cid}.png').convert('RGBA');sheet=Image.open(base/'contact-sheets'/f'{cid}.png').convert('RGB');all48=Image.open(base/'contact-sheets'/f'{cid[:-2]}-all48.png').convert('RGB');direction=cid[-1];row=['N','E','S','W'].index(direction)
 assert ImageChops.difference(sheet,all48.crop((0,row*176,1152,(row+1)*176))).getbbox() is None
 for i in range(12):
  raw=Image.open(base/'frames'/cid/f'{i:03d}.png').convert('RGBA');assert raw.size==(384,640);im.seek(i);assert im.convert('RGBA').tobytes()==raw.tobytes();assert atlas.crop((i%6*384,i//6*640,(i%6+1)*384,(i//6+1)*640)).tobytes()==raw.tobytes()
  thumb=raw.resize((96,160),Image.Resampling.LANCZOS);bg=Image.new('RGB',(96,160),'#70757a');bg.paste(thumb,(0,0),thumb);assert ImageChops.difference(bg,sheet.crop((i*96,16,(i+1)*96,176))).getbbox() is None
 blob=ap.read_bytes();off=8;delays=[];plays=None
 while off<len(blob):
  n=struct.unpack('>I',blob[off:off+4])[0];typ=blob[off+4:off+8];data=blob[off+8:off+8+n]
  if typ==b'acTL':nf,plays=struct.unpack('>II',data)
  if typ==b'fcTL':delays.append(list(struct.unpack('>HH',data[20:24])))
  off+=n+12
 assert nf==12 and delays==[[1,12]]*12
 expectedPlays=1 if cid[:-2] in ['sit-down','stand-up','happy'] else 0;assert plays==expectedPlays
 clips.append({'path':str(ap.relative_to(O)),'framesEqualNative':12,'atlasFramesEqualNative':12,'sheetTilesEqualNative':12,'sheetRowEqualsAll48':True,'12fpsExact':True,'plays':plays})
(R/'round05-independent-frame-atlas-apng-check.json').write_text(json.dumps({'clips':clips,'totalClips':len(clips),'totalFrames':12*len(clips),'allPassed':len(clips)==48},indent=2)+'\n')
a=Image.open(P/'repeatability-0.png').convert('RGBA');b=Image.open(P/'repeatability-1.png').convert('RGBA');diff=ImageChops.difference(a,b);maximum=max(y for x,y in diff.getextrema());changed=sum(any(x) for x in diff.getdata());assert maximum==3
(R/'round05-independent-repeatability.json').write_text(json.dumps({'sameInputNativeRepeatMax8BitDifference':maximum,'changedPixels':changed,'nativeReportedTolerance':3},indent=2)+'\n')
entries=[(k,v) for k,v in d['previews'].items() if v['path'].startswith('previews/')]
for page in range(0,len(entries),4):
 batch=entries[page:page+4];out=Image.new('RGB',(1536,4*352),'#454545')
 for j,(k,v) in enumerate(batch):
  im=Image.open(P/v['path']).convert('RGB');im.thumbnail((1536,352));out.paste(im,((1536-im.width)//2,j*352))
 out.save(R/f'round05-declared-preview-montage-{page//4+1}.jpg',quality=95)
(R/'round05-preview-montage-map.json').write_text(json.dumps(entries,indent=2)+'\n')
# Reuse the read-only judge APNG viewer layout; bind every image URL to new immutable round05 bytes.
html=(R/'round04-apng-review.html').read_text().replace('round-04','round-05').replace('Exact sealed APNG','Round05 exact sealed APNG').replace('<!doctype html>','<!doctype html><meta charset="utf-8">');(R/'round05-apng-review.html').write_text(html)
print('independent exact APNG/native/atlas/sheet frames',len(clips),12*len(clips),'repeat max',maximum,'changed',changed,'montage pages',(len(entries)+3)//4)
