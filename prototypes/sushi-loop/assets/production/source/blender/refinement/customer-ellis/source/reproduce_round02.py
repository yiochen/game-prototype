"""Portable path adapter around the unchanged, actually executed native recipe.

Open resources/original-main.blend (or original-runtime.blend), run this file,
and pass -- main (or -- runtime). Writes only new reproduction outputs; the
reviewed .blend and its rendered bytes are never overwritten.
"""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
recipe=HERE/'build_round02.py'
text=recipe.read_text()
replacements={
 "OBJ/'brief.json'":"HERE/'resources/frozen-brief.json'",
 "OBJ/'reviews/proposed-food-mappings.json'":"HERE/'resources/frozen-food-mappings.json'",
 "heightPath=HERE/'resources/hair-height-envelope.json'":"heightPath=HERE/('reproductions/hair-height-envelope.json' if MODE=='main' else 'resources/hair-height-envelope.json')",
 "path=HERE/('round-02.blend' if MODE=='main' else 'round-02-runtime.blend')":"path=HERE/'reproductions'/('round-02.blend' if MODE=='main' else 'round-02-runtime.blend')",
 "OBJ/'candidates/round-02/study'":"OBJ/'candidates/reproduction-round02/study'",
}
for before,after in replacements.items():
 if before not in text:raise RuntimeError('Executed recipe path adapter no longer matches: '+before)
 text=text.replace(before,after)
(HERE/'reproductions').mkdir(exist_ok=True)
exec(compile(text,str(recipe),'exec'))
