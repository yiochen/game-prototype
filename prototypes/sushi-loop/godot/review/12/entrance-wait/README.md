# Issue 12 — entrance wait and trapped-guest feedback

The [behavior contract](contract.md) targets signed Android **0.4.7 / code 47**. New arrivals with no free/reachable usable seat wait at the entrance for four simulation seconds with puzzled feedback, retry when seating becomes available and leave if it does not. They never wander. Guests already trapped inside keep wandering indefinitely with scared feedback until their route is repaired.

Implementation and verification are in progress. The approved 2D puzzled and panic artwork is reused. Planned actual Android coverage upgrades normal 0.4.6 without altering legacy state, runs the existing touch and route regressions, captures scared wandering and puzzled entrance waiting, pauses/reopens both feedback clocks, observes the unavailable-seat departure and verifies that the same waiting arrival can claim a newly available usable seat. The fixture uses real UI input on a separate read-only AVD clone with no app-state injection.

The [0.4.6 wandering proof](../guest-wandering/README.md) remains unchanged history. Package names, save identity, signer and v8 editor composition remain unchanged. This remains issue #12 / PR #36; the full #14 rescue ticket is not included.
