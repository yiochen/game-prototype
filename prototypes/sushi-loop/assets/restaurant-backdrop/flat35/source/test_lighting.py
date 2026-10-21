"""Build an isolated temporary Godot proof, capture it, then remove the project."""
from pathlib import Path
import subprocess, tempfile, shutil, sys, json
ROOT=Path(__file__).resolve().parents[1]
output=ROOT/'lighting-proof';output.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sushi-wall-light-proof-') as folder:
    project=Path(folder)
    (project/'project.godot').write_text('''config_version=5
[application]
config/name="Isolated wall lighting proof"
[display]
window/size/viewport_width=1120
window/size/viewport_height=480
window/size/window_width_override=1120
window/size/window_height_override=480
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
environment/defaults/default_clear_color=Color(0.1,0.1,0.1,1)
''')
    for source,name in [(ROOT/'renders/assembled.png','assembled.png'),(ROOT/'camera.json','camera.json'),(Path(__file__).with_name('lighting_probe.gd'),'lighting_probe.gd')]:
        shutil.copyfile(source,project/name)
    env=__import__('os').environ.copy();env['BACKDROP_PROOF_OUTPUT']=str(output.resolve())
    for args in [['--headless','--editor','--import'],['--windowed','--audio-driver','Dummy','--resolution','1120x480','--script','res://lighting_probe.gd']]:
        result=subprocess.run(['godot','--path',str(project),*args],env=env,capture_output=True,text=True,timeout=60)
        print(result.stdout);print(result.stderr)
        if result.returncode or 'ERROR:' in result.stdout+result.stderr:raise SystemExit(result.returncode or 1)
print(json.dumps(json.loads((output/'lighting-check.json').read_text())['checks']))
