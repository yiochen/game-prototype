from pathlib import Path
import json,shutil,hashlib
B=Path(__file__).resolve().parent.parent;E=B.parent/'dock-entry';OUT=B/'candidates/round-03';R=B/'source/resources/family-rigs';R.mkdir(parents=True,exist_ok=True)
shutil.copytree(E/'candidates/round-05/native-context-v2',OUT/'native-context-v2',dirs_exist_ok=True)
shutil.copyfile(E/'candidates/round-05/paired-native-validation-v2.json',OUT/'paired-family-original-evidence.json')
shutil.copyfile(E/'source/capture-pair-family.py',B/'source/resources/entry-context-original-recipe.py')
for aid in ['submarine-yellow','dock-cover','customer-rosa']:
 src=B.parent/aid/'inputs/source-rig.json';shutil.copyfile(src,R/(aid+'.json'))
s=(E/'source/capture-pair-family.py').read_text().replace("OUT=B/'candidates/round-05'","OUT=B/'candidates/round-03'").replace("FAM=OUT/'native-context-v2'","FAM=OUT/'native-context-replay'")
s=s.replace("entryfile=B/'source/round-05.blend';floorfile=B/'inputs/paired-native/dock-floor-round-03.blend';original=B.parents[1]/'backups/b1765262bfa897ad-sushi-loop-world-library.blend'","entryfile=B/'inputs/paired-native/dock-entry-round-05.blend';floorfile=B/'source/round-03.blend';original=B/'source/resources/original-library.blend'")
s=s.replace("(B.parent/asset/'inputs/source-rig.json')","(B/'source/resources/family-rigs'/(asset+'.json'))")
s=s.replace("(B/'source/paired-source-binding.json')","(B/'source/paired-source-binding.json')").replace("OUT/'paired-native-validation-v2.json'","OUT/'paired-family-replay-evidence.json'")
(B/'source/capture-family.py').write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(B/'source/paired-source-binding.json').write_text(json.dumps({'floor':{'path':'source/round-03.blend','sha256':sha(B/'source/round-03.blend')},'entry':{'path':'inputs/paired-native/dock-entry-round-05.blend','sha256':sha(B/'inputs/paired-native/dock-entry-round-05.blend')},'inMemoryAppendOnly':True},indent=2))
