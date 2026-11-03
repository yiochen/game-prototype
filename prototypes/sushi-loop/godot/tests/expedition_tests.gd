extends SceneTree
## Issue #21 rules through the public command/time/save boundary, with a
## controlled wall clock (`now`) and fixed route seeds.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func exp_state(s) -> Dictionary: return s.snapshot().expedition

## The saved run dictionary, wherever the save nests the expedition state.
func _find_run(value: Variant) -> Dictionary:
	if value is Dictionary:
		if value.has("run") and value.has("charge") and value.run is Dictionary: return value.run
		for key in value:
			var found := _find_run(value[key])
			if not found.is_empty(): return found
	return {}
func roundtrip(s):
	var restored = Session.new()
	check(restored.restore(JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))), "JSON save restores")
	return restored

## Steer like a careful player: stay clear of rock now and just ahead, pushing
## the stick toward the clearest column.
func steer_clear(s, rows: Array) -> void:
	var run: Dictionary = exp_state(s).run
	var half := Vector2(0.32, 0.44)
	var y := float(run.y)
	var best := float(run.x)
	var best_score := INF
	for i in range(1, 22):
		var x := i * 0.5
		var score := absf(x - float(run.x)) * 0.01
		for ahead in [0.0, 0.3, 0.6, 1.0, 1.4]:
			if Book._overlaps(rows, x, y - ahead, half): score += 10.0 / (1.0 + ahead)
		if score < best_score: best_score = score; best = x
	s.command({"type": "expedition_steer", "input": clampf((best - float(run.x)) * 3.0, -1.0, 1.0)})

func travel(s, now: float, seconds: float, steer := true) -> Array:
	var events: Array = []
	var rows: Array = Book.route(int(exp_state(s).run.seed)).rows if exp_state(s).run != null else []
	var t := 0.0
	while t < seconds and exp_state(s).run != null:
		if steer: steer_clear(s, rows)
		var result: Dictionary = s.command({"type": "expedition_advance", "elapsed": 0.05, "now": now + t})
		events.append_array(result.get("events", []))
		t += 0.05
	return events

func run() -> void:
	var s = Session.new_session(21)
	var start_random: String = s.save_data().random_state
	check(Book.charge(s._state, 0).ready and exp_state(s).run == null, "a new restaurant begins with one full battery")
	check(not s.command({"type": "expedition_start"}).ok, "Start needs the wall clock")
	var started: Dictionary = s.command({"type": "expedition_start", "now": 1000.0, "seed": 21})
	check(started.ok and exp_state(s).run.seed == 21, "Start begins one expedition on the requested route")
	check(not Book.charge(s._state, 1000.0).ready, "Start consumes the charge")
	check(not s.command({"type": "expedition_start", "now": 1001.0, "seed": 21}).ok, "a second Start is rejected while travelling")
	check(not Book.charge(s._state, 999999.0).ready, "an unfinished expedition never recharges")
	var rows: Array = Book.route(21).rows
	check(float(exp_state(s).run.y) == rows.size() - 0.5 and float(exp_state(s).run.hull) == 100.0, "travel starts at the route bottom with full hull")
	var lead: Dictionary = Book.launch(21)
	var spans: Array = Book.route(21).spans
	check(spans[0].kind == "launch" and spans[1].kind == "launch" and spans[2].kind == "start", "routes open with two launch chunks before the start chunk")
	check(float(lead.hover) < float(lead.bottom) - 20.0 and float(lead.hover) > float(spans[1].y0), "preparation cruises most of the launch lead-in and hovers inside it")
	var y := float(lead.bottom)
	while y > float(lead.hover):
		check(not Book._overlaps(rows, float(lead.x), y, Vector2(.32, .44)), "the preparation cruise lane is open water at row %.1f" % y); y -= .25
	var cruising = Session.new_session(5)
	check(not cruising.command({"type": "expedition_start", "now": 10.0, "seed": 21, "y": float(lead.hover) - 1.0}).ok, "Start cannot skip past the launch lead-in")
	check(cruising.command({"type": "expedition_start", "now": 10.0, "seed": 21, "y": float(lead.hover)}).ok and float(exp_state(cruising).run.y) == float(lead.hover), "Start begins where the preparation cruise reached")

	# Pause freezes movement and timers; steering is ignored while paused.
	s.command({"type": "expedition_pause"})
	var frozen: Dictionary = exp_state(s).run
	var paused: Dictionary = s.command({"type": "expedition_advance", "elapsed": 5.0, "now": 1005.0})
	check(paused.ok and paused.events.is_empty() and exp_state(s).run == frozen, "Pause freezes travel and timers")
	check(not s.command({"type": "expedition_steer", "input": 1.0}).ok, "paused ship does not steer")
	s.command({"type": "expedition_resume"})

	var rules: Dictionary = Book.definition()
	check(float(rules.lateral_columns_per_second) / float(rules.forward_rows_per_second) >= float(Route.QY) / Route.QX, "full stick covers the sideways slide chunk validation assumes per row")
	check(float(rules.ship_collider[0]) == 2 * Route.SHIP_HALF[0] and float(rules.ship_collider[1]) == 2 * Route.SHIP_HALF[1], "chunk validation flies the same hull collider as travel")
	# Joystick (own run): a held stick keeps the ship moving sideways; letting go runs straight.
	var j = Session.new_session(9)
	j.command({"type": "expedition_start", "now": 10.0, "seed": 21})
	var x0 := float(exp_state(j).run.x)
	j.command({"type": "expedition_steer", "input": 1.0})
	j.command({"type": "expedition_advance", "elapsed": 0.5, "now": 11.0})
	var x1 := float(exp_state(j).run.x)
	check(x1 > x0 + 1.0 and absf(float(exp_state(j).run.vx) - float(Book.definition().lateral_columns_per_second)) < 0.001, "a held stick moves the ship sideways at the configured speed")
	j.command({"type": "expedition_steer", "input": 0.0})
	j.command({"type": "expedition_advance", "elapsed": 0.3, "now": 11.5})
	var x2 := float(exp_state(j).run.x)
	j.command({"type": "expedition_advance", "elapsed": 0.5, "now": 12.0})
	check(float(exp_state(j).run.vx) == 0.0 and float(exp_state(j).run.x) == x2 and x2 < x1 + 0.5, "releasing the stick eases to a stop and runs straight")
	j.command({"type": "expedition_steer", "input": 0.4}); j.command({"type": "expedition_pause"})
	check(float(exp_state(j).run.steer) == 0.0 and float(exp_state(j).run.vx) == 0.0, "Pause lets go of the stick")
	j.command({"type": "expedition_resume"})
	check(j.command({"type": "expedition_steer", "input": -5.0}).ok and float(exp_state(j).run.steer) == -1.0, "stick input is clamped to full deflection")
	var edge_guard := 0
	while exp_state(j).run != null and float(exp_state(j).run.x) > 0.4 and edge_guard < 200:
		j.command({"type": "expedition_advance", "elapsed": 0.05, "now": 13.0}); edge_guard += 1
	check(exp_state(j).run != null and float(exp_state(j).run.x) == 0.4 and float(exp_state(j).run.vx) == 0.0, "steering clamps at the world edge")

	# Push into the canyon wall until the first contact, then hold the stick still.
	s.command({"type": "expedition_steer", "input": -1.0})
	var approach := 0
	while approach < 200 and not s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 1008.0}).events.any(func(e): return e.type == "impact"): approach += 1
	s.command({"type": "expedition_steer", "input": 0.0})
	s.command({"type": "expedition_advance", "elapsed": 0.25, "now": 1008.5})

	# Impacts: damage, brief protection, steering preserved without knockback.
	var hits := 0
	var x_before := float(exp_state(s).run.x)
	var t := 0.0
	var first_hit := -1.0
	var second_hit := -1.0
	while t < 3.0 and exp_state(s).run != null:
		var result: Dictionary = s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 1010.0 + t})
		for e in result.events:
			if e.type == "impact":
				hits += 1
				if first_hit < 0: first_hit = t
				elif second_hit < 0: second_hit = t
		t += 0.05
	check(first_hit >= 0.0 and float(exp_state(s).run.hull) < 100.0, "running into rock damages the hull")
	check(second_hit < 0 or second_hit - first_hit >= 1.15, "hit protection prevents repeated damage from one collision")
	check(exp_state(s).run == null or float(exp_state(s).run.x) == x_before, "impacts never push the ship sideways")
	check(exp_state(s).run == null or exp_state(s).run.low_hull == (exp_state(s).run.hull_fraction <= 0.35), "low hull flag follows the configured threshold")

	# Keep crashing to deplete the hull.
	var ended: Dictionary = {}
	var guard := 0
	while exp_state(s).run != null and guard < 2000:
		var result: Dictionary = s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 1020.0})
		for e in result.events:
			if e.type == "ended": ended = e.result
		guard += 1
	check(ended.get("outcome") == "hull_depleted" and ended.bonus == 0, "zero hull ends as Hull depleted without completion bonus")
	check(exp_state(s).salvage == ended.total and ended.total == ended.pickups, "earned pickups are banked on failure")
	check(exp_state(s).result.outcome == "hull_depleted", "the receipt stays for the results screen")
	check(s.save_data().random_state == start_random, "expeditions never consume restaurant randomness")

	# Night recharge: fixed duration from the end, offline, capped at one launch.
	check(not Book.charge(s._state, 1020.0 + 149.0).ready and absf(Book.charge(s._state, 1169.0).remaining - 1.0) < 0.001, "charging shows the actual time remaining")
	check(Book.charge(s._state, 1020.0 + 150.0).ready, "recharge completes after the configured duration")
	check(Book.charge(s._state, 5_000_000.0).ready and Book.charge(s._state, 900.0).remaining == 150.0, "offline time recharges; a clock moved back never extends the wait")
	check(not s.command({"type": "expedition_start", "now": 2000.0, "seed": 7}).ok, "results must be acknowledged before departing again")
	var receipt_id: int = exp_state(s).result.id
	var reloaded = roundtrip(s)
	check(reloaded.snapshot().expedition.salvage == exp_state(s).salvage and reloaded.snapshot().expedition.result == exp_state(s).result, "reloading a finished expedition never replays its rewards")
	check(s.command({"type": "expedition_acknowledge", "id": receipt_id}).ok and exp_state(s).result == null, "Restaurant acknowledges the receipt")
	check(s.command({"type": "expedition_acknowledge", "id": receipt_id}).changed == false, "a repeated acknowledgement does nothing")
	var banked: int = exp_state(s).salvage

	# A careful complete run earns pickups plus the completion bonus.
	var rotation: int = s.snapshot().floor_styles.rotation
	check(s.command({"type": "expedition_start", "now": 5000.0, "seed": 7}).ok, "a recharged battery allows exactly one new departure")
	check(not s.command({"type": "expedition_start", "now": 99999.0, "seed": 7}).ok, "charge cannot bank a second launch")
	var events := travel(s, 5000.0, 400.0)
	var finish: Dictionary = {}
	for e in events:
		if e.type == "ended": finish = e.result
	var pickups := events.filter(func(e): return e.type == "pickup").size()
	check(finish.get("outcome") == "complete", "steering clear of rock reaches Expedition complete (%s)" % finish.get("outcome"))
	check(finish.get("bonus") == int(Book.definition().completion_bonus) and finish.pickups == pickups * int(Book.definition().salvage_per_pickup), "complete earns pickups plus the completion bonus")
	check(exp_state(s).salvage == banked + finish.total, "salvage is committed exactly once")
	check(s.snapshot().floor_styles.rotation == rotation + 1, "an ended expedition refreshes floor stock once")
	s.command({"type": "expedition_acknowledge"})

	# Suspend mid-run and reopen: identical travel continues deterministically.
	check(s.command({"type": "expedition_start", "now": 99999.0, "seed": 3}).ok, "depart again after recharge")
	travel(s, 99999.0, 6.0)
	s.command({"type": "expedition_pause"})
	var reopened = roundtrip(s)
	check(reopened.snapshot().expedition.run == exp_state(s).run, "background/close saves the unfinished run exactly")
	check(not Book.charge(reopened._state, 1e9).ready, "a suspended expedition does not recharge")
	var joystick_save: Dictionary = JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))
	var legacy_run: Dictionary = _find_run(joystick_save)
	legacy_run.erase("steer"); legacy_run.erase("vx")
	var straight = Session.new()
	check(straight.restore(joystick_save) and float(straight.snapshot().expedition.run.steer) == 0.0 and float(straight.snapshot().expedition.run.vx) == 0.0, "unfinished runs saved before joystick steering reopen running straight")
	for session in [s, reopened]:
		session.command({"type": "expedition_resume"})
		session.command({"type": "expedition_advance", "elapsed": 1.0, "now": 100010.0})
	check(reopened.snapshot().expedition.run == exp_state(s).run, "resumed travel continues identically after reopening")

	# Early return needs the pause card, keeps the haul and gives no bonus.
	check(not s.command({"type": "expedition_return_early", "now": 100020.0}).ok, "early return is only offered while paused")
	s.command({"type": "expedition_pause"})
	var haul: int = exp_state(s).run.salvage
	var early: Dictionary = s.command({"type": "expedition_return_early", "now": 100020.0})
	check(early.ok and early.result.outcome == "returned_early" and early.result.bonus == 0 and early.result.pickups == haul, "Return early keeps the haul without a completion bonus")
	check(not Book.charge(s._state, 100020.0 + 100.0).ready and Book.charge(s._state, 100020.0 + 150.0).ready, "early return starts the night recharge")

	# Corrupt or future saves are rejected without touching the session.
	s.command({"type": "expedition_acknowledge"})
	s.command({"type": "expedition_start", "now": 200000.0, "seed": 5})
	travel(s, 200000.0, 3.0)
	var good: Dictionary = JSON.parse_string(JSON.stringify(s.save_data()))
	for kind in ["future", "zero_hull", "duplicate_pickup", "salvage_mismatch", "charge_during_run", "bad_seed"]:
		var corrupt: Dictionary = good.duplicate(true)
		var run_data: Dictionary = corrupt.state.expedition.run
		match kind:
			"future": corrupt.expedition_version = 99
			"zero_hull": run_data.hull = 0
			"duplicate_pickup": run_data.collected = [0, 0]; run_data.salvage = 4
			"salvage_mismatch": run_data.salvage = int(run_data.salvage) + 1
			"charge_during_run": corrupt.state.expedition.charge = {"ready": true, "recharge_started": null}
			"bad_seed": run_data.seed = 0
		var target = Session.new_session(9)
		var before: Dictionary = target.save_data()
		check(not target.restore(corrupt) and target.save_data() == before, "corrupt %s save rejected without mutating the session" % kind)

	# Saves from before #21 migrate with a full battery and no salvage.
	var legacy: Dictionary = JSON.parse_string(JSON.stringify(Session.new_session(4).save_data()))
	legacy.erase("expedition_version"); legacy.state.erase("expedition")
	var migrated = Session.new()
	check(migrated.restore(legacy) and Book.charge(migrated._state, 0).ready and migrated.snapshot().expedition.salvage == 0, "legacy saves gain one full battery")

	print("Expedition rules: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)
