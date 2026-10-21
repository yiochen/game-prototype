"""Diagnostic alias for the closed actual original-animation measurement."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).resolve().parent/'measure-original.py'),run_name='__main__')
