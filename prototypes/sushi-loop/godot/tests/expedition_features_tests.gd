extends SceneTree
## Issue #22 rules: lateral currents, the shield (travel boost), the optional
## portal into a safe bonus passage, and their save/pause behaviour, through
## the public command/time/save boundary with a controlled clock.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
const SEED := 22
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

## Equal after a JSON round trip (floats may differ in the last bit).
func same(a: Variant, b: Variant) -> bool:
	if a is Dictionary and b is Dictionary:
		return a.size() == b.size() and a.keys().all(func(k): return b.has(k) and same(a[k], b[k]))
	if a is Array and b is Array:
		return a.size() == b.size() and range(a.size()).all(func(i): return same(a[i], b[i]))
	if (a is float or a is int) and (b is float or b is int): return absf(float(a) - float(b)) < 1e-9
	return a == b

func _initialize() -> void: call_deferred("run")

func run_of(s) -> Dictionary: return s.snapshot().expedition.run

func started() -> Variant:
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	return s

## Test-only placement: move the saved run to a spot on its route.
func place(s, x: float, y: float) -> void:
	var r: Dictionary = s._state.expedition.run
	r.x = x; r.y = y; r.vx = 0.0; r.steer = 0.0

func advance(s, seconds: float) -> Array:
	var events: Array = []
	var t := 0.0
	while t < seconds - 0.0001 and run_of(s) != null:
		events.append_array(s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 2000.0 + t}).get("events", []))
		t += 0.05
	return events

func roundtrip(s):
	var restored = Session.new()
	check(restored.restore(JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))), "JSON save restores")
	return restored

func types(events: Array) -> Array: return events.map(func(e): return e.type)

func run() -> void:
	var rules := Book.definition()
	var path := Book.route(SEED)
	var kinds: Array = path.spans.map(func(span): return span.kind)
	check("current" in kinds and "portal" in kinds and "boost" in kinds, "current, portal and shield chunks join the run plan: %s" % [kinds])
	check(not path.currents.is_empty() and path.shields.size() >= 1 and path.portals.size() == 1, "the route carries current fields, a shield and one portal")
	var finish: Dictionary = path.spans.filter(func(span): return span.kind == "finish")[0]
	check(path.shields.all(func(b): return b.y > float(path.encounter_edge)) and path.portals.all(func(p): return p.y > float(path.encounter_edge)), "the encounter (finish) holds neither shields nor portals")
	# Issue #23: the encounter arena now precedes the finish; route version 2 still ends at the finish chunk.
	var arena: Dictionary = path.spans.filter(func(span): return span.kind == "encounter")[0]
	var arena_at: int = path.spans.find(arena)
	check(float(path.encounter_edge) == float(arena.y1) + 1.0 and path.spans[arena_at + 1 + int(Book.definition().encounter.pursuit_chunks)] == finish, "the encounter edge is the arena's entry, the pursuit chunks before the finish")
	var v2 := Book.route(SEED, 2)
	var v2_finish: Dictionary = v2.spans.filter(func(span): return span.kind == "finish")[0]
	check(float(v2.encounter_edge) == float(v2_finish.y1) + 1.0, "route version 2 keeps the finish chunk as its encounter edge")
	var legacy := Book.route(SEED, 1)
	check(legacy.currents.is_empty() and legacy.shields.is_empty() and legacy.portals.is_empty() and not legacy.spans.any(func(span): return span.kind in ["current", "portal", "boost"]), "route version 1 keeps the issue #21 plan without features")

	# Currents: the push adds to steering and continues after letting go.
	var cell: Vector2i = path.currents.keys()[0]
	for key in path.currents:
		# A cell with current on both sides and the row above keeps the test inside the field.
		if path.currents.has(key + Vector2i(1, 0)) and path.currents.has(key - Vector2i(1, 0)) and path.currents.has(key - Vector2i(0, 1)): cell = key; break
	var dir := int(path.currents[cell])
	var s = started()
	place(s, cell.x + 0.5, cell.y + 0.9)
	advance(s, 0.2)
	var drift := float(run_of(s).x) - (cell.x + 0.5)
	check(absf(drift - dir * float(rules.current_columns_per_second) * 0.2) < 0.01, "a current pushes the released ship sideways at its speed (%.3f)" % drift)
	place(s, cell.x + 0.5, cell.y + 0.9)
	s.command({"type": "expedition_steer", "input": float(-dir)})
	advance(s, 0.2)
	var against := float(run_of(s).vx)
	check(against == -dir * float(rules.lateral_columns_per_second), "steering stays available inside a current")
	s.command({"type": "expedition_steer", "input": 0.0})
	var before := float(run_of(s).x)
	advance(s, 0.4)
	check(float(run_of(s).vx) == 0.0 and signf(float(run_of(s).x) - before) == dir, "releasing stops the player's part without cancelling the current")

	# Shield: normal speed, no collision damage, still solid rock, no pickup multiplier, ends on time.
	var shield: Vector2 = path.shields[0]
	s = started()
	place(s, shield.x, shield.y + 0.5)
	var events := advance(s, 0.3)
	check("shield" in types(events) and float(run_of(s).shield) > 0.0, "flying over the shield picks it up")
	var y0 := float(run_of(s).y)
	advance(s, 1.0)
	check(absf((y0 - float(run_of(s).y)) - float(rules.forward_rows_per_second)) < 0.01, "the shield keeps normal forward speed")
	var hull := float(run_of(s).hull)
	var rock := Vector2(-1, -1)
	var rows: Array = path.rows
	for y in range(int(run_of(s).y) - 1, int(run_of(s).y) - 6, -1):
		for x in range(Route.COLUMNS):
			if Route.is_rock(str(rows[y])[x]) and rock.x < 0: rock = Vector2(x + 0.5, y + 0.5)
	place(s, rock.x, rock.y)
	events = advance(s, 0.3)
	check(float(run_of(s).hull) == hull and "shield_bump" in types(events) and not "impact" in types(events), "rocks bump the shield without damage")
	check(not Book._collides(rows, float(run_of(s).x), float(run_of(s).y), float(rules.ship_radius) + float(rules.rock_radius)), "a shielded ship is still knocked out of the rock")
	var salvage := int(run_of(s).salvage)
	var gold: Vector2 = path.pickups.filter(func(p): return p.y < float(run_of(s).y) - 0.5 and p.y > float(path.encounter_edge))[0]
	place(s, gold.x, gold.y + 0.3)
	events = advance(s, 0.2)
	check("pickup" in types(events) and int(run_of(s).salvage) == salvage + int(rules.salvage_per_pickup), "shielded pickups keep their normal value")
	s.command({"type": "expedition_pause"})
	var held := float(run_of(s).shield)
	advance(s, 1.0)
	check(float(run_of(s).shield) == held, "Pause freezes the shield timer")
	var reopened = roundtrip(s)
	check(float(reopened.snapshot().expedition.run.shield) == held and float(reopened.snapshot().expedition.run.protection) == float(run_of(s).protection), "save keeps the shield time without adding protection")
	s.command({"type": "expedition_resume"})
	events = advance(s, float(rules.shield_seconds))
	check(float(run_of(s).shield) == 0.0 and "shield_end" in types(events), "the shield runs out after its time")
	place(s, 5.5, float(path.encounter_edge) + 3.0)
	s._state.expedition.run.shield = float(rules.shield_seconds)
	advance(s, 1.5)
	check(float(run_of(s).shield) == 0.0 and float(run_of(s).y) < float(path.encounter_edge) + 0.6, "the shield ends before the encounter")
	place(s, shield.x, shield.y + 0.5)
	events = advance(s, 0.3)
	check(not "shield" in types(events), "a taken shield is gone")

	# Portal: optional, spent on entry, a safe automatic ride through salvage, then rejoin.
	var portal: Dictionary = path.portals[0]
	s = started()
	place(s, float(portal.x) + 2.0, float(portal.y) + 1.0)
	events = advance(s, 0.6)
	check(not "passage_enter" in types(events), "passing beside the portal does not enter it")
	place(s, float(portal.x), float(portal.y) + 0.3)
	events = advance(s, 0.2)
	check("passage_enter" in types(events) and run_of(s).passage != null and 0 in run_of(s).portals_used, "steering onto the portal spends it and enters the passage")
	var info := Book.passage(SEED, 0)
	s.command({"type": "expedition_steer", "input": 1.0})
	advance(s, 1.0)
	var ride: Dictionary = run_of(s).passage
	check(absf(float(ride.x) - Book.passage_centre(info, float(ride.y))) < 0.001, "the passage current steers the ship; input has no effect")
	hull = float(run_of(s).hull)
	advance(s, 1.5)
	check(run_of(s).passage.collected.size() > 0 and float(run_of(s).hull) == hull, "the ride collects salvage and takes no damage")
	s.command({"type": "expedition_pause"})
	reopened = roundtrip(s)
	check(same(reopened.snapshot().expedition.run, run_of(s)), "save and reopen keep passage progress and its pickups")
	var mid_salvage := int(run_of(s).salvage)
	for session in [s, reopened]:
		session.command({"type": "expedition_resume"})
	events = advance(s, 12.0)
	advance(reopened, 12.0)
	check("passage_exit" in types(events) and run_of(s).passage == null, "the passage ends and rejoins the main route")
	check(Vector2(float(run_of(s).x), float(run_of(s).y)).distance_to(portal.rejoin) < 0.01 or float(run_of(s).y) < float(portal.rejoin.y), "the ship rejoins further along the main route")
	check(float(portal.rejoin.y) < float(portal.y) - 10.0, "the rejoin point lies past the next chunk")
	check(reopened.snapshot().expedition.run.salvage == run_of(s).salvage and int(run_of(s).salvage) > mid_salvage, "reopened rides earn the same passage salvage")
	check(int(run_of(s).salvage) == (run_of(s).collected.size() + int(run_of(s).passage_pickups)) * int(rules.salvage_per_pickup), "passage pickups are counted once")
	place(s, float(portal.x), float(portal.y) + 0.3)
	events = advance(s, 0.3)
	check(not "passage_enter" in types(events) and run_of(s).passage == null, "a spent portal cannot be re-entered")

	# Saves: corrupt feature fields are rejected; older runs keep their route.
	s = started()
	place(s, float(portal.x), float(portal.y) + 0.3)
	advance(s, 0.4)
	var good: Dictionary = JSON.parse_string(JSON.stringify(s.save_data()))
	for kind in ["unspent_portal", "duplicate_passage_gold", "long_shield", "unknown_version"]:
		var corrupt: Dictionary = good.duplicate(true)
		var data: Dictionary = corrupt.state.expedition.run
		match kind:
			"unspent_portal": data.portals_used = []
			"duplicate_passage_gold": data.passage.collected = [0, 0]
			"long_shield": data.shield = float(rules.shield_seconds) + 1.0
			"unknown_version": data.route_version = 99
		var target = Session.new_session(9)
		check(not target.restore(corrupt), "corrupt %s save is rejected" % kind)
	var old = Session.new_session(7)
	old.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	var legacy_save: Dictionary = JSON.parse_string(JSON.stringify(old.save_data()))
	var legacy_run: Dictionary = legacy_save.state.expedition.run
	for field in ["route_version", "shield", "shields_taken", "portals_used", "passage", "passage_pickups"]: legacy_run.erase(field)
	legacy_run.y = float(legacy.rows.size()) - 0.5
	var migrated = Session.new()
	check(migrated.restore(legacy_save), "a run saved before #22 restores")
	var mr: Dictionary = migrated.snapshot().expedition.run
	check(int(mr.route_version) == 1 and Book.run_route(mr).rows == legacy.rows and mr.passage == null and float(mr.shield) == 0.0, "it keeps flying its original issue #21 route")

	print("Expedition features: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)
