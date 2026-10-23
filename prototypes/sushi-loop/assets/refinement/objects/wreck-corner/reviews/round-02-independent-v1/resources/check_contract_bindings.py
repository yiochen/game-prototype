from pathlib import Path
import json,hashlib,numpy as np
P=Path(__file__).resolve().parents[1];O=P.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();audit=json.loads((P/'native-independent-audit.json').read_text())['candidate'];original=json.loads((O/'reviews/preparation-v1/original-native-audit.json').read_text());checks=[]
def simplify(v):
 p=[np.array(x,dtype=float)for x in v];changed=True
 while changed and len(p)>3:
  changed=False
  for i in range(len(p)):
   if np.linalg.norm(np.cross(p[i]-p[i-1],p[(i+1)%len(p)]-p[i]))<1e-7:p.pop(i);changed=True;break
 return p
rail=lambda n:'rear'if 'rear_'in n or'back_'in n else'lower'if'lower_'in n else'upper'
for view in audit['views']:
 for side,faces in view['caps'].items():
  for face in faces:
   src=next(f for f in original['caps'][side]if rail(f['object'])==rail(face['owner']));a=simplify(face['vertices']);b=simplify(src['vertices']);err=max(min(float(np.linalg.norm(x-y))for y in b)for x in a);checks.append({'view':view['direction'],'port':side,'rail':rail(face['owner']),'actualCornerCountAfterCollinearSimplification':len(a),'sourceCornerCount':len(b),'finiteContourMaxDistance':err,'sameContour':len(a)==len(b)==4 and err<1e-6})
old=json.loads((O/'candidates/round-01/packet.json').read_text());new=json.loads((P/'resources/packet.json').read_text());thin=json.loads((P/'resources/native-validation02.json').read_text());ledger=json.loads((P/'resources/native-ledger01.json').read_text());result={'candidatePacketSHA256':sha(P/'resources/packet.json'),'sourceSHA256':sha(P/'resources/candidate.blend'),'all24ActualPortContours':checks,'allContoursMatch':all(x['sameContour']for x in checks),'metadataOnlyRound02':{'sameSourceSHA256':old['files']['candidateProject']['sha256']==new['files']['candidateProject']['sha256'],'sameEveryHeroAndPreviewHash':all(old[g][name]['sha256']==rec['sha256']for g in ['candidateRenders','previews']for name,rec in new[g].items()),'thinViewsExactlyOriginalMeasuredViews':thin['views']==ledger['views'],'supportedThinLedgerOmitsUnsupportedGeometryShape':'nativeGeometryMeasurements'not in thin,'originalCompleteLedgerSHA256':sha(P/'resources/native-ledger01.json'),'newMeasurementsClaimed':thin.get('newMeasurements'),'approvalOrPriorCoverageInferred':False},'scope':'Original01 was unsubmitted preflight. All current candidate art independently inspected afresh, no prior candidate visual coverage reused.'}
(P/'contract-and-evidence02-binding.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k!='all24ActualPortContours'},indent=2))
