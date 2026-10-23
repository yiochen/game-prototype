from pathlib import Path
import json,shutil,hashlib
P=Path(__file__).resolve().parent.parent
R=P/'source/round-01/resources';R.mkdir(parents=True,exist_ok=True)
b=json.loads((P/'brief.json').read_text())
files={'frozen-brief.json':P/'brief.json','frozen-criteria.json':P/'reviews/proposedcriteria.json','source-contract-summary.json':P/'reviews/source-contract-summary.json','food-mapping-proposal.json':P/'reviews/food-mapping-proposal.json','source-main-rig.json':P/'inputs/source-rig.json','source-runtime-rig.json':P/'inputs/runtime-variants/export/source/customer-samir/rig.json','source-camera.json':P/'inputs/source-camera.json','source-main-audit.json':P/'reviews/baseline-main/audit.json','source-runtime-audit.json':P/'reviews/baseline-runtime/audit.json','native_actions.py':P.parents[2]/'production/source/blender/native_actions.py','target.png':P/'inputs/target.png','original.png':P/'inputs/original.png','family-concept.png':P/'inputs/family-concept.png','plant-style-reference.png':P.parents[1]/'style/warm-soft-reference.png'}
for food in ['dish-cucumber','dish-salmon']:
 dep=b['foodDependencies'][food]
 for key in ['artwork','packet','review']:files[food+'-'+('canonical.png' if key=='artwork' else key+'.json')]=(P/dep[key]).resolve()
manifest={}
for name,path in files.items():
 shutil.copyfile(path,R/name); manifest[name]={'sourcePath':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(P/'source/round-01/input-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
(P/'source/criteria-acknowledged.json').write_text(json.dumps({'frozenBriefSHA256':hashlib.sha256((P/'brief.json').read_bytes()).hexdigest(),'criteriaSHA256':manifest['frozen-criteria.json']['sha256'],'agreedOutcomes':b['qualityCriteria']['rankedOutcomes'],'technicalPolicy':b['constraints'],'implementationChosen':'Native refined cap crown and curved bill, smooth rebuilt ellipsoid hair/face details, tailored collar and soft bevel garment construction. Same geometry recipe for main/runtime. One alpha128 fixed canonical fullUV semantic map per composition, fixed .30 world-cell camera-ray depth. No mesh count or source vertex-coordinate equality assumption.','approval':'Pending independent judge; editor does not self-approve.'},indent=2)+'\n')
