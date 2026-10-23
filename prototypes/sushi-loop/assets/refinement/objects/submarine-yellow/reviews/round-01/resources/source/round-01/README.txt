Final canonical submarine candidate, round-01. Original judge review is pending.

project.blend is the selected editable native source. Blender5.2.2 LTS (d13f752e3b9c)
rendered it directly at640x768, square pixels, EEVEE64, filter.5, camera65degrees.
Logical frame320x384/root160,288; native root320,576. No4x reduction, fitting,
alpha/RGB patching, or environment camera transplant is involved.

Exact bodyv6 source and all3 signed canonical IDLE neutral component projects and
resources are in resources/. adopt.py imports these native collections without
rebuilding geometry/materials, removes only explicit PROVISIONAL objects and
mounts approved roots at the already frozen positive uniform native transforms.
Standalone ACTIVE actions are detached after realizing signedIDLE; none is mapped
to main clips. New native hide_render/hide_viewport actions implement existing
base/upgraded visibility semantics. Body actions/materials/camera/lights unchanged.

Replay with native_common.py apply(clip, sourceFrame, direction, rootLocation).
The frozen root.nativeActions JSON and archived legacy visibility actions remain
verbatim; deleted PROVISIONAL owners are explicitly skipped by this helper. New
canonicalVisibilityActions live on WarmSoft_submarine-yellow_stage1. The bound
rig.json resolves the full actual owner/action map. Use this provided helper/map,
not the archived root map alone, to reproduce upgraded captures.

Portable rebuild: python rebuild.py /absolute/NEW-destination. It copies only the
required exact native sources/signed resources and runs adopt.py in that NEW
directory; it refuses an existing destination. Rebuild container bytes can differ;
all persistent resource/action/camera fingerprints are proven exactly identical.
To export, run Blender background --python render_final.py -- N E S W from this
source folder; it reads project.blend and writes a NEW candidate output location
when used in a fresh copied object tree. Do not rerun into sealed evidence.
publish_frames.py performs lossless6x2 placement and APNG construction only.

Runtime sourceframes1..12 become atlas indices0..11. All12clips remain12fps.
Impact/upgraded-impact are one-shot and retain original nonneutral last-runtime
frame; diagnostic frame13 is neutral and is NOT inserted into the atlas. Other
ten clips close at13 outside the runtime atlas. APNG uses exact rational1/12s,
SOURCE fullcanvas replacement, infinite loops except impact plays once.

Native body/dock physical context retains main65degree camera. It measures fixed
root[-.70,-.42,.23] against actual accepted deck triangles including nails/bevels,
all4mainfacings/all4dockmodes/runtime/half/closure. Companions stay at fixed roots.
Consumer evidence independently uses own published55degree environment sprites
and65degree main sprite, current shared height projection89.6/support ordering,
ordinary wholecanvas filtering and rendererSHA570a0d0d. These different registered
projections do not imply pixelidentity or a single-camera sprite reconstruction.
Cover remains unapproved and is absent. No final family approval is claimed.

384fullChrome dock cases cover directions/modes/fractions/backgrounds/native and
logical display. Phone/landscape/repeated/human/equipment contexts are bound too.
The48-concurrent-animation stress page skipped frames under overload; retained
trace says so. Fresh individual actual consumer playbacks each saw every0..11
frame at12fps. All48 lossless APNG files have independently decoded exact rawRGBA.
Replay controls report tiny native render-order/session color noise honestly;
alpha is identical. Selected capture bytes remain authoritative, not repaired.

Review entrypoints are delivery-round-01.json, candidates/round-01/validation.json,
visual-coverage-inventory.json, handoff.json and editor-seal.json. The original
judge must visibly cover all576states,48playbacks, declared previews and native/
consumer/contact/motion evidence. No editor self-approval or production write.
