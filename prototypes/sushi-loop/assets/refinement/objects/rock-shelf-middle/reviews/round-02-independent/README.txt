Original independent judge, sealed round-02 review of rock-shelf-middle.

The verdict is in ../round-02.json. The supplemental manifest binds the exact
candidate packet and every file in this directory except manifest.json and
seal.json. seal.json binds that manifest and the verdict. Do not rerun helpers
in this sealed directory: replay in a new review directory or disposable copy.
No candidate geometry, material, source, published media or old review was edited.

Input closure:
  resources/source.blend is the exact saved candidate, not a reconstruction.
  resources/{packet,brief,criteria,root-native-contract}.json bind the experiment.
  resources/original.png and target.png are frozen comparison references.
  resources/sealed-renders contains exact packet native single/strip inputs.
  resources/published contains exact packet 2x published single frames.
  resources/editor-technical contains disclosed technical evidence only; editor
  construction rationale and self-ratings were withheld from this art review.
  resources/consumer-frozen is the packet-frozen renderer. resources/consumer
  is the current shared renderer captured during review; they are not falsely
  described as hash-identical. See evidence/consumer-bindings.json and the
  independent eight-case frozen-current-consumer-control.json.

Independent operations, in order (use absolute paths for <review>):
  /opt/homebrew/bin/blender --background <review>/resources/source.blend
      --python <review>/reopen_native.py
  /opt/homebrew/bin/blender --background <review>/resources/source.blend
      --python <review>/resource_signatures.py
  <pinned-python> <review>/prepare_consumer.py
  <pinned-node> <review>/capture_consumer.cjs
  <pinned-python> <review>/measure_seams.py

The scripts open saved native geometry; no editor construction recipe is run
and no blend is saved. All render residuals are retained. BOX is applied to
complete native canvases without pixel repair. The browser uses the actual
consumer layout/paint functions with a minimal unused React-hook stub, then
ordinary final whole-canvas CSS filtering. Screenshots cover all four directions,
light/gray/dark, logical 128-cell and phone 32-cell; provided packet sheets also
cover phone fractional phases. Every declared packet media path was directly
viewed, not inferred from metrics or a hash-only alias.

The current shared raster helper was changed by root in separate work. Root
identified that change as c2c6062fa; that is coordination context, not an editor
alteration or a version change to the frozen consumer contract. The independent
control finds byte-identical canvas output for the eight actual integral-native
joined/independent cases. It makes no claim about other fractional native sprite
placements. Logical/CSS fractional display phase coverage remains explicit.

resources/node_modules and resources/python-library freeze the executable minimal
helper closure. Runtime binaries/versions are externally pinned in
resources/external-runtime-identities.json; no file exceeds 100 MB. Do not infer
family, end/corner, full-game, device, production or promotion approval.
