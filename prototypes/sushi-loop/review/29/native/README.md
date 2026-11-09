# #29 time away: native evidence

Captures from `godot/tests/capture_away.gd` (phone 390×844 and a wider 1180×820
window with portrait containment) and the review video from
`godot/tests/record_away.gd`.

| Capture | State |
| --- | --- |
| `01-return-short-cue-dot` | "+420 while away" under the balance; red new-stock dot on Edit |
| `02-long-cue` | a seven-digit credit fits the reserved line |
| `03-zero-suppressed` | zero income: no cue, nothing moves |
| `04-reduced-motion-cue` | reduced motion: the cue appears without fade or rise |
| `05-edit-shop-dot` | Edit dock: red dot on the walnut Shop action |
| `06-shop-entered-dot-cleared` | entering Shop clears the dot |

Catalog sections checked: 3 (HUD balance), 5 (Shop), 14 (badges). The cue reuses
the approved cash icon, body font and odometer; the new-stock marker is the
shared red dot (`new_dot.gd`) also used by the Workshop tabs.

The video's long absences (a 20-minute dive, a 2-hour close) are produced by
moving the saved time-away history earlier, a test-only clock skip that the
captions announce. Its checks: the restaurant does not tick during the dive or
results, the return credits the estimate once and restores the exact restaurant
left at Start, Edit/Shop show the red dot until Shop is entered, and a reopen restores
the saved restaurant and credits the absence once.
