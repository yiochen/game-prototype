# Issue 16 — direct Recipes and deferred new-chef dots (0.8.2 / 69)

The user's latest amendments replace the separate chef profile screen with direct Recipes navigation. Every People photo, whether placed or stored, opens the shared native recipe picker. Unplaced staff retain recipe browsing, prices, eligibility and preparation-time information, but have no Prepare button or misleading Preparing status. The footer contracts to its informational content. Placed chefs retain the existing explicit Prepare behavior. The public command also rejects unplaced preparation atomically; inspection remains available.

The removed profile's nodes, signals, layout and placement action are deleted. Photo taps and keyboard activation route directly to the same recipe picker used by restaurant chefs. Direction-locked upward photo dragging remains the placement path and opens the idle recipe picker on a successful drop.

New-chef dots have no real-time expiry. While People is foreground and unobscured, photos at least 85% visible are collected as viewed. Opening Recipes also records that new chef as viewed, without clearing its dot. Closing People, switching inventory tabs, or leaving Edit acknowledges the collected IDs through the saved command boundary. Offscreen unseen chefs remain unread. Opening/closing Recipes, covered trays, and elapsed time do not clear dots. Visibility history survives temporary focus loss in the current tray visit, without treating background content as viewed.

`chef_recipe_flow_tests.gd` sends real viewport touch events and tests direct navigation, placed/unplaced controls, hidden-button activation, public-command rejection, a 1.6-second wait with the dot still visible, tab-switch acknowledgement, tray-close acknowledgement, offscreen preservation and save/restore. Phone and wide captures use Godot Mobile on Metal, with no profile substitute. Other navigation, hiring and native app tests are recorded in `verification.json`.

Normal release 0.8.2 / code 69 retains the original package/save identity/release signer. No texture-quality or architecture changes are included in this interaction update.

The signed 0.8.2 / 69 update was installed successfully on Pixel 10 Pro using `adb --no-incremental -r`, with package version readback and no data reset. The dedicated desktop demo was refreshed. Drive name, byte count and SHA-256 were independently verified; observed release metadata is in `drive-release.json`.
