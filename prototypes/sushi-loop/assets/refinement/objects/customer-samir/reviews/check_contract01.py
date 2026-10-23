import json,pathlib,math,hashlib,subprocess,collections
from PIL import Image,ImageChops,ImageStat
import numpy as np
P=pathlib.Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/customer-samir');C=P/'candidates/round-01';R=P/'reviews';E=R/'round-01-evidence';mapd=json.loads((R/'food-mapping-proposal.json').read_text());report={'native':{},'adapter':{},'videos':[],'replayRenders':[],'submittedSheets':[]}
flatten=lambda v:[v] if isinstance(v,(int,float)) else sum([flatten(x) for x in v.values()],[]) if isinstance(v,dict) else sum([flatten(x) for x in v],[])
ray=np.array([0,-math.cos(math.radians(35)),math.sin(math.radians(35))]);basis=np.array([[256,0,0],[0,-256*math.sin(math.radians(35)),-256*math.cos(math.radians(35))]])
for mode,meal in [('main','cucumber'),('runtime','salmon')]:
 src=json.loads((R/('baseline-'+mode)/'audit.json').read_text());a=json.loads((R/('round-01-native-'+mode)/'audit.json').read_text());m=mapd['proposals'][meal]['thresholdSensitivity']['128'];food=a['food'];verts=np.array(food['vertices']);expected=np.array(m['newFullUVLocalVertices']);uv=food['UV'];stats={'samples':0,'restMatchesSource':a['rig']['restSHA256']==src['rig']['restSHA256'],'allActionCurveHashesMatchSource':a['rig']['actionSHA256']==src['rig']['actionSHA256'],'frame':a['nativeRenderSettings'],'rootProjection':a['rootProjection'],'bodyGeometryWeightsSignature':a['bodyGeometryMaterialsWeights'],'foodPackedSHA256':food['packedSHA256'],'foodVertexMaxErrorLocal':float(abs(verts-expected).max()),'fullUV':uv==[[0,0],[1,0],[1,1],[0,1]],'maxContactWorldError':0,'maxFunctionalBoneMatrixError':0,'maxRootMatrixError':0,'maxFoodRootWorldError':0,'maxXYAbsBody':0,'maxZEnvelopeExcess':-999,'maxVisibleFlagError':0,'depthMin':999,'depthMax':-999,'rayPerpendicularMax':0,'projectedCornerInvarianceMaxNativePixels':0,'actualRecordedCameraCornerInvarianceMaxNativePixels':0,'actualRecordedCameraRimInvarianceMaxNativePixels':0,'mappedRimSupportErrorLocal':0,'directionCounts':collections.Counter()}
 for clip,cv in a['clips'].items():
  for x,y in zip(cv['samples'],src['clips'][clip]['samples']):
   stats['samples']+=1;stats['directionCounts'][x['direction']]+=1
   for out,key in [('maxContactWorldError','evaluatedContactsWorld'),('maxFunctionalBoneMatrixError','functionalBoneWorldMatrices'),('maxRootMatrixError','rootMatrix'),('maxFoodRootWorldError','foodRootWorld')]:stats[out]=max(stats[out],max(abs(i-j) for i,j in zip(flatten(x[key]),flatten(y[key]))))
   stats['maxXYAbsBody']=max(stats['maxXYAbsBody'],*[abs(v) for b in x['bodyBounds'] for v in b[:2]]);stats['maxZEnvelopeExcess']=max(stats['maxZEnvelopeExcess'],x['bodyBounds'][1][2]-src['clips'][clip]['boundsUnion'][1][2]);stats['maxVisibleFlagError']=max(stats['maxVisibleFlagError'],int(x['foodVisible']!=y['foodVisible']))
   mat=np.array(x['foodPlaneMatrix']);delta=mat[:3,3]-np.array(x['foodRootWorld']);depth=float(delta@ray);stats['depthMin']=min(stats['depthMin'],depth);stats['depthMax']=max(stats['depthMax'],depth);stats['rayPerpendicularMax']=max(stats['rayPerpendicularMax'],float(np.linalg.norm(delta-depth*ray)))
   # A depth change adds one constant registered camera-ray vector to every canonical mapped corner, hence all support points as well.
   toward_source=(.6-depth)*ray
   view=np.linalg.inv(np.array(a['camera']['matrix']));projection=np.array(a['camera']['projectionMatrix']);source_plane=np.array(y['foodPlaneMatrix'])
   def actual_px(local,plane_matrix):
    world=plane_matrix@np.array([local[0],local[1],local[2],1]);ndc=projection@view@world;ndc=ndc/ndc[3];return np.array([(ndc[0]+1)*192,(1-ndc[1])*320])
   for corner in verts:stats['actualRecordedCameraCornerInvarianceMaxNativePixels']=max(stats['actualRecordedCameraCornerInvarianceMaxNativePixels'],float(abs(actual_px(corner,mat)-actual_px(corner,source_plane)).max()))
   rimlocal=m['sourceBottomRimLocalXY']+[0];stats['actualRecordedCameraRimInvarianceMaxNativePixels']=max(stats['actualRecordedCameraRimInvarianceMaxNativePixels'],float(abs(actual_px(rimlocal,mat)-actual_px(rimlocal,source_plane)).max()))
   stats['projectedCornerInvarianceMaxNativePixels']=max(stats['projectedCornerInvarianceMaxNativePixels'],float(abs(basis@toward_source).max()))
  drs=['S','E','N','W']
  for dr in drs:
   submitted=C/mode/'frames'/clip.replace('_','-')/dr/'04.png';replay=R/('round-01-native-'+mode)/(clip+'-'+dr+'-f05.png');im=Image.open(submitted).convert('RGBA');got=Image.open(replay).convert('RGBA');diff=ImageChops.difference(im,got);report['replayRenders'].append({'submitted':str(submitted),'nativeReopenedRender':str(replay),'exactObservedRGBAEquality':diff.getbbox(alpha_only=False) is None,'RGBAmeanAbsoluteDifference':ImageStat.Stat(diff).mean,'scope':'Empirical replay of these exact inputs/settings on this machine; no universal render determinism claim.'})
 # full UV isotropic aspect proof and canonical bottom-rim local point on the unchanged mapper
 r=json.loads((R/'food-raster-baseline.json').read_text())['canonical-'+meal];W,H=r['size'];rp=r['thresholds']['128']['bottomRimSupportTopOriginEdges'];rim=verts[0,:2]+np.array([(rp[0]/W)*(verts[1,0]-verts[0,0]),((H-rp[1])/H)*(verts[3,1]-verts[0,1])]);stats['mappedRimSupportErrorLocal']=float(abs(rim-np.array(m['sourceBottomRimLocalXY'])).max());stats['quadAspectError']=abs((verts[1,0]-verts[0,0])/(verts[3,1]-verts[0,1])-W/H)
 report['native'][mode]=stats
 phases=json.loads((P/'candidates/round-01-import-adapter'/('candidate-phases.json' if mode=='main' else 'runtime-native-phases.json')).read_text());lookup={(c.replace('_','-'),s['direction'],s['frame']):s for c,v in a['clips'].items() for s in v['samples']};errors=[]
 for q in phases:
  s=lookup[(q['clip'],q['direction'],q['nativeFrame'])]
  if max(abs(i-j) for i,j in zip(flatten(q['actualRootMatrix']),flatten(s['rootMatrix'])))>1e-5:errors.append(q['path'])
  oldv=json.loads((C/mode/'validation-native.json').read_text());v=oldv
  for piece in q['measurementSource']['jsonPointer'].strip('/').split('/'):v=v[int(piece)] if isinstance(v,list) else v[piece]
  if v!=q['actualRootMatrix']:errors.append('old-pointer:'+q['path'])
 report['adapter'][mode]={'samples':len(phases),'originalActualMatrixPointerAndIndependentNativeMatrixErrors':errors,'counts':dict(collections.Counter(q['direction'] for q in phases))}
 for v in sorted((C/mode/'playback').glob('*.mp4')):
  p=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-select_streams','v:0','-count_frames','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,nb_read_frames,duration','-of','json',str(v)]));report['videos'].append({'path':str(v),'probe':p['streams'][0]})
 # Submitted background sheet raster cells must match same native frames, at exact logical size; background aliases are reviewed by equivalence plus directly viewed examples.
 for atlas in sorted((C/mode/'atlases').glob('*.png')):
  state,dr=atlas.stem.rsplit('-',1)
  for bg in ['light','gray','dark']:
   sp=C/'sheets'/(state+'-'+dr+'-'+bg+'.png');sheet=Image.open(sp).convert('RGB');pixel=sheet.getpixel((0,0));bad=[]
   for i in range(12):
    f=Image.open(C/mode/'frames'/state/dr/f'{i:02}.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);flat=Image.new('RGB',(192,320),pixel);flat.paste(f,(0,0),f);piece=sheet.crop((i*192,26,(i+1)*192,346));d=ImageChops.difference(flat,piece)
    if d.getbbox(alpha_only=False):bad.append(i)
   report['submittedSheets'].append({'path':str(sp),'background':pixel,'nativeFrameCellRasterErrors':bad})
(E/'independent-contract-summary.json').write_text(json.dumps(report,indent=2)+'\n');print('NATIVE',json.dumps(report['native'],indent=2));print('SUMMARY',{'adapterErrors':sum(len(v['originalActualMatrixPointerAndIndependentNativeMatrixErrors']) for v in report['adapter'].values()),'videoCount':len(report['videos']),'replayed':len(report['replayRenders']),'observedExactReplays':sum(v['exactObservedRGBAEquality'] for v in report['replayRenders']),'sheetCount':len(report['submittedSheets']),'sheetCellErrors':sum(len(v['nativeFrameCellRasterErrors']) for v in report['submittedSheets'])})
