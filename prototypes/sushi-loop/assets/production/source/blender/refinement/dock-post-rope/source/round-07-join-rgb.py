"""Report exact rendered RGB continuity and package unchanged-pixel diagnostic crops.
This does not modify any sprite, atlas, native assembly image, or Blender scene.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import statistics,json,hashlib,shutil
P=Path(__file__).resolve().parent.parent;O=P/'candidates/round-07';OLD=P/'candidates/round-06';V=json.loads((O/'validation.json').read_text());D=json.loads((P/'delivery.json').read_text());stats=[]
for direction in ['E','W']:
 n=Image.open(O/f'joined-native-{direction}.png').convert('RGBA');i=Image.open(O/f'joined-independent-{direction}.png').convert('RGBA');pn=Image.open(OLD/f'joined-native-{direction}.png').convert('RGBA');pi=Image.open(OLD/f'joined-independent-{direction}.png').convert('RGBA')
 for seam in [484,740]:
  item={'direction':direction,'rootRotationZ':next(r['rootRotationZ'] for r in V['captureRecords'] if r['direction']==direction),'sharedRow':seam,'sampleX':[541,610],'rows':[]}
  for y in range(seam-2,seam+3):
   delta=[[i.getpixel((x,y))[c]-n.getpixel((x,y))[c] for x in range(541,611)] for c in range(3)];old=[[pi.getpixel((x,y))[c]-pn.getpixel((x,y))[c] for x in range(541,611)] for c in range(3)]
   item['rows'].append({'y':y,'meanIndependentMinusNativeRGB':[statistics.mean(d) for d in delta],'medianIndependentMinusNativeRGB':[statistics.median(d) for d in delta],'meanAbsoluteDeltaRGB':[statistics.mean(abs(v) for v in d) for d in delta],'previousRound06MeanIndependentMinusNativeRGB':[statistics.mean(d) for d in old],'allNativeAndIndependentAlpha255':all(n.getpixel((x,y))[3]==i.getpixel((x,y))[3]==255 for x in range(541,611))})
  stats.append(item)
# Nearest enlargement preserves exact source pixels; labels remain outside crops.
sheet=Image.new('RGB',(1728,920),(235,232,225));draw=ImageDraw.Draw(sheet)
for c,label in enumerate(['REVIEWED ROUND 06: INDEPENDENT','ROUND 07: NATIVE MESH JOIN','ROUND 07: INDEPENDENT SPRITES']):draw.text((c*576+8,8),label,fill=(25,25,25))
for row,(direction,y) in enumerate([('E',484),('E',740),('W',484),('W',740)]):
 draw.text((8,30+row*220),f'{direction}, SHARED ROW {y}; 6x NEAREST, UNALTERED RGB',fill=(25,25,25))
 for col,(folder,name) in enumerate([(OLD,'joined-independent'),(O,'joined-native'),(O,'joined-independent')]):
  im=Image.open(folder/f'{name}-{direction}.png').convert('RGBA').crop((528,y-16,624,y+16));bg=Image.new('RGBA',im.size,(235,232,225,255));bg.alpha_composite(im);sheet.paste(bg.convert('RGB').resize((576,192),Image.Resampling.NEAREST),(col*576,50+row*220))
sheet.save(O/'cap-shared-edge-crops.png')
preview={'id':'cap-shared-edge-crops','kind':'unaltered-nearest-native-independent-cap-crops','path':'candidates/round-07/cap-shared-edge-crops.png','size':list(sheet.size)}
V['previews'].append(preview);D['previews'].append(preview)
for name,original,kind in [('repeated.png','joined-independent-S.png','independent-runtime-repeated'),('repeated-native.png','joined-native-S.png','native-mesh-repeated')]:
 shutil.copyfile(O/original,O/name);p={'id':name.removesuffix('.png'),'kind':kind,'direction':'S','rootRotationZ':0.0,'path':'candidates/round-07/'+name,'size':[1152,1216]};V['previews'].append(p);D['previews'].append(p)
V['sharedCapRGBComparison']={'method':'Exact saved RGBA samples, native assembly versus standard alpha-over of independent native captures. No opacity proxy. Pixel deltas reported as evidence, without a visual approval claim.','samples':stats,'diagnostics':{'script':'source/diagnose-cap-seam.py','linearSamples':'candidates/cap-seam-diagnostics/linear-samples.json','singleNativeLinearEXR':'candidates/cap-seam-diagnostics/single-E.exr','joinedNativeLinearEXR':'candidates/cap-seam-diagnostics/native-E.exr'},'crops':'candidates/round-07/cap-shared-edge-crops.png'}
V['geometry']['capDetail']='Accepted cap rings, top normals and mesh geometry remain. Only cap cut faces have a native procedural camera-ray top-radiance field to remove vertical-cut hemisphere contamination; all non-camera rays retain the accepted BSDF.'
D['supportingRecipes'].append('source/round-07-join-rgb.py');D['notes'].append('Reviewed E/W cap stripe addressed natively on cap cut-face materials with a common symmetric top-radiance field. Native linear diagnostics identify the vertical face hemisphere cause. Exact RGB seam-row measurements and unchanged-pixel nearest crops are included; no sprite postprocessing.')
(O/'validation.json').write_text(json.dumps(V,indent=2));(P/'delivery.json').write_text(json.dumps(D,indent=2));(O/'delivery.json').write_text(json.dumps(D,indent=2))
print(json.dumps({'projectSHA256':hashlib.sha256((P/D['project']).read_bytes()).hexdigest(),'freshReloadPixelExact':V['freshReload']['renderPixelExactMatch'],'seamRGB':[{'direction':r['direction'],'row':r['sharedRow'],'mean':next(q['meanIndependentMinusNativeRGB'] for q in r['rows'] if q['y']==r['sharedRow'])} for r in stats],'profileError':V['profileMeasurements']['opposingYZProfileHausdorffError'],'previewCount':len(D['previews'])},indent=2))
