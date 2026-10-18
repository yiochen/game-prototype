from pathlib import Path
import subprocess,json,time
ROOT=Path('/private/tmp/sushi33-production')
REPO=Path('/Users/yiouchen/.codex/worktrees/sushi-loop-33-art-catalog/game-prototype')
PYTHON='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
RAW=ROOT/'export/raw-clusters-v1'
ids=['restaurant-border-garden-a', 'restaurant-border-garden-b', 'restaurant-corner-garden-a', 'restaurant-corner-garden-b', 'underwater-reef-garden-a', 'underwater-reef-garden-b', 'underwater-coral-garden-a', 'underwater-coral-garden-b', 'entry-finished']
done=[]
def ready(aid):
 meta=json.loads((ROOT/'export/source'/aid/'asset.json').read_text())
 for clip,config in meta['clips'].items():
  for direction in ['N','E','S','W']:
   folder=RAW/aid/(clip+'-'+direction)
   for index in range(config['frames']):
    p=folder/(f'{index:03d}.png')
    receipt=p.with_suffix('.capture.json')
    if not p.is_file() or not receipt.is_file():return False
    try:
     if json.loads(receipt.read_text()).get('state')!='complete':return False
    except (ValueError,OSError):return False
 return True
while len(done)<len(ids):
 for aid in ids:
  if aid in done or not ready(aid):continue
  print('Publishing complete asset',aid,flush=True)
  result=subprocess.run([PYTHON,str(ROOT/'publish_captures.py'),'--repo',str(REPO),'--native',str(ROOT/'export'),'--ids',aid,'--raw-root',str(RAW)],check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  print(result.stdout.strip(),flush=True);done.append(aid)
  p=ROOT/'clusters-publication-status.json';q=p.with_suffix('.tmp');q.write_text(json.dumps({'published':done,'remaining':[x for x in ids if x not in done]},indent=2)+'\n');q.replace(p)
 if len(done)<len(ids):time.sleep(3)
print('All9 complete cluster and entrance sets published',flush=True)
