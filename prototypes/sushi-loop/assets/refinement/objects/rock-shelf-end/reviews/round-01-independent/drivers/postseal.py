from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R.parent.parent;W=O.parents[5]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
review=O/'reviews/round-01.json';manifest=R/'supplemental-manifest.json';gate=R/'logs/acceptance-contract.log';tool=R/'resources/acceptance_contract.py'
v=json.loads(review.read_text());m=json.loads(manifest.read_text());g=json.loads(gate.read_text())
assert g['asset']=='rock-shelf-end' and g['method']=='independent-review' and g['sha256']==sha(review)
assert v['supplementalEvidence']['sha256']==sha(manifest) and m['candidatePacketSHA256']==v['candidatePacketSHA256']
for item in m['files']:assert sha(O/item['path'])==item['sha256'],item['path']
seal={'asset':'rock-shelf-end','round':'round-01','verdict':v['verdict'],'candidatePacketSHA256':v['candidatePacketSHA256'],'review':{'path':'reviews/round-01.json','sha256':sha(review)},'supplementalManifest':{'path':'reviews/round-01-independent/supplemental-manifest.json','sha256':sha(manifest)},'gate':{'path':'reviews/round-01-independent/logs/acceptance-contract.log','sha256':sha(gate),'unchangedValidatorSHA256':sha(tool),'result':g},'acyclicOrder':'supplemental inputs/artifacts -> manifest -> review -> gate result -> this postseal; manifest excludes review/gate/postseal','sourceSHA256':sha(O/'source/round-01.blend'),'noFurtherPermission':'Asset/candidate-specific visual approval only; no family derivative, production, publish or Godot approval inferred.'}
(R/'postseal.json').write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps(seal,indent=2))
