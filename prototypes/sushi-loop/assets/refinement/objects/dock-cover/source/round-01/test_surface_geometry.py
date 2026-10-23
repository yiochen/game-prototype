"""Regression for real defect: tolerance-inflated clipping of nearly vertical triangles."""
import sys,importlib.util,json
from pathlib import Path
from mathutils import Vector
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;O=H.parents[1];s=importlib.util.spec_from_file_location('cover_geometry_test',H/'native_geometry.py');g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
def row(n,v,t):return{'name':n,'vertices':[Vector(p)for p in v],'triangles':t}
lower=g.surface([row('cloth',[(0,0,2),(0,1,2),(1,0,2)],[(0,1,2)])],False)
upper=g.surface([row('near_vertical_hut_bevel',[(0,0,1),(1e-8,1,1.8),(0,1,1)],[(0,1,2)])],True)
r=g.finite_gap(lower,upper);assert abs(r['minimumGapWorld']-.2)<1e-7,r;assert abs(r['maximumGapWorld']-1)<1e-7,r
contact=g.finite_gap(g.surface([row('sole',[(0,0,.22),(0,1,.22),(1,0,.22)],[(0,1,2)])],False),g.surface([row('deck',[(0,0,.22),(1,0,.22),(0,1,.22)],[(0,1,2)])],True),True);assert abs(contact['contactArea']-.5)<1e-9,contact
out={'nearVerticalFiniteTriangle':r,'analyticFlatContact':contact,'assertionsPassed':4};(O/'candidates/round-01/geometry-helper-regression.json').write_text(json.dumps(out,indent=2)+'\n');print('PASSED FINITE SURFACE REGRESSION')
