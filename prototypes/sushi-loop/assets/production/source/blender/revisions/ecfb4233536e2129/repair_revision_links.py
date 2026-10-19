from pathlib import Path
import os,hashlib,shutil,json
base=Path('/Users/yiouchen/.codex/worktrees/sushi-loop-33-art-catalog/game-prototype/prototypes/sushi-loop/assets/production/source/blender')
original=Path('/private/tmp/sushi33-production/production_library-before-state-coverage.py')
expected='9e9fbb9bf6e1f5573ee5c0602980863934746ca82a1ad5fc6332c1ab72babbbe'
assert hashlib.sha256(original.read_bytes()).hexdigest()==expected
destination=base/'revisions'/expected[:16]/'production_library.py'
temporary=destination.with_name(destination.name+'.repair-tmp');shutil.copy2(original,temporary);os.replace(temporary,destination)
old=base/'revisions/1892f72fd6b2eb43/sushi-loop-world-library.blend'
if old.exists():
 actual=hashlib.sha256(old.read_bytes()).hexdigest()
 if not actual.startswith('1892f72fd6b2eb43'):
  quarantine=base/'recovered-link-overwrite/1892f72fd6b2eb43';quarantine.mkdir(parents=True,exist_ok=True)
  shutil.copy2(old,quarantine/'replacement-complete-library.blend')
  (quarantine/'provenance.json').write_text(json.dumps({'status':'historical-hardlink-was-overwritten-current-complete-source-retained','missingOriginalSHA256':'1892f72fd6b2eb4356a15fb56487e926fbd787286e42d851b52f7790d32939c3','retainedReplacementSHA256':actual,'currentCompleteSource':'../../sushi-loop-world-library.blend','manifestRequiresRepublishToCurrentCompleteSource':True},indent=2)+'\n')
  old.unlink()
print('Restored exact original wrapper; quarantined overwritten historical blend under explicit provenance. Current complete project remains intact.')
