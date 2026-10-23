import sys
sys.dont_write_bytecode=True
from pathlib import Path
H=Path(__file__).resolve().parent;S=H/'resources/source/round-01';O=H/'native-checks';O.mkdir(exist_ok=True)
for n in ['prove_body_identity.py','audit_final.py','audit_visible_interfaces.py']:
 code=(S/n).read_text()
 # Retain exact audit logic/dependencies; redirect writes to fresh judge-owned outputs.
 if n=='prove_body_identity.py':code=code.replace("O=B/'candidates/round-01'","O=Path("+repr(str(O))+")")
 else:code=code.replace("F=runpy.run_path", "O=Path("+repr(str(O))+");F=runpy.run_path") if n=='audit_final.py' else code.replace("s,root,col=open_source()", "O=Path("+repr(str(O))+");s,root,col=open_source()")
 print('INDEPENDENT_REEXECUTION',n,flush=True)
 exec(compile(code,str(S/n),'exec'),{'__file__':str(S/n),'__name__':'__main__'})
