from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
B=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/belt-straight-n');P=B/'candidates/round-11';O=B/'candidates/round-10'
p=json.loads((P/'packet.json').read_text());o=json.loads((O/'packet.json').read_text());d=json.loads((P/'delivery.json').read_text());brief=json.loads((B/'brief.json').read_text())
def digest(q): return hashlib.sha256(q.read_bytes()).hexdigest()
errors=[];bound={};entries=0
for g in ['files','candidateRenders','previews']:
 for n,r in p[g].items():
  q=(P/r['path']).resolve();h=digest(q);bound[str(q)]=h;entries+=1
  if h!=r['sha256']: errors.append([g,n,'hash'])
for n,r in enumerate(d['resources']):
 if isinstance(r,str): q=Path(r)
 else: q=Path(r['path'])
 if not q.is_absolute(): q=P/q
 if str(q.resolve()) not in bound:errors.append(['delivery.resources',n,str(q),'unbound'])
prior={n:r for n,r in p['previews'].items() if n in o['previews']}
for n,r in prior.items():
 if r!=o['previews'][n]: errors.append(['preview changed',n])
new={n:r for n,r in p['previews'].items() if n not in o['previews']}
for n,r in p['candidateRenders'].items():
 if r!=o['candidateRenders'][n]: errors.append(['hero changed',n])
if p['qualityCriteria']!=brief['qualityCriteria']:errors.append('frozen criteria mismatch')
# Make a review-owned contact sheet for every actual starter screenshot.
out=B/'reviews/round-11-evidence';out.mkdir(exist_ok=True)
files=[]
for orient in ['portrait','landscape']:
 fs=sorted((P/f'coordinator-game/starter-{orient}').glob('*.png'));files.extend([str(f.relative_to(P)) for f in fs]);sz=(195,422) if orient=='portrait' else (360,250)
 sheet=Image.new('RGB',(sz[0]*7,sz[1]+26),(235,233,222));draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(fs):
  im=Image.open(f).convert('RGB');im.thumbnail(sz,Image.Resampling.BICUBIC,reducing_gap=2.0);sheet.paste(im,(i*sz[0],26));draw.text((i*sz[0]+4,6),f.name[:29],fill=(20,40,40))
 sheet.save(out/f'all7-starter-{orient}.png')
r={'packetSHA256':digest(P/'packet.json'),'checkedHashEntries':entries,'hashFailures':errors,'deliveryResourcesExplicitlyBound':len(d['resources']),'sourceFramesExplicitlyBound':len(d['rawFrames']),'originalLayoutAtlasesExplicitlyBound':len(d['atlases']),'criteriaExactToFrozenBrief':p['qualityCriteria']==brief['qualityCriteria'],'inheritedPreviewEntriesExact':len(prior),'newPreviewEntries':len(new),'newPreviewPaths':[r['path'] for r in new.values()],'distinctDeclaredHeroPreviewPaths':len(set(r['path'] for g in ['candidateRenders','previews'] for r in p[g].values())),'starterCapturePaths':files}
(out/'independent-packet-checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
