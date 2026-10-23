import pathlib,json,gzip,math,hashlib
R=pathlib.Path(__file__).resolve().parent;O=R.parent;brief=json.loads((O/'brief.json').read_text());maps=json.loads((R/'semantic-food-mapping.json').read_text());results={};sem={};envelopes={};ok=True
for kind,entry in zip(['main','runtime'],maps):
 old=json.loads(gzip.decompress((R/f'source-samples-{kind}.json.gz').read_bytes()));new=json.loads(gzip.decompress((R/f'source-samples-round05-{kind}.json.gz').read_bytes()));o=json.loads((R/f'source-contract-{kind}.json').read_text());n=json.loads((R/f'source-contract-round05-{kind}.json').read_text());errors={'bones':0,'contacts':0,'foodRoot':0};counts=0;v=0;maxp=0;m=entry['thresholds'][1];qw,qh=m['proposedFullUVQuadWorld'];dx=m['proposedFullUVCenterOffsetXWorld'];up=m['proposedFullUVBottomOffsetWorld'];visibility=True
 for clip,arr in old.items():
  for a,b in zip(arr,new[clip]):
   assert (a['facing'],a['frame'])==(b['facing'],b['frame']);counts+=1;v+=b['foodVisible'];visibility&=a['foodVisible']==b['foodVisible']
   for group in ['bones','contacts']:
    for k,xyz in a[group].items():errors[group]=max(errors[group],max(abs(x-y) for x,y in zip(xyz,b[group][k])))
   errors['foodRoot']=max(errors['foodRoot'],max(abs(x-y) for x,y in zip(a['foodRoot'],b['foodRoot'])))
   if a['foodVisible']:
    corners=a['projectedCorners'];cx=(corners[0][0]+corners[1][0])/2+dx*256;y=corners[0][1]-up*256;expected=[[cx-qw*128,y],[cx+qw*128,y],[cx+qw*128,y-qh*256],[cx-qw*128,y-qh*256]];maxp=max(maxp,max(abs(x-y) for aa,bb in zip(expected,b['projectedCorners']) for x,y in zip(aa,bb)))
 actionsEqual=all([a['sha256'] for a in o['clips'][c]['actions']]==[a['sha256'] for a in n['clips'][c]['actions']] for c in o['clips']);restEqual=o['restBones']==n['restBones'];rows=[]
 for clip,values in n['clips'].items():
  lim=brief['constraints']['functionalGeometryEnvelope']['perClipBodyZWorld'][clip.replace('_','-')];mn,mx=values['physicalGeometryBounds'];passed=min(mn[0],mn[1])>=-.50001 and max(mx[0],mx[1])<=.50001 and mn[2]>=lim[0]-1e-5 and mx[2]<=lim[1]+1e-5;ok&=passed;rows.append({'clip':clip,'bounds':[mn,mx],'allowedZ':lim,'passed':passed})
 results[kind]={'poses':counts,'maxError':errors,'allVisibilityEqual':visibility,'visibleFoodSamples':v,'restBonesEqual':restEqual,'actionsEqual':actionsEqual,'rootScale':n['rootScale'],'camera':n['registeredCamera'],'foodBytes':n['food']['packedSHA256'],'uv':n['food']['uv'],'foodVertices':n['food']['localVertices'],'depthDrivers':n['food']['drivers']};sem[kind]={'visibleSamplesCompared':v,'maxCorrectedSemanticCornerErrorPx':maxp,'correctedCanonicalQuadWorld':[qw,qh],'screenXOffsetWorld':dx,'screenUpBottomOffsetWorld':up};envelopes[kind]=rows
for f,d in [('round05-independent-native-comparison.json',results),('round05-independent-semantic-projection.json',sem),('round05-independent-envelope.json',{'allPassed':ok,'checks':envelopes})]:(R/f).write_text(json.dumps(d,indent=2)+'\n')
print(json.dumps({'native':{k:{x:v[x] for x in ['poses','maxError','allVisibilityEqual','visibleFoodSamples','restBonesEqual','actionsEqual']} for k,v in results.items()},'semantic':sem,'allEnvelopesPassed':ok},indent=2))
