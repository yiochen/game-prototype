import json,hashlib,copy
from pathlib import Path
O=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-cover');R=O/'reviews/round-03-independent';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();submitted=read(O/'candidates/round-03/consumer/consumer-evidence.json');fresh=read(R/'reproduction/consumer/consumer-evidence.json');key=lambda r:(r['case'],r['direction'],r['clip'],r['index']);by={key(r):r for r in submitted['humanCases']};rows=[]
for row in fresh['humanCases']:
 other=by[key(row)];a=copy.deepcopy(row);b=copy.deepcopy(other);a.pop('path');b.pop('path');assert a==b
 assert sha(O/row['path'])==sha(O/other['path'])==row['sha256'];rows.append({'case':list(key(row)),'recordExceptOutputPathExact':True,'imageSHA256':row['sha256'],'imageBytesExact':True})
controls={key(r):r for r in submitted['equalityControls']}
for row in fresh['equalityControls']:
 other=controls[key(row)];a=copy.deepcopy(row);b=copy.deepcopy(other);a['correctedImage'].pop('path');b['correctedImage'].pop('path');assert a==b
assert fresh['contacts']==submitted['contacts'];assert fresh['humanSupports']==submitted['humanSupports'];assert fresh['errors']==[]
native=read(R/'reproduction/native-input-verification.json');assert native['verifiedRawFrames']==96 and native['repackedOriginalLayoutAtlases']==8 and native['nativeRerendered']is False;assert all(r['exactPNGBytes']for r in native['atlases']);assert not(R/'reproduction/repacked-native-inputs').exists()
report={'candidatePacketSHA256':sha(O/'candidates/round-03/packet.json'),'scope':'Fresh actual execution of inspected bounded portable recipe; no native rerender. Eight byte-identical atlases temporarily reconstructed from96 preserved raw references, then removed. All108 source-derived rows compared;36 actual regenerated images,72 reused rows.','freshRowsExactExceptOutputPath':108,'actualFreshCorrectedImages':36,'equalityControlsExactExceptOutputPath':36,'sameFiniteContactEvidence':True,'sameTruthfulSupportMap':True,'errors':[],'rows':rows};(R/'reproduction-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: 36 actual fresh images,108 exact non-path rows,36 original-control identities; unchanged native art')
