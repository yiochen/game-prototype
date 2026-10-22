import json,hashlib,shutil,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
B=Path(__file__).resolve().parent;O=B.parent;C=O/'candidates/round-01';P=C/'previews';P.mkdir(exist_ok=True)
bgs={'light':'#f6f0e5','gray':'#80878f','dark':'#13243a'};ledger=[];previews={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def bg(im,color):o=Image.new('RGBA',im.size,color);o.alpha_composite(im);return o.convert('RGB')
def sheet(name,tiles,columns):
 widths=[max(t[1].width for i,t in enumerate(tiles) if i%columns==c) for c in range(columns)];rows=math.ceil(len(tiles)/columns);heights=[max(t[1].height+24 for t in tiles[r*columns:(r+1)*columns]) for r in range(rows)];im=Image.new('RGB',(sum(widths)+12*(columns+1),sum(heights)+12*(rows+1)),'#e8e8e8');dr=ImageDraw.Draw(im);m=[]
 for i,(label,tile,sources,derivation) in enumerate(tiles):
  col=i%columns;row=i//columns;x=12+sum(widths[:col])+12*col;y=12+sum(heights[:row])+12*row;dr.text((x,y),label,fill='#111');im.paste(tile,(x,y+22));m.append({'label':label,'tileRect':[x,y+22,tile.width,tile.height],'sources':sources,'derivation':derivation})
 p=P/(name+'.png');im.save(p);previews[name]=str(p.relative_to(O));ledger.append({'preview':str(p.relative_to(O)),'sha256':sha(p),'size':list(im.size),'tiles':m})
def crop_union(paths):
 boxes=[load(p).getbbox() for p in paths];return (min(x[0] for x in boxes if x),min(x[1] for x in boxes if x),max(x[2] for x in boxes if x),max(x[3] for x in boxes if x))
def pair(a,b,color,roi):
 aa=bg(load(a).crop(roi),color);bb=bg(load(b).crop(roi),color);o=Image.new('RGB',(aa.width*2+8,aa.height),'#e8e8e8');o.paste(aa,(0,0));o.paste(bb,(aa.width+8,0));return o
hero=[C/f'frames/static/{d}/000.png' for d in 'NESW'];sheet('four-view-sheet',[(d,bg(load(p),bgs['gray']),[str(p.relative_to(O))],'Exact native384x704 PNG on gray; no resizing.') for d,p in zip('NESW',hero)],4)
tiles=[]
for color,h in bgs.items():
 for size in [128,32]:
  for d,p in zip('NESW',hero):
   im=load(p).resize((int(192*size/128),int(352*size/128)),Image.Resampling.LANCZOS);tiles.append((f'{d} cell{size} {color}',bg(im,h),[str(p.relative_to(O))],'Intended-size presentation of exact whole registered frame, native2x->cell128 or32, no fitting.'))
sheet('hero-size-backgrounds',tiles,4)
sheet('registered-style-comparison',[(label,bg(load(p).resize((384,704),Image.Resampling.LANCZOS),bgs['gray']),[str(p.relative_to(O))],'Whole-frame uniform normalized comparison; target registration drift is visible, never fitted.') for label,p in [('Original',O/'inputs/original.png'),('Fixed target',O/'inputs/target.png'),('Native candidate S',hero[2])]],3)
for kind in ['primary','topology']:
 sheet('native-'+kind+'-all4',[(f'{kind} {d} cell128 - actual native scene',bg(load(C/f'evidence/native-{kind}-{d}.png').resize((704,864),Image.Resampling.LANCZOS),bgs['gray']),[f'candidates/round-01/evidence/native-{kind}-{d}.png'],'Whole registered native1408x1728 source shown at logical704x864. Same camera for all4; topology corner/end provisional.') for d in 'NESW'],2)
for backend in ['full-chromium','headless-shell']:
 data=json.loads((C/f'consumer/{backend}-results.json').read_text())
 for d in 'NESW':
  tiles=[]
  for size in [128,32]:
   rows=[r for r in data['records'] if r['kind']=='primary' and r['d']==d and r['size']==size];allpaths=[C/f'consumer/{backend}/{r["id"]}/{k}.png' for r in rows for k in ['native','independent']];roi=crop_union(allpaths);roi=(max(0,roi[0]-4),max(0,roi[1]-4),roi[2]+4,roi[3]+4)
   for color,h in bgs.items():
    for r in rows:
     a=C/f'consumer/{backend}/{r["id"]}/native.png';b=a.with_name('independent.png');tiles.append((f'{d} {size} root{r["rootPhase"]}/pan{r["panPhase"]} {color}',pair(a,b,h,roi),[str(a.relative_to(O)),str(b.relative_to(O))],{'evidenceOnlyCrop':roi,'resampling':False,'coverage':'Every visible source pixel retained; common crop per direction/size across all phases. Left actual native, right independent current consumer.'}))
  sheet('raster-'+backend+'-'+d,tiles,4)
 # Actual CSS screenshots: exact screenshot pixels, crop only empty background, every visible pixel retained.
 for kind in ['primary','topology']:
  tiles=[]
  for size in [128,32]:
   rows=[r for r in data['records'] if r['kind']==kind and r['size']==size and (r['rootPhase'],r['panPhase']) in [(0,0),(.25,.75)]]
   for r in rows:
    case=C/f'consumer/{backend}/{r["id"]}';roi=crop_union([case/'native.png',case/'independent.png']);roi=(max(0,roi[0]-5),max(0,roi[1]-5),roi[2]+5,roi[3]+5);w=r['display']['width'];
    for color,h in bgs.items():
     p=case/f'actual-css-{color}.png';im=Image.open(p).convert('RGB');left=im.crop(roi);right=im.crop((roi[0]+w+16,roi[1],roi[2]+w+16,roi[3]));tile=Image.new('RGB',(left.width*2+8,left.height),'#e8e8e8');tile.paste(left,(0,0));tile.paste(right,(left.width+8,0));tiles.append((f'{r["d"]} {size} root{r["rootPhase"]}/pan{r["panPhase"]} {color}',tile,[str(p.relative_to(O))],{'actualCSSScreenshot':True,'evidenceOnlySourceRects':[roi,[roi[0]+w+16,roi[1],roi[2]+w+16,roi[3]]],'resampling':False,'coverage':'Left native / right independent, exact intended-size CSS pixels. Empty background outside registered source observation ROI omitted only in evidence sheet; raw full screenshot retained.'}))
  sheet('css-'+backend+'-'+kind,tiles,3)
write(C/'preview-coverage-map.json',{'scope':'Media-to-tile coverage instructions for original independent judge, not a claim of inspection or approval. Every declared preview covers explicit exact source media; crops only remove unused transparent/background margins from evidence and do not change final source PNGs.','previews':ledger})
# Byte and pixel replay, publication, clipping measurements.
replays=[]
for d,p in zip('NESW',hero):
 native=C/f'native/static/{d}/000.png';rep=C/f'reopened/native/static/{d}/000.png';atlas=C/f'atlases/static-{d}.png';im=load(p);box=im.getbbox();diff=ImageChops.difference(im,load(rep));replays.append({'direction':d,'sourceSHA256':sha(B/'round-01.blend'),'publishedNativeAtlasByteIdentical':len({sha(x) for x in [native,p,atlas]})==1,'replayDecodedRGBAIdentical':not diff.getbbox(),'replayByteIdentical':sha(p)==sha(rep),'alphaBounds':box,'size':list(im.size),'noCanvasClipping':box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height})
write(C/'replay-publication-comparison.json',{'records':replays,'replayMethod':'Clean reopen existing saved blend, no construction, unchanged capture routine; all4 root matrices and source hash in reopened/capture-measurements.json.'})
cap=json.loads((C/'capture-measurements.json').read_text());contract=json.loads((C/'evidence/native-contract-comparison.json').read_text());reports=[json.loads((C/f'consumer/{b}-results.json').read_text()) for b in ['full-chromium','headless-shell']];records=[r for report in reports for r in report['records']]
summary={'caseCount':len(records),'primaryCases':sum(r['kind']=='primary' for r in records),'topologyCases':sum(r['kind']=='topology' for r in records),'backends':[{k:r[k] for k in ['backend','browserVersion','options','executable','processArgs','errors','helperHashes']} for r in reports],'maximumMetrics':{k:max(r['metrics'][k] for r in records) for k in records[0]['metrics']},'trueInteriorLossCases':[{'id':r['id'],'metrics':r['metrics']} for r in records if r['metrics']['nativeInteriorAlphaLoss'] or r['metrics']['independentInteriorAlphaLoss']],'limits':'Raw whole-frame and local RGB/contour alpha residuals retained. Native connected context has finite area-light/location/occlusion differences from separately lit centered sprites; unequal image source extents can affect nearest-tie sampling. Metrics are measurements, not visual approval or a waiver. Original corner/end are provisional sources; their old dark shading remains visible.'}
write(C/'consumer-summary.json',summary)
asset=json.loads((O/'inputs/source-assetRecord.json').read_text());asset.update(scale=2,artStyle={'revision':'reef-edge warm-soft native round01','lighting':'exact canonical middle02 soft symmetric rig','endpointMaterial':'exact native middle02 fields','publication':'direct native2x filter.01'});write(C/'assetRecord.json',asset)
rig=json.loads((O/'inputs/source-rig.json').read_text());rig.update(groundRootObject='reef-edge__root',source='source/round-01.blend',sourceFiles={'reproduce-round-01.py':sha(B/'reproduce-round-01.py')},status='native-static-saved-replay-measured-awaiting-independent-review');write(C/'rig.json',rig)
checks={**contract['checks'],'all4ReplayExact':all(r['replayDecodedRGBAIdentical'] for r in replays),'all4PublicationExact':all(r['publishedNativeAtlasByteIdentical'] for r in replays),'all4Unclipped':all(r['noCanvasClipping'] for r in replays),'all160BrowserCasesCaptured':len(records)==160,'noPageErrors':all(not r['errors'] for r in reports),'noTrueInteriorAlphaLoss':not summary['trueInteriorLossCases']}
write(C/'validation.json',{'asset':'reef-edge','round':'round-01','sourceProject':'source/round-01.blend','sourceSHA256':sha(B/'round-01.blend'),'allChecksPassed':all(checks.values()),'checks':checks,'captureRecords':cap['captureRecords'],'camera':json.loads((C/'published-camera.json').read_text()),'nativeAudit':'candidates/round-01/evidence/candidate-native-audit.json','bandComparison':'candidates/round-01/evidence/native-contract-comparison.json','contextTopology':'candidates/round-01/evidence/context-geometry.json','consumerSummary':'candidates/round-01/consumer-summary.json','reviewStatus':'awaiting_original_independent_judge','limits':summary['limits']})
write(B/'preview-index.json',{'previews':previews})
print(json.dumps({'previews':len(previews),'checks':checks,'consumerMaximums':summary['maximumMetrics']}))
