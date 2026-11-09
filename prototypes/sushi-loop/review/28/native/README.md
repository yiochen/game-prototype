# #28 Workshop · native evidence

The user approved the composition from `design/workshop-preview/` on 2026-11-08. These captures come from the native Godot build (macOS, Metal, Forward Mobile): `phone/` at a 780×1688 viewport and `wide/` at a 1440×1000 window with portrait containment (the same flow). They were made with `tests/capture_workshop.gd` and `tests/capture_edit_tabs.gd`:

```
python3 godot/tools/test_native.py --script tests/capture_workshop.gd --visible --resolution 780x1688 --output review/28/native/phone
```

| File | Shows |
| --- | --- |
| `01-restaurant-dock` | Live restaurant: the ImageGen ship and the hut, both with the #61 cyan interactable outline |
| `02-iris-closing` | The shared scene transition closing on the hut (navy with a cream rim) |
| `03-loading` | The loading beat: the salvage chunk over rising bubbles |
| `04-workshop-equipment` | The full-screen Workshop room: sign title, doorway tag, salvage pill, cradle and ship, Equipment tab (dot on Power-ups) |
| `05-hull-lv3-new-look` | Two Hull upgrades: Lv 3 swaps to the reinforced hull, with NEW |
| `06-harpoon-test-fire` | A Harpoon upgrade test-fires the Lv 2 harpoon from the nose hatch |
| `07-workshop-powerups` | Power-ups tab: neon glyphs, what each does, "▲" direction, no units |
| `08-not-enough-salvage` | Every Upgrade disabled, no shortage message |
| `09-back-on-dock` | Leaving through the doorway: the dock ship shows the new hull |
| `10-dive-prep` | Dive preparation with the Workshop gear |
| `11-dive-launch-shield` | Shield at start: a violet (Shield Lv 3) bubble at launch |
| `12-dive-portal-signal` | The portal entrance with the lime "good, interactable" signal and a violet passage whirlpool |
| `13-dive-shield-pickup` | The shield pickup's lime signal. The red flash is the capture teleporting the ship into rock, not gameplay |
| `edit-layout`, `edit-people`, `edit-floor` | The Edit inventory dock on the shared tab control |

Results on 2026-11-08: the full native suite had 50 of 55 scripts passing. The 5 that failed expected the old placeholder Workshop sheet, the instant prep screen or a sprite-only ship hit record; after updating them for the approved behaviour, all 5 pass. `tests/workshop_native_tests.gd`: 32 checks, 0 failures.

Rules: `tests/workshop_tests.gd` (56 checks: one-level payment, token replay across save and reopen, caps, gear frozen at departure, and equivalent runs for reeling, attraction, hull, shield and passage). Presentation: `tests/workshop_native_tests.gd`.
