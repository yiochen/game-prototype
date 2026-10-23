Creature-fish factual rig supplement v1 — preparation only, no approval

This separately versioned supplement leaves sealed reviews/preparation-v1 byte-for-byte unchanged. ROOT requested actual pose modes/channel compatibility and within-loop bone-relative response. ROOT also explicitly authorized a temporary UNSAVED source-only compatibility diagnostic if a real mismatch emerged, with original geometry/actions/timing/materials and no art tuning.

Observed actual source:
- Armature object rotation_mode=XYZ; all five pose bones rotation_mode=QUATERNION.
- Every one of the eleven actions has51 FCurves: object location and rotation_euler, plus each of5bones location/rotation_euler/scale. No bone quaternion FCurve exists. Bone Euler channels have nonconstant authored phase values; location/scale remain neutral.
- Actual evaluated armature-local bone matrices do not vary within ANY clip (max difference0). Relative evaluated mesh vertices after removing armature.world motion vary only by <=2.52881e-7 world units, floating-point transform residual. Existing visible animation is armature OBJECT bob/rotation, not relative body/spine deformation.
- The original source pipeline/bone modifiers and closure13=1 alone did not prove active spine response. Any wording in sealed preparation-v1 such as "deforming actor" or visible "bend" must be interpreted/corrected using this supplement: rig/deformation capability exists structurally, but body deformation is not active under saved source modes. Original allframe bounds and native replay pixel equality remain valid for the actual source.

Authorized compatibility-only comparison:
- In one isolated process, after recording actual source, changed only the five in-memory pose bone rotation_mode values to XYZ. No save, no geometry/material/key/action/timing/camera/art changes, no candidate.
- Replayed all528 unique frame/facing combinations plus32 loop closing keys and12 one-shot extrapolated boundary samples per branch. Relative mesh coordinates are evaluated world vertices transformed by armature.matrix_world.inverted(), removing object movement from the deformation measurement.
- With existing Euler curves interpreted by XYZ modes, all clips show nonzero evaluated bone/relative mesh variation. Max bone matrix entry difference from frame1=1.29590774; max relative mesh-vertex displacement=1.32959265 in caught. These are factual changes from original keyed values, not a quality judgment or suggested art amplitude.
- Original actual all-motion evaluated bounds: XY +/-0.89807338, Z0.08126275..1.09259975.
- Temporary Euler-compatible all-motion evaluated bounds: XY +/-0.94412685, Z0.03934786..1.10754896. This is additional source-interpretation evidence for ROOT's envelope reconciliation, not a newly imposed design budget or approved pose envelope.
- Both branches: every loop frame13 vs1 has zero evaluated bone/relative-vertex/object-matrix residual; every one-shot extrapolated native frame24 vs12 has zero residual. Runtime atlas behavior still uses12frames/12fps with one-shots clamped toindex11.

Files:
- raw-modes-channels.json: actual modes, exact channels, phase samples, source/geometry hashes and method.
- actual-authored-modes.json: actual original source measurements for all phases/facings.
- temporary-euler-interpretation.json: compatibility-only unsaved measurements.
- summary.json: compact perclip/facing response and boundary metrics.
- inspect_rig.py + inspect-rig.log + commands.txt: exact executed script/environment/command.
- hashmanifest.json + supplement-seal.json: immutable byte binding with explicit dependencies into the unchanged first preparation packet.

Source blendSHA b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6 before and after; no saved candidate/model/source/production writes. No rendering or aesthetic review of the temporary interpretation is claimed. ROOT will bind BOTH packets and decide/freeze the technical contract before a fresh editor.
