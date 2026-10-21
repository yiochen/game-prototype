from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np,json,hashlib
R=Path(__file__).resolve().parent;O=R.parents[1]/'candidates/round-09';M=O/'markers';data=json.loads((M/'marker-record.json').read_text());rows=[]
for r in data['captures']:
 x,y,w,h=r['tile'];sample_y=y+(2+w*.1 if r['marker']=='ground' else h*.5);iy=int(np.floor(sample_y));lo=int(np.floor(x))-4;hi=int(np.floor(x))+int(np.ceil(max(10,w*.30)));values={}
 for mode in ['baseline','native']:
  image=np.asarray(Image.open(r[mode])).astype(float);a=image[:,:,3]/255;profile=a[iy-1:iy+2,lo:hi].mean(axis=0);fill=float(np.median(a[iy-1:iy+2,int(x+w*.35):int(x+w*.65)]));coverage=np.clip((profile-fill)/(1-fill),0,1);positions=np.arange(lo,hi)+.5;centroid=float((coverage*positions).sum()/coverage.sum());core=positions[coverage>.5]
  values[mode]={'effectiveStrokeCoveragePixels':float(coverage.sum()),'strokeCentroidX':centroid,'coreWidthAtHalfCoverage':int(len(core)),'coreCentroidX':float(core.mean()) if len(core) else None,'rowRange':[iy-1,iy+2],'xRange':[lo,hi],'alphaProfile':profile.tolist(),'strokeCoverageProfile':coverage.tolist(),'fillAlpha':fill,'sha256':hashlib.sha256(Path(r[mode]).read_bytes()).hexdigest()}
 a=np.asarray(Image.open(r['baseline']),dtype=np.int16);b=np.asarray(Image.open(r['native']),dtype=np.int16);crop=[int(np.floor(x))-4,int(np.floor(y))-4,int(np.ceil(x+w))+4,int(np.ceil(y+h))+4];diff=np.abs(a[crop[1]:crop[3],crop[0]:crop[2]]-b[crop[1]:crop[3],crop[0]:crop[2]])
 rows.append({'name':r['name'],'marker':r['marker'],'fixture':r['fixture'],'cell':w,'nominal':{'groundInsetPx':r['ground_inset_px'],'groundStrokePx':r['ground_stroke_px'],'expectedGroundStrokePx':max(2,w*.04),'ghostInsetPx':r['ghost_inset_px'],'ghostStrokePx':r['ghost_stroke_px']},'crossSections':values,'centroidDifferencePx':abs(values['baseline']['strokeCentroidX']-values['native']['strokeCentroidX']),'coreWidthDifferencePx':abs(values['baseline']['coreWidthAtHalfCoverage']-values['native']['coreWidthAtHalfCoverage']),'effectiveCoverageDifferencePx':abs(values['baseline']['effectiveStrokeCoveragePixels']-values['native']['effectiveStrokeCoveragePixels']),'markerCropMaxRGBA':diff.reshape(-1,4).max(axis=0).tolist()})
summary={'actualGPUComparisons':len(rows),'allFixedPixelRoundTripsWithin1e6':all(abs(r['fixed_pixel_roundtrip']-1)<1e-6 for r in data['captures']),'groundNominalStrokeMaxErrorPx':max(abs(r['nominal']['groundStrokePx']-r['nominal']['expectedGroundStrokePx']) for r in rows),'maxStrokeCentroidDifferencePx':max(r['centroidDifferencePx'] for r in rows),'maxHalfCoverageCoreWidthDifferencePx':max(r['coreWidthDifferencePx'] for r in rows),'maxEffectiveStrokeCoverageDifferencePx':max(r['effectiveCoverageDifferencePx'] for r in rows),'probeFailures':data['failures']}
result={'method':'Actual Godot GPU PNGs from the unchanged baseline marker functions and fixed candidate functions through full native layer/area reduction. Three-row cross-sections halfway along the left bracket arm or ghost left border; stroke coverage is inferred from alpha above the measured fill plateau. Core width uses >0.5 inferred stroke coverage. Different vector antialias/pixel-area rasterization can change coverage; native and direct images are not claimed pixel-identical.','summary':summary,'pairs':rows};(M/'marker-metrics.json').write_text(json.dumps(result,indent=2))
for phase in ['aligned','fractional']:
 canvas=Image.new('RGB',(1800,1800),(243,241,231));draw=ImageDraw.Draw(canvas);draw.text((12,8),'Original direct markers | fixed native-world markers (actual GPU pixels, nearest enlarged for inspection)',fill=(25,40,50));Y=40;maxwidth=0
 for fixture in ['phone32','phone55','portrait','landscape']:
  draw.text((10,Y),fixture+' / '+phase,fill=(25,40,50));Y+=20;X=10;maxheight=0
  for marker in ['ground','ghost-valid','ghost-invalid']:
   r=next(x for x in data['captures'] if x['name']==fixture+'-'+phase+'-'+marker);x,y,w,h=r['tile'];box=(int(x)-4,int(y)-4,int(np.ceil(x+w))+4,int(np.ceil(y+h))+4);factor=4 if w<=55 else 2
   for mode in ['baseline','native']:
    im=Image.open(r[mode]).convert('RGBA').crop(box);rgb=Image.new('RGBA',im.size,(238,231,206,255));rgb.alpha_composite(im);rgb=rgb.convert('RGB').resize((im.width*factor,im.height*factor),Image.Resampling.NEAREST);draw.text((X,Y),marker+' '+mode,fill=(25,40,50));canvas.paste(rgb,(X,Y+16));X+=rgb.width+8;maxheight=max(maxheight,rgb.height)
  Y+=maxheight+30;maxwidth=max(maxwidth,X)
 canvas=canvas.crop((0,0,maxwidth,Y));canvas.save(M/('marker-comparison-'+phase+'.png'))
print(json.dumps(summary,indent=2))
