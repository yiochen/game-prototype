import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
S=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/dock-cover/source/round-02');R=S.parents[1]/'reviews/round-02-independent'
# Inspected packet-bound setup loads exact companion projects in this background process only; it has no saves or output writes.
setup=S/'context_setup.py';globals()['__file__']=str(setup);exec(compile(setup.read_text(),str(setup),'exec'),globals());OUT=R
r={'sourceSHA256':sha(H/'cover.blend'),'setupSHA256':sha(setup),'geometryModuleSHA256':sha(H/'native_geometry.py'),'fixtureSourceHashes':sourceHashes,'savedJoinedSource':False,'support':[],'limitingCases':[],'humanMinimumCase':{}}
subpose('upgraded-dock-ready');coverpose('covered',1,'S');deck=g.surface(g.geometry(fc),True)
for row in g.geometry(cover):
 if 'bearing_sole' not in row['name']:continue
 lower=g.surface([row],False);v=g.finite_gap(lower,deck,True);v.update(name=row['name'],soleArea=sum(g.area(t['xy'])for t in lower));v['fraction']=v['contactArea']/v['soleArea'];assert v['minimumGapWorld']>=-1e-5 and v['contactArea']>.006;r['support'].append(v)
for cl,f in [('uncover',8.5),('uncover',6.)]:
 for mode in ['dock-ready','dock-charging','upgraded-dock-ready','upgraded-dock-charging']:
  coverpose(cl,f,'S');subpose(mode);coverpose(cl,f,'S');cg=g.geometry(cover);lower=g.surface([v for v in cg if any(k in v['name']for k in ['attached_canvas','carrier','spindle','rounded_joint','cantilever','top_ferrule'])],False);cb,cn=g.bvh(cg);record={'clip':cl,'frame':f,'mode':mode,'companions':{}}
  for aid,c in [('hut',hc),('sub',subc)]:
   gg=g.geometry(c);v=g.finite_gap(lower,g.surface(gg,True));tb,tn=g.bvh(gg);pairs=cb.overlap(tb);v['triangleIntersections']=len(pairs);v['noXYSurfaceOverlap']=v['minimumGapWorld'] is None;assert not pairs and (v['minimumGapWorld'] is None or v['minimumGapWorld']>.02);record['companions'][aid]=v
  r['limitingCases'].append(record)
coverpose('uncover',2,'S');cg=g.geometry(cover);lower=g.surface([v for v in cg if any(k in v['name']for k in ['attached_canvas','carrier','spindle','rounded_joint','cantilever','top_ferrule'])],False);c=actorSnapshots['front-right-branch'];c.hide_render=False;gg=g.geometry(c);v=g.finite_gap(lower,g.surface(gg,True));cb,cn=g.bvh(cg);tb,tn=g.bvh(gg);v['triangleIntersections']=len(cb.overlap(tb));assert v['minimumGapWorld']>.02 and v['triangleIntersections']==0;r['humanMinimumCase']=v
r['scope']='Independent compact rerun of actual finite support and editor-evidence limiting cases for all four declared docked modes, plus minimum human pose. Full208 mode/phase and832 rigid covariance tables separately audited; no unnecessary Cartesian expansion or future-family approval.'
(R/'family-independent.json').write_text(json.dumps(r,indent=2)+'\n');print('INDEPENDENT FAMILY',len(r['support']),len(r['limitingCases']),v['minimumGapWorld'])
