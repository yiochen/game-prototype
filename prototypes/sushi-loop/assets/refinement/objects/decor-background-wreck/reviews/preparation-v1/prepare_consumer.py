from pathlib import Path
import json,shutil
root=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');p=root/'prototypes/sushi-loop/assets/refinement/objects/decor-background-wreck/reviews/preparation-v1';r=p/'resources'
library=json.loads((root/'prototypes/sushi-loop/assets/production/library.json').read_text());fixture=[]
for ident,clipId,directions in [('decor-background-wreck','static',['N','E','S','W']),('submarine-yellow','travel',['N']),('creature-eel','swim',['N']),('floor-underwater','scroll',['S'])]:
    original=next(o for o in library['objects'] if o['id']==ident)
    keys=['id','name','family','kind','layer','blocking','frameSize','root','sourceScale','footprint','height','directionFootprints','directionRootCells','rootCell','occupiedCells','supportCells','overheadCells','registration','requirements','interactions','sockets','portProfiles']
    o={k:original[k] for k in keys if k in original};clip=next(c for c in original['clips'] if c['id']==clipId);o['clips']=[clip];fixture.append(o)
    for facing,v in clip['directions'].items():
        if facing not in directions:continue
        src=root/'prototypes/sushi-loop/assets/production'/v['image'];dst=r/'consumer'/v['image'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
(r/'consumer/fixture.json').write_text(json.dumps({'objects':fixture,'source':'exact current production metadata bounded to required context clips; companion roles only, no other object review consulted'},indent=2)+'\n')
