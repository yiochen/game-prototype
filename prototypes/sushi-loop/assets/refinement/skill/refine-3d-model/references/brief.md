# Brief and artifact contract

Keep a self-contained experiment with prompts, inputs, target, backups, sources, candidates and reviews. Paths in `brief.json` are relative to its directory unless absolute. The coordinator owns this JSON. Preserve original project/resources; its backup is byte-identical.

Minimum helper-compatible brief, illustrated with a single-view clay vase (values are examples, not defaults):

```json
{
  "asset": "ceramic-vase",
  "style": "Handmade clay miniature with a matte finish",
  "source": {
    "project": "../models/vase.blend",
    "backup": "backups/vase.blend",
    "snapshot": "inputs/original-front.png"
  },
  "target": {
    "image": "targets/target-v01.png",
    "provenance": "imagegen",
    "prompt": "targets/imagegen-prompt.txt"
  },
  "capture": {"frame": [512, 512], "views": ["front"]},
  "constraints": {
    "camera": "Use the measured source camera and framing",
    "lockedParts": ["opening diameter and base contact"]
  },
  "qualityCriteria": {
    "shapeVolume": "Rounded clay volume with recognizable source proportions",
    "color": "Selected reference's clay palette",
    "lightingHighlights": "Broad restrained matte-clay highlights",
    "materialDetail": "Subtle handmade variation visible at presentation size",
    "artifactFreeReadability": "No black patches, broken joins or clipping"
  }
}
```

Measure the actual camera matrices/lens/projection, pixel aspect, root, world units, bounds and delivery needs in `capture`, `constraints` and native validation. For registered sprites use explicit numeric values instead of the example camera prose. For supplied targets use `provenance: "user-provided"`; do not invent a generation prompt.

When modeling freedom matters, record `modelingPolicy` with `allowed`, `locked` and a judging interpretation. A user-authorized design exploration can change nonfunctional forms, proportions, construction and decoration. Camera/frame/root, function, clearance, rig behavior and shared modular connections remain locked as declared. The editor and judge share this policy; source part counts and weak shapes are not implicit constraints. Apply changed direction to follow-on work or a versioned target/brief, keeping already sealed rounds intact.

For multi-scene or asset-library projects, also identify `source.scene` and the asset object/collection. The scene active when the file opens may belong to another model. Measure and edit the named asset scene rather than assuming the active scene is the export source. Keep project-backup hashes distinct from any earlier production-library hash recorded in inherited measurements.

The judge independently proposes `reviews/criteria.json`; reconcile it with user intent and freeze `brief.qualityCriteria` before candidate submission. Packets bind the brief, source, backup, snapshot, target and saved prompt. Changes invalidate existing packet/review binding.

`capture.views` names every required native PNG view/frame. Supply one `--render name=path` for each, all with the declared frame. For motion these can be frame identifiers; keep playback/time metadata in validation. For tiles record module-specific registrations in native evidence rather than implying every module has the hero frame.

Optional `capture.previews` lists required preview names, such as `["independent-assembly", "animation-loop"]`. Supply each with `--preview name=path` when creating the packet. Additional previews are allowed. These may have different dimensions/formats and are hashed separately; the judge must list all submitted previews in `inspectedFiles` for approval. Rebuild them from the submitted round, not a previous round's gallery. Each round keeps its own files, so the brief and criteria stay fixed while preview paths differ.

Native `validation.json` must contain measured evidence relevant to the asset: source/target/recipe hashes, Blender version, source/current capture settings, evaluated bounds, relevant topology/normals/UV/rig checks, lighting, alpha/clipping and continuity/motion checks. State unknowns. Hash checks do not prove topology or visual quality.

Pack textures/linked resources into the candidate copy where suitable, or supply their actual files with repeated `--resource name=path`. The helper includes these in integrity checks without requiring the judge to visually inspect every texture/library separately. It cannot discover missing dependencies; the editor's native validation must inventory them and establish that the finalized project resolves its resources. Preserve the original resource versions separately when backing up.

Suggested layout:

```text
brief.json
prompts/{judge,editor}.txt
backups/original.blend
inputs/original.png
targets/{target-v01.png,imagegen-prompt.txt,provenance.json}
source/{round-01.blend,editor-round-01.py}
candidates/round-01/{front.png,validation.json,packet.json}
reviews/{initial.json,criteria.json,round-01.json}
final/{model.blend,front.png,selection.json}
```

The helper checks handoff integrity, not Blender appearance. `verify` checks hashes, frame/view coverage and, if supplied, the review's exact packet binding, approval, evidence coverage and empty blockers. It does not grant approval. Finalize the approved bytes and selection hashes separately.
