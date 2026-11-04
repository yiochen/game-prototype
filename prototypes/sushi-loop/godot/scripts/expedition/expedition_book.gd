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
## Balance lives in res://content/expedition.json; routes in route.gd.
const VERSION := 1
const Route = preload("res://scripts/expedition/route.gd")
const FloorBook = preload("res://scripts/floor_book.gd")
const OUTCOMES := ["complete", "returned_early", "hull_depleted"]
const MAX_INTEGER := 9007199254740991
static var _content: Dictionary = {}
static var _library: Array = []
static var _routes: Dictionary = {}

static func definition() -> Dictionary:
	if _content.is_empty(): _content = JSON.parse_string(FileAccess.get_file_as_string("res://content/expedition.json"))
	return _content

static func library() -> Array:
	if _library.is_empty():
		var analysis := Route.analyze_library(Route.load_chunks())
		for id in analysis.problems: push_warning("Expedition chunk %s left out: %s" % [id, "; ".join(analysis.problems[id])])
		_library = analysis.chunks
	return _library

## Assembled grid, spans, gold and steering guide for a seed (cached).
static func route(seed_value: int) -> Dictionary:
	if not _routes.has(seed_value):
		var sequence := Route.generate(seed_value, library(), definition().plan)
		var assembled := Route.assemble(sequence)
		var pickups: Array = []
		for y in range(assembled.rows.size()):
			var row: String = assembled.rows[y]
			for x in range(row.length()):
				if row[x] == "$": pickups.append(Vector2(x + 0.5, y + 0.5))
		var launch_top := float(assembled.rows.size()) - 0.5
		for span in assembled.spans:
			if span.kind == "launch": launch_top = minf(launch_top, float(span.y0))
		_routes[seed_value] = {"rows": assembled.rows, "spans": assembled.spans, "pickups": pickups, "columns": Route.COLUMNS, "launch_top": launch_top}
	return _routes[seed_value]

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
		run.rows = route(int(run.seed)).rows.size()
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
				"hull": float(definition().hull_max), "salvage": 0, "collected": [], "protection": 0.0, "paused": false, "elapsed": 0.0, "impacts": 0}
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
	var path := route(int(run.seed))
	var half := Vector2(float(rules.ship_collider[0]), float(rules.ship_collider[1])) * 0.5
	var radius := float(rules.pickup_radius)
	# Sub-steps keep a frame hitch from tunnelling through a one-cell rock.
	var remaining := elapsed
	while remaining > 0.0:
		var dt := minf(remaining, 0.05)
		remaining -= dt
		run.elapsed = float(run.elapsed) + dt
		run.protection = maxf(0.0, float(run.protection) - dt)
		run.y = float(run.y) - float(rules.forward_rows_per_second) * dt
		var want := float(run.steer) * float(rules.lateral_columns_per_second)
		run.vx = move_toward(float(run.vx), want, float(rules.lateral_acceleration) * dt)
		run.x = float(run.x) + float(run.vx) * dt
		if float(run.x) < 0.4 or float(run.x) > Route.COLUMNS - 0.4:
			run.x = clampf(float(run.x), 0.4, Route.COLUMNS - 0.4); run.vx = 0.0
		for i in range(path.pickups.size()):
			if i in run.collected: continue
			var p: Vector2 = path.pickups[i]
			if absf(p.x - float(run.x)) <= radius and absf(p.y - float(run.y)) <= radius:
				run.collected.append(i)
				run.salvage = int(run.salvage) + int(rules.salvage_per_pickup)
				events.append({"type": "pickup", "index": i, "x": p.x, "y": p.y, "value": int(rules.salvage_per_pickup)})
		if float(run.protection) <= 0.0 and _overlaps(path.rows, float(run.x), float(run.y), half):
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
		"collected": run.collected.size(), "available": route(int(run.seed)).pickups.size()}
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
		var pickups: int = route(int(run.seed)).pickups.size()
		var seen := {}
		for index in run.collected:
			if not _integer(index) or int(index) >= pickups or seen.has(int(index)): return false
			seen[int(index)] = true
		if int(run.salvage) != run.collected.size() * int(definition().salvage_per_pickup): return false
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
	if data.result is Dictionary:
		for field in ["id", "seed", "pickups", "bonus", "total", "collected", "available"]:
			if data.result.has(field): data.result[field] = int(data.result[field])

static func _finite(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func _integer(value: Variant) -> bool:
	return _finite(value) and float(value) >= 0 and float(value) == floor(float(value)) and float(value) <= MAX_INTEGER
