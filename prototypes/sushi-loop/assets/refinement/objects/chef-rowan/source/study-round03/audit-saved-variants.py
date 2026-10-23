"""Compare saved diagnostic variants with exact01, reusing the sealed semantic serializer."""
import bpy,json,hashlib,ast,importlib.util
from pathlib import Path
HERE=Path(__file__).parent;OBJ=HERE.parents[1]
rig=json.loads((OBJ/'inputs/source-rig.json').read_text())
spec=importlib.util.spec_from_file_location('native',OBJ/'source/resources/original-native-actions.py');native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
serializer=OBJ/'source/audit-round02-depth-only.py';tree=ast.parse(serializer.read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['flat','custom','drivers','node_tree','semantic']]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(serializer),'exec'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def h(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def snapshot(p):
 bpy.ops.wm.open_mainfile(filepath=str(p));return json.loads(json.dumps(semantic(),default=lambda v:list(v)))
base=OBJ/'inputs/baseline-round01.blend';baseline=snapshot(base);records=[]
for d in [.5,.525,.55,.575]:
 p=HERE/f'variants/d{round(d*1000):03}.blend';current=snapshot(p)
 sections={k:dict(baselineSHA256=h(baseline[k]),variantSHA256=h(current[k]),equal=baseline[k]==current[k]) for k in baseline}
 assert all(v['equal'] for v in sections.values())
 records.append(dict(depth=d,path=str(p.relative_to(OBJ)),sha256=sha(p),allPermittedSemanticSectionsEqual=True,sections=sections))
report=dict(activeBrief='brief-v3-food-depth.json',baseline='inputs/baseline-round01.blend',baselineSHA256=sha(base),serializer='source/audit-round02-depth-only.py',serializerSHA256=sha(serializer),allowedMaskedFields=['existing plane.location (world ray audited separately all192)','existing plane.location X/Y driver common scalar','existing plane camera_ray_depth_bias_world_cells property'],allPassed=True,records=records)
(HERE/'saved-variant-semantic-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('ALL4_SAVED_VARIANTS_SEMANTIC_EQUAL',flush=True)
