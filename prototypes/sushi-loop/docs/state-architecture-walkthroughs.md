# State architecture: feature walkthroughs

**Status: proposed (2026-11-06).** These walkthroughs test the [state architecture](state-architecture.md) against features planned for Sushi Loop, before any of it is built. For each feature they ask: which tables does it add, does it change an existing durable component, does it need a save migration, and what must the engine provide? None of these features is designed yet; the mechanics below are assumptions made only to test the state model.

## Summary

| Feature | New tables | Changed durable component | Migration | Engine features used |
| --- | --- | --- | --- | --- |
| 1. Boss types (trench digger, bomb thrower) | `creature`, `attack`, `projectile`, `terrain_edits` (run world) | — | none | worlds, machines, spawn/despawn in steps |
| 2. Expedition objects (chest, speed boost) | `route_object` (run world) | — | none | stable content ids, effects |
| 3. Belt intersection | — | `belt` | belt v1 → v2, one component | migrations |
| 4. Unique customers (critic, celebrity) | `guest_type`, `reputation` slice | — | none | hooks, effects, derived stats |
| 5. Waiter | `waiter` | `staff` gains `role` (defaulted) | none | shared navigation, soft refs, effects |
| 6. Connected rooms | `rooms` slice | `placement`, `body` | placement v1 → v2 (`body` is transient) | migrations, cross-room navigation |
| 7. Accidents (fire) | `hazard`, `condition` | — | none | references on delete, hooks, effects, random |

Five of the seven need no migration. Belt crossings and connected rooms each need one, limited to a single durable component. Neither is decided, so neither is designed into the first version. Under today's single-dictionary model, every row above would touch `session.gd` validation and `restore()`.

## 1. Boss types

**Today.** One creature, the Storm Eel. Its fight lives in `run.encounter` (`{state: "aiming", t, cooldown, harpoon, shots, x, hook}`), its discharges in `discharge.gd` with fairness tables precomputed per creature chunk. Terrain is derived from the seed and `route_version` and never saved.

**With the design.** The fight belongs to the `run` world.

- The creature is an entity with `body`, `creature` (`species`, resistance) and one `attack` row per attack, each running a machine (discharge: windup → strike). Species content lists its attacks: `{"storm_eel": ["discharge"], "mole_crab": ["dig"], "bomb_fish": ["bomb"]}`. Each attack type is one small feature module.
- **Trench digger.** Digging changes terrain during a run, which today cannot happen because terrain is purely derived. A `terrain_edits` table (`{cell: "trench"}`) is an overlay that collision and drawing read on top of the derived route. The dig guard must keep the route passable; `route.gd` already checks reachability for gold, so that check is reused. This fairness rule is the real design work, not the state.
- **Bomb thrower.** Bombs are short-lived entities with `body` and `projectile` (`velocity`, `fuse`, `thrower`). If the player can deflect a bomb back, that is a change to `projectile.thrower` and velocity, nothing more. Spawning inside a step needs deterministic ids from the world counter.
- New chunk kinds keep using `route_version`, which stays the expedition's content version.

**Verdict:** fits. Each new boss adds attack modules and content, not fields on a shared encounter record. Needs worlds, machines and spawning in steps.

## 2. More expedition objects

**Today.** Gold is the `$` glyph in chunk rows. The run stores `collected` as indexes into the derived pickup list, and shields as `shields_taken` indexes. Each new object type means a new glyph, a new index list on `run`, and new validation in `expedition_book.gd`.

**With the design.**

- Chunk content maps glyphs to object types (`$` gold, `T` chest, `>` boost). Route derivation gives each object a stable id (`"<span>:<x>,<y>"`) instead of an array index, so routes can change without remapping indexes.
- The `run` world stores only touched objects in a `route_object` table: `{consumed: true}` for gold, or a machine for objects with state (chest: closed → opening → open, maybe needing several harpoon hits).
- A speed boost adds an effect `{stat: "ship_speed", op: "mul", value: 1.3, remaining: 3}`. The existing shield becomes the same kind of effect (`collision_immune`).

**Verdict:** fits well. Adding an object is content plus one handler. Needs stable content ids and effects.

## 3. Belt intersection

**Today.** A belt tile has exactly one `next_id` and one `input_facing`, and carries one `dish` with `travel_elapsed`. `belt_routes.gd` is built on "one explicit successor per tile"; `incoming()` returns a single predecessor.

**With the design.** The `belt` component holds `lanes`: `[{input, next → belt, dish, travel}]`. A straight tile has one lane; a crossing has two (north–south and east–west), and a merge or split is two lanes sharing an end.

- Dishes move per lane. Whether two dishes can meet in the crossing's centre is a game rule (lanes independent, or one yields) to decide when the feature is designed.
- Chefs and seats face a tile, so they need a rule for which lane they load from or take from, such as "the lane passing the side I face".
- References are per lane (`belt.lanes.next`, policy `clear`), so removing a tile clears every lane pointing at it.

**Migration.** A belt v1 → v2 migration turns `next` and `dish` into `lanes[0]`: a few lines, limited to one component. Under today's model the same change touches validation, the editor, routing and rendering.

**Verdict:** fits, with one small migration if crossings are adopted.

## 4. Unique customers

**Assumption.** A food critic rates the dish and changes arrivals for a while; a celebrity draws a crowd and pays a bonus.

**With the design.**

- Some arrivals get a `guest_type` row (`critic`, `celebrity`); absent means an ordinary guest. Rendering adds a badge or sprite variant through a presenter.
- A `special_guests` feature handles the customers feature's `dish_served` and `customer_arrived` hooks. The critic's rating, from the dish tier, adds a world effect `{stat: "arrival_rate", op: "mul", value: 1.2, remaining: 120}`. The celebrity adds a patience effect to nearby guests and asks the economy for a bonus with `ctx.request("earn_coins", ...)`.
- If ratings should last, a durable `reputation` slice owned by `special_guests` holds them.
- Arrival rate must become a derived stat (`ctx.stat("world", "arrival_rate", base)`). Today `expansion_book.arrival_multiplier` derives it from cleared floor area only.

**Migration:** none; `guest_type` is transient like the visit itself.

**Verdict:** fits. This walkthrough is why the design has declared hooks: the critic must react to a decision the customers feature owns, without writing its data.

## 5. Waiter

**Assumption.** A waiter walks to a waiting customer and pours tea, which slows their waiting clock.

**Today.** Staff means chefs: `staff.hired` maps hire ids to applicants, capacity counts chefs, and pathfinding is customer code inside `session.gd`.

**With the design.**

- A waiter is an entity with `staff` (`role: "waiter"`), `body`, `navigation` and a `waiter` machine: idle → walking → pouring → returning.
- Its target customer is a **soft reference**: if the guest leaves, the machine returns to idle.
- Tea adds `{stat: "patience_rate", op: "mul", value: 0.5, remaining: 20}` to the customer. The customers feature reads its waiting clock rate through `ctx.stat`, so patience must be a derived stat rather than the hard-coded `waiting_elapsed` logic.
- `staff.role` gets the default `"chef"`, so existing rows need no migration. `development` applies to waiters unchanged if their growth stat comes from role content.
- "Placed" for a waiter means having a `body` on the floor; the People tray lists them like chefs.

**The real cost:** navigation must become a shared service (paths, occupancy, reservations) used by customers and waiters. Plan step 7 already does this.

**Verdict:** fits, depending on the navigation extraction and patience as a stat.

## 6. Connected rooms

**Today.** One floor grid (21×13 after expansion, 7 starter columns). Expansion clears trash patches (`expansion.cleared` ids, `revealed`), and `arrival_multiplier` and `staff_bonus` derive from cleared area. Positions are bare `x, y`.

**With the design.**

- Content defines rooms: grid size, world origin, doors linking rooms, unlock requirement. A durable `rooms` slice records which are unlocked. A restaurant level, if leveling drives unlocks, is another slice.
- `placement.room` and `body.room` say where things are. Rendering offsets each room by its origin, so presenters do not change.
- Navigation works per room grid, joined at doors. Doors are entities with `placement` and a `door` row, so the route cache depends on their revisions.
- Area-based derived values (staff slots, arrival rate) sum over unlocked rooms.

**Migration.** Placement v1 → v2 adds `room: "main"` to every row. `body` is transient, so customer positions are dropped rather than migrated.

**Verdict:** fits, with one small migration if rooms are adopted.

## 7. Accidents: fire

**Assumption.** Fires start at random, spread, wear down nearby equipment, scare customers, and need the player to tap them out.

**With the design.**

- A `hazards` feature spawns fire entities (`placement`, `hazard` machine: smouldering → burning → spreading → out) using `ctx.random` at a rate that is a derived stat, so a fire-extinguisher decoration can lower it with an effect. Balance lives in content.
- Damage adds a durable `condition` row (`wear` 0–1) to equipment in range; absent means intact. The kitchen reads `condition` and its station machine refuses to work when broken. Reading another feature's table is allowed.
- Destroyed equipment is `ctx.delete(id)`, and the reference policies handle the rest: belts pointing at a burnt belt are cleared, seated guests on a burnt seat are stood up through `notify`, and any other fire attached to that equipment is deleted with it (`cascade`).
- The `hazard_started` hook lets customers add a flee transition to the `visit` machine (transient, so no migration) and add a world effect lowering `arrival_rate`.
- `extinguish` is an ordinary command; returned events drive camera alerts and sounds. Fires pause in Edit, like visits.

**Verdict:** fits, and exercises the most engine features at once: deletion policies, hooks, effects, machines and randomness.

## What the walkthroughs changed in the design

1. **Effects and derived stats** (critic, tea, fire, boost, shield) became an engine feature.
2. **Declared hooks** replace "events go out, not around", and settle the cross-feature question: requests for changing another feature's data, hooks for reacting to its decisions.
3. **Worlds** separate the restaurant from an expedition run.
4. **Navigation** is a shared service, not customer code.
5. **Stable content ids** replace array indexes for route objects.
6. **Schema defaults** make an added optional field a non-event for saves.

Belt lanes and rooms in positions were considered as first-version fields to avoid two migrations, and left out because neither feature is decided.

## Risks the state model does not solve

- Fairness of terrain-changing bosses, and crossing rules for belts, are design problems.
- Extracting navigation from `session.gd` is the largest single refactor.
- Hook order is fixed in one registry, but two handlers on one hook can still interact in surprising ways; tests should cover each hook's full handler list.
- Every effect makes the balance harder to reason about; keep effect values in content so they can be tuned.
