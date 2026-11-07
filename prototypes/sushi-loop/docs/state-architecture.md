# State architecture

**Status: in progress (2026-11-06).** Steps 1–8 of the [migration plan](#migration-plan) are implemented: the engine (`godot/scripts/engine/`), features in `godot/scripts/features/`, and `dispatch()`. Step 9 is done as decided on 2026-11-06 (JSON stays; derived values are not saved; game rules are checked on load). The first section describes the code before the migration; everything after it is the target design. [Feature walkthroughs](state-architecture-walkthroughs.md) test the design against planned features. The decision is recorded in [ADR 0005](adr/0005-entities-and-component-tables.md).

## Today

All restaurant state is one untyped dictionary inside [`session.gd`](../godot/scripts/session.gd) (2,539 lines). The session and static "Book" modules (`recipe_book`, `staff_book`, `chef_development`, `shop_book`, `floor_book`, `expansion_book`, `expedition/expedition_book`) edit it directly, and it is saved whole as JSON.

| Part | Role |
| --- | --- |
| `session.gd` | `command()` routes requests through an if-chain on their names. `advance()` runs fixed time steps for customers, belts, chefs and arrivals. `snapshot()` deep-copies state into view data. `restore()` checks 15 version stamps, upgrades old saves and validates. Also holds customers, pathfinding, the layout editor and most validation. |
| Book modules | Static `initialize`, `command`, `valid`, `snapshot` functions that edit the shared dictionary. |
| [`game.gd`](../godot/scripts/game.gd) | Connects screens to the session. 31 command calls and 20 save calls, each deciding on its own whether to save, block or redraw. Reads the session's private `_state` in 4 places. |
| [`save_store.gd`](../godot/scripts/save_store.gd) | Writes, verifies and promotes save files with a backup. Validates every save with a full `Session.new().restore(data)`, then again after re-reading the file. |

The state's shape:

- `state.objects` is one list of `{kind: chef | belt | seat | decor, ...}` records whose fields depend on `kind`.
- `state.inventory` holds a second copy of every chef (`stored_object`), plus counts of unplaced goods.
- `state.customers` is a separate list; each customer carries `phase`, `visual_phase`, `preference_phase` and navigation fields side by side.
- Belt tiles carry one `next_id`, `input_facing`, and the `dish` riding on them.

### Problems

1. **Data lives in several places.** A placed chef is a layout object; an unassigned chef is nested inside its inventory entry, which also copies `level`, `level_cap`, `cooking_speed`, `growth_rate` and `base_cooking_speed`, kept in step by `Development.sync`.
2. **Calculated values are saved.** `cooking_speed` follows from base speed, level and growth. Cooking progress is stored in seconds, so a level-up must rescale it, and validation compares stored against recalculated values exactly.
3. **`kind` switches everywhere.** Code and validation branch on `kind` (for example `if object.get("kind") != "chef"`), and must know which optional fields belong to which kind.
4. **Hand-written follow-ups.** After a chef is fired the session re-clamps editor pages and calls `_rebuild_access()`. Removing a seat relies on `_carry_or_release_seat` remembering every customer that points at it.
5. **Save handling repeats per call site**, and loading, upgrading and validation are one function, so every save pays for a full load.
6. **Lifecycles are flags, not states.** Much of `_valid_saved_state` exists to reject impossible combinations of phase flags.

**Case study: the chef upgrade save failure (0.16.1).** Leveling up a chef who held a finished dish set `preparation_elapsed` to the in-memory duration. On save the file was re-read and the duration recalculated from a JSON-parsed `cooking_speed` one rounding step smaller, so `preparation_elapsed > duration` rejected every save and every Retry. Problems 1, 2 and 5 combined. The shipped fix is a tolerance in that check; this design removes the cause.

## Principles

1. **One owner per fact.** Every component table and every singleton has exactly one owning feature, the only code that writes it. Others read it, or ask the owner through a request.
2. **Save facts, derive the rest.** Speeds, durations, "assigned" flags and page counts are calculated on read. Progress is a 0–1 fraction, not seconds that depend on a speed.
3. **New feature, new table.** A feature adds components rather than new fields on someone else's record. Old saves simply have no rows in the new table.
4. **Commands are all or nothing**, enforced by the engine, not by each handler.
5. **Determinism is the engine's job**: fixed steps, one seeded random generator, a stable order.
6. **No free event bus.** Features affect each other only through requests and declared hooks with a fixed order. Events returned to the UI are output only.
7. **Lifecycles are state machines**, so impossible combinations cannot be stored.

## Entity model

### Entities and components

An entity is only an id. A component is a table keyed by entity id whose rows are plain dictionaries. What an entity *is* comes from which components it has, not from a `kind` field.

```
entities:    { "chef-3": {}, "seat-7": {}, "belt-12": {}, "customer-41": {} }
item:        { "seat-7": {catalog: "stool"}, "belt-12": {catalog: "belt"} }
placement:   { "chef-3": {x, y, facing}, "seat-7": {...}, "belt-12": {...} }
staff:       { "chef-3": {name, art_id, role: "chef", hired_from} }
development: { "chef-3": {level, growth} }
station:     { "chef-3": {machine, recipe_id, progress} }
belt:        { "belt-12": {next, input_facing, dish, travel} }
seat:        { "seat-7": {} }
body:        { "customer-41": {x, y, facing} }
navigation:  { "customer-41": {goals, path, path_index, status} }
visit:       { "customer-41": {machine, claim, preference, clocks} }
```

- **No copies.** Unassigning a chef removes its `placement` row. The `staff`, `development` and `station` rows stay, so nothing is copied into inventory. "Assigned" is `placement.has(id)`.
- **Grid vs free movement.** Chefs, belts and seats share `placement` (grid cell), so the editor handles them with one piece of code. Customers and other walkers have `body` (fractional position) and `navigation`. A chef and a customer share no components, because they share no behaviour.
- **Catalog type is not behaviour.** `item.catalog` names the content entry (sprite, price, editor stock), never a branch in game rules.
- **Singletons stay slices.** Coins, the clock, the recipe book, shop stock, floor styles, expansion progress and fungible inventory counts are plain owned dictionaries, not entities.
- **Ids are never reused.** Counters only grow, so a stale reference can never point at a new entity.

### Proposed restaurant components

| Component | Owner | Fields | Durability |
| --- | --- | --- | --- |
| `item` | layout | `catalog` | durable |
| `placement` | layout | `x, y, facing` | durable |
| `staff` | staff | `name, art_id, role, hired_from` | durable |
| `development` | development | `level, growth` | durable |
| `station` | kitchen | `machine, recipe_id, progress, held_dish` | durable |
| `belt` | belts | `next → belt, input_facing, dish, travel` | durable |
| `seat` | seating | — | durable |
| `body` | movement | `x, y, facing` | transient |
| `navigation` | navigation | `goals, path, path_index, status` | transient |
| `visit` | customers | `machine, claim → seat, preference, clocks` | transient |
| `effects` | engine | list of timed modifiers, see below | follows its entity |

Belts keep today's single successor and positions keep today's single floor. Belt crossings and connected rooms are undecided; if they are adopted, each needs one small migration of one component (see the walkthroughs).

### Durable and transient

Every component is declared **durable** or **transient**.

- Durable components (placement, development, station, belts) must survive every game version, through migrations.
- Transient components (customer visits, bodies, navigation, a running expedition) have no migrations. If a save's version of a transient table does not match, the loader drops the table and any entity left with no components. Customers simply walk in again.

This keeps redesigns of the most-changed systems free of migration code.

### Worlds

The store holds named **worlds**, each with its own component tables.

- `restaurant`: durable layout, staff and service.
- `run`: one expedition run (ship, creature, projectiles, route objects the player touched). Created at launch, discarded at the end. Results reach restaurant slices (salvage, recipe discovery) through requests.

### Content and state

Content in `godot/content/` defines types: recipes, catalog goods, belt kinds, chunks, creatures, guest types. State refers to content by id. Saves keep only facts that changed during play. Whether configuration is still copied into each save is an open question.

## Commands, steps and transactions

All changes go through `store.dispatch(request)`.

1. Look up `request.type` in the command table the features registered. Unknown → `{ok: false, reason: "unknown_command"}`.
2. Begin a transaction: tables are copied on first write (copy-on-write per table).
3. Run `handler(request, ctx)`. A handler writes its own tables and may call `ctx.request(type, args)` to ask another feature to change its own data in the same transaction.
4. On `ok`, commit the copies, bump table revisions and mark dependent caches stale. On failure, drop the copies: nothing changed.
5. Return `{ok, reason, events}`.

`store.advance(dt)` runs fixed steps. Each feature's `step(ctx, dt)` runs in a declared order (today: customers, belts, chefs, arrivals), edits its tables in place without copies, and appends events. Instances step in id order, never dictionary insertion order.

This removes per-command atomicity code that the tests check by hand today ("replayed input is atomic", "invalid reassignment is atomic").

### Hooks

Some features must react to decisions owned by another feature: a food critic reacts when a dish is served, a fire scares customers. A feature may declare named hooks at its decision points:

```gdscript
# customers.gd declares, and calls inside its own step:
ctx.hook("dish_served", {"customer": id, "recipe_id": recipe, "seat": seat})
```

Other features register handlers in the feature registry, which fixes their order in one place. Handlers run synchronously in the same step or transaction and may only write their own tables or use `ctx.request`. There is no runtime subscription, so the full list of reactions is readable in the registry.

## Relations between entities

Interconnected state is where most bugs hide: two things must agree, and one changes without the other. The rules below decide where a relation lives and whether it is stored at all.

### Case study: the stuck stool

Reproduced on 2026-11-06 with a headless probe on the starter restaurant:

1. A guest is walking to a stool (`phase: "walking"`, `seat_id: "seat-2"`).
2. In Edit, the player drags the guest into a cell walled in by placed decor.
3. Back in Live, navigation finds no route and switches to wandering, but the visit stays `walking` with `seat_id` set.
4. `_seat_reserved` counts every guest who is not leaving and has that `seat_id`, so the stool stays taken indefinitely: arrivals skip it and new guests wait at the entrance.

A seated guest dragged the same way is stood up and releases the stool correctly; another guest sat on it within 30 seconds. **Fixed in the current code** (rule decided 2026-11-06: stools are first come, first served): a wandering walker no longer holds the stool, and when a route opens they return to it only if it is still free (`_holds_seat` in `session.gd`, test in `guest_wandering_tests.gd`). The causes:

- **One field, two meanings.** `seat_id` means "heading there" while walking and "sitting there" while waiting or eating, so every reader must also check the phase.
- **Two lifecycles disagree.** Navigation has given up; the visit still says it is walking to a seat. Nothing turns the navigation failure into a decision about the seat.
- **The rule is written three times.** "Is this stool taken?" is `_seat_reserved` in `session.gd` and two separate checks in `restaurant_view.gd`.
- **No limit.** The current recovery contract deliberately lets a trapped guest resume their seat later, but without bounding how long the stool is held.

### Where to store it

| Approach | For | Against |
| --- | --- | --- |
| The stool stores its occupant | "Is it free?" is a field read | A second copy that both sides must update; it drifts like the chef copies did |
| The guest stores its seat (today) | One copy, owned by the lifecycle that decides | "Who is on this stool?" needs a reverse lookup |
| Derive it from positions | Nothing stored | Cannot express a reservation before arrival; a guest dragged onto or walking across a stool would count as seated |

**Recommendation:** the guest's `visit` stores a `claim` on the seat, bound to the visit machine. Seat occupancy is a derived index, rebuilt when the `visit` table's revision changes.

### Rules

1. **Store a relation once, on the side whose lifecycle creates and ends it.** The visit decides to take, keep and give up a stool; the stool is passive. Reverse questions come from a derived index, never a stored back-pointer.
2. **One field, one meaning.** A claim ("this seat is mine") and a physical fact ("my body is on it") are different fields if both are needed.
3. **Bind references to machine states.** The visit machine declares the states that require a claim (walking to a seat, seated, eating) and clears it on leaving them. Validation rejects a claim outside those states or a missing one inside them. With a `trapped` state, the stuck stool cannot be stored.
4. **Every claim has a release path for each failure:** the target is deleted (reference policy `notify`), the target is unreachable (navigation reports `unreachable` and the owner decides), or time runs out (a claim may carry a deadline). Keeping a seat for a trapped guest is then an explicit, bounded choice, such as a soft claim another guest may take over.
5. **Use geometry only for physical facts:** collisions, what is under a tap, whether a cell is walkable. Commitments, assignments and ownership are stored explicitly.
6. **Ask each question in one place.** `seating.is_free(seat, ctx)` is the only definition of "taken"; the view reaches it through its presenter instead of copying the rule.
7. **Store decisions, derive consequences.** Store what the player or a lifecycle decided and nothing else can reproduce: a reservation, an assignment, a belt successor the player built. Derive what follows from other data: occupancy, adjacency, which belt a chef faces, reachability, staff counts, "assigned".

## Navigation

Today about 21 functions in `session.gd` mix three concerns for customers only: grid search (two breadth-first searches), choosing where to go (seat, exit, entrance, wander target), and walking (traffic, passing offsets). The design splits them:

| Layer | Owner | Does |
| --- | --- | --- |
| Path search | shared, pure functions | Builds the walkable grid from layout, cached by layout revision. `find_path(from, goals, options)` returns a path or `unreachable`. Goals are a set of cells, so "nearest free seat" is one multi-goal search instead of one search per seat as `_try_reseat` does today. Breadth-first search suits today's uniform grid; A* with a distance heuristic replaces it if the grid grows. No feature knowledge. |
| Movement | navigation feature, owns `navigation` | Follows the path with speed, traffic and passing offsets. Sets `navigation.status` to `moving`, `arrived`, `blocked` or `unreachable`, and re-plans when the layout revision changes. |
| Destination choice | each feature | Customers pick a seat, the exit or a wander target; a waiter picks a guest; a fire's fleeing guests pick the exit. The feature asks with `ctx.request("navigate", {entity, goals, purpose})`, and its machine reacts to `status`. |

In the stuck-stool case, `unreachable` moves the visit machine to `trapped`, whose entry releases the claim, or keeps a bounded soft claim if that is the chosen rule. Random wander targets are destination policy, chosen by the feature with `ctx.random`; the search itself is deterministic. Searches run when a goal or the layout changes, never every frame.

## References

A component declares every field that holds an entity id, with a policy for deletion, like a database foreign key.

```gdscript
const REFS := {
	"visit.claim":      {"to": "seat", "on_delete": "notify"},  # customers stands the guest up
	"belt.next":        {"to": "belt", "on_delete": "clear"},
	"hazard.target":    {"to": "placement", "on_delete": "cascade"},  # a fire on removed equipment goes out
}
```

- `clear` sets the field to empty. `cascade` deletes the referrer. `notify` calls the owning feature's `on_ref_removed(entity, field, ctx)` in the same transaction. `restrict` refuses the delete.
- `ctx.delete(id)` removes the entity's rows, then scans only declared reference fields. A restaurant has at most a few hundred entities (the expansion floor is 21×13), and deletes are commands, not per-frame work, so a scan costs little even on a phone. A reverse index (`target → referrers`), rebuilt on load and never saved, is added only if profiling asks for it.
- **Soft references** (`{"soft": true}`) are for short-lived targeting, such as a waiter heading to a customer. They have no policy; readers use `ctx.get(id)`, which returns `{}` for a missing entity, and handle that case.
- Loading checks that every hard reference resolves, so a dangling reference is a clear load error instead of a later crash.

## Effects and derived stats

Many features temporarily change a number another feature uses: tea extends patience, a critic raises arrivals, fire lowers them, a pickup speeds up the ship. These are **effects**, kept by the engine:

```
effects: { "customer-41": [{id: "tea", stat: "patience_rate", op: "mul", value: 0.5, remaining: 20.0, source: "waiter-2"}],
           "world":       [{id: "critic-praise", stat: "arrival_rate", op: "mul", value: 1.2, remaining: 120.0}] }
```

- The feature that owns a number derives it: `ctx.stat(entity, "arrival_rate", base)` applies the entity's and the world's effects (adds, then multiplies, in id order).
- The engine counts `remaining` down inside the fixed step and removes expired effects. An effect without `remaining` lasts until removed.
- Effects on durable entities are saved; effects on transient entities go with them.
- Today's expedition shield (`run.shield`) becomes an effect.

## Statecharts

Lifecycles use a small xstate-style helper (about 150 lines, plain data). We port the idea, not the library: full xstate is more than the game needs, and node-based Godot statechart addons do not suit dozens of saveable entities in a pure simulation.

```gdscript
const STATION := {
	"initial": "idle",
	"states": {
		"idle":    {"on": {"assign": "working"}},
		"working": {"progress": "duration", "done": "holding", "emit": "prepared"},
		"holding": {"on": {"belt_free": "loading"}},
		"loading": {"after": "loading_seconds", "to": "idle", "emit": "loaded"},
	},
}
```

- Stored form: `{machine: "working", elapsed: 1.4}` inside the component row. Plain JSON.
- `Machine.send(def, row, "belt_free")` moves to the target state if the current one accepts the event.
- `after` counts seconds; `progress` advances a 0–1 fraction by `dt / duration(ctx)`, so a speed change needs no rescaling. Both advance only inside the fixed step.
- Guards and actions are named functions the feature supplies.
- Validation is free: a stored state must be one the machine declares.
- An entity may run parallel machines in separate components (a customer's `visit` and `navigation`).

| Use a machine | Keep as data |
| --- | --- |
| Chef station: idle, working, holding, loading | Level, growth, name |
| Customer visit: entrance wait, walking, standing, eating, leaving | Position, path, preference |
| Expedition run, creature attacks (Storm Eel discharge: windup, strike) | Route, salvage counts |
| Save-recovery dialog | Coins, inventory counts, the layout grid |

## Persistence and migrations

```
{ "format": "sushi-loop-session", "engine": 2,
  "worlds": { "restaurant": { "next_id": 812,
      "components": { "placement": {"version": 1, "rows": {...}}, "visit": {"version": 3, "rows": {...}}, ... } } },
  "slices": { "coins": {"version": 1, "data": 1240}, "recipe_book": {"version": 2, "data": {...}}, ... },
  "clock": {...}, "random_state": "..." }
```

- **Load:** each durable table and slice runs its migrations from the saved version to the current one (`migrations()[v]` turns v into v+1). Transient tables with another version are dropped. A missing table or slice starts empty or from `initial()`.
- **Defaults:** a schema may give a new optional field a default (`role: "chef"`). Adding a defaulted field is not a version change.
- **Validate = structure only:** types, ranges, references that resolve, machine states that exist. No recalculated-value comparisons, because calculated values are never saved.
- **Derived fields** are declared per component; the engine rejects a save that contains one, so the chef bug class cannot return.
- **Save:** serialize, run the same structural checks on the serialized data, write. No full reload. `save_store.gd` keeps its pending file, backup and verified promote.
- **Older saves:** none are upgraded; the game is unreleased and its data was reset when the store format shipped.

## Rendering

Screens never read tables. A **render projection** builds one props dictionary per visible entity:

```gdscript
for id in visible_ids:                          # entities with placement or body
	var props := {"id": id}
	props.merge(placement.get(id, body.get(id, {})))
	for presenter in presenters:                # each visible feature adds its part
		presenter.decorate(props, id, ctx)      # station: dish + progress; development: badge
	out.append(props)
```

- **Cost:** a few hundred entities times a few O(1) lookups each, less work than today's `snapshot()`, which deep-copies floor, recipes, editor, camera and stats and rebuilds every object on each refresh. Phone GDScript is several times slower than desktop, so this must be profiled on a device before any claim of headroom.
- **Feature-blind view:** a new feature adds a presenter; `restaurant_view.gd` never learns its tables and loses most `kind` branches.
- **Revisions:** edit-time props (placement, item, floor) are cached and rebuilt only when those tables' revisions change. Simulation props (bodies, progress) refresh each frame.
- Picking keeps the [sprite selection contract](../godot/review/12/sprite-selection/contract.md): hit records carry the owning entity id.

## UI boundary

`game.gd` gets one `dispatch()`:

```gdscript
func dispatch(request: Dictionary) -> Dictionary:
	if save_blocked: return {"ok": false, "reason": "save_blocked"}
	var result := store.dispatch(request)
	if not result.ok:
		feedback.reject(result.reason)
		return result
	if store.dirty and not save_now(): _block_edit_save()
	for event in result.events: presenters.handle(event)   # sounds, coin pops, toasts
	_refresh()
	return result
```

- The 31 command sites and 20 save sites collapse into this. Screen follow-ups (close the shop, open the recipe picker) react to returned events.
- View-only commands (camera, mode) are flagged `persist: false` and skip the save.
- `store.advance(dt)` returns events; autosave keeps its 3-second cadence and worker thread.

## Determinism and performance

- One seeded generator owned by the engine, passed as `ctx.random`. Features never create their own; its state is saved as a string, as now.
- Machine transitions, effect expiry and hooks happen only inside fixed steps or commands, never from wall-clock timers or Godot signals.
- Steps edit tables in place. Only commands copy, and only tables they write.
- Per-frame code builds indexes once per pass (as `restaurant_view.gd` already does) and never rescans every entity per item.

## Feature contract

Each feature is one script:

| Member | Purpose |
| --- | --- |
| `COMPONENTS` | Tables it owns: fields, defaults, durability, version, derived fields |
| `REFS` | Reference fields and deletion policies |
| `migrations()` | Per durable table, one step per version |
| `commands()` | Command name → handler |
| `hooks()` | Hooks it handles, with handlers |
| `step(ctx, dt)` | One fixed step |
| `presenter` | `decorate(props, id, ctx)` for rendering; `view(ctx)` for screens |

## Migration plan

Move one feature at a time behind the existing `GameSession` API. Every step ships with all native test scripts passing and the legacy fixtures loading.

1. **Engine core. Done.** `engine/store.gd` (worlds, component tables, slices, copy-on-first-write transactions, references with deletion policies, hooks, effects, revisions, versioned save and load) and `engine/machine.gd`. Tested by `tests/engine_tests.gd`.
2. **Bridge. Done.** `GameSession` holds `_store` beside `_state`, and `command()` runs every command in a store transaction. Saves carry an `engine` section (`engine_version` 1). A save without one is upgraded once through the existing pipeline, then moved into the store. While other features are on the old code, their validators run on a copy with chef records rebuilt (`Chefs.hydrate`); the live state never holds them.
3. **Chefs. Done.** `staff`, `development` and `station` rows replace the chef fields in layout objects and the inventory copies (`stored_object`). A chef's grid position stays a layout object until step 6. Speed is calculated, progress is a 0–1 fraction, and the station state doubles as the animation phase. The old tolerance check stays only for saves written before the store, such as those affected by the 0.16.1 bug.
4. **`dispatch()` in `game.gd`. Done.** Player commands go through one function that refuses while a save is pending, saves once and blocks on failure; callers keep their screen follow-ups. Commands do not return events yet.
5. **Singletons. Done.** Shop, floor styles, recipe book, staff, expansion, plus the inventory, editor and expedition records, are store slices. Commands declare the slices they write, so a failed command restores them. Until step 9 they are still saved under `state` with their version stamps, and `_state` refers to the same objects (never copies) so code not yet moved can read them; after each command the session re-links any record old code replaced. The expansion map is cached by the slice's revision.
6. **Layout. Done, as one table.** Placed objects are rows of one `layout` table in placement order (`features/layout.gd`), with O(1) lookup by id. Editor commands roll back through the store. Removing a seat, belt or decor deletes the entity, and declared references follow their policies. **Follow-up:** split the row into `placement`, `belt`, `seat` and `item` tables; belt routing and dish contents still share the belt's row, so layout caches cannot yet be keyed by revision (the row changes every step).
7. **Customers. Done.** Guests are rows of a `customer` table (`features/customers.gd`). A guest's stool is the `seat_id` reference with an on-delete `notify` policy, which stands the guest up; stools are first come, first served (`Customers.holds_seat`). Path search is pure (`features/navigation.gd`: multi-goal breadth-first search and flood fill over a usable-floor set cached by expansion revision); movement and destination choice stay in the session. The `VISIT` machine defines phases and their animations, and validation uses it. **Follow-up:** split rows into `body`, `navigation` and `visit`; "trapped" remains the navigation's `wander` mode rather than its own visit state; move destination choice and movement out of `session.gd`.
8. **Expedition. Done, for the shield.** The expedition record is a slice. Each run gets a transient `run` world, created at launch and dropped when the run ends; the ship's shield is a timed effect there, counted down by the engine and saved in the `engine` section. Older saves' `run.shield` is adopted on load. **Follow-up:** move the rest of the run (ship, creature, harpoon) into the world when the next expedition feature needs it.
9. **Saving and validation. Done.** Decided with the user: JSON stays the format.
   - **Not saved:** `elapsed` (from `step_index`), the guest counter `next_customer_id` (from arrivals), `stats.served` (equal to sales) and the chefs' `assigned` flag (from the layout). They are recalculated on load (`_derive_saved`), and a stale copy in an older save is replaced rather than rejected. Their cross-checks, and the dish-count equation, are gone.
   - **Checked on load:** rules about the restaurant (no shared cells, valid belt routes, unique dish ids below the counter, ids that resolve, visit and station states) and types and ranges.
   - **Saving** never runs the game rules on the data being written, so it can never block. It verifies the file's checksum and that it parses. The previous generation becomes the backup only if it passes the rules (cached per file); otherwise the old backup stays. A full save went from 6.6 ms to 4.5 ms; most of what is left is that backup check, which autosaves run on the worker thread.
   - **One store save (version 3).** A save is `{version, configuration, engine, remainder, random_state}`; `engine` is `store.save()` with every slice (including the session's own `core` slice) and every table. The layout and guest tables are saved as ordered lists, since JSON writers sort keys. There is no upgrade code for older saves: the game is unreleased, so data was reset (2026-11-06) and files in an older envelope format are discarded on load.
   - **One validator.** `_valid_store` checks every feature's rules directly on store data: chefs in `Chefs.valid` and `Chefs.valid_recipes`, staff and recipe book through store-aware `valid(..., store)`, layout, editor, inventory and guests in the existing validators run in store mode. It runs on load and after each edit, with no rebuilt copy.
   - **`GameSession.flat_view(save)`** shows a save as one dictionary (`state` plus the chef tables) for tools and tests; `restore()` accepts it through a pure conversion.
   - **Remaining cost.** Loading and validation take about 2.4 ms on desktop, mostly guest path checks and the editor's inventory accounting.

## Profile

Desktop medians (`tests/profile_state.gd`, starter restaurant after a minute: 16 objects, 5 guests, 3 chefs; results in `godot/review/state-engine/`). The rendered frame is unchanged (about 8.3 ms in `tests/profile_pan.gd`).

| Case | Before | After step 8 |
| --- | --- | --- |
| Level up a chef (includes one snapshot) | 1,399 µs | 837 µs (−40%) |
| Editor rotate | 1,509 µs | 1,139 µs (−25%) |
| `snapshot()` | 164 µs | 218 µs (+33%) |
| Whole app frame, Live | 390 µs | 453 µs (+16%) |
| Save validation / load | 2,364 / 2,356 µs | 2,512 / 2,524 µs (+6–7%) |

Commands are faster because rollback is generic, a level-up no longer rebuilds every customer route, and lookups by id are O(1). Frames are slower because chef views are assembled from three tables and the bridge rebuilds old-shaped records for saving and validation. Step 9 removes the bridge cost; the layout split (step 6 follow-up) lets layout views be cached by revision.

## Serialization

Godot's binary `var_to_bytes` / `bytes_to_var` (also `FileAccess.store_var`) measured on this save: 87 µs to write and 90 µs to read, against 182 µs and 212 µs for JSON. Floats and integers round-trip exactly, which removes the class of bug behind 0.16.1 and the integer normalization code. It is larger (20.6 KB against 12.1 KB) and not human-readable. Never pass `allow_objects = true` when reading a save: it can instantiate scripts. Candidate for step 9, with a JSON export kept for debugging and test fixtures.

## Open questions

- **Dish identity.** Dishes stay values carried inside `belt`, `station` and `visit` rows, handed over by request (proposed), or become entities?
- **Typed wrappers.** Plain dictionaries keep saving trivial; thin typed accessors would add autocomplete.
- **Configuration in saves.** Keep copying recipes and floor content into each save, or save a content version and reload `res://content/`?
- **Bridge period.** How many releases write both formats?
- **Machine depth.** Flat machines plus parallel components (proposed), or nested states?
- **Mid-run saves across versions.** Dropping a transient `run` world ends an expedition in progress. Acceptable, or should runs migrate?
- **Sharing.** The engine stays inside Sushi Loop, per the repository's independent-games rule, unless another prototype needs it.
