import pathlib,json,math,itertools,hashlib
out=pathlib.Path(__file__).resolve().parent
poses=json.loads((out/'source-replay/poses.json').read_text());curves=json.loads((out/'source-replay/native-curves.json').read_text());cam=json.loads((out/'resources/experiment/inputs/source-camera.json').read_text())
ux=cam['calibration']['unitX'][0]/cam['captureScale'];uy=-cam['calibration']['unitDepth'][1]/cam['captureScale'];uz=cam['calibration']['unitHeight'][1]/cam['captureScale']
boxes=[[[-.52,-.30,0],[-.34,.30,.16]],[[.34,-.30,0],[.52,.30,.16]]]
corners=[p for box in boxes for p in itertools.product(*[(box[0][i],box[1][i]) for i in range(3)])]
def bb(pp):return [[min(p[i] for p in pp) for i in range(len(pp[0]))],[max(p[i] for p in pp) for i in range(len(pp[0]))]]
def phase(theta,p):
 s=1+.015*math.sin(theta);b=.008*(1-math.cos(theta));return [p[0]*s,p[1]*s,p[2]*s+b]
def analytic(a,b,c):
 r=math.hypot(b,c);return [a-r,a+r]
source={}
for d in ['N','E','S','W']:
 ps=[p for p in poses if p['direction']==d and p['clip']=='active' and p['frame']<=12];idle=next(p for p in poses if p['direction']==d and p['clip']=='idle');last=next(p for p in poses if p['direction']==d and p['clip']=='active' and p['frame']==13)
 source[d]={'neutralNativeBounds':idle['nativeBounds'],'activeNativeSweep':[[min(p['nativeBounds'][0][i] for p in ps) for i in range(3)],[max(p['nativeBounds'][1][i] for p in ps) for i in range(3)]],'activeLogicalSweep':[[min(p['logicalBounds'][0][i] for p in ps) for i in range(2)],[max(p['logicalBounds'][1][i] for p in ps) for i in range(2)]],'uniquePoseStates':len({json.dumps(p['owners'],sort_keys=True) for p in ps}),'closureOwnersExact':last['owners']==ps[0]['owners']}
proposed={}
for d,ang in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 c,s=math.cos(ang),math.sin(ang);rot=lambda p:(c*p[0]-s*p[1],s*p[0]+c*p[1],p[2]);native=[];pixel=[];samples=[];ranges=[[],[],[]];pxranges=[[],[]]
 for p in corners:
  x,y,z=rot(p)
  ranges[0].append(analytic(x,.015*x,0));ranges[1].append(analytic(y,.015*y,0));ranges[2].append(analytic(z+.008,.015*z,-.008))
  pxranges[0].append(analytic(96+ux*x,.015*ux*x,0))
  flat=uy*y+uz*z
  pxranges[1].append(analytic(248+flat+uz*.008,.015*flat,-uz*.008))
 for f in range(13):
  pp=[rot(phase(math.tau*f/12,p)) for p in corners];xy=[[96+ux*p[0],248+uy*p[1]+uz*p[2]] for p in pp];samples.append({'runtimeFrame':f,'nativeBounds':bb(pp),'logicalBounds':bb(xy),'scale':1+.015*math.sin(math.tau*f/12),'bob':.008*(1-math.cos(math.tau*f/12))})
 continuous=[[min(t[0] for t in r) for r in ranges],[max(t[1] for t in r) for r in ranges]];projection=[[min(t[0] for t in r) for r in pxranges],[max(t[1] for t in r) for r in pxranges]]
 proposed[d]={'continuousConservativeNativeSweep':continuous,'continuousConservativeLogicalSweep':projection,'insideLockedFrameContinuously':projection[0][0]>=0 and projection[0][1]>=0 and projection[1][0]<=192 and projection[1][1]<=352,'samples':samples}
# If old pivot/pulse/bob law were applied unchanged to new Z0 saddle underside.
old_pivot_min=min(.18+(-.18)*(1+.015*math.sin(math.tau*f/12))+.008*math.cos(math.tau*f/12) for f in range(12))
record={'scope':'Numeric source audit plus proposed motion-envelope feasibility; no new geometry or candidate approval','sourceMechanics':{'derivedFrom':'All actual saved native F-curves in source-replay/native-curves.json, not clip names','formula':'global uniform s=1+.015*sin(theta), about local pivot(0,0,.18), plus .008*cos(theta) Z bob; theta=2*pi*(frame-1)/12. Owner translations and scales reconstruct this affine transform.','staticNeutral':'idle is s1,bob0. active frame1 is s1,bob+.008, so active frame1 must not be used as canonical neutral.','directions':source},'newNeutralStaticReservation':boxes,'reconciliation':{'requestedBy':'Root coordinator during preparation','proposedLaw':'s=1+.015*sin(theta), pivot at ground origin; zBob=.008*(1-cos(theta)); theta=2*pi*(frame-1)/12','meaning':'Subtle 1.5% breathing with gentle 0..016 Z lift; no mechanical opening or new game effect. Main adopts exact idle only.','timing':{'fps':12,'idleFrames':1,'activeRuntimeFrames':12,'closingKeyFrame':13,'runtimeFrameOrder':list(range(12))},'oldLawMinimumZOnNewSaddle':old_pivot_min,'newLawContinuousMinimumZ':0,'newLawContinuousMaximumZ':.168+math.hypot(.0024,.008),'mountChange':False,'rootCameraChange':False,'noPenetrationForAnyNeutralVertexWithZNonnegative':True,'requiredFreezes':['Approve this explicit motion repair instead of silently treating old F-curves as preserved','Keep neutral static occupied side boxes separate from standalone active swept reservation','Integrate only exact approved idle local mesh/normals/UV/material resources at frozen transform; no active mapping']},'proposedNewReservationFeasibility':proposed}
(out/'motion-envelope-proposal.json').write_text(json.dumps(record,indent=2));print(json.dumps({'source':source,'newLawMinimumZ':0,'newLawMaximumZ':record['reconciliation']['newLawContinuousMaximumZ'],'newContinuousSweeps':{d:{k:v for k,v in r.items() if k!='samples'} for d,r in proposed.items()}},indent=2))
