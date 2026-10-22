Original independent judge, exact sealed round-03 rock-shelf-middle review.

The final verdict is ../round-03.json. manifest.json binds this supplemental
resource/evidence closure. seal.json binds the manifest, final verdict and the
unchanged strict acceptance log ../round-03-acceptance.log. The gate log sits
outside the supplemental directory to avoid a hash cycle: the validator prints
the final verdict hash, whose bytes already include the manifest hash. No signed
verdict or manifest is rewritten after the gate. Do not rerun helpers here after
sealing; use a new review directory or disposable copy.

Exact input closure:
  resources/source.blend: selected candidate, copied without reconstruction.
  resources/prior-source.blend: exact prior candidate for read-only comparison.
  resources/{packet,brief,criteria,root-native-contract}.json and comparison PNGs.
  resources/sealed-renders: exact submitted native singles and three-middle strips.
  resources/published: exact submitted published single frames.
  resources/editor-technical: disclosed technical records, without construction
  rationale or editor self-ratings. Initial visible observations were saved first.
  resources/consumer: actual current consumer functions, matching this packet's
  new source-resource snapshot. resources/consumer-frozen: older preparation
  helper for explicit output-equivalence control only. Neither is silently
  substituted for the other or described as hash-identical.

Independent operations (use absolute paths for <review>):
  /opt/homebrew/bin/blender --background <review>/resources/source.blend
      --python <review>/reopen_native.py
  /opt/homebrew/bin/blender --background <review>/resources/source.blend
      --python <review>/resource_signatures.py
  /opt/homebrew/bin/blender --background --python <review>/readonly_compare.py
  <pinned-python> <review>/prepare_consumer.py
  <pinned-node> <review>/capture_consumer.cjs
  <pinned-python> <review>/measure_seams.py
  <pinned-python> <review>/check_evidence.py

No editor construction recipe is run and no blend is saved. The initial read-only
comparison incorrectly assumed unchanged whole-core topology; a second broad
spatial selection also included changed shoulder topology. Failed helper versions
and logs are retained. The final comparison discovers actual shared face-prefix
correspondence and measures its bounds/position/albedo/corner normals, while
reporting changed body topology honestly. No candidate image is retried/repaired
to force equality. All native reopen residuals and broad area-light RGB residuals
remain in the evidence.

Actual consumer layout/paint functions use the frozen object registration and
exact selected published images. The common native canvas restores nearest after
resize, followed by ordinary final whole-canvas CSS filtering. Independent captures
cover all four directions on light/gray/dark at logical128/phone32, plus all four
directions at CSS phases0/.25/.5/.75 at both sizes. Every exact declared packet
render/preview was directly viewed. Counts/hashes do not replace that inspection.

Minimal executable Pillow/Playwright helper closure is copied. External Blender,
Python, Node and Chromium runtime identities are pinned; full runtime trees are
not duplicated. No file exceeds100MB. Final approval is limited to this exact
canonical middle source/static views and inspected repeated behavior; no family,
end/corner, full-game, device, production or promotion approval is inferred.
