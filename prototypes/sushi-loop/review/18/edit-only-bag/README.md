# Issue 18 · Edit-only Shop and shopping bag revision

The user's review feedback supersedes the first-draft Live entry, left HUD shortcut, curled return and purchase receipts. Shop opens only from Edit's inventory tray. The tray is hidden while Shop is open, restores its scroll/focus on close, and remains paused. The same shared cream round X is now used by Shop, chef and applicant popups.

The floating shopping bag receives separate copies of purchased item art through independent 680ms flights, then pulses for 240ms. Reduced motion omits travel and fades the bag. Transactions commit before animation. There is no purchase-status copy. The scroll viewport ends above the bag, preserving access to every price at phone and landscape sizes.

Captures cover the full scene and shared gallery at 320×720, 390×844, 844×390 and 1440×1000: Shop, purchase flight and arrival, disabled, sold-out, selected placement, pressed Shared, Live with no Shop and Edit tray entry. Existing neighboring captures are copied into `neighbor-close-check/`; historical issue 17 evidence was restored after those regression tests.

Five model tests, 15 feature browser checks and 36 neighboring chef/applicant browser checks passed. Build passed with its existing chunk-size advisory. No Godot source or native saves changed. The prototype still awaits user approval before native integration.
