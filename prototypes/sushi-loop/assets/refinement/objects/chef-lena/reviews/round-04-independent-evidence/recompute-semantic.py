from pathlib import Path
p=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-lena/source/semantic_audit_round03.py')
code=p.read_text().replace("(C/'semantic-parity.json').write_text","Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/chef-lena/reviews/round-04-independent-evidence/semantic-parity.json').write_text")
exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'independent_semantic_recompute'})
