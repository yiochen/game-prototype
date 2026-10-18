# Forward walk verification — issue 33

The reported moonwalk came from the native gait. The grounded foot moved toward the character’s front instead of backward relative to the advancing body. Native walk/panic foot travel was corrected before rebaking and recapturing the four customers. The catalog frame order, facing mapping and frontend remain unchanged.

## Final focused results

- **32 walk/panic facing cases pass:** four customers × two clips × four directions. Every one of the 384 frame rectangles matches its published atlas registration.
- All **32 fetched atlas byte hashes** match the current native exports. All 16 walk atlases differ from the historical baseline. Image decoding succeeds throughout.
- Live playback advances `0…11 → 0` for every customer. Native 12-frame clips at 12 fps, fixed roots, capture size and all existing clip cadence are preserved.
- All **113 noncustomer records** retain the exact capture fingerprints, clips and interaction fixtures from commit `8104b82`; this includes the connected conveyor revision.
- At 390px phone width, all four pages stay contained with **zero nested vertical scrollers**. No page exceptions or HTTP/image failures. Focused browser pass: **8.545 seconds**.
- A narrow Rosa recapture guard also passes: stand, seated-wait and eat, four facings at frames0/3/6/9 (48 sampled poses), with no image or runtime errors (2.503 seconds). Sampled front/side comparisons match the earlier appearance; stool support and held-food placement show no visible regression. The ordinary seated-wait context is captured unchanged. The eat-on-stool image is explicitly a verification-only transient DOM substitution, not a production catalog change.
- The independent [native after report](../../../assets/production/source/evaluations/character-gait/native-character-gait-after.json) passes 32 cases / 416 samples with zero errors. It uses actual evaluated baked transforms and deformed sole contacts rather than repeating the authoring phase formula.

## Visual evidence and historical failure

`before-after-stance.png` preserves the original failure on its **Before** row. The **Corrected** row shows the planted boot staying in the same place on the ground as the body advances. `four-customer-stance.png` shows that contact sequence for all four corrected customers. The [native before report](../../../assets/production/source/evaluations/character-gait/native-character-gait-before.json) is historical failure evidence: it reports 192 moonwalk/contact errors and must not be read as the current result.

`customer-rosa-walk-translating.gif` is a verification-only preview: two forward cycles, then a reset. It composites complete registered frames uniformly without alpha fitting, mirroring or reversing frames. Forward translation is .56 world units per gait cycle, using the actual camera calibration; the 35° character camera projects depth differently from screen X. The production catalog retains its in-place sprite review.

`browser-report.json` contains exact frame coverage, observed playback order and scope guards. `before-frontend-inspection.json` records the historical ascending frame order, source revision and atlas hashes. The four phone walk images and representative panic image show the actual catalog layouts.

The `rosa-*-before-after.png` sheets preserve sampled stand/seated/eat appearance comparisons. `rosa-seated-wait-actual-stool-context.png` is the ordinary catalog context; `rosa-eat-transient-stool-diagnostic.png` is the labeled temporary composition used only for contact review. `rosa-other-states-report.json` records this narrow check.

## Reproduce

With the current production preview running at port 4189 and commit `8104b82` available locally, run `node prototypes/sushi-loop/review/33/forward-walk/customer-walk-qa.mjs`. Output stays in `/private/tmp/sushi-object-review/walk-gait/final/`.

Use the bundled workspace Python/Pillow runtime to run `translating-diagnostic.py --output /private/tmp/sushi-walk-diagnostic`. It reads the saved manifest, camera calibration and native sprites; it does not modify production files. Final scene-asset approval remains pending.
