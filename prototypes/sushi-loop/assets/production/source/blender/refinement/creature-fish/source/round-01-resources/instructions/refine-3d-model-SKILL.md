---
name: refine-3d-model
description: "Refine an existing 3D model in Blender toward a user-chosen style: reskin an exported snapshot with imagegen, then iterate native exports with independent editor and judge agents. Use for model, material, lighting and sprite-style refinement, including tiled assets; not for creating a model from scratch or delivering only an AI-painted sprite."
---

# Refine 3D Model

Turn a style-reskinned snapshot into an editable 3D result. Coordinate exactly two fresh-context subagents: an independent visual judge and a Blender editor. Both use the same fixed target, source constraints and explicit definition of good. The judge approves rendered outcomes; the editor chooses implementation.

For an explicit preparation-only or stage-limited request, perform only that scope and mark the remaining stages pending. Do not generate images, dispatch agents, edit a model or issue approval merely to complete the full workflow when those actions were excluded.

## Establish the source and capture contract

Locate the editable project, exported snapshot, desired style and output location from the request and project context. Ask only for missing information that affects the result. If style is absent, ask for it; do not silently choose warm cartoon. Continue source inspection and backups while awaiting the answer, but wait before style-dependent generation or editing.

Create a versioned experiment. Save an untouched byte-for-byte project backup and SHA-256 before editing; preserve external textures and linked resources, too. Work in a separate copy. An image alone is not an editable model: if the source is unavailable, prepare the reference and identify the missing project without claiming model refinement.

Record `brief.json` using [references/brief.md](references/brief.md). Discover constraints from the actual asset. For sprites, record camera, frame, pixel aspect, world scale, ground root, footprint, geometry envelope, required views and connector/animation requirements. For ordinary model presentation use its actual requested camera/views. Preserve rigs, UVs, attachments and locked parts where applicable.

Lighting symmetry, no cast shadow, four directions, transparency and particular pixel dimensions are conditional project requirements, not universal defaults. Resolve unknown hard constraints before editing; do not infer them from silhouette bounds alone.

## Generate and freeze the style target

Apply the available `imagegen` skill and built-in generation tool. Edit the **actual exported snapshot**: inspect local images first, pass the snapshot as the edit reference, and identify additional style images separately. Preserve the user's chosen style rather than adding a default palette or genre.

Adapt [references/target-prompt.txt](references/target-prompt.txt). Record the authorized modeling freedom in `brief.modelingPolicy`, distinguishing allowed design changes from locked technical constraints. For a reskin, preserve major forms and proportions. When the user grants design freedom, let ImageGen improve forms, proportions, construction and purposeful decoration; the editor can rebuild those improvements natively. Preserve the declared camera, registration, identity, functional contacts/clearances, rig behavior and modular connection contract. Do not preserve weak geometry or old part counts merely for fidelity. Ask for real transparency when required. Imagegen can drift internally even on an identical canvas: its result is an aesthetic target, never proof of registration or tile continuity.

Save the raw target in the experiment, exact submitted prompt, input roles/hashes and generation provenance. Inspect that it expresses the requested style and remains relevant to the asset. Correct a materially wrong target before model iterations. Reuse a suitable target the user already supplied or selected; do not regenerate or seek repeated approval.

Freeze the selected target. Never regenerate an easier reference to justify a candidate. User changes to style or constraints require a versioned target/brief and recalibrated criteria, retaining prior evidence. Final exports render from the editable scene, not paint-over, image warping or a camera-facing card of the target.

## Define judge and editor; agree on good

Copy [assets/judge-prompt.txt](assets/judge-prompt.txt) and [assets/editor-prompt.txt](assets/editor-prompt.txt) into the experiment. Save actual prompts used and provide paths through the brief. Spawn exactly these two subagents with fresh context (`fork_turns="none"` when available). Give both the request/style, brief, original snapshot, target and relevant raw assets. Withhold prior coordinator aesthetic conclusions. If independent subagents are unavailable, report that limitation instead of claiming an independent review.

- **Judge owns `reviews/`.** Independently inspect source/target, save `reviews/initial.json`, and propose visible success criteria in `reviews/criteria.json`: shape/volume, color, light/highlights, material/detail, intended-size readability and absence of defects. Do not read editor proposals first.
- **Editor owns `source/`, `candidates/` and final exports.** Independently inspect the source scene and target. It may inspect while criteria are prepared, then acknowledge the agreed outcomes and choose methods. It does not grade itself or alter reviews, target, brief or originals.

Reconcile proposed criteria with user intent, modeling freedom and hard constraints; freeze them in `brief.qualityCriteria` and share with both agents before candidate submission. Reward useful native design improvements when authorized; differing from the source alone is not a defect. Both should understand what a successful visible result looks like. Clarify technical feasibility collaboratively; never lower the bar to excuse a failed method. An editor may identify a constraint conflict without dictating the verdict. Scores are comparative evidence, not universal numeric approval thresholds.

## Iterate native Blender captures

Give the editor the judge's ranked desired outcomes, allowing its own implementation. Read [references/blender-techniques.md](references/blender-techniques.md) for relevant techniques and diagnostic lessons. Geometry, normals, shaders, materials, lighting and compositing are options; choose by visible effect and preserve the declared contract.

Each numbered round retains an editable `.blend`, exact recipe/settings, required native views/frames and technical validation. Keep one capture contract across views, without per-view fitting or recoloring. Include connected and independently assembled previews for tiles, or representative frames/playback for animated assets, when part of the delivery.

Create an immutable hash-bound handoff with the helper, or equivalent evidence for other formats:

In shell examples, `SKILL_DIR` is this skill's directory and `EXPERIMENT` is the created experiment folder.

```sh
python3 "$SKILL_DIR/scripts/candidate_packet.py" create \
  --brief "$EXPERIMENT/brief.json" \
  --project "$EXPERIMENT/source/round-01.blend" \
  --render front="$EXPERIMENT/candidates/round-01/front.png" \
  --validation "$EXPERIMENT/candidates/round-01/validation.json" \
  --output "$EXPERIMENT/candidates/round-01/packet.json"
```

Repeat `--render name=path` for every required native view/frame. Declare additional assembly/motion previews in the brief. Pack candidate resources into the edited project or bind external textures/libraries with repeated `--resource name=path`; preserve their paths/dependency closure. The helper checks PNG frames and supplied-file hashes; native validation must establish actual camera/root, topology, bounds, lighting and other constraints. A manifest cannot certify appearance or discover undeclared dependencies.

Send the judge the packet and actual images/previews, fixed target, brief, original and relevant previous candidates. Withhold editor self-ratings and persuasive rationale. Save its `revise`, `approve` or `needs_evidence` verdict in `reviews/round-NN.json`, bound to the packet SHA-256.

Relay at most three ranked blockers with desired visible outcomes to the editor. Revise into a new round; never overwrite reviewed files. Continue while meaningful progress is possible. On a sustained plateau try a materially different approach; if completion requires changing user intent or hard constraints, report the best saved result and specific tradeoff needing input. Never manufacture approval or retry cosmetic variations indefinitely.

## Finalize the exact approved bytes

Approval requires visible improvement toward the agreed style, no material defects/dead spots in required views and a passing capture/asset contract. Missing evidence is not a pass. A single-view target does not establish unseen reference views.

```sh
python3 "$SKILL_DIR/scripts/candidate_packet.py" verify \
  --packet "$EXPERIMENT/candidates/round-01/packet.json" \
  --review "$EXPERIMENT/reviews/round-01.json"
```

Copy the exact approved source/render bytes to final filenames and record hashes. Retain backups, target/prompt, frozen criteria, all round sources/reviews and capture metadata. No post-approval re-render or art tweak without another review. Inspect a deliverable comparison if requested, at consistent registration/scale; reuse an existing review surface rather than automatically building a website.

Report the model, renders, target, saved prompts, verdict and material remaining differences. Approval is asset- and candidate-specific. Honor already-authorized integration/deployment; judge approval itself does not expand permission to publish or replace unrelated assets.
