import json,struct,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
H=Path(__file__).resolve().parent;B=H/'resources';C=B/'candidates/round-01';O=H/'visual';O.mkdir(exist_ok=True)
clips=['idle','travel','impact','protection','dock-charging','dock-ready','upgraded-idle','upgraded-travel','upgraded-impact','upgraded-protection','upgraded-dock-charging','upgraded-dock-ready'];ds=['N','E','S','W'];rows=[];frames=[];crop=(65,165,255,360)
for clip in clips:
 sheet=Image.new('RGB',(6*194,8*216),(160,168,176));draw=ImageDraw.Draw(sheet)
 for di,d in enumerate(ds):
  ap=C/'playbacks'/f'{clip}-{d}.png';a=Image.open(ap);raw=ap.read_bytes();pos=8;fc=[];ac=None
  while pos<len(raw):
   n=struct.unpack('>I',raw[pos:pos+4])[0];typ=raw[pos+4:pos+8];data=raw[pos+8:pos+8+n];pos+=n+12
   if typ==b'fcTL':fc.append(struct.unpack('>IIIIIHHBB',data))
   if typ==b'acTL':ac=struct.unpack('>II',data)
  atlas=Image.open(C/'atlases'/f'{clip}-{d}.png').convert('RGBA');checks=[]
  for i in range(12):
   p=C/'frames'/f'{clip}-{d}'/f'{i:03}.png';im=Image.open(p).convert('RGBA');a.seek(i);decoded=a.convert('RGBA');tile=atlas.crop((i%6*640,i//6*768,i%6*640+640,i//6*768+768));bbox=im.getchannel('A').getbbox();checks.append(decoded.tobytes()==im.tobytes() and tile.tobytes()==im.tobytes());assert im.size==(640,768) and bbox and min(bbox[:2])>0 and bbox[2]<640 and bbox[3]<768
   logical=im.resize((320,384),Image.Resampling.LANCZOS).crop(crop);bg=[(245,241,232),(160,168,176),(35,42,50)][i%3];patch=Image.new('RGBA',logical.size,bg+(255,));patch.alpha_composite(logical);x=(i%6)*194;y=(di*2+i//6)*216;sheet.paste(patch.convert('RGB'),(x,y+18));draw.text((x+3,y+3),f'{d} {i:02} '+['light','gray','dark'][i%3],fill=(255,255,255));frames.append({'path':str(p.relative_to(B)),'bbox':bbox,'sheet':f'visual/{clip}-decoded48.png','sheetCell':[i%6,di*2+i//6],'decodedAPNG':str(ap.relative_to(B)),'atlas':str((C/'atlases'/f'{clip}-{d}.png').relative_to(B))})
  assert all(checks) and a.n_frames==12 and len(fc)==12 and all(t[5:7]==(1,12) for t in fc) and ac==(12,1 if clip.endswith('impact') else 0)
  rows.append({'path':str(ap.relative_to(B)),'12DecodedFramesExactWholeRGBA':all(checks),'atlas12TilesExactWholeRGBA':True,'fcTLDelays':[[t[5],t[6]] for t in fc],'plays':ac[1]})
 sheet.save(O/f'{clip}-decoded48.png')
# Native diagnostic contact sheets, each exact native crop reduced to logical for overview.
for clip in clips:
 sheet=Image.new('RGB',(12*194,216),(160,168,176));draw=ImageDraw.Draw(sheet)
 for di,d in enumerate(ds):
  names=[f'frames/{clip}-{d}/000.png',f'diagnostics/{clip}-{d}-meaningful-half.png',f'diagnostics/{clip}-{d}-closure-or-terminal.png']
  for j,n in enumerate(names):
   im=Image.open(C/n).convert('RGBA').resize((320,384),Image.Resampling.LANCZOS).crop(crop);bg=Image.new('RGBA',im.size,(245,241,232,255));bg.alpha_composite(im);x=(di*3+j)*194;sheet.paste(bg.convert('RGB'),(x,18));draw.text((x+2,2),d+' '+['first','half','end'][j],fill='white')
 sheet.save(O/f'{clip}-diagnostics.png')
# Four candidate renders with full native pixel crop, no rescale.
sheet=Image.new('RGB',(4*360,390),(35,42,50));draw=ImageDraw.Draw(sheet)
for di,d in enumerate(ds):
 im=Image.open(C/f'frames/dock-ready-{d}/000.png').convert('RGBA').crop((140,340,500,700));bg=Image.new('RGBA',im.size,(35,42,50,255));bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(di*360,25));draw.text((di*360+5,3),'dock-ready '+d+' native1:1',fill='white')
sheet.save(O/'four-candidates-native.png')
(H/'pixel-audit.json').write_text(json.dumps({'all48APNGAndAtlasesPass':True,'runtimeFrameCount':len(frames),'cropLogical':crop,'cropChangesInspectionOnly':True,'playbacks':rows,'frames':frames},indent=2)+'\n');print('PIXELS',len(rows),len(frames),'exact rational12fps and fullRGBA; sheets',len(list(O.iterdir())))
