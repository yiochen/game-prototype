# Projection comparison browser review

Final focused run:5tests passed in11.6seconds. Tested320px/390px phones,844px landscape and1440px desktop. Native source/PNG calibration is independently audited in the parent review folder.

Browser checks cover all four ratio columns on representative stool, chef and connected-group rows; exact native frame/root/grid registration and pixel dimensions; one shared48/64/96px world tile pitch; ratio labels; separate current35° character-camera reference; offscreen image mounting/unmounting; horizontal panning; document-only vertical touch scrolling; and page overflow. No pending captures or browser errors were found.

The actual projected sources remain unmodified. Native gridOrigin is stored in logical capture pixels; the UI converts it through root to world cells. Solo square floor bounds are[-.5,-.5,1,1], assembly bounds[-2.5,-1,5,4].

Selected views:

- desktop-stool-row.png and chef-lena-1440-row.png show all four standalone ratios at48px/tile.
- assembly-1440-visible-strip.png shows the horizontally panned group comparison in the actual desktop viewport; neighboring columns beyond the viewport remain available by panning.
- context-l-belt-390-70.png shows the entire70% group on a390px phone after the assembly-name label was allowed to scroll away.
- chef-lena-390-70.png shows the phone character comparison.

The wide assembly TR screenshot from an earlier attempt is deliberately excluded: Playwright resized its capture viewport and recorded the adjacent reference section instead. It was a screenshot artifact, not valid visual evidence.

Initial test setup sampled changed SVG attributes before the next painted size. diagnostic.json preserves48px→64px evidence: width attribute96 while layout still72, then painted width96. The final test polls the painted dimensions. The first corrected run passed5/5 in17.2seconds; after a scoped assembly sticky-label usability fix, the final run passed5/5 in11.6seconds. No native geometry, production sprites or lighting changed.

The temporary spec/config are retained exactly as run, including this workspace's absolute dependency and fixture paths. Serve the built worktree on127.0.0.1:4185, then run the Playwright CLI with the retained config. results.json records the final bounded run; summary files record the representative viewport checks.
