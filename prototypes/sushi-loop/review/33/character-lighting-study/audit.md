# Independent lighting-study audit

The final source is
`c39ea3ed6e2e487899c6fe23319135daa5cb0d20512cf85371ec1627f76184ba`.
This is an isolated comparison awaiting the user's choice; production art and
the locked art decisions are unchanged.

[Native inspection](native-audit.json) verifies the actual saved Blender data:

- All four variants share identical geometry, root and camera. The 58 frozen
  meshes exactly match evaluated production Noor, idle frame 4, with zero vertex
  displacement. Canvas is 192 × 320 logical pixels, root (96,248), ordinary35,
  square pixels and 4× capture resolution.
- Baseline output surfaces are emission. Candidate output surfaces are actual
  Principled BSDF, with emission strength 0, roughness .85 and specular .03.
  Their Base Color directly retains the original material × lower-height ramp;
  the former view-normal color multiplier is bypassed.
- Candidate top lamps are real overhead area disks at (0,0,4.5), using 100, 140
  and 180 W. Four identical 100 W disk fills sit at radius 3, height 1.8.
  The actual position, direction, power, size and color light set is invariant
  under 90°, 180° and 270° world-yaw rotations. World strength remains zero.
  This establishes cardinal rig symmetry; asymmetric character views need not
  have identical average brightness.
- Every color scene keeps its own 135% sRGB compositor and ungraded alpha path.
  The debug mask uses actual hat polygon normals: red for Z ≥ .65, blue for
  Z ≤ .35, and black elsewhere. Its compositor is disabled.

All [20 capture files](capture-integrity.json) have matching recorded hashes and
768 × 1280 dimensions: sixteen color stills and four mask images. All twelve
candidate/same-facing baseline alpha arrays are byte-identical.

The [pixel audit](pixel-audit.json) measures linear Rec.709 luminance after sRGB
decoding. It uses common opaque mask interiors, eroded by two source pixels, to
exclude antialiasing boundaries. The ranges below cover all four facings.

| Treatment | Top light | Mean top/side luminance ratio | Top green pixels clipped at 254+ |
| --- | --- | --- | --- |
| Current emission baseline | None | 1.065–1.116 | 0% |
| Soft overhead | 100 W | 1.706–1.903 | 0% |
| Faceted overhead | 140 W | 2.135–2.405 | 0% |
| Crisp overhead | 180 W | 2.562–2.911 | 0% |

These measurements show distinct upward/side surfaces without green-channel
clipping in the measured regions. They do not automatically select a treatment.

The recreated study baseline is geometrically identical to production, but its
RGBA bytes are not asserted identical to the old production capture: the study
uses 64 EEVEE samples and production used 32. Across opaque pixels, mean RGB
differences are only .016–.019 of one 8-bit channel unit; a small set of edge-alpha
pixels differs by at most 13 units. This is consistent with the sampling change.
Candidate comparisons all use the same study sampling and retain exact alpha.

Earlier overbright attempts remain in `attempts/01-overbright/` and
`attempts/02-clipped-green/`, including their source projects, recipes, manifests,
South captures and pixel measurements. Attempt 02 also has an independent native
audit tied to its archived source hash. Its brighter green clipping is not a
property of the final 100/140/180 W set.

The reusable read-only checks are [audit_saved_study.py](audit_saved_study.py) and
[measure_lighting_pair.py](measure_lighting_pair.py). They write reports and do
not save Blender projects or edit production sprites.
