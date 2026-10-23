from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops,ImageStat,ImageDraw
H=Path(__file__).resolve().parent;O=H.parent.parent;C=O/'candidates/round-01';P=C/'packet.json';S=O/'source/round-01.blend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,x):(H/name).write_text(json.dumps(x,indent=2)+'\n')
assert sha(P)=='d7be0b28d1431db44377d85c3ab8687f15d11e80a8b14e55491f02c7e3bfe2ba';assert sha(S)=='dc8f792ad097e30096719a075042e040b928ef8c79b58941061651192bfe4f36'
p=json.loads(P.read_text());bound=[]
for label,r in p['files'].items():
 f=(C/r['path']).resolve();assert sha(f)==r['sha256'],(label,f);bound.append({'label':label,'path':str(f),'sha256':r['sha256']})
for group in ['candidateRenders','previews']:
 for label,r in p[group].items():assert sha(C/r['path'])==r['sha256']
for rel in ['reviews/preparation-v1/hashmanifest.json','candidates/round-01/resource-manifest-v1.json']:
 m=json.loads((O/rel).read_text())
 for r in m['files']:assert sha(O/r['path'])==r['sha256'],r['path']
write('binding-report.json',{'candidatePacketSHA256':sha(P),'sourceSHA256':sha(S),'packetFilesVerified':len(bound),'packetMediaVerified':len(p['candidateRenders'])+len(p['previews']),'sourceBindings':bound,'preparation202AndCandidate226ManifestsVerified':True,'topDeliveryAliasSHA256':sha(O/'delivery.round-01.json'),'noVisualApprovalFromHashes':True})
D=['N','E','S','W'];decoded=[];full=Image.open(C/'previews/all48-published-fullframe.png').convert('RGB');hero=Image.open(C/'previews/four-view-sheet.png').convert('RGB');bg=(119,119,119)
def flattened(im):
 out=Image.new('RGB',im.size,bg);out.paste(im,(0,0),im.getchannel('A'));return out
for row,d in enumerate(D):
 apng=Image.open(C/f'previews/enter-{d}.png');assert apng.n_frames==12 and apng.info['loop']==1
 durations=[]
 for i in range(12):
  apng.seek(i);im=apng.convert('RGBA');pub=Image.open(C/f'frames/enter/{d}/{i:03d}.png').convert('RGBA');same=im.tobytes()==pub.tobytes();assert same,(d,i)
  durations.append(apng.info.get('duration'));atlas=Image.open(C/f'atlases/{d}.png').convert('RGBA');cell=atlas.crop((i%6*384,i//6*768,i%6*384+384,i//6*768+768));assert pub.tobytes()==cell.tobytes()
  sheet=full.crop((i*384,row*788+20,(i+1)*384,row*788+788));assert sheet.tobytes()==flattened(pub).tobytes(),('all48-sheet',d,i)
  decoded.append({'path':f'previews/enter-{d}.png','frame':i,'decodedSHA256':hashlib.sha256(im.tobytes()).hexdigest(),'exactPublishedFrame':f'frames/enter/{d}/{i:03d}.png','all48PreviewCell':[i*384,row*788+20,384,768],'durationMs':apng.info.get('duration')})
 assert all(abs(t-1000/12)<.001 for t in durations)
 h=Image.open(C/p['candidateRenders'][d]['path']).convert('RGBA');assert hero.crop((row*384,20,(row+1)*384,788)).tobytes()==flattened(h).tobytes()
# Decoding every combined APNG frame, and every full-frame direction cell, supports useful visual coverage beyond its default frame.
motion=Image.open(C/'previews/motion.png');assert motion.n_frames==12 and motion.info['loop']==1;motionmap=[]
for start in [0,4,8]:
 sheet=Image.new('RGB',(768,4*404),bg);draw=ImageDraw.Draw(sheet)
 for j,i in enumerate(range(start,start+4)):
  motion.seek(i);im=motion.convert('RGBA');assert im.size==(768,384)
  reference=Image.new('RGBA',(768,384))
  for col,d in enumerate(D):
   src=Image.open(C/f'frames/enter/{d}/{i:03d}.png').convert('RGBA').resize((192,384),Image.Resampling.LANCZOS);reference.paste(src,(col*192,0))
  assert im.tobytes()==reference.tobytes(),('motion',i)
  flat=flattened(im);sheet.paste(flat,(0,j*404+20));draw.text((2,j*404+3),f'Actual decoded motion.png frame {i}: N | E | S | W',fill='white');motionmap.append({'path':'previews/motion.png','frame':i,'decodedSHA256':hashlib.sha256(im.tobytes()).hexdigest(),'sheet':f'phase-group-{start:02d}-{start+3:02d}.png','sheetRect':[0,j*404+20,768,384],'facings':D,'durationMs':motion.info.get('duration')})
 sheet.save(H/f'phase-group-{start:02d}-{start+3:02d}.png')
write('preview-content-proof.json',{'candidatePacketSHA256':sha(P),'apngFrames':decoded,'combinedMotion':motionmap,'all48PreviewVerifiedExactAtEveryCompleteFullframeCell':True,'fourHeroSheetCellsExact':True,'atlasCellsExactOriginal6x2Order':True,'aliases':'No differing whole-file hashes claimed as identical-file aliases. APNG decoded frames and sheet cells have explicit verified decoded-pixel content mappings.'})
# Independent source replay differs only in rendering residuals, if any; no repair or fitting.
checks=[];measure=json.loads((H/'native-measurements.json').read_text())
for r in measure['views']:
 d,i=r['direction'],r['index'];a=Image.open(H/r['path']).convert('RGBA');b=Image.open(C/f'native/enter/{d}/{i:03d}.png').convert('RGBA');pub=Image.open(C/f'frames/enter/{d}/{i:03d}.png').convert('RGBA');delta=ImageChops.difference(a,b);sampled=a.resize((384,768),Image.Resampling.LANCZOS);pd=ImageChops.difference(sampled,pub)
 alpha=pub.getchannel('A');edge=any(alpha.crop(z).getbbox() for z in [(0,0,1,768),(383,0,384,768),(0,0,384,1),(0,767,384,768)])
 checks.append({'direction':d,'index':i,'independentNative':r['path'],'submittedNative':f'native/enter/{d}/{i:03d}.png','nativeChangedPixels':sum(any(px) for px in delta.get_flattened_data()),'nativeMaxRGBA':[x[1] for x in delta.getextrema()],'nativeMeanAbsRGBA':list(ImageStat.Stat(delta).mean),'wholeFramePublishedMaxRGBA':[x[1] for x in pd.getextrema()],'submittedPublishedNativeReductionExact':Image.open(C/f'native/enter/{d}/{i:03d}.png').convert('RGBA').resize((384,768),Image.Resampling.LANCZOS).tobytes()==pub.tobytes(),'publishedAlphaBounds':alpha.getbbox(),'anyPublishedFrameBorderAlpha':edge})
write('native-replay-comparison.json',{'candidatePacketSHA256':sha(P),'sourceSHA256':sha(S),'pillowVersion':Image.__version__,'resampling':'Complete768x1536 RGBA canvas to384x768 LANCZOS; no other processing','frames':checks,'all48NativeBound':len(checks)==48})
print('MEDIA_AND_BINDING_COMPLETE',len(bound),'packet inputs',len(decoded),'direction APNG frames',len(motionmap),'combinedAPNGframes','nativeMax',max(max(r['nativeMaxRGBA']) for r in checks),'publicationMax',max(max(r['wholeFramePublishedMaxRGBA']) for r in checks))
