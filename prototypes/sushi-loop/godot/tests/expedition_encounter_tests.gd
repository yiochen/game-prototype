extends SceneTree
## Issue #23 rules: the creature encounter's shooting window, one-shot-per-press
## harpoon with reload, misses, restless expiry and escape, and the held hook
## handoff, through the public command/time/save boundary with a controlled
## clock. Positions are set through the saved run only to stage a scenario.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const SEED := 23
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func run_of(s) -> Variant: return s.snapshot().expedition.run
func live(s) -> Dictionary: return s._state.expedition.run

func started() -> Variant:
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	return s

func advance(s, seconds: float) -> Array:
	var events: Array = []
	var t := 0.0
	while t < seconds - 0.0001 and run_of(s) != null:
		events.append_array(s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 2000.0 + t}).get("events", []))
		t += 0.05
	return events

## Equal after a JSON round trip (floats may differ in the last bit).
func same(a: Variant, b: Variant) -> bool:
	if a is Dictionary and b is Dictionary:
		return a.size() == b.size() and a.keys().all(func(k): return b.has(k) and same(a[k], b[k]))
	if (a is float or a is int) and (b is float or b is int): return absf(float(a) - float(b)) < 1e-9
	return a == b

## Advance while steering clear of rock like a careful player (rock is solid).
func advance_steering(s, seconds: float) -> Array:
	var events: Array = []
	var t := 0.0
	var reach := float(Book.definition().ship_radius) + .1
	while t < seconds - 0.0001 and run_of(s) != null:
		var r: Dictionary = live(s)
		var rows: Array = Book.run_route(r).rows
		var best := float(r.x)
		var best_score := INF
		for i in range(1, 22):
			var x := i * 0.5
			var score := absf(x - float(r.x)) * 0.01
			for ahead in [0.0, 0.5, 1.0, 1.6, 2.2]:
				if Book._collides(rows, x, float(r.y) - ahead, reach): score += 10.0 / (1.0 + ahead)
			if score < best_score: best_score = score; best = x
		s.command({"type": "expedition_steer", "input": clampf((best - float(r.x)) * 3.0, -1.0, 1.0)})
		events.append_array(s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 2000.0 + t}).get("events", []))
		t += 0.05
	return events

func types(events: Array) -> Array: return events.map(func(e): return e.type)

func roundtrip(s):
	var restored = Session.new()
	check(restored.restore(JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))), "JSON save restores")
	return restored

## Stage the ship at the window's opening row (in the arena's centre column) and open it.
func at_encounter(s) -> void:
	var r: Dictionary = live(s)
	var path := Book.run_route(r)
	r.y = float(path.encounter_start) + 0.02; r.x = 5.5; r.vx = 0.0; r.steer = 0.0
	var events := advance(s, 0.1)
	check("encounter_start" in types(events), "the shooting window opens a few rows into the arena")

## Put the ship under (or beside) the creature's current column.
func line_up(s, offset := 0.0) -> void:
	var r: Dictionary = live(s)
	r.x = Book.creature_centre(r).x + offset; r.vx = 0.0; r.steer = 0.0

func run() -> void:
	var rules: Dictionary = Book.definition().encounter
	var path := Book.route(SEED)
	var kinds: Array = path.spans.map(func(span): return span.kind)
	var chase := int(rules.pursuit_chunks)
	check(kinds[kinds.size() - 2 - chase] == "encounter" and kinds.slice(-1 - chase, -1) == ["normal", "creature", "normal", "creature", "normal"] and kinds[-1] == "finish", "route version 5 puts the arena %d chunks before the finish, ordinary and creature chunks alternating: %s" % [chase, kinds.slice(-2 - chase)])
	var v4: Array = Book.route(SEED, 4).spans.map(func(span): return span.kind)
	check(v4.slice(-1 - chase, -1).all(func(k): return k == "normal"), "a version 4 run keeps its all-ordinary pursuit: %s" % [v4.slice(-1 - chase)])
	check(Book.route(SEED, 3).spans.map(func(span): return span.kind).slice(-2) == ["encounter", "finish"], "route version 3 (saves from #23) keeps its arena right before the finish")
	check(path.arena != null and int(path.arena.y1) - int(path.arena.y0) + 1 == int(rules.arena_rows), "the arena has the configured length")
	check(float(path.encounter_edge) == float(path.arena.y1) + 1.0, "shields end at the arena's entry")
	check(path.shields.all(func(b): return b.y > float(path.encounter_edge)) and path.portals.all(func(p): return p.y > float(path.encounter_edge)), "no shield or portal reaches the encounter")
	var open := true
	for y in range(int(path.arena.y0) + 1, int(path.arena.y1) + 1):
		for x in range(2, 9): open = open and not str(path.rows[y])[x] in ["#"]
	check(open, "the arena keeps seven open columns for aiming")
	check(Book.route(SEED, 2).arena == null, "route version 2 (saves from #22) keeps its route without an arena")

	# Before the window: no target, and older runs never open one.
	var s = started()
	check(s.command({"type": "expedition_fire"}).reason == "no_target", "the harpoon is unavailable before the encounter")
	var old = started()
	live(old).route_version = 2
	live(old).y = 20.0
	check(not "encounter_start" in types(advance(old, 0.5)) and run_of(old).encounter == null, "a route version 2 run never starts an encounter")

	# Aiming: resistance stays full, the creature weaves ahead of the ship.
	s = started(); at_encounter(s)
	var enc: Dictionary = run_of(s).encounter
	check(enc.state == "aiming" and enc.harpoon == null and int(enc.shots) == 0, "aiming starts with a ready harpoon")
	var c0 := Book.creature_centre(run_of(s))
	check(c0.y < float(run_of(s).y) - float(rules.lead_rows), "the creature arrives from further north")
	advance(s, float(rules.arrive_seconds))
	var ahead := float(run_of(s).y) - Book.creature_centre(run_of(s)).y
	check(absf(ahead - float(rules.lead_rows)) < .01, "then swims %.1f rows ahead, at the ship's speed" % ahead)
	var xs: Array = []
	for i in range(6): advance(s, 0.6); xs.append(Book.creature_centre(run_of(s)).x)
	check(xs.max() - xs.min() > 1.0, "the creature weaves sideways")

	# A miss: one shot per press, straight up, reels back, then the cooldown ends.
	line_up(s, 2.0)
	var fired: Dictionary = s.command({"type": "expedition_fire"})
	check(fired.ok and int(run_of(s).encounter.shots) == 1, "a fresh press fires once")
	check(s.command({"type": "expedition_fire"}).reason == "reloading", "pressing again (or holding) never fires a second harpoon")
	var shot_x := float(run_of(s).encounter.harpoon.x)
	live(s).steer = 1.0
	advance(s, 0.2)
	check(float(run_of(s).encounter.harpoon.x) == shot_x, "a shot keeps its column while the ship steers on")
	live(s).steer = 0.0
	var events := advance(s, 2.5)
	check("harpoon_missed" in types(events) and not "hooked" in types(events), "a shot past the creature misses")
	enc = run_of(s).encounter
	check(enc.state == "aiming" and enc.harpoon == null and float(enc.cooldown) == 0.0, "the harpoon reels back in and reloads")
	check(int(enc.shots) == 1, "misses spend no ammunition and fire nothing extra")

	# Pause freezes the window and the reload.
	line_up(s, 2.0); s.command({"type": "expedition_fire"})
	var frozen: Dictionary = run_of(s).encounter.duplicate(true)
	s.command({"type": "expedition_pause"})
	advance(s, 1.0)
	check(run_of(s).encounter == frozen, "Pause freezes the window, the shot and the reload")
	check(s.command({"type": "expedition_fire"}).reason == "not_travelling", "nothing fires while paused")
	# Save mid-flight: the shot and reload continue exactly where they were.
	var restored = roundtrip(s)
	check(same(run_of(restored).encounter, frozen), "a saved shot in flight and its reload survive reopening")
	s.command({"type": "expedition_resume"}); advance(s, 3.0)

	# A hit: the hook is recorded and the run holds still for the pursuit handoff.
	line_up(s)
	var y_before := float(run_of(s).y)
	check(s.command({"type": "expedition_fire"}).ok, "aim under the creature and fire")
	var near := false
	var hooked := []
	for i in range(60):
		if Book.strike_point(run_of(s), float(rules.slow_motion_lookahead_rows)) != null: near = true
		hooked = advance(s, 0.05).filter(func(e): return e.type == "hooked")
		if not hooked.is_empty(): break
	check(near, "the strike is announced a moment before it lands (slow motion)")
	check(hooked.size() == 1, "the harpoon hooks the creature")
	enc = run_of(s).encounter
	check(enc.state == "hooked" and enc.harpoon.state == "attached" and enc.hook is Dictionary, "the hook pins the harpoon where it struck")
	check(absf(float(enc.hook.along)) <= 1.0 and absf(float(enc.hook.across)) <= 1.0, "the hook position lies on the hit area")
	check(float(run_of(s).encounter.resistance) == float(rules.resistance), "a hook starts the pursuit at full resistance")
	var held: Dictionary = run_of(s).duplicate(true)
	advance(s, 1.0)
	check(float(run_of(s).y) < float(held.y) and float(run_of(s).encounter.resistance) < float(rules.resistance), "the hook starts the chase: travel continues and resistance drains")
	check(s.command({"type": "expedition_fire"}).reason == "no_target", "only one harpoon: the button is gone once hooked")
	check(float(run_of(s).y) < y_before + 0.001, "the hook happened on the way forward")
	restored = roundtrip(s)
	check(same(run_of(restored).encounter, run_of(s).encounter), "the pursuit is saveable")
	restored.command({"type": "expedition_pause"})
	var returned: Dictionary = restored.command({"type": "expedition_return_early", "now": 3000.0})
	check(returned.ok and returned.result.outcome == "returned_early" and not returned.result.has("creature"), "Return early leaves the pursuit without a recipe")

	# Expiry: no hook in time -> the creature escapes; the route then finishes as usual.
	s = started(); at_encounter(s)
	line_up(s, 2.5)
	var window := float(rules.window_seconds)
	var restless_from := window - float(rules.restless_seconds)
	events = advance(s, restless_from + 0.2)
	check(run_of(s).encounter.state == "aiming" and not "creature_escaped" in types(events), "the window is still open while restless")
	events = advance(s, float(rules.restless_seconds))
	check("creature_escaped" in types(events) and run_of(s).encounter.state == "escaped", "the window expires and the creature escapes")
	check(s.command({"type": "expedition_fire"}).reason == "no_target", "no shots after the escape")
	events = advance_steering(s, 90.0)
	var ended: Array = events.filter(func(e): return e.type == "ended")
	check(ended.size() == 1 and ended[0].result.outcome == "complete" and not ended[0].result.has("recipe"), "the route finishes without awarding a recipe")

	# A shot already on its way when the window closes still counts.
	s = started(); at_encounter(s)
	advance(s, float(rules.arrive_seconds))
	live(s).encounter.t = window - 0.05
	line_up(s)
	s.command({"type": "expedition_fire"})
	events = advance(s, 1.0)
	check("hooked" in types(events) and not "creature_escaped" in types(events), "a harpoon in flight at expiry can still hook")

	# Debug cheats (offered only behind the cheats flag): a shield now, and a skip to the arena.
	s = started()
	check(s.command({"type": "expedition_cheat_shield"}).ok and float(run_of(s).shield) == float(Book.definition().shield_seconds), "the shield cheat raises a shield")
	check(s.command({"type": "expedition_cheat_encounter"}).ok, "the encounter cheat skips ahead")
	check(float(run_of(s).shield) == 0.0 and float(run_of(s).y) == float(path.arena.y1) + 0.5, "it lands at the arena's entry with no shield")
	check(s.command({"type": "expedition_cheat_shield"}).reason == "no_shields_here", "no shield cheat inside the encounter")
	events = advance(s, 3.0)
	check("encounter_start" in types(events), "the encounter then starts as usual")
	check(s.command({"type": "expedition_cheat_encounter"}).reason == "no_encounter", "and the skip cannot repeat")

	# Invalid saves are rejected.
	s = started(); at_encounter(s)
	var data: Dictionary = s.save_data()
	data.state.expedition.run.encounter.state = "hooked"
	check(not Session.new().restore(data), "a hook without an attached harpoon is rejected")
	data = s.save_data()
	data.state.expedition.run.encounter.cooldown = 99.0
	check(not Session.new().restore(data), "an impossible reload time is rejected")
	data = s.save_data()
	data.state.expedition.run.route_version = 2
	check(not Session.new().restore(data), "an encounter on a route without an arena is rejected")

	print("Expedition encounter tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() else 0)
