from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parents[2];obj=B.parents[1];old=obj/'reviews/round-01-independent';D=B/'resources/drivers'
for name in ['freeze_used.py','inspect_replay.py','consumer.html','consumer.mjs','analyze_evidence.py','probe_runtimes.mjs']:
 s=(old/'resources/drivers'/name).read_text().replace('round-01','round-02').replace('round01','round02').replace('Round01','Round02')
 if name=='inspect_replay.py':s=s.replace("'ADD':lambda:a+b}","'ADD':lambda:a+b,'SQRT':lambda:math.sqrt(max(0,a))}")
 if name=='analyze_evidence.py':s=s.replace("('interior groove',550)","('interior crown sample',550)").replace('Interior authored top stone grooves around x+.225 create the transverse feature near y550 in the supplied detail crop.','The middle sample is an interior crown sample, not a claimed port crossing.').replace('The transverse band near550 is native interior stone relief, not the true port at473.344. True collar center top samples are clean; no cap/top stripe inferred from mislabeled location.','Actual true port samples are separated from the interior crown sample. Do not infer a port failure solely from an interior facet boundary.')
 (D/name).write_text(s)
# Verify reused instructions are byte-identical to actually read prior versions.
repo=obj.parents[5];pairs=[(repo/'AGENTS.md',old/'resources/instructions/AGENTS-root.md'),(repo/'prototypes/sushi-loop/AGENTS.md',old/'resources/instructions/AGENTS-game.md'),(Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),old/'resources/instructions/refine-3d-model-SKILL.md'),(obj/'prompts/judge.txt',old/'resources/judge.txt')]
records=[]
for p,q in pairs:
 assert p.read_bytes()==q.read_bytes();records.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'sameAsPreviouslyRead':str(q)})
(B/'evidence/reused-instruction-equivalence.json').write_text(json.dumps(records,indent=2)+'\n')
