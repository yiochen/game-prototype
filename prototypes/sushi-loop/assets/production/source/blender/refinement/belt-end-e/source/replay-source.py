"""Replay native build/capture from only executable recipes and untouched .blend inputs."""
import pathlib,tempfile,shutil,subprocess,hashlib,json,sys,os
from PIL import Image
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-01'
blender=sys.argv[1] if len(sys.argv)>1 else shutil.which('blender') or '/Applications/Blender.app/Contents/MacOS/Blender'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='corner-source-only-') as tmp:
 root=pathlib.Path(tmp)/'portable-object';(root/'source').mkdir(parents=True)
 for name in ['build-round01.py','capture-round01.py']:shutil.copy2(P/'source'/name,root/'source'/name)
 shutil.copytree(P/'source/resources',root/'source/resources')
 inputs={p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
 for name in ['build-round01.py','capture-round01.py']:
  result=subprocess.run([blender,'-b','-t','4','--python',str(root/'source'/name)],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  (O/f'replay-{name}.log').write_text(result.stdout)
  if result.returncode or 'Traceback' in result.stdout:raise RuntimeError(name+' replay failed')
 rows=[]
 for kind in ['frames','closure','family-frames','connected','unbroken']:
  for p in sorted((O/kind).glob('*.png')):
   rel=p.relative_to(O);q=root/'candidates/round-01'/rel;a=Image.open(p).convert('RGBA');b=Image.open(q).convert('RGBA');rows.append({'path':rel.as_posix(),'expectedSHA256':sha(p),'replaySHA256':sha(q),'fileBytesEqual':sha(p)==sha(q),'expectedRGBAsha256':hashlib.sha256(a.tobytes()).hexdigest(),'replayRGBAsha256':hashlib.sha256(b.tobytes()).hexdigest(),'equal':a.size==b.size and a.tobytes()==b.tobytes(),'metadataDifferences':{k:[Image.open(p).info.get(k),Image.open(q).info.get(k)] for k in set(Image.open(p).info)|set(Image.open(q).info) if Image.open(p).info.get(k)!=Image.open(q).info.get(k)}})
 report={'schemaVersion':1,'method':'Fresh unrelated temporary directory receives only executable build/capture recipes and original/family native .blend resources, no candidate project or rendered images. Blender reconstructs and captures all native samples there.','freshDirectory':str(root),'blender':blender,'portableInputHashes':inputs,'nativePNGsCompared':len(rows),'allExact':all(x['equal'] for x in rows),'equalityDefinition':'Decoded registered RGBA pixels exactly equal. Blender PNG provenance text contains the fresh directory File path and is recorded separately from pixel hashes.','mismatches':[x for x in rows if not x['equal']],'rows':rows}
 (O/'portable-replay.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:report[k] for k in ['nativePNGsCompared','allExact','mismatches']},indent=2))
