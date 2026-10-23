import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageChops
B=Path(__file__).resolve().parent;O=B.parent.parent;E=B/'evidence';P=O/'candidates/round-01';reports=[]
for be in ['full-chrome-155','shell-153']:
 d=json.loads((E/(be+'-report.json')).read_text());assert len(d['records'])==64 and len(d['controls'])==4
 assert all(c['discardedVisiblePixels']==0 and c['integerRestoration']['differingPixels']==0 for c in d['controls'])
 reports.append({'backend':be,'browserVersion':d['browserVersion'],'cases':64,'actualMaxAlphaDelta':max(r['actualConsumerResidual']['maxAlphaDelta'] for r in d['records']),'actualMaxOpaqueRGBDelta':max(r['actualConsumerResidual']['maxOpaqueRGBDelta'] for r in d['records']),'diagnosticMaxAlphaDelta':max(r['comparisonOnlyEqualExtentsResidual']['maxAlphaDelta'] for r in d['records']),'diagnosticMaxOpaqueRGBDelta':max(r['comparisonOnlyEqualExtentsResidual']['maxOpaqueRGBDelta'] for r in d['records']),'minimumActualFinitePortInteriorAlpha':min(r['finitePortInterior']['native-actual']['minIndependentAlpha'] for r in d['records']),'maximumActualFinitePortInteriorRGBDelta':max(r['finitePortInterior']['native-actual']['maxRGBDelta'] for r in d['records']),'maximumDiagnosticFinitePortInteriorRGBDelta':max(r['finitePortInterior']['native-equal-extents-diagnostic']['maxRGBDelta'] for r in d['records']),'diagnosticVisiblePixelsDiscarded':sum(c['discardedVisiblePixels'] for c in d['controls']),'diagnosticIntegerRestorationDifferences':sum(c['integerRestoration']['differingPixels'] for c in d['controls'])})
(E/'independent-consumer-findings.json').write_text(json.dumps({'candidatePacketSHA256':'8b37245ce44d02d4782e5d8bfcf8d4efca27813262b2f051eb5ad99abcca4849','reports':reports,'interpretation':'Exact frozen570consumer and099layout independently replayed128candidate cases. Actual fullChrome extent-dependent nearest-tie residuals are retained; equal-extents diagnostic is comparison-only and proved0visiblepixelsdiscarded/exactinteger restoration. All tested true finite-port interior alpha255. Local RGB residuals/outer residuals are retained, not waived. Pixel source identity/port field continuity is independently established in native findings. Actual visible local joins are assessed separately from known unequal-texture sampler residuals.','scope':'Static frame1/all4/12fps; no motion clip is declared or required for reef-middle.'},indent=2)+'\n')
# Full 1:1 pixel coverage of large declared sheets, without presentation downscaling.
coverage=[]
for name in ['repeated.png','shell-repeated.png','fractional-joins-sheet.png']:
 im=Image.open(P/name).convert('RGBA');pieces=[];rebuilt=Image.new('RGBA',im.size)
 boxes=[(0,0,im.width,min(960,im.height)),(0,min(960,im.height),im.width,im.height)] if im.width<=1536 else [(0,0,830,im.height),(830,0,im.width,im.height)]
 for i,box in enumerate(boxes):
  piece=im.crop(box);out=E/f'coverage-{name[:-4]}-{i}.png';piece.save(out);rebuilt.paste(piece,box[:2]);pieces.append({'path':str(out.relative_to(O)),'sourceRectangle':list(box),'uniformScale':1,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
 diff=ImageChops.difference(im,rebuilt);assert not any(c.getbbox() for c in diff.split());coverage.append({'packetPreviewPath':name,'sourceSHA256':hashlib.sha256((P/name).read_bytes()).hexdigest(),'pieces':pieces,'allSourcePixelsCoveredExactly':True})
# Registered closeups highlight the visual concern without altering candidate pixels.
for d in ['N','E','S','W']:
 im=Image.open(P/f'frames/static/{d}/000.png').convert('RGBA');im.crop((60,280,324,630)).resize((528,700),Image.Resampling.NEAREST).save(E/f'visual-closeup-{d}.png')
(E/'coverage-map.json').write_text(json.dumps({'largePreviewCoverage':coverage,'closeups':'Fixed common sourceRectangle[60,280,324,630] ×2nearest all4; diagnosis only, no alpha-bound fit or candidate change.','heroAliasMapping':'Independent reopened renders differ only PNG encoding, exact decodedRGBA equality for all4, so original hero inspection also covers pixel-identical reopen outputs.'},indent=2)+'\n');print(json.dumps(reports))
