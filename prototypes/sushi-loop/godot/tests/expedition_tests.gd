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

func types_of(events: Array) -> Array: return events.map(func(e): return e.type)

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
	check(float(rules.ship_radius) <= minf(Route.SHIP_HALF[0], Route.SHIP_HALF[1]), "the travel hull circle fits inside the box chunk validation flies, so validated routes stay passable")
	# Round collision: a glancing pass by a rock's corner is forgiven; a head-on touch still hits.
	var reach := float(rules.ship_radius)
	var lone := ["...", ".#.", "..."]
	check(Book._overlaps(lone, 2.25, 2.3, Vector2(.32, .44)) and not Book._collides(lone, 2.25, 2.3, reach), "brushing a rock's corner no longer dents the hull")
	check(Book._collides(lone, 1.5, 2.1, reach) and Book._collides(lone, 2.15, 1.5, reach), "touching a rock's face still does")
	# A straight wall is one flat face: no notches at the seams between rocks.
	var wall := ["...........", "..######...", "...........", "...........", "..........."]
	var r_ship := float(rules.ship_radius)
	var face := 2.0 - float(rules.rock_inset)
	var flat := true
	for i in range(0, 41):
		var wx := 2.6 + i * 0.1
		flat = flat and Book._collides(wall, wx, face + r_ship - 0.01, r_ship) and not Book._collides(wall, wx, face + r_ship + 0.01, r_ship)
	check(flat, "a wall of rocks presents one flat face, seams included")
	# Pressed into it while steering, the ship slides along instead of catching in a seam.
	var slide := Vector2(3.0, 2.6)
	for i in range(30):
		slide += Vector2(float(rules.lateral_columns_per_second), -float(rules.forward_rows_per_second)) * 0.05
		if Book._collides(wall, slide.x, slide.y, r_ship): slide = Book._nearest_clear(wall, slide, r_ship + float(rules.knockback_clearance))
	check(slide.x > 7.5, "steering along a wall slides past its seams (reached x %.2f)" % slide.x)

	# Against a current pushing the other way, steering still slides along a wall and out of its gap.
	var rows_cw: Array = []
	for row in range(40): rows_cw.append("##########." if row == 20 else "...........")
	var currents_cw := {}
	for row in range(20, 26):
		for col in range(11): currents_cw[Vector2i(col, row)] = -1
	Book._routes["9999:%d" % int(rules.route_version)] = {"rows": rows_cw, "spans": [], "pickups": [], "columns": 11, "launch_top": 39.5, "currents": currents_cw,
		"shields": [], "portals": [], "encounter_edge": 0.0, "version": int(rules.route_version), "arena": null, "encounter_start": null}
	var cw = Session.new_session(5)
	cw.command({"type": "expedition_start", "now": 10.0, "seed": 9999})
	var cr: Dictionary = cw._state.expedition.run
	cr.x = 5.5; cr.y = 21.6; cr.vx = 0.0
	cw.command({"type": "expedition_steer", "input": 1.0})
	for i in range(100):
		cr.protection = 5.0
		cw.command({"type": "expedition_advance", "elapsed": 0.05, "now": 11.0})
	check(float(cr.y) < 20.0, "steering against a current slides along a wall and escapes through its gap (x %.2f, y %.2f)" % [float(cr.x), float(cr.y)])
	Book._routes.erase("9999:%d" % int(rules.route_version))

	# Rock is solid: a hit knocks the ship back to the nearest clear water, once per dent.
	var k = Session.new_session(11)
	k.command({"type": "expedition_start", "now": 10.0, "seed": 21})
	var krows: Array = Book.route(21).rows
	var rock := Vector2(-1, -1)
	for ry in range(krows.size() - 30, 40, -1):
		for rx in range(2, 9):
			if Route.is_rock(str(krows[ry])[rx]) and not Route.is_rock(str(krows[ry + 1])[rx]) and not Route.is_rock(str(krows[ry + 2])[rx]): rock = Vector2(rx + .5, ry + .5); break
		if rock.x > 0: break
	var kr: Dictionary = k._state.expedition.run
	kr.x = rock.x; kr.y = rock.y + .65; kr.vx = 0.0; kr.steer = 0.0
	var kres: Dictionary = k.command({"type": "expedition_advance", "elapsed": 0.05, "now": 11.0})
	var knocked: Array = kres.get("events", []).filter(func(e): return e.type == "impact")
	check(knocked.size() == 1 and float(kr.hull) == 75.0, "running into rock dents the hull once")
	check(not Book._collides(krows, float(kr.x), float(kr.y), reach), "and knocks the ship out to clear water")
	var moved := Vector2(float(kr.x), float(kr.y)).distance_to(Vector2(float(knocked[0].from_x), float(knocked[0].from_y)))
	check(moved > 0.0 and moved < 1.0 and float(kr.y) >= float(knocked[0].from_y) - .001, "the knock-back is the shortest way out, never ahead (%.2f cells)" % moved)
	kr.x = rock.x; kr.y = rock.y + .65
	var bumped: Array = k.command({"type": "expedition_advance", "elapsed": 0.05, "now": 11.1}).events
	check(types_of(bumped) == ["bump"] and float(exp_state(k).run.hull) == 75.0 and not Book._collides(krows, float(exp_state(k).run.x), float(exp_state(k).run.y), reach), "during hit protection rock still pushes the ship out, without damage")

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
		# Hit protection held on, so leaning on the wall never wrecks the hull.
		j._state.expedition.run.protection = 5.0
		j.command({"type": "expedition_advance", "elapsed": 0.05, "now": 13.0}); edge_guard += 1
	var jx := float(exp_state(j).run.x) if exp_state(j).run != null else -1.0
	check(jx >= 0.4 and not Book._collides(Book.route(21).rows, jx, float(exp_state(j).run.y), float(rules.ship_radius)), "steering stops at the canyon wall or the world edge, never inside rock")

	# Push into the canyon wall until the first contact, then hold the stick still.
	s.command({"type": "expedition_steer", "input": -1.0})
	var approach := 0
	while approach < 200 and not s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 1008.0}).events.any(func(e): return e.type == "impact"): approach += 1

	# Impacts: damage, brief protection, and a knock-back out of the rock.
	# Keep pushing into the wall: later dents wait for hit protection.
	var hits := 1 if approach < 200 else 0
	var t := 0.0
	var first_hit := 0.0 if hits else -1.0
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
	s.command({"type": "expedition_steer", "input": 0.0})
	check(exp_state(s).run == null or not Book._collides(Book.route(21).rows, float(exp_state(s).run.x), float(exp_state(s).run.y), float(rules.ship_radius)), "impacts push the ship out of the rock")
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
	for session in [s, reopened]:
		session.command({"type": "expedition_resume"})
		session.command({"type": "expedition_advance", "elapsed": 1.0, "now": 100010.0})
	check(reopened.snapshot().expedition.run == exp_state(s).run, "resumed travel continues identically after reopening")

	# Give up needs the pause card, keeps the haul and gives no bonus.
	check(not s.command({"type": "expedition_give_up", "now": 100020.0}).ok, "Give up is only offered while paused")
	s.command({"type": "expedition_pause"})
	var haul: int = exp_state(s).run.salvage
	var gave_up: Dictionary = s.command({"type": "expedition_give_up", "now": 100020.0})
	check(gave_up.ok and gave_up.result.outcome == "gave_up" and gave_up.result.bonus == 0 and gave_up.result.pickups == haul, "Give up keeps the haul without a completion bonus")
	check(not Book.charge(s._state, 100020.0 + 100.0).ready and Book.charge(s._state, 100020.0 + 150.0).ready, "Give up starts the night recharge")

	# Corrupt or future saves are rejected without touching the session.
	s.command({"type": "expedition_acknowledge"})
	s.command({"type": "expedition_start", "now": 200000.0, "seed": 5})
	travel(s, 200000.0, 3.0)
	var good: Dictionary = JSON.parse_string(JSON.stringify(s.save_data()))
	for kind in ["future", "zero_hull", "duplicate_pickup", "salvage_mismatch", "charge_during_run", "bad_seed"]:
		var corrupt: Dictionary = GameSession.flat_view(good.duplicate(true))
		var run_data: Dictionary = corrupt.state.expedition.run
		match kind:
			"future": corrupt.version = 99
			"zero_hull": run_data.hull = 0
			"duplicate_pickup": run_data.collected = [0, 0]; run_data.salvage = 4
			"salvage_mismatch": run_data.salvage = int(run_data.salvage) + 1
			"charge_during_run": corrupt.state.expedition.charge = {"ready": true, "recharge_started": null}
			"bad_seed": run_data.seed = 0
		var target = Session.new_session(9)
		var before: Dictionary = target.save_data()
		check(not target.restore(corrupt) and target.save_data() == before, "corrupt %s save rejected without mutating the session" % kind)

	print("Expedition rules: %s checks, %s failures" % [count, failures.size()])
	quit(0 if failures.is_empty() else 1)
