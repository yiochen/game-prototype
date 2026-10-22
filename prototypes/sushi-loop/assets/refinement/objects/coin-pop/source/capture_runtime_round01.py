from pathlib import Path
import subprocess
O=Path(__file__).resolve().parent.parent;N=O/'source/runtime-godot';R=O/'candidates/round-01/runtime-frames';R.mkdir(parents=True,exist_ok=True)
subprocess.run(['godot','--headless','--path',str(N),'--editor','--import'],check=True)
subprocess.run(['godot','--path',str(N),'--','--output',str(R)],check=True)
