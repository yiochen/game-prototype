import runpy,json,math
from pathlib import Path
G=runpy.run_path(str(Path(__file__).with_name('physical_scene.py')));pose=G['pose'];geometry=G['geometry'];projected=G['projected'];solve=G['solve'];support=G['walking_support']();hc=G['hc'];records=[]
cases=[('ground',-2.25),*[(f'first-{i}',y)for i,y in enumerate([-2.03,-2,-1.98,-1.96,-1.94,-1.93,-1.92,-1.91])],*[(f'second-{i}',y)for i,y in enumerate([-1.86,-1.84,-1.82,-1.8,-1.78,-1.77,-1.76,-1.75,-1.74])],*[(f'terminal-{i}',y)for i,y in enumerate([-1.69,-1.67,-1.65,-1.63,-1.62,-1.61,-1.6,-1.59,-1.58,-1.56])]]
for cid,y in cases:
 pose(0,y,0);r=solve(projected(geometry(hc,True)),support);r.update(case=cid,xy=[0,y],clip='stand',sourceFrame=12,sourceScale=[1.25]*3);records.append(r);print('SUPPORT_STUDY',cid,y,r['solvedRootZ'],[(x['contactArea'],x['fractionOfFlatSole'])for x in r['perShoe']],flush=True)
out=G['O']/'study/stand12-support-scan.json';out.write_text(json.dumps({'sourceHashes':G['sourceHashes'],'method':'Actual full visible shoe triangle overlap vs actual upward native floor/tread/bevel/seam/nail surfaces; post/caps excluded as walking support. Rigid rootZ max(supportZ-shoeZ), plus grounddomainZ>=0. Exact source stand12 selected; finite areas/centroids/spans reported. Study only, not approved candidate.','cases':records},indent=2))
