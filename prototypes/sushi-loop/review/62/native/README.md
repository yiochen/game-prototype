# #62 native evidence: tea requests and the one-pour minigame

Approved composition: `design/tea-pour-preview/` (2026-11-08). Captured from the
Godot game with real touch input on the tilt arc:

    python3 godot/tools/test_native.py --script tests/capture_tea.gd --visible --resolution 390x844 --output review/62/native/phone

- `01-tea-request-and-happy` — the tea-green request bubble on one guest, a happy bubble on another (never both on one guest).
- `02-pour-sheet` — tapping dismisses the bubble and opens the sheet; the restaurant keeps running above it.
- `03-pouring` — a touch drag down the arc tilts the ImageGen teapot; the acceptance zone is on the cup.
- `04-result` — letting go ends the one pour; drops land, then it is graded.
- `05-sip` — the sheet closes and the guest resumes.
- `06-overflow-pouring`, `07-overflow-result`, `08-surprised` — holding full tilt over a tea bowl spills; the guest is surprised.

Rules and session behaviour are covered headless by `godot/tests/tea_tests.gd`.
