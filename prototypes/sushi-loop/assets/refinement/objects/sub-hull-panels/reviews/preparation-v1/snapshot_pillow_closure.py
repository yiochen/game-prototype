import pathlib,runpy,sys,shutil,hashlib,json
out=pathlib.Path(__file__).resolve().parent
runpy.run_path(str(out/'make_sheets.py'),run_name='__main__')
import PIL
base=pathlib.Path(PIL.__file__).parent;records=[]
for name,m in sorted(sys.modules.items()):
 if not name.startswith('PIL') or not getattr(m,'__file__',None):continue
 p=pathlib.Path(m.__file__)
 if not p.is_file():continue
 dst=out/'resources/tools/python/PIL'/p.relative_to(base);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
 records.append({'module':name,'source':str(p),'snapshot':str(dst.relative_to(out)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size})
(out/'pillow-closure.json').write_text(json.dumps({'python':sys.version,'pillow':PIL.__version__,'scope':'Exact PIL modules loaded by actual make_sheets replay, including native extension. Python runtime is recorded as tool environment; standard library is external.','files':records},indent=2))
print('PIL_CLOSURE',len(records),sum(x['bytes'] for x in records))
