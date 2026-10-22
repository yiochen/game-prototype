import sys,pathlib,json
sys.dont_write_bytecode=True
out=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(out/'resources/python'))
from PIL import Image,ImageChops
ex=out.parents[1];audit=json.loads((out/'native-independent-audit.json').read_text());rows=[]
for r in audit['nativeRenders']:
 if r['clip']=='half':expected=ex/f'candidates/round-01/motion-evidence/{r["direction"]}-{r["frame"]:04.1f}.png'
 elif r['frame']==13:expected=ex/f'candidates/round-01/motion-evidence/{r["direction"]}-13.0.png'
 else:expected=ex/f'candidates/round-01/native-frames/{r["clip"]}-{r["direction"]}/{r["frame"]-1:03}.png'
 rows.append((out/r['path'],expected))
for r in audit['mountedRenders']:rows.append((out/r['path'],ex/f'candidates/round-01/mounted/neutral-{r["direction"]}.png'))
records=[]
for a,b in rows:
 im=Image.open(a).convert('RGBA');target=Image.open(b).convert('RGBA');diff=ImageChops.difference(im,target);ext=diff.getextrema();records.append({'path':str(a.relative_to(out)),'sealedSourcePath':str(b.relative_to(ex)),'pixelsExact':im.tobytes()==target.tobytes(),'maximumRGBDifference':max(x[1] for x in ext[:3]),'maximumAlphaDifference':ext[3][1],'differingPixels':sum(p!=q for p,q in zip(im.get_flattened_data(),target.get_flattened_data())),'rgbDifferenceBounds':ImageChops.difference(im.convert('RGB'),target.convert('RGB')).getbbox()})
assert max(r['maximumRGBDifference'] for r in records)<=1 and not any(r['maximumAlphaDifference'] for r in records)
summary={'captures':len(records),'bitExact':sum(r['pixelsExact'] for r in records),'maximumRGBDifference':max(r['maximumRGBDifference'] for r in records),'maximumAlphaDifference':max(r['maximumAlphaDifference'] for r in records),'totalDifferingPixels':sum(r['differingPixels'] for r in records),'maximumDifferingPixelsPerCapture':max(r['differingPixels'] for r in records),'qualification':'Supplemental batch re-rendering introduces only isolated 1-LSB RGB differences. Approved supplied packet bytes remain authoritative; these diagnostic replays do not replace them. All supplied native-to-published BOX pixels and both atlas sets are exact.'}
(out/'replay-pixel-parity.json').write_text(json.dumps({'summary':summary,'captures':records},indent=2))
# Whole visible native artwork fits the fixed crop used for phase detail coverage.
for r in audit['nativeRenders']:
 im=Image.open(out/r['path']);b=im.getchannel('A').getbbox();assert b[0]>=80 and b[1]>=600 and b[2]<=688 and b[3]<=1320,(r,b)
print(json.dumps(summary))
