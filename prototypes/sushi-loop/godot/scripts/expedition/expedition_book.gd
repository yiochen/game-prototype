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
## boost) speeds the ship up and blocks collision damage for a few seconds,
## ending before the finish encounter. Steering onto an optional portal spends
## it and enters a separate safe passage: a current carries the ship
## automatically through salvage, then it rejoins the main route further on.
## A run keeps the route version it started with, so older saves fly the
## route they began.
## Balance lives in res://content/expedition.json; routes in route.gd.
const VERSION := 1
const Route = preload("res://scripts/expedition/route.gd")
const FloorBook = preload("res://scripts/floor_book.gd")
const OUTCOMES := ["complete", "returned_early", "hull_depleted"]
const MAX_INTEGER := 9007199254740991
static var _content: Dictionary = {}
static var _library: Array = []
static var _routes: Dictionary = {}
static var _passages: Dictionary = {}
static var _docs: Dictionary = {}

static func definition() -> Dictionary:
	if _content.is_empty(): _content = JSON.parse_string(FileAccess.get_file_as_string("res://content/expedition.json"))
	return _content

static func library() -> Array:
	if _library.is_empty():
		var analysis := Route.analyze_library(Route.load_chunks())
		for id in analysis.problems: push_warning("Expedition chunk %s left out: %s" % [id, "; ".join(analysis.problems[id])])
		_library = analysis.chunks
	return _library

## Assembled grid, spans, gold and features for a seed (cached). Version 1
## is the issue #21 plan (no feature slots); newer runs use the current plan.
static func route(seed_value: int, version: int = -1) -> Dictionary:
	if version < 0: version = int(definition().route_version)
	var cache_key := "%d:%d" % [seed_value, version]
	if not _routes.has(cache_key):
		var plan: Array = definition().plan if version == int(definition().route_version) else definition().legacy_plans[str(version)]
		var sequence := Route.generate(seed_value, library(), plan)
		var assembled := Route.assemble(sequence)
		var pickups: Array = []
		for y in range(assembled.rows.size()):
			var row: String = assembled.rows[y]
			for x in range(row.length()):
				if row[x] == "$": pickups.append(Vector2(x + 0.5, y + 0.5))
		var launch_top := float(assembled.rows.size()) - 0.5
		var encounter_edge := 0.0
		for span in assembled.spans:
			if span.kind == "launch": launch_top = minf(launch_top, float(span.y0))
			# The finish chunk stands in for the creature encounter: no shields reach it.
			if span.kind == "finish": encounter_edge = float(span.y1) + 1.0
		var currents := {}
		var shields: Array = []
		var portals: Array = []
		var spans: Array = assembled.spans
		for i in range(spans.size()):
			var span: Dictionary = spans[i]
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
			"currents": currents, "shields": shields, "portals": portals, "encounter_edge": encounter_edge, "version": version}
	return _routes[cache_key]

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
static func passage(seed_value: int, portal: int) -> Dictionary:
	var cache_key := "%d:%d" % [seed_value, portal]
	if not _passages.has(cache_key):
		var rules := definition()
		var count := int(rules.passage_rows)
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

## The route a run flies (its own route version; saves before #22 are version 1).
static func run_route(run: Dictionary) -> Dictionary:
	return route(int(run.seed), int(run.get("route_version", 1)))

## Preparation cruise: rows the ship may cover before Start, ending in a hover.
static func launch(seed_value: int) -> Dictionary:
	var path := route(seed_value)
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

static func snapshot(state: Dictionary) -> Dictionary:
	var data: Dictionary = state.expedition.duplicate(true)
	if data.run is Dictionary:
		var run: Dictionary = data.run
		var hull_max := float(definition().hull_max)
		run.hull_fraction = clampf(float(run.hull) / hull_max, 0.0, 1.0)
		run.low_hull = run.hull_fraction <= float(definition().low_hull_fraction)
		run.rows = run_route(run).rows.size()
	data.next_seed = next_seed(state)
	return data

## The route the next departure will take (preparation previews it).
static func next_seed(state: Dictionary) -> int:
	var data: Dictionary = state.expedition
	return 1 + posmod(int(Route.cell_hash(int(data.sequence), int(data.seed_base), 61) * 2147483646.0), 2147483646)

# ------------------------------------------------------------ commands

static func command(config: Dictionary, state: Dictionary, request: Dictionary) -> Dictionary:
	var data: Dictionary = state.expedition
	var run = data.run
	match request.get("type"):
		"expedition_start":
			if not _finite(request.get("now")): return {"ok": false, "reason": "invalid_time"}
			if run != null: return {"ok": false, "reason": "expedition_active"}
			if data.result != null: return {"ok": false, "reason": "results_pending"}
			if not charge(state, float(request.now)).ready: return {"ok": false, "reason": "charging"}
			var seed_value: int
			if request.has("seed"):
				if not _integer(request.seed) or int(request.seed) < 1: return {"ok": false, "reason": "invalid_seed"}
				seed_value = int(request.seed)
			else:
				seed_value = next_seed(state)
			var path := route(seed_value)
			if path.rows.is_empty(): return {"ok": false, "reason": "no_route"}
			var start_x: float = _start_x(path.rows)
			var lead := launch(seed_value)
			var start_y: float = lead.bottom
			if request.has("y"):
				if not _finite(request.y) or float(request.y) < float(lead.hover) - 0.001 or float(request.y) > float(lead.bottom) + 0.001: return {"ok": false, "reason": "invalid_start"}
				start_y = float(request.y)
			data.charge = {"ready": false, "recharge_started": null}
			data.sequence = int(data.sequence) + 1
			data.run = {"id": int(data.sequence), "seed": seed_value, "y": start_y, "x": start_x, "steer": 0.0, "vx": 0.0,
				"hull": float(definition().hull_max), "salvage": 0, "collected": [], "protection": 0.0, "paused": false, "elapsed": 0.0, "impacts": 0,
				"route_version": int(definition().route_version), "shield": 0.0, "shields_taken": [], "portals_used": [], "passage": null, "passage_pickups": 0}
			return {"ok": true, "changed": true, "seed": seed_value, "id": data.run.id}
		"expedition_steer":
			if run == null or run.paused: return {"ok": false, "reason": "not_travelling"}
			if not _finite(request.get("input")): return {"ok": false, "reason": "invalid_steer"}
			run.steer = clampf(float(request.input), -1.0, 1.0)
			return {"ok": true}
		"expedition_advance":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			if not _finite(request.get("elapsed")) or float(request.elapsed) < 0.0 or not _finite(request.get("now")): return {"ok": false, "reason": "invalid_time"}
			return {"ok": true, "events": _advance(config, state, float(request.elapsed), float(request.now))}
		"expedition_pause":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			# A paused ship lets go of the stick; it resumes running straight.
			run.paused = true; run.steer = 0.0; run.vx = 0.0
			return {"ok": true}
		"expedition_resume":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			run.paused = false
			return {"ok": true}
		"expedition_return_early":
			if run == null: return {"ok": false, "reason": "no_expedition"}
			if not run.paused: return {"ok": false, "reason": "pause_required"}
			if not _finite(request.get("now")): return {"ok": false, "reason": "invalid_time"}
			return {"ok": true, "result": _end(config, state, "returned_early", float(request.now))}
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

static func _advance(config: Dictionary, state: Dictionary, elapsed: float, now: float) -> Array:
	var data: Dictionary = state.expedition
	var run: Dictionary = data.run
	var events: Array = []
	if run.paused or elapsed <= 0.0: return events
	var rules := definition()
	var path := run_route(run)
	var half := Vector2(float(rules.ship_collider[0]), float(rules.ship_collider[1])) * 0.5
	var radius := float(rules.pickup_radius)
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
			var info := passage(int(run.seed), int(ride.portal))
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
		var shielded := float(run.shield) > 0.0
		run.y = float(run.y) - float(rules.forward_rows_per_second) * (float(rules.shield_forward_multiplier) if shielded else 1.0) * dt
		if shielded:
			run.shield = maxf(0.0, float(run.shield) - dt)
			# The shield always ends before the encounter.
			if float(run.y) <= float(path.encounter_edge) + 0.5: run.shield = 0.0
			if float(run.shield) <= 0.0: events.append({"type": "shield_end"})
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
				run.shield = float(rules.shield_seconds)
				events.append({"type": "shield", "index": i, "x": b.x, "y": b.y})
		for i in range(path.portals.size()):
			var portal: Dictionary = path.portals[i]
			if i in run.portals_used: continue
			if absf(float(portal.x) - float(run.x)) <= float(rules.portal_radius) and absf(float(portal.y) - float(run.y)) <= float(rules.portal_radius):
				# Entering spends the portal first, so a save can never repeat it.
				run.portals_used.append(i)
				run.shield = 0.0; run.vx = 0.0
				var info := passage(int(run.seed), i)
				var start_y := float(info.rows_count) - float(rules.passage_ride_rows)
				run.passage = {"portal": i, "y": start_y, "x": passage_centre(info, start_y), "collected": []}
				events.append({"type": "passage_enter", "portal": i, "from_x": portal.x, "from_y": portal.y, "x": run.passage.x, "y": start_y})
				return events
		if _overlaps(path.rows, float(run.x), float(run.y), half):
			if float(run.shield) > 0.0:
				# Rocks only bump the shield; a short guard keeps the feedback from repeating every step.
				if float(run.protection) <= 0.0:
					run.protection = 0.3
					events.append({"type": "shield_bump", "x": run.x, "y": run.y})
			elif float(run.protection) <= 0.0:
				run.hull = maxf(0.0, float(run.hull) - float(rules.impact_damage))
				run.protection = float(rules.hit_protection_seconds)
				run.impacts = int(run.impacts) + 1
				events.append({"type": "impact", "x": run.x, "y": run.y, "hull": run.hull})
				if float(run.hull) <= 0.0:
					events.append({"type": "ended", "result": _end(config, state, "hull_depleted", now)})
					return events
		if float(run.y) <= 0.5:
			events.append({"type": "ended", "result": _end(config, state, "complete", now)})
			return events
	return events

static func _overlaps(rows: Array, x: float, y: float, half: Vector2) -> bool:
	for cy in range(int(floor(y - half.y)), int(floor(y + half.y)) + 1):
		if cy < 0 or cy >= rows.size(): continue
		var row: String = rows[cy]
		for cx in range(int(floor(x - half.x)), int(floor(x + half.x)) + 1):
			if cx >= 0 and cx < row.length() and Route.is_rock(row[cx]): return true
	return false

## Commit once: bank salvage (+ completion bonus), start the night recharge,
## refresh cosmetic stock, and leave a receipt for the results screen.
static func _end(config: Dictionary, state: Dictionary, outcome: String, now: float) -> Dictionary:
	var data: Dictionary = state.expedition
	var run: Dictionary = data.run
	var bonus := int(definition().completion_bonus) if outcome == "complete" else 0
	var total := int(run.salvage) + bonus
	data.salvage = mini(MAX_INTEGER, int(data.salvage) + total)
	data.result = {"id": int(run.id), "seed": int(run.seed), "outcome": outcome, "pickups": int(run.salvage), "bonus": bonus, "total": total,
		"collected": run.collected.size(), "available": run_route(run).pickups.size()}
	data.run = null
	data.charge = {"ready": false, "recharge_started": now}
	if state.has("floor_styles"):
		FloorBook.command(config, state, {"type": "floor_refresh", "expected_rotation": state.floor_styles.rotation})
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
		if float(run.hull) <= 0.0 or float(run.hull) > float(definition().hull_max): return false
		if not _features_valid(run): return false
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
	return true

static func normalize(state: Dictionary) -> void:
	var data: Dictionary = state.expedition
	for field in ["salvage", "sequence", "seed_base"]: data[field] = int(data[field])
	if data.run is Dictionary:
		for field in ["id", "seed", "salvage", "impacts"]: data.run[field] = int(data.run[field])
		data.run.collected = data.run.collected.map(func(i): return int(i))
		# Saves from before joystick steering hold no stick input.
		data.run.steer = float(data.run.get("steer", 0.0)); data.run.vx = float(data.run.get("vx", 0.0))
		# Saves from before issue #22 keep their original route and carry no features.
		var run: Dictionary = data.run
		run.route_version = int(run.get("route_version", 1))
		run.shield = float(run.get("shield", 0.0)); run.passage_pickups = int(run.get("passage_pickups", 0))
		for field in ["shields_taken", "portals_used"]: run[field] = run.get(field, []).map(func(i): return int(i))
		if run.get("passage") is Dictionary:
			run.passage.portal = int(run.passage.portal); run.passage.y = float(run.passage.y); run.passage.x = float(run.passage.x)
			run.passage.collected = run.passage.collected.map(func(i): return int(i))
		else: run.passage = null
	if data.result is Dictionary:
		for field in ["id", "seed", "pickups", "bonus", "total", "collected", "available"]:
			if data.result.has(field): data.result[field] = int(data.result[field])

## Issue #22 run fields (optional in older saves): shield time, spent shields
## and portals, and the passage ride, which must belong to a spent portal.
static func _features_valid(run: Dictionary) -> bool:
	var rules := definition()
	var version = run.get("route_version", 1)
	if not _integer(version) or (int(version) != int(rules.route_version) and not rules.legacy_plans.has(str(int(version)))): return false
	if not _finite(run.get("shield", 0.0)) or float(run.get("shield", 0.0)) < 0.0 or float(run.get("shield", 0.0)) > float(rules.shield_seconds): return false
	if not _integer(run.get("passage_pickups", 0)): return false
	var path := run_route(run)
	if not _unique_indices(run.get("shields_taken", []), path.shields.size()) or not _unique_indices(run.get("portals_used", []), path.portals.size()): return false
	var ride = run.get("passage")
	if ride != null:
		if not ride is Dictionary or not _integer(ride.get("portal")) or not _finite(ride.get("y")) or not _finite(ride.get("x")): return false
		if int(ride.portal) >= path.portals.size() or not run.get("portals_used", []).any(func(i): return int(i) == int(ride.portal)): return false
		if not _unique_indices(ride.get("collected"), passage(int(run.seed), int(ride.portal)).pickups.size()): return false
	return true

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
