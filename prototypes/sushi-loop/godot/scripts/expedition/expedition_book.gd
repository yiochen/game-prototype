extends RefCounted
## Expedition rules through the public command/save boundary (issue #21).
##
## One battery: Start consumes it; an ended expedition begins a fixed
## wall-clock night recharge that also runs offline and caps at one launch.
## Unfinished runs (active or suspended) never recharge. Travel advances only
## through `expedition_advance` with an explicit elapsed time, so Pause and
## closing the app freeze it. Earned salvage is committed exactly once when a
## run ends; the receipt stays until acknowledged and is never re-awarded.
## Steering is a joystick: `expedition_steer` sets a lateral input in [-1, 1]
## and travel integrates the ship's sideways speed; input 0 runs straight.
## Routes open with launch chunks the preparation screen cruises through; Start
## may begin anywhere in that open-water lead-in.
##
## Issue #22: lateral current fields push the ship on top of steering (letting
## go removes only the player's part). A shield pickup (the spec's travel
## boost) blocks collision damage for a few seconds at normal speed,
## ending before the finish encounter. Steering onto an optional portal spends
## it and enters a separate safe passage: a current carries the ship
## automatically through salvage, then it rejoins the main route further on.
## A run records the route version it started with; only the current one loads.
##
## Issue #23: route version 3 adds an open-water arena before the finish. When
## the ship is a few rows in, a creature arrives ahead and the shooting window
## opens (no countdown; the last seconds are "restless"). `expedition_fire`
## launches one harpoon straight up from the ship on a fresh press; a miss
## reels back and the cooldown must finish before the next shot. The creature
## swims forward with the ship, weaving sideways, and its hit area is a fixed
## ellipse whatever its animation does. A hit records the hook and enters a
## held handoff: travel and the creature hold still until the pursuit (#24)
## lands, and Pause → Give up leaves. Window expiry without a hook lets
## the creature escape, awards nothing and the route finishes as usual.
##
## Issue #24: route version 4 moves the arena a few ordinary chunks before the
## finish. A hook starts the pursuit: ship and creature speed up together
## through that terrain, the cable stretches freely (no range limit) and the
## creature's resistance, its health, drains steadily and never refills.
## Collisions cost hull only. Zero resistance commits the catch and the
## species' recipe discovery at once and ends the run as complete (the ship
## finishes on its own; hazards are over). Zero hull ends it as hull depleted:
## the creature escapes, with no recipe and no second attempt. Reaching the
## finish while still hooked also lands the catch.
##
## Issue #25: route version 5 alternates the pursuit's ordinary chunks with the
## creature's own chunks (wide open water). Only there, and only while hooked,
## the creature discharges: it picks one fixed strip from the chunk's table of
## fair strikes (discharge.gd), leaning towards the ship but never tracking
## it, warns for a moment, then the strip goes live. A ship inside it loses
## hull (hit protection applies; no knock-back, no resistance change). A catch
## or escape ends the run, which removes any warning or strike with it.
##
## Issue #70: a second species, the Inkfin Cuttlefish. Each run flies for one
## creature (`run.creature`): Start picks at random among the species whose
## recipe is still undiscovered, then among all of them. The cuttlefish's route
## (version 6) puts ordinary chunks in the plan's creature slots; each is an
## ink zone. While hooked, entering one makes the cuttlefish warn for a moment
## and then black out the sea: the ink seeps in, holds through the zone and a
## few rows of the next chunk, then lifts. Only the ship's light shows the
## water ahead, so ink zones and the chunks the ink lingers into must pass
## the sight check (sight.gd). Ink does no damage and never changes collision.
##
## Issue #28: Start copies the Workshop gear into the run (`run.gear`), so
## later upgrades never change an expedition under way: maximum hull, reeling
## strength (resistance drain multiplier), Collector reach (pickup attraction
## radius), shield-pickup duration, passage ride length and a launch shield.
## Encounters never scale with equipment.
## Balance lives in res://content/expedition.json; routes in route.gd.
const VERSION := 1
const Route = preload("res://scripts/expedition/route.gd")
const FloorBook = preload("res://scripts/floor_book.gd")
const RecipeBook = preload("res://scripts/recipe_book.gd")
const Discharge = preload("res://scripts/expedition/discharge.gd")
const Sight = preload("res://scripts/expedition/sight.gd")
const WorkshopBook = preload("res://scripts/workshop_book.gd")
const ShopBook = preload("res://scripts/shop_book.gd")
const OUTCOMES := ["complete", "gave_up", "hull_depleted"]
const MAX_INTEGER := 9007199254740991
static var _content: Dictionary = {}
static var _library: Array = []
static var _routes: Dictionary = {}
static var _passages: Dictionary = {}
static var _docs: Dictionary = {}
static var _sight: Dictionary = {}

## A run's transient world in the state store. The ship's shield is a timed
## effect there, counted down by the engine; screens see it as `run.shield`.
const WORLD := "run"
const SHIP := "ship"

static func shield(store) -> float:
	if store == null: return 0.0
	for effect in store.table(WORLD, store.EFFECTS).get(SHIP, []):
		if effect.id == "shield": return float(effect.remaining)
	return 0.0

static func set_shield(store, seconds: float) -> void:
	store.create_world(WORLD)
	if seconds > 0.0: store.add_effect(WORLD, SHIP, {"id": "shield", "stat": "shielded", "op": "add", "value": 1.0, "remaining": seconds})
	else: store.remove_effect(WORLD, SHIP, "shield")

static func shield_valid(store) -> bool:
	var effects: Dictionary = store.table(WORLD, store.EFFECTS)
	for owner in effects:
		if owner != SHIP: return false
		for effect in effects[owner]:
			if effect.get("id") != "shield" or not _finite(effect.get("remaining")) or float(effect.remaining) <= 0.0 or float(effect.remaining) > max_shield_seconds() + 0.001: return false
	return true

## A run's gear (runs saved before #28 fly with base gear).
static func gear(run: Dictionary) -> Dictionary:
	var value = run.get("gear")
	return value if value is Dictionary and value.has("tiers") else WorkshopBook.base_gear()

## Longest shield any gear can grant, for validating saved effects.
static func max_shield_seconds() -> float:
	return maxf(WorkshopBook.value("shield", WorkshopBook.max_level("shield")), WorkshopBook.value("launch", WorkshopBook.max_level("launch")))

static func definition() -> Dictionary:
	if _content.is_empty(): _content = JSON.parse_string(FileAccess.get_file_as_string("res://content/expedition.json"))
	return _content

static func library() -> Array:
	if _library.is_empty():
		var chunks: Array = []
		for chunk in Route.load_chunks():
			# A creature chunk joins only with an up-to-date, accepted discharge table.
			if chunk.kind == "creature":
				var table = _doc(str(chunk.id)).get("chunk", {}).get("discharge")
				var problems := Discharge.table_problems(chunk, table, definition()) if Route.validate_chunk(chunk).is_empty() else []
				if not problems.is_empty():
					push_warning("Expedition chunk %s left out: %s" % [chunk.id, "; ".join(problems)]); continue
				# JSON numbers come back as floats: strips are whole cells.
				chunk.discharge = {"strikes": table.strikes.map(func(e): return {"row": float(e.row), "fair": e.fair.map(func(p): return [int(p[0]), int(p[1])])})}
			chunks.append(chunk)
		var analysis := Route.analyze_library(chunks)
		for id in analysis.problems: push_warning("Expedition chunk %s left out: %s" % [id, "; ".join(analysis.problems[id])])
		_library = analysis.chunks
	return _library

## Species ids, in catalog order.
static func creatures() -> Array:
	return definition().encounter.creatures.keys()

## One species' entry: {name, recipe, attack, …}. Unknown ids read as the default species.
static func species(creature: String) -> Dictionary:
	var all: Dictionary = definition().encounter.creatures
	return all.get(creature, all[str(definition().encounter.creature)])

## The species a run flies for (runs saved before #70 chase the default one).
static func creature_of(run: Dictionary) -> String:
	var id := str(run.get("creature", ""))
	return id if definition().encounter.creatures.has(id) else str(definition().encounter.creature)

## The species the next departure will meet: at random among those whose recipe
## is still undiscovered, then among all (issue #27's rule, in its simplest form).
static func next_creature(state: Dictionary) -> String:
	var known: Array = state.get("recipe_book", {}).get("discovered", [])
	var pool: Array = creatures().filter(func(id): return not str(species(id).recipe) in known)
	if pool.is_empty(): pool = creatures()
	var data: Dictionary = state.expedition
	return str(pool[mini(pool.size() - 1, int(Route.cell_hash(int(data.sequence), int(data.seed_base), 67) * pool.size()))])

## Whether the ink may cover a chunk: an ordinary chunk that passes the sight check.
static func ink_fair(chunk: Dictionary) -> bool:
	if str(chunk.kind) != "normal": return false
	if not _sight.has(chunk.id): _sight[chunk.id] = Sight.problems(chunk.rows, definition()).is_empty()
	return _sight[chunk.id]

## Library for one creature's route: its own creature chunks, no other species'.
## The Inkfin has no chunks of its own: its ink falls on ordinary chunks, so its
## library leaves out any ordinary chunk that fails the sight check.
static func _library_for(creature: String) -> Array:
	if str(species(creature).attack) == "ink":
		return library().filter(func(c): return c.kind != "creature" and (c.kind != "normal" or ink_fair(c)))
	return library().filter(func(c): return c.kind != "creature" or str(c.get("creature")) == creature)

## Assembled grid, spans, gold and features for a seed and species (cached).
static func route(seed_value: int, creature := "") -> Dictionary:
	var version := int(definition().route_version)
	creature = creature_of({"creature": creature})
	var inked: bool = str(species(creature).attack) == "ink"
	var cache_key := "%d:%d:%s" % [seed_value, version, creature]
	if not _routes.has(cache_key):
		# The Inkfin's creature slots are ordinary chunks: its ink zones.
		var slots: Array = definition().plan
		var plan: Array = slots.map(func(slot): return float(definition().encounter.ink.chunk_difficulty) if inked and slot is String and slot == "creature" else slot)
		var sequence := Route.generate(seed_value, _library_for(creature), plan)
		var assembled := Route.assemble(sequence)
		if inked:
			for i in range(mini(slots.size(), assembled.spans.size())):
				if slots[i] is String and slots[i] == "creature": assembled.spans[i].ink = true
		assembled = _with_arena(assembled, seed_value, int(definition().encounter.pursuit_chunks))
		var pickups: Array = []
		for y in range(assembled.rows.size()):
			var row: String = assembled.rows[y]
			for x in range(row.length()):
				if row[x] == "$": pickups.append(Vector2(x + 0.5, y + 0.5))
		var launch_top := float(assembled.rows.size()) - 0.5
		var encounter_edge := 0.0
		var arena = null
		for span in assembled.spans:
			if span.kind == "launch": launch_top = minf(launch_top, float(span.y0))
			# Shields never reach the encounter arena.
			if span.kind == "finish" and arena == null: encounter_edge = float(span.y1) + 1.0
			if span.kind == "encounter":
				arena = {"y0": int(span.y0), "y1": int(span.y1)}
				encounter_edge = float(span.y1) + 1.0
		var currents := {}
		var shields: Array = []
		var portals: Array = []
		var spans: Array = assembled.spans
		# Issue #25: where the creature may discharge, with each chunk's fair strikes.
		var zones: Array = []
		var by_id := {}
		for c in library(): by_id[c.id] = c
		for i in range(spans.size()):
			if spans[i].kind == "creature": zones.append({"span": i, "id": spans[i].id, "y0": int(spans[i].y0), "y1": int(spans[i].y1), "strikes": by_id[spans[i].id].discharge.strikes})
		# Issue #70: where the Inkfin blacks out the sea. The ink lingers into the
		# next chunk (`end`), but only when that chunk passes the sight check too.
		var ink_zones: Array = []
		for i in range(spans.size()):
			if not spans[i].get("ink", false): continue
			var linger := 0
			var after: Dictionary = spans[i + 1] if i + 1 < spans.size() else {}
			if not after.is_empty() and by_id.has(after.id) and ink_fair(by_id[after.id]):
				linger = mini(int(definition().encounter.ink.linger_rows), int(after.y1) - int(after.y0) + 1)
			ink_zones.append({"span": i, "id": spans[i].id, "y0": int(spans[i].y0), "y1": int(spans[i].y1), "end": int(spans[i].y0) - linger})
		for i in range(spans.size()):
			var span: Dictionary = spans[i]
			if span.kind == "encounter": continue
			for p in _doc(str(span.id)).get("placements", []):
				var x := int(p.x)
				var y := int(span.y0) + int(p.y)
				match [str(p.get("layer")), str(p.get("object"))]:
					["currents", "current-east"]: currents[Vector2i(x, y)] = 1
					["currents", "current-west"]: currents[Vector2i(x, y)] = -1
					["features", "boost"]: shields.append(Vector2(x + 0.5, y + 0.5))
					["features", "portal-ring"]:
						# Rejoin at the entry row of the chunk after the skipped one(s).
						var rejoin: Dictionary = spans[mini(spans.size() - 1, i + 1 + int(definition().passage_rejoin_skips_chunks))]
						var row := int(rejoin.y1)
						portals.append({"x": x + 0.5, "y": y + 0.5, "rejoin": Vector2(_centre_of(assembled.rows[row]), row + 0.5)})
		_routes[cache_key] = {"rows": assembled.rows, "spans": spans, "pickups": pickups, "columns": Route.COLUMNS, "launch_top": launch_top,
			"currents": currents, "shields": shields, "portals": portals, "encounter_edge": encounter_edge, "version": version, "zones": zones, "ink_zones": ink_zones, "creature": creature,
			"arena": arena, "encounter_start": (float(arena.y1) + 1.0 - float(definition().encounter.window_opens_rows_into_arena)) if arena != null else null}
	return _routes[cache_key]

## Open water between the last challenge and the finish where the creature
## encounter plays out: seven open columns (the finish chunk's width), quiet
## decor along the walls, narrowing into the finish's three-wide entry.
## From version 4 the arena sits `pursuit_chunks` ordinary chunks before the
## finish, so a hooked chase runs through real terrain, and it opens fully.
static func _with_arena(assembled: Dictionary, seed_value: int, pursuit_chunks := 0) -> Dictionary:
	var spans: Array = assembled.spans
	var finish: Dictionary = spans[spans.size() - 1 - pursuit_chunks]
	var count := int(definition().encounter.arena_rows)
	var rng := Route.Mulberry32.new(seed_value * 53 + 23)
	var arena: Array = []
	for y in range(count):
		var row := "###.....###" if y == 0 and pursuit_chunks == 0 else "##.......##"
		if y > 1:
			for x in [2, 8]:
				if rng.next() < 0.12: row = row.substr(0, x) + "," + row.substr(x + 1)
		arena.append(row)
	var at := int(finish.y1) + 1
	var rows: Array = assembled.rows.slice(0, at) + arena + assembled.rows.slice(at)
	var shifted: Array = []
	for span in spans:
		var copy: Dictionary = span.duplicate()
		if int(copy.y0) >= at: copy.y0 = int(copy.y0) + count; copy.y1 = int(copy.y1) + count
		shifted.append(copy)
	shifted.insert(shifted.size() - 1 - pursuit_chunks, {"id": "arena", "kind": "encounter", "difficulty": null, "y0": at, "y1": at + count - 1})
	return {"rows": rows, "spans": shifted}

## Raw chunk document, for the feature layers route.gd does not read.
static func _doc(id: String) -> Dictionary:
	if not _docs.has(id):
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(Route.CHUNK_DIR.path_join(id + ".json")))
		_docs[id] = parsed if parsed is Dictionary else {}
	return _docs[id]

## Centre of the open run nearest the middle of a row.
static func _centre_of(row: String) -> float:
	var best: Array = Route.runs(row)[0]
	for run in Route.runs(row):
		if absf((run[0] + run[1] + 1) / 2.0 - Route.COLUMNS / 2.0) < absf((best[0] + best[1] + 1) / 2.0 - Route.COLUMNS / 2.0): best = run
	return (best[0] + best[1] + 1) / 2.0

## Bonus passage behind a portal: a winding three-wide channel with gold every
## few rows, seeded by the run and portal. The ride follows its centre.
static func passage(seed_value: int, portal: int, ride_rows := -1) -> Dictionary:
	var rules := definition()
	var count := int(rules.passage_rows) if ride_rows < 0 else ride_rows
	var cache_key := "%d:%d:%d" % [seed_value, portal, count]
	if not _passages.has(cache_key):
		var rng := Route.Mulberry32.new(seed_value * 101 + portal * 7 + 3)
		var info := {"rows_count": count, "phase": rng.next() * 6.0, "amp": 1.6 + rng.next() * 0.6}
		var rows: Array = []
		var pickups: Array = []
		for y in range(count):
			var c := passage_centre(info, y)
			var wide := 2 if y < 3 or y > count - 4 else 1
			var row := ""
			for x in range(Route.COLUMNS):
				var inside := absf(x + 0.5 - c) <= wide + 0.5
				var gold := inside and absf(x + 0.5 - c) < 0.5 and y > 3 and y < count - 4 and y % int(rules.passage_gold_every_rows) == 0
				var decor := inside and not gold and rng.next() < 0.12
				row += ("$" if gold else ("," if decor else ".")) if inside else "#"
				if gold: pickups.append(Vector2(x + 0.5, y + 0.5))
			rows.append(row)
		info.rows = rows; info.pickups = pickups
		_passages[cache_key] = info
	return _passages[cache_key]

static func passage_centre(info: Dictionary, y: float) -> float:
	var count := float(info.rows_count)
	return Route.COLUMNS / 2.0 + float(info.amp) * sin(y * 0.24 + float(info.phase)) * minf(1.0, minf(y, count - 1.0 - y) / 4.0)

## The route a run flies.
static func run_route(run: Dictionary) -> Dictionary:
	return route(int(run.seed), creature_of(run))

## Preparation cruise: rows the ship may cover before Start, ending in a hover.
static func launch(seed_value: int, creature := "") -> Dictionary:
	var path := route(seed_value, creature)
	var bottom := float(path.rows.size()) - 0.5
	var hover := minf(bottom, float(path.launch_top) + float(definition().launch_hover_rows))
	return {"x": _start_x(path.rows), "bottom": bottom, "hover": hover}

static func initialize(state: Dictionary, seed_value: int) -> void:
	state.expedition = {"charge": {"ready": true, "recharge_started": null}, "salvage": 0, "sequence": 0,
		"seed_base": posmod(seed_value * 7919 + 17, 2147483647), "run": null, "result": null}

# ------------------------------------------------------------ views

## Battery at wall-clock `now` (unix seconds): ready, or seconds until full.
static func charge(state: Dictionary, now: float) -> Dictionary:
	var data: Dictionary = state.expedition.charge
	if data.ready: return {"ready": true, "remaining": 0.0, "fraction": 1.0}
	if data.recharge_started == null: return {"ready": false, "remaining": INF, "fraction": 0.0}
	var total := float(definition().recharge_seconds)
	# A clock moved backwards never lengthens the wait beyond one full night.
	var elapsed := clampf(now - float(data.recharge_started), 0.0, total)
	return {"ready": elapsed >= total, "remaining": total - elapsed, "fraction": elapsed / total}

static func snapshot(state: Dictionary, store = null) -> Dictionary:
	var data: Dictionary = state.expedition.duplicate(true)
	if data.run is Dictionary:
		var run: Dictionary = data.run
		run.shield = shield(store)
		var hull_max := float(gear(run).hull)
		run.hull_max = hull_max
		run.hull_fraction = clampf(float(run.hull) / hull_max, 0.0, 1.0)
		run.low_hull = run.hull_fraction <= float(definition().low_hull_fraction)
		run.rows = run_route(run).rows.size()
	data.next_seed = next_seed(state)
	data.next_creature = next_creature(state)
	return data

## The route the next departure will take (preparation previews it).
static func next_seed(state: Dictionary) -> int:
	var data: Dictionary = state.expedition
	return 1 + posmod(int(Route.cell_hash(int(data.sequence), int(data.seed_base), 61) * 2147483646.0), 2147483646)

# ------------------------------------------------------------ commands

static func command(config: Dictionary, state: Dictionary, request: Dictionary, store = null) -> Dictionary:
	var data: Dictionary = state.expedition
	var run = data.run
	match request.get("type"):
		"expedition_start":
			if not _finite(request.get("now")): return {"ok": false, "reason": "invalid_time"}
			if run != null: return {"ok": false, "reason": "expedition_active"}
			if data.result != null: return {"ok": false, "reason": "results_pending"}
			if not charge(state, float(request.now)).ready: return {"ok": false, "reason": "charging"}
			var seed_value: int
			# A chosen seed (tests, galleries) meets the default species unless it names one.
			var creature := str(definition().encounter.creature)
			if request.has("creature"):
				if not request.creature is String or not definition().encounter.creatures.has(request.creature): return {"ok": false, "reason": "invalid_creature"}
				creature = str(request.creature)
			elif not request.has("seed"):
				creature = next_creature(state)
			if request.has("seed"):
				if not _integer(request.seed) or int(request.seed) < 1: return {"ok": false, "reason": "invalid_seed"}
				seed_value = int(request.seed)
			else:
				seed_value = next_seed(state)
			var path := route(seed_value, creature)
			if path.rows.is_empty(): return {"ok": false, "reason": "no_route"}
			var start_x: float = _start_x(path.rows)
			var lead := launch(seed_value, creature)
			var start_y: float = lead.bottom
			if request.has("y"):
				if not _finite(request.y) or float(request.y) < float(lead.hover) - 0.001 or float(request.y) > float(lead.bottom) + 0.001: return {"ok": false, "reason": "invalid_start"}
				start_y = float(request.y)
			data.charge = {"ready": false, "recharge_started": null}
			data.sequence = int(data.sequence) + 1
			var fitted := WorkshopBook.gear(state)
			data.run = {"id": int(data.sequence), "seed": seed_value, "y": start_y, "x": start_x, "steer": 0.0, "vx": 0.0,
				"hull": float(fitted.hull), "gear": fitted, "salvage": 0, "collected": [], "protection": 0.0, "paused": false, "elapsed": 0.0, "impacts": 0,
				"route_version": int(definition().route_version), "shields_taken": [], "portals_used": [], "passage": null, "passage_pickups": 0,
				"encounter": null, "creature": creature}
			# Each run starts a fresh transient world.
			store.drop_world(WORLD)
			store.create_world(WORLD)
			# Shield at start: the run launches already shielded.
			if float(fitted.launch) > 0.0: set_shield(store, float(fitted.launch))
			return {"ok": true, "changed": true, "seed": seed_value, "id": data.run.id, "launch_shield": float(fitted.launch), "creature": creature}
		"expedition_steer":
			if run == null or run.paused: return {"ok": false, "reason": "not_travelling"}
			if not _finite(request.get("input")): return {"ok": false, "reason": "invalid_steer"}
			run.steer = clampf(float(request.input), -1.0, 1.0)
			return {"ok": true}
		"expedition_advance":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			if not _finite(request.get("elapsed")) or float(request.elapsed) < 0.0 or not _finite(request.get("now")): return {"ok": false, "reason": "invalid_time"}
			return {"ok": true, "events": _advance(config, state, float(request.elapsed), float(request.now), store)}
		"expedition_fire":
			if run == null or run.paused: return {"ok": false, "reason": "not_travelling"}
			var encounter = run.get("encounter")
			if not encounter is Dictionary or encounter.state != "aiming": return {"ok": false, "reason": "no_target"}
			if encounter.harpoon != null or float(encounter.cooldown) > 0.0: return {"ok": false, "reason": "reloading"}
			# Straight up from the ship's nose; the shot keeps its column.
			encounter.harpoon = {"state": "flying", "x": float(run.x), "d": 0.0}
			encounter.cooldown = float(definition().encounter.cooldown_seconds)
			encounter.shots = int(encounter.shots) + 1
			return {"ok": true, "shot": int(encounter.shots)}
		# Debug cheats: the presentation offers these only behind the single
		# `cheats` flag (branding.json or --cheats); the rules stay deterministic.
		"expedition_cheat_shield":
			if run == null or run.paused or run.passage != null: return {"ok": false, "reason": "not_travelling"}
			if float(run.y) <= float(run_route(run).encounter_edge) + 0.5: return {"ok": false, "reason": "no_shields_here"}
			set_shield(store, float(gear(run).shield))
			return {"ok": true, "events": [{"type": "shield", "index": -1, "x": run.x, "y": run.y}]}
		"expedition_cheat_encounter":
			if run == null or run.paused or run.passage != null: return {"ok": false, "reason": "not_travelling"}
			var arena = run_route(run).arena
			if not arena is Dictionary or run.encounter != null: return {"ok": false, "reason": "no_encounter"}
			if float(run.y) <= float(arena.y1) + 0.5: return {"ok": false, "reason": "already_there"}
			run.y = float(arena.y1) + 0.5; run.x = 5.5; run.vx = 0.0; set_shield(store, 0.0); run.protection = 0.0
			return {"ok": true}
		"expedition_cheat_zone":
			# Debug: skip ahead to the entry of the next creature chunk while hooked.
			if run == null or run.paused or not _hooked(run): return {"ok": false, "reason": "not_hooked"}
			var done: Array = run.encounter.get("inked", [])
			var ahead: Array = (run_route(run).zones + run_route(run).ink_zones).filter(func(z): return float(z.y0) < float(run.y) - 1.0 and not int(z.y0) in done)
			if ahead.is_empty(): return {"ok": false, "reason": "no_zone_ahead"}
			var zone: Dictionary = ahead.reduce(func(a, b): return a if int(a.y0) > int(b.y0) else b)
			var rows: Array = run_route(run).rows
			run.y = float(zone.y1) + 0.6; run.x = _centre_of(str(rows[int(zone.y1)])); run.vx = 0.0; run.protection = 0.0
			run.encounter.discharge = null; run.encounter.discharge_cooldown = 0.0; run.encounter.ink = null
			return {"ok": true}
		"expedition_cheat_catch":
			if run == null or run.paused or not _hooked(run): return {"ok": false, "reason": "not_hooked"}
			run.encounter.resistance = minf(float(run.encounter.resistance), 1.0)
			return {"ok": true}
		"expedition_pause":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			# A paused ship lets go of the stick; it resumes running straight.
			run.paused = true; run.steer = 0.0; run.vx = 0.0
			return {"ok": true}
		"expedition_resume":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			run.paused = false
			return {"ok": true}
		"expedition_give_up":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			if not run.paused: return {"ok": false, "reason": "pause_required"}
			if not _finite(request.get("now")): return {"ok": false, "reason": "invalid_time"}
			return {"ok": true, "result": _end(config, state, "gave_up", float(request.now))}
		"expedition_acknowledge":
			if data.result == null: return {"ok": true, "changed": false}
			if request.get("id") != null and int(request.id) != int(data.result.id): return {"ok": false, "reason": "stale_result"}
			data.result = null
			return {"ok": true, "changed": true}
	return {"ok": false, "reason": "unknown_command"}

static func _start_x(rows: Array) -> float:
	var bottom: String = rows[rows.size() - 1]
	var best: Array = Route.runs(bottom)[0]
	for run in Route.runs(bottom):
		if absf((run[0] + run[1] + 1) / 2.0 - Route.COLUMNS / 2.0) < absf((best[0] + best[1] + 1) / 2.0 - Route.COLUMNS / 2.0): best = run
	return (best[0] + best[1] + 1) / 2.0

static func _advance(config: Dictionary, state: Dictionary, elapsed: float, now: float, store = null) -> Array:
	var data: Dictionary = state.expedition
	var run: Dictionary = data.run
	var events: Array = []
	if run.paused or elapsed <= 0.0: return events
	var rules := definition()
	var path := run_route(run)
	var reach := float(rules.ship_radius)
	# The Collector's reach: salvage within it is drawn in (base reach is the pickup radius).
	var radius := maxf(float(rules.pickup_radius), float(gear(run).collector))
	var per := int(rules.salvage_per_pickup)
	# Sub-steps keep a frame hitch from tunnelling through a one-cell rock.
	var remaining := elapsed
	while remaining > 0.0:
		var dt := minf(remaining, 0.05)
		remaining -= dt
		run.elapsed = float(run.elapsed) + dt
		run.protection = maxf(0.0, float(run.protection) - dt)
		if run.passage != null:
			# Safe ride: the passage current carries the ship along the channel
			# centre; steering has no effect and nothing damages the hull.
			var ride: Dictionary = run.passage
			var info := passage(int(run.seed), int(ride.portal), int(gear(run).passage))
			ride.y = float(ride.y) - float(rules.passage_forward_rows_per_second) * dt
			ride.x = passage_centre(info, float(ride.y))
			run.vx = 0.0
			for i in range(info.pickups.size()):
				if i in ride.collected: continue
				var g: Vector2 = info.pickups[i]
				if absf(g.x - float(ride.x)) <= radius and absf(g.y - float(ride.y)) <= radius:
					ride.collected.append(i)
					run.passage_pickups = int(run.passage_pickups) + 1
					run.salvage = int(run.salvage) + per
					events.append({"type": "pickup", "passage": true, "index": i, "x": g.x, "y": g.y, "value": per})
			if float(ride.y) <= float(rules.passage_ride_rows):
				var portal: Dictionary = path.portals[int(ride.portal)]
				var rejoin: Vector2 = portal.rejoin
				events.append({"type": "passage_exit", "portal": int(ride.portal), "from_x": ride.x, "from_y": ride.y, "x": rejoin.x, "y": rejoin.y})
				run.passage = null; run.x = rejoin.x; run.y = rejoin.y
				# The rest of this step belongs to the exit transition.
				return events
			continue
		if _encounter_step(run, path, dt, events, store): continue
		var shielded := shield(store) > 0.0
		run.y = float(run.y) - float(rules.forward_rows_per_second) * pursuit_speed(run) * dt
		if shielded:
			store.tick_effects(WORLD, dt)
			# The shield always ends before the encounter.
			if float(run.y) <= float(path.encounter_edge) + 0.5: set_shield(store, 0.0)
			if shield(store) <= 0.0: events.append({"type": "shield_end"})
		var want := float(run.steer) * float(rules.lateral_columns_per_second)
		run.vx = move_toward(float(run.vx), want, float(rules.lateral_acceleration) * dt)
		# A current adds to steering; letting go removes only the player's part.
		var push := float(path.currents.get(Vector2i(floori(float(run.x)), floori(float(run.y))), 0)) * float(rules.current_columns_per_second)
		run.x = float(run.x) + (float(run.vx) + push) * dt
		if float(run.x) < 0.4 or float(run.x) > Route.COLUMNS - 0.4:
			run.x = clampf(float(run.x), 0.4, Route.COLUMNS - 0.4); run.vx = 0.0
		for i in range(path.pickups.size()):
			if i in run.collected: continue
			var p: Vector2 = path.pickups[i]
			if absf(p.x - float(run.x)) <= radius and absf(p.y - float(run.y)) <= radius:
				run.collected.append(i)
				run.salvage = int(run.salvage) + per
				events.append({"type": "pickup", "index": i, "x": p.x, "y": p.y, "value": per})
		for i in range(path.shields.size()):
			var b: Vector2 = path.shields[i]
			if i in run.shields_taken or float(run.y) <= float(path.encounter_edge) + 0.5: continue
			if absf(b.x - float(run.x)) <= float(rules.shield_radius) and absf(b.y - float(run.y)) <= float(rules.shield_radius):
				run.shields_taken.append(i)
				set_shield(store, float(gear(run).shield))
				events.append({"type": "shield", "index": i, "x": b.x, "y": b.y})
		for i in range(path.portals.size()):
			var portal: Dictionary = path.portals[i]
			if i in run.portals_used: continue
			if absf(float(portal.x) - float(run.x)) <= float(rules.portal_radius) and absf(float(portal.y) - float(run.y)) <= float(rules.portal_radius):
				# Entering spends the portal first, so a save can never repeat it.
				run.portals_used.append(i)
				set_shield(store, 0.0); run.vx = 0.0
				var info := passage(int(run.seed), i, int(gear(run).passage))
				var start_y := float(info.rows_count) - float(rules.passage_ride_rows)
				run.passage = {"portal": i, "y": start_y, "x": passage_centre(info, start_y), "collected": []}
				events.append({"type": "passage_enter", "portal": i, "from_x": portal.x, "from_y": portal.y, "x": run.passage.x, "y": start_y})
				return events
		if _collides(path.rows, float(run.x), float(run.y), reach):
			# Rock is solid, shield or not: the ship is knocked back to the closest clear water.
			var from := Vector2(float(run.x), float(run.y))
			var to := _nearest_clear(path.rows, from, reach + float(rules.knockback_clearance))
			run.x = to.x; run.y = to.y
			# Only a sideways knock against the ship's motion stops it: pressed into a
			# wall ahead, steering keeps its speed and slides along, even against a current.
			if absf(to.x - from.x) > 0.001 and signf(to.x - from.x) != signf(float(run.vx)): run.vx = 0.0
			if shield(store) > 0.0:
				# The shield takes the knock without damage; a short guard keeps the feedback from repeating every step.
				if float(run.protection) <= 0.0:
					run.protection = 0.3
					events.append({"type": "shield_bump", "x": run.x, "y": run.y, "from_x": from.x, "from_y": from.y})
				else:
					events.append({"type": "bump", "x": run.x, "y": run.y, "from_x": from.x, "from_y": from.y})
			else:
				# Only the first touch dents the hull; hit protection keeps later bumps free.
				if float(run.protection) <= 0.0:
					run.hull = maxf(0.0, float(run.hull) - float(rules.impact_damage))
					run.protection = float(rules.hit_protection_seconds)
					run.impacts = int(run.impacts) + 1
					events.append({"type": "impact", "x": run.x, "y": run.y, "from_x": from.x, "from_y": from.y, "hull": run.hull})
					if float(run.hull) <= 0.0:
						# A hooked creature gets away for good: the cable snaps.
						var lost := {"id": creature_of(run), "outcome": "escaped"} if _hooked(run) else {}
						if not lost.is_empty(): events.append({"type": "creature_lost"})
						events.append({"type": "ended", "result": _end(config, state, "hull_depleted", now, lost)})
						return events
				else:
					events.append({"type": "bump", "x": run.x, "y": run.y, "from_x": from.x, "from_y": from.y})
		if _hooked(run):
			if str(species(creature_of(run)).attack) == "ink": _ink_step(run, path, dt, events)
			elif _discharge_step(config, state, run, path, dt, events, now): return events
		if _hooked(run) and (float(run.encounter.resistance) <= 0.0 or float(run.y) <= 0.5):
			events.append_array(_catch(config, state, now))
			return events
		if float(run.y) <= 0.5:
			events.append({"type": "ended", "result": _end(config, state, "complete", now)})
			return events
	return events

## Pursuit travel speed: ramps from 1 to the multiplier after the hook.
static func pursuit_speed(run: Dictionary) -> float:
	if not _hooked(run): return 1.0
	var rules: Dictionary = definition().encounter
	var k := clampf(float(run.encounter.chase_t) / float(rules.pursuit_ramp_seconds), 0.0, 1.0)
	return lerpf(1.0, float(rules.pursuit_speed_multiplier), k)

static func _hooked(run: Dictionary) -> bool:
	var encounter = run.get("encounter")
	return encounter is Dictionary and encounter.state == "hooked"

## Zero resistance: the catch and the recipe discovery commit before anything
## is presented, then the run ends as complete (hazards are over).
static func _catch(config: Dictionary, state: Dictionary, now: float) -> Array:
	var run: Dictionary = state.expedition.run
	var rules: Dictionary = definition().encounter
	var recipe := str(species(creature_of(run)).recipe)
	var first: bool = not recipe in state.recipe_book.discovered
	RecipeBook.command(config, state, {"type": "discover_recipe", "recipe_id": recipe})
	var centre := creature_centre(run)
	var caught := {"id": creature_of(run), "outcome": "caught", "recipe": recipe, "first": first}
	return [{"type": "caught", "x": centre.x, "y": centre.y, "first": first, "recipe": recipe},
		{"type": "ended", "result": _end(config, state, "complete", now, caught)}]

# ------------------------------------------------------------ encounter (#23)

## Advance the encounter by one step. Always returns false: travel continues
## (a hooked creature is chased, at pursuit speed).
static func _encounter_step(run: Dictionary, path: Dictionary, dt: float, events: Array, store = null) -> bool:
	var rules: Dictionary = definition().encounter
	var encounter = run.get("encounter")
	if encounter == null:
		if path.get("encounter_start") == null or float(run.y) > float(path.encounter_start): return false
		encounter = {"state": "aiming", "t": 0.0, "cooldown": 0.0, "harpoon": null, "shots": 0, "x": Route.COLUMNS / 2.0, "hook": null}
		run.encounter = encounter
		set_shield(store, 0.0)
		events.append({"type": "encounter_start"})
	encounter.t = float(encounter.t) + dt
	if encounter.state == "hooked":
		# Pursuit: resistance is the creature's health and only drains.
		encounter.chase_t = float(encounter.chase_t) + dt
		encounter.resistance = maxf(0.0, float(encounter.resistance) - float(rules.resistance_drain_per_second) * float(gear(run).harpoon) * dt)
		# It weaves, but holds over its strip while discharging (#25).
		var weave := Route.COLUMNS / 2.0 + float(rules.weave_columns) * sin(TAU * float(encounter.t) / float(rules.weave_period_seconds))
		var strike = encounter.get("discharge")
		var goal := float(strike.x0) + float(strike.w) / 2.0 if strike is Dictionary else weave
		encounter.x = move_toward(float(encounter.x), goal, float(rules.discharge.glide_columns_per_second) * dt)
		return false
	if encounter.state == "aiming": encounter.x = Route.COLUMNS / 2.0 + float(rules.weave_columns) * sin(TAU * float(encounter.t) / float(rules.weave_period_seconds))
	encounter.cooldown = maxf(0.0, float(encounter.cooldown) - dt)
	var shot = encounter.harpoon
	if shot is Dictionary:
		if shot.state == "flying":
			var from := float(shot.d)
			shot.d = from + float(rules.harpoon_rows_per_second) * dt
			if encounter.state == "aiming":
				# Sample the swept segment so a long frame cannot pass through the body.
				var steps := maxi(1, int(ceil((float(shot.d) - from) / 0.25)))
				for i in range(1, steps + 1):
					var d := lerpf(from, float(shot.d), float(i) / steps)
					var hit = _hit_point(run, float(shot.x), d)
					if hit != null:
						shot.d = d; shot.state = "attached"
						encounter.state = "hooked"; encounter.hook = hit
						encounter.resistance = float(rules.resistance); encounter.chase_t = 0.0
						encounter.discharge = null; encounter.discharge_cooldown = 0.0; encounter.strikes = 0
						encounter.ink = null; encounter.inked = []
						events.append({"type": "hooked", "along": hit.along, "across": hit.across})
						return false
			if float(shot.d) >= float(rules.harpoon_range_rows):
				shot.state = "reeling"; events.append({"type": "harpoon_missed"})
		elif shot.state == "reeling":
			shot.d = float(shot.d) - float(rules.reel_rows_per_second) * dt
			if float(shot.d) <= 0.0: encounter.harpoon = null
	# The window closes once nothing is in flight; a shot on its way still counts.
	if encounter.state == "aiming" and float(encounter.t) >= float(rules.window_seconds) and encounter.harpoon == null:
		encounter.state = "escaped"; encounter.escaped_at = float(encounter.t)
		events.append({"type": "creature_escaped"})
	return false

# ------------------------------------------------------------ discharge (#25)

## The hooked creature's discharge for one step. Returns true when a strike
## ended the run (zero hull). A windup starts only inside a creature chunk, at
## full chase speed, when the coming strike row is in the chunk's table.
static func _discharge_step(config: Dictionary, state: Dictionary, run: Dictionary, path: Dictionary, dt: float, events: Array, now: float) -> bool:
	var rules := definition()
	var d: Dictionary = rules.encounter.discharge
	var encounter: Dictionary = run.encounter
	encounter.discharge_cooldown = maxf(0.0, float(encounter.get("discharge_cooldown", 0.0)) - dt)
	var strike = encounter.get("discharge")
	if strike is Dictionary:
		strike.t = float(strike.t) + dt
		if strike.phase == "windup" and float(strike.t) >= float(d.warn_seconds):
			strike.phase = "strike"; events.append({"type": "discharge_strike", "x0": int(strike.x0), "w": int(strike.w)})
		if strike.phase == "strike":
			var centre := float(strike.x0) + float(strike.w) / 2.0
			if float(run.protection) <= 0.0 and absf(float(run.x) - centre) < float(strike.w) / 2.0 + float(d.hit_slack_columns):
				# Lightning: hull only, with the usual hit protection; no knock-back.
				run.hull = maxf(0.0, float(run.hull) - float(d.damage))
				run.protection = float(rules.hit_protection_seconds)
				run.impacts = int(run.impacts) + 1
				events.append({"type": "zapped", "x": run.x, "y": run.y, "hull": run.hull})
				if float(run.hull) <= 0.0:
					events.append({"type": "creature_lost"})
					events.append({"type": "ended", "result": _end(config, state, "hull_depleted", now, {"id": creature_of(run), "outcome": "escaped"})})
					return true
			if float(strike.t) >= float(d.warn_seconds) + float(d.active_seconds):
				encounter.discharge = null
				encounter.strikes = int(encounter.get("strikes", 0)) + 1
				var cooldown: Array = d.cooldown_seconds
				encounter.discharge_cooldown = lerpf(float(cooldown[0]), float(cooldown[1]), Route.cell_hash(int(run.seed), int(encounter.strikes), 26))
				events.append({"type": "discharge_end"})
		return false
	if float(encounter.discharge_cooldown) > 0.0 or pursuit_speed(run) < float(rules.encounter.pursuit_speed_multiplier) - 1e-6: return false
	var zone = null
	for z in path.get("zones", []):
		if float(run.y) >= float(z.y0) and float(run.y) < float(z.y1) + 1.0: zone = z
	if zone == null: return false
	var strike_row := float(run.y) - float(zone.y0) - float(d.warn_seconds) * Discharge.chase_rows_per_second(rules)
	var entry = null
	for s in zone.strikes:
		if absf(float(s.row) - strike_row) <= float(d.fairness.row_step) / 2.0: entry = s
	if entry == null: return false
	# One fixed strip from the fair choices near the ship, leaning towards it.
	var x := float(run.x)
	var pool: Array = entry.fair.filter(func(s): return absf(float(s[0]) + float(s[1]) / 2.0 - x) <= float(d.aim_reach_columns))
	if pool.is_empty(): return false
	var spread := float(d.aim_spread_columns)
	var weights: Array = pool.map(func(s): return exp(-pow(float(s[0]) + float(s[1]) / 2.0 - x, 2) / (2.0 * spread * spread)))
	var r: float = Route.cell_hash(int(run.seed), int(encounter.get("strikes", 0)), 25) * float(weights.reduce(func(a, b): return a + b, 0.0))
	var pick: Array = pool[pool.size() - 1]
	for i in range(pool.size()):
		r -= float(weights[i])
		if r <= 0.0: pick = pool[i]; break
	encounter.discharge = {"phase": "windup", "t": 0.0, "x0": int(pick[0]), "w": int(pick[1]), "zone": int(zone.span), "row": float(entry.row)}
	events.append({"type": "discharge_windup", "x0": int(pick[0]), "w": int(pick[1])})
	return false

# ------------------------------------------------------------ ink (#70)

## The hooked Inkfin's ink for one step. One burst per ink zone, starting as
## the ship enters it at full chase speed: a warning with the sea still in
## view, then the ink seeps in and holds until the ship's clear sight reaches
## where the ink ends (the zone's top plus the rows it lingers), then lifts.
static func _ink_step(run: Dictionary, path: Dictionary, dt: float, events: Array) -> void:
	var rules := definition()
	var k: Dictionary = rules.encounter.ink
	var encounter: Dictionary = run.encounter
	var ink = encounter.get("ink")
	if ink is Dictionary:
		ink.t = float(ink.t) + dt
		if ink.phase == "warn" and float(ink.t) >= float(k.warn_seconds):
			ink.phase = "spread"; ink.t = 0.0; events.append({"type": "ink_spread"})
		elif ink.phase == "spread" and float(ink.t) >= float(k.spread_seconds):
			ink.phase = "hold"; ink.t = 0.0
		if ink.phase in ["spread", "hold"] and float(run.y) - float(ink.end) < float(k.clear_rows):
			# A lift that interrupts the spread starts from the cover reached so far.
			ink["from"] = ink_cover(run); ink.phase = "lift"; ink.t = 0.0; events.append({"type": "ink_lift"})
		if ink.phase == "lift" and float(ink.t) >= float(k.lift_seconds):
			encounter.ink = null; events.append({"type": "ink_end"})
		return
	if pursuit_speed(run) < float(rules.encounter.pursuit_speed_multiplier) - 1e-6: return
	var done: Array = encounter.get("inked", [])
	for zone in path.get("ink_zones", []):
		if float(run.y) < float(zone.y0) or float(run.y) >= float(zone.y1) + 1.0 or int(zone.y0) in done: continue
		if float(zone.y1) + 1.0 - float(run.y) < float(k.entry_rows): continue
		done.append(int(zone.y0)); encounter.inked = done
		encounter.ink = {"phase": "warn", "t": 0.0, "zone": int(zone.span), "end": int(zone.end), "from": 1.0}
		events.append({"type": "ink_warn"})
		return

## How much ink covers the sea, 0 (clear) to 1 (full).
static func ink_cover(run: Dictionary) -> float:
	var encounter = run.get("encounter")
	var ink = encounter.get("ink") if encounter is Dictionary else null
	if not ink is Dictionary: return 0.0
	var k: Dictionary = definition().encounter.ink
	match str(ink.phase):
		"spread": return clampf(float(ink.t) / float(k.spread_seconds), 0.0, 1.0)
		"hold": return 1.0
		"lift": return float(ink.get("from", 1.0)) * clampf(1.0 - float(ink.t) / float(k.lift_seconds), 0.0, 1.0)
	return 0.0

## Creature body centre on the route: ahead of the ship by the lead (arriving
## from further north as the window opens), at its weaving column.
static func creature_centre(run: Dictionary) -> Vector2:
	var encounter = run.get("encounter")
	if not encounter is Dictionary: return Vector2(Route.COLUMNS / 2.0, float(run.y) - float(definition().encounter.lead_rows))
	var rules: Dictionary = definition().encounter
	var k := clampf(float(encounter.t) / float(rules.arrive_seconds), 0.0, 1.0)
	var arrive := float(rules.arrive_rows) * (1.0 - k * k * (3.0 - 2.0 * k))
	return Vector2(float(encounter.x), float(run.y) - float(rules.lead_rows) - arrive)

## Where a harpoon `d` rows past the nose meets the fixed hit ellipse, or null.
## `along` runs -1 (snout, north) to 1 (tail); `across` -1 (west) to 1 (east).
static func _hit_point(run: Dictionary, x: float, d: float) -> Variant:
	var rules: Dictionary = definition().encounter
	var centre := creature_centre(run)
	var tip := float(run.y) - float(rules.nose_rows) - d
	# Each species may carry its own fixed hit ellipse.
	var body := species(creature_of(run))
	var u := (x - centre.x) / float(body.get("hit_half_columns", rules.hit_half_columns))
	var v := (tip - centre.y) / float(body.get("hit_half_rows", rules.hit_half_rows))
	if u * u + v * v > 1.0: return null
	return {"along": v, "across": u}

## Where a flying harpoon will first reach the hit area within `rows` more
## travel (route coordinates), or null. The presentation slows the game and
## focuses on this point for the strike.
static func strike_point(run: Dictionary, rows: float) -> Variant:
	var encounter = run.get("encounter")
	if not encounter is Dictionary or encounter.state != "aiming" or not encounter.harpoon is Dictionary or encounter.harpoon.state != "flying": return null
	var d := float(encounter.harpoon.d)
	var step := 0.0
	while step <= rows:
		if _hit_point(run, float(encounter.harpoon.x), d + step) != null:
			return Vector2(float(encounter.harpoon.x), float(run.y) - float(definition().encounter.nose_rows) - d - step)
		step += 0.2
	return null

## Travel collision: the hull is a circle of radius `reach`; each rock cell is
## a rounded square. Faces open to water sit `rock_inset` inside the cell and
## exposed corners are rounded, so glancing passes are forgiven. Faces shared
## with a neighbouring rock reach across the seam, so a wall of rocks is one
## flat face the ship slides along instead of a row of notches to catch in.
## It stays inside the box chunk validation flies (`_overlaps`).
static func _collides(rows: Array, x: float, y: float, reach: float) -> bool:
	var p := Vector2(x, y)
	for cy in range(int(floor(y - reach - 1.0)), int(floor(y + reach + 1.0)) + 1):
		if cy < 0 or cy >= rows.size(): continue
		for cx in range(int(floor(x - reach - 1.0)), int(floor(x + reach + 1.0)) + 1):
			if cx >= 0 and cx < str(rows[cy]).length() and _rock_at(rows, cx, cy) and _rock_distance(rows, cx, cy, p) < reach: return true
	return false

## Rock for collision shapes; beyond the side columns the canyon wall continues.
static func _rock_at(rows: Array, cx: int, cy: int) -> bool:
	if cy < 0 or cy >= rows.size(): return false
	var row: String = rows[cy]
	if cx < 0 or cx >= row.length(): return true
	return Route.is_rock(row[cx])

## Signed distance from `p` to rock cell (cx, cy)'s rounded-square shape.
static func _rock_distance(rows: Array, cx: int, cy: int, p: Vector2) -> float:
	var rules := definition()
	var inset := float(rules.rock_inset)
	var corner := float(rules.rock_corner_radius)
	# Open faces pull in; faces against another rock overlap it by the corner radius.
	var x0 := cx + (inset if not _rock_at(rows, cx - 1, cy) else -corner)
	var x1 := cx + 1.0 - (inset if not _rock_at(rows, cx + 1, cy) else -corner)
	var y0 := cy + (inset if not _rock_at(rows, cx, cy - 1) else -corner)
	var y1 := cy + 1.0 - (inset if not _rock_at(rows, cx, cy + 1) else -corner)
	var centre := Vector2(x0 + x1, y0 + y1) * 0.5
	var half := Vector2(x1 - x0, y1 - y0) * 0.5
	var q := (p - centre).abs() - (half - Vector2.ONE * corner)
	return Vector2(maxf(q.x, 0.0), maxf(q.y, 0.0)).length() + minf(maxf(q.x, q.y), 0.0) - corner

## The clear spot nearest `at`: sideways or back down the route (never ahead,
## which would skip travel), inside the route's side margins.
static func _nearest_clear(rows: Array, at: Vector2, reach: float) -> Vector2:
	for offset: Vector2 in _knock_offsets():
		var p := at + offset
		if p.x < 0.4 or p.x > Route.COLUMNS - 0.4: continue
		if not _collides(rows, p.x, p.y, reach): return p
	return at

## Knock-back candidates (up to 3 columns aside, 2 rows back), nearest first.
static var _offsets: Array = []
static func _knock_offsets() -> Array:
	if _offsets.is_empty():
		for iy in range(0, 21):
			for ix in range(-60, 61): _offsets.append(Vector2(ix * 0.05, iy * 0.1))
		_offsets.sort_custom(func(a: Vector2, b: Vector2): return a.length_squared() < b.length_squared())
	return _offsets

static func _overlaps(rows: Array, x: float, y: float, half: Vector2) -> bool:
	for cy in range(int(floor(y - half.y)), int(floor(y + half.y)) + 1):
		if cy < 0 or cy >= rows.size(): continue
		var row: String = rows[cy]
		for cx in range(int(floor(x - half.x)), int(floor(x + half.x)) + 1):
			if cx >= 0 and cx < row.length() and Route.is_rock(row[cx]): return true
	return false

## Commit once: bank salvage (+ completion bonus), start the night recharge,
## rotate limited Shop stock and the floor offer, and leave a receipt for the results screen.
static func _end(config: Dictionary, state: Dictionary, outcome: String, now: float, creature := {}) -> Dictionary:
	var data: Dictionary = state.expedition
	var run: Dictionary = data.run
	var bonus := int(definition().completion_bonus) if outcome == "complete" else 0
	var total := int(run.salvage) + bonus
	data.salvage = mini(MAX_INTEGER, int(data.salvage) + total)
	data.result = {"id": int(run.id), "seed": int(run.seed), "outcome": outcome, "pickups": int(run.salvage), "bonus": bonus, "total": total,
		"collected": run.collected.size(), "available": run_route(run).pickups.size()}
	if not creature.is_empty(): data.result.creature = creature
	data.run = null
	data.charge = {"ready": false, "recharge_started": now}
	if state.has("floor_styles"):
		FloorBook.command(config, state, {"type": "floor_refresh", "expected_rotation": state.floor_styles.rotation})
	if state.has("shop"): ShopBook.rotate(state)
	return data.result.duplicate()

# ------------------------------------------------------------ save

static func valid(state: Dictionary) -> bool:
	if not state.get("expedition") is Dictionary: return false
	var data: Dictionary = state.expedition
	if not data.get("charge") is Dictionary or not data.charge.get("ready") is bool: return false
	if data.charge.recharge_started != null and not _finite(data.charge.recharge_started): return false
	if data.charge.ready and data.charge.recharge_started != null: return false
	if not _integer(data.get("salvage")) or not _integer(data.get("sequence")) or not _integer(data.get("seed_base")): return false
	if data.get("run") != null:
		var run = data.run
		if not run is Dictionary: return false
		if data.charge.ready or data.charge.recharge_started != null: return false
		for field in ["y", "x", "hull", "protection", "elapsed"]:
			if not _finite(run.get(field)): return false
		for field in ["steer", "vx"]:
			if run.has(field) and not _finite(run[field]): return false
		if absf(float(run.get("steer", 0.0))) > 1.0: return false
		if not _integer(run.get("id")) or not _integer(run.get("seed")) or int(run.seed) < 1 or not _integer(run.get("salvage")) or not _integer(run.get("impacts")): return false
		if not run.get("paused") is bool or not run.get("collected") is Array: return false
		if run.has("gear") and not _gear_valid(run.gear): return false
		if float(run.hull) <= 0.0 or float(run.hull) > float(gear(run).hull): return false
		if run.has("creature") and (not run.creature is String or not definition().encounter.creatures.has(run.creature)): return false
		if not _features_valid(run): return false
		if not _encounter_valid(run): return false
		var pickups: int = run_route(run).pickups.size()
		var seen := {}
		for index in run.collected:
			if not _integer(index) or int(index) >= pickups or seen.has(int(index)): return false
			seen[int(index)] = true
		if int(run.salvage) != (run.collected.size() + int(run.get("passage_pickups", 0))) * int(definition().salvage_per_pickup): return false
	if data.get("result") != null:
		var result = data.result
		if not result is Dictionary or str(result.get("outcome")) not in OUTCOMES: return false
		for field in ["id", "pickups", "bonus", "total"]:
			if not _integer(result.get(field)): return false
		if int(result.total) != int(result.pickups) + int(result.bonus): return false
		var creature = result.get("creature")
		if creature != null:
			if not creature is Dictionary or str(creature.get("outcome")) not in ["caught", "escaped"] or not creature.get("id") is String: return false
			if creature.outcome == "caught" and (not creature.get("recipe") is String or not creature.get("first") is bool or result.outcome != "complete"): return false
	return true

static func normalize(state: Dictionary) -> void:
	var data: Dictionary = state.expedition
	for field in ["salvage", "sequence", "seed_base"]: data[field] = int(data[field])
	if data.run is Dictionary:
		for field in ["id", "seed", "salvage", "impacts"]: data.run[field] = int(data.run[field])
		data.run.collected = data.run.collected.map(func(i): return int(i))
		data.run.steer = float(data.run.steer); data.run.vx = float(data.run.vx)
		var run: Dictionary = data.run
		run.route_version = int(run.route_version)
		if run.has("shield"): run.shield = float(run.shield)
		run.passage_pickups = int(run.get("passage_pickups", 0))
		if run.get("gear") is Dictionary:
			for id in run.gear.tiers: run.gear.tiers[id] = int(run.gear.tiers[id])
			for id in run.gear:
				if id != "tiers": run.gear[id] = float(run.gear[id])
		for field in ["shields_taken", "portals_used"]: run[field] = run.get(field, []).map(func(i): return int(i))
		if run.get("passage") is Dictionary:
			run.passage.portal = int(run.passage.portal); run.passage.y = float(run.passage.y); run.passage.x = float(run.passage.x)
			run.passage.collected = run.passage.collected.map(func(i): return int(i))
		else: run.passage = null
		var encounter = run.get("encounter")
		if encounter is Dictionary:
			encounter.shots = int(encounter.shots); encounter.t = float(encounter.t); encounter.cooldown = float(encounter.cooldown); encounter.x = float(encounter.x)
			if encounter.harpoon is Dictionary: encounter.harpoon.x = float(encounter.harpoon.x); encounter.harpoon.d = float(encounter.harpoon.d)
			if encounter.hook is Dictionary: encounter.hook.along = float(encounter.hook.along); encounter.hook.across = float(encounter.hook.across)
			if encounter.state == "hooked":
				encounter.resistance = float(encounter.get("resistance", definition().encounter.resistance)); encounter.chase_t = float(encounter.get("chase_t", 0.0))
				encounter.discharge_cooldown = float(encounter.get("discharge_cooldown", 0.0)); encounter.strikes = int(encounter.get("strikes", 0))
				var strike = encounter.get("discharge")
				if strike is Dictionary:
					strike.t = float(strike.t); strike.x0 = int(strike.x0); strike.w = int(strike.w); strike.zone = int(strike.zone); strike.row = float(strike.row)
				else: encounter.discharge = null
				encounter.inked = encounter.get("inked", []).map(func(i): return int(i))
				var ink = encounter.get("ink")
				if ink is Dictionary:
					ink.t = float(ink.t); ink.zone = int(ink.zone); ink.end = int(ink.end); ink["from"] = float(ink.get("from", 1.0))
				else: encounter.ink = null
		else: run.encounter = null
	if data.result is Dictionary:
		for field in ["id", "seed", "pickups", "bonus", "total", "collected", "available"]:
			if data.result.has(field): data.result[field] = int(data.result[field])

## A saved gear copy must be one the Workshop can produce.
static func _gear_valid(value) -> bool:
	if not value is Dictionary or not value.get("tiers") is Dictionary: return false
	for entry in WorkshopBook.tracks():
		if not _finite(value.get(entry.id)): return false
		if not float(value[entry.id]) in entry.levels.map(func(v): return float(v)): return false
	return true

## Issue #22 run fields: spent shields
## and portals, and the passage ride, which must belong to a spent portal.
static func _features_valid(run: Dictionary) -> bool:
	var rules := definition()
	if not _integer(run.get("route_version")) or int(run.route_version) != int(rules.route_version): return false
	var longest := maxf(float(gear(run).shield), float(gear(run).launch))
	if not _finite(run.get("shield", 0.0)) or float(run.get("shield", 0.0)) < 0.0 or float(run.get("shield", 0.0)) > longest + 0.001: return false
	if not _integer(run.get("passage_pickups", 0)): return false
	var path := run_route(run)
	if not _unique_indices(run.get("shields_taken", []), path.shields.size()) or not _unique_indices(run.get("portals_used", []), path.portals.size()): return false
	var ride = run.get("passage")
	if ride != null:
		if not ride is Dictionary or not _integer(ride.get("portal")) or not _finite(ride.get("y")) or not _finite(ride.get("x")): return false
		if int(ride.portal) >= path.portals.size() or not run.get("portals_used", []).any(func(i): return int(i) == int(ride.portal)): return false
		if not _unique_indices(ride.get("collected"), passage(int(run.seed), int(ride.portal), int(gear(run).passage)).pickups.size()): return false
	return true

## Issue #23 encounter (optional; null until the window opens). A hook needs
## an attached harpoon and vice versa; only v3 routes have an arena.
static func _encounter_valid(run: Dictionary) -> bool:
	var encounter = run.get("encounter")
	if encounter == null: return true
	if not encounter is Dictionary or run_route(run).get("arena") == null: return false
	if str(encounter.get("state")) not in ["aiming", "hooked", "escaped"]: return false
	for field in ["t", "cooldown", "x"]:
		if not _finite(encounter.get(field)) or float(encounter[field]) < 0.0: return false
	if float(encounter.cooldown) > float(definition().encounter.cooldown_seconds) or float(encounter.x) > Route.COLUMNS: return false
	if not _integer(encounter.get("shots")): return false
	var shot = encounter.get("harpoon")
	if shot != null:
		if not shot is Dictionary or str(shot.get("state")) not in ["flying", "reeling", "attached"] or not _finite(shot.get("x")) or not _finite(shot.get("d")): return false
		if int(encounter.shots) < 1: return false
	var hooked: bool = encounter.state == "hooked"
	var attached: bool = shot is Dictionary and shot.state == "attached"
	if hooked != attached: return false
	var hook = encounter.get("hook")
	if hooked != (hook is Dictionary): return false
	if hook is Dictionary and (not _finite(hook.get("along")) or not _finite(hook.get("across")) or absf(float(hook.along)) > 1.001 or absf(float(hook.across)) > 1.001): return false
	if hooked:
		# A #23 hooked handoff has neither yet; normalize starts its pursuit.
		for field in ["resistance", "chase_t"]:
			if encounter.has(field) and (not _finite(encounter.get(field)) or float(encounter[field]) < 0.0): return false
		if not encounter.has("resistance"): return true
		if float(encounter.resistance) > float(definition().encounter.resistance): return false
		if not _discharge_valid(run, encounter): return false
		if not _ink_valid(run, encounter): return false
	return true

## Issue #70 ink fields on a hooked encounter.
static func _ink_valid(run: Dictionary, encounter: Dictionary) -> bool:
	var k: Dictionary = definition().encounter.ink
	var zones: Array = run_route(run).ink_zones
	if not _unique_indices(encounter.get("inked", []), MAX_INTEGER): return false
	for y0 in encounter.get("inked", []):
		if not zones.any(func(z): return int(z.y0) == int(y0)): return false
	var ink = encounter.get("ink")
	if ink == null: return true
	if not ink is Dictionary or str(ink.get("phase")) not in ["warn", "spread", "hold", "lift"]: return false
	if not _finite(ink.get("t")) or float(ink.t) < 0.0 or not _finite(ink.get("from", 1.0)) or float(ink.get("from", 1.0)) < 0.0 or float(ink.get("from", 1.0)) > 1.0: return false
	var limit := {"warn": float(k.warn_seconds), "spread": float(k.spread_seconds), "lift": float(k.lift_seconds)}
	if limit.has(str(ink.phase)) and float(ink.t) > float(limit[str(ink.phase)]) + 0.051: return false
	if not _integer(ink.get("zone")) or not _finite(ink.get("end")): return false
	return zones.any(func(z): return int(z.span) == int(ink.zone) and int(z.end) == int(ink.end))

## Issue #25 discharge fields on a hooked encounter.
static func _discharge_valid(run: Dictionary, encounter: Dictionary) -> bool:
	var d: Dictionary = definition().encounter.discharge
	var cooldown = encounter.get("discharge_cooldown", 0.0)
	if not _finite(cooldown) or float(cooldown) < 0.0 or float(cooldown) > float(d.cooldown_seconds[1]): return false
	if not _integer(encounter.get("strikes", 0)): return false
	var strike = encounter.get("discharge")
	if strike == null: return true
	if not strike is Dictionary or str(strike.get("phase")) not in ["windup", "strike"]: return false
	if not _finite(strike.get("t")) or float(strike.t) < 0.0 or float(strike.t) > float(d.warn_seconds) + float(d.active_seconds) + 0.001: return false
	if not _integer(strike.get("x0")) or not _integer(strike.get("w")) or not d.width_columns.any(func(w): return int(w) == int(strike.w)): return false
	if int(strike.x0) < 1 or int(strike.x0) + int(strike.w) > Route.COLUMNS - 1: return false
	if not _integer(strike.get("zone")) or not _finite(strike.get("row")): return false
	return run_route(run).zones.any(func(z): return int(z.span) == int(strike.zone))

static func _unique_indices(values: Variant, count: int) -> bool:
	if not values is Array: return false
	var seen := {}
	for value in values:
		if not _integer(value) or int(value) >= count or seen.has(int(value)): return false
		seen[int(value)] = true
	return true

static func _finite(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func _integer(value: Variant) -> bool:
	return _finite(value) and float(value) >= 0 and float(value) == floor(float(value)) and float(value) <= MAX_INTEGER
