"""Portable native hair/temple recipe. Background Blender --python this.py -- main|runtime.
Loads the hash-bound immutable round-02 native source, writes reproductions only.
"""
import bpy,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['main']
mode=args[0]
bpy.ops.wm.open_mainfile(filepath=str(HERE/('round-02.blend' if mode=='main' else 'round-02-runtime.blend')))
sys.argv=[sys.argv[0],'--',mode,'reproduce']
recipe=HERE/'build_round03.py'
exec(compile(recipe.read_text(),str(recipe),'exec'))
