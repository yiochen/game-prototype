extends SceneTree
## Issue #24 rules: the hooked pursuit (shared speed-up through route terrain,
## resistance as the creature's draining health, hull-only collisions), the
## catch that commits the recipe discovery before any presentation, the escape
## when the hull gives out, and their save/reopen behaviour, through the public
## command/time/save boundary with a controlled clock.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
const SEED := 23
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func run_of(s) -> Variant: return s.snapshot().expedition.run
func live(s) -> Dictionary: return s._state.expedition.run
func types(events: Array) -> Array: return events.map(func(e): return e.type)

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

## A run hooked in the arena, ship under the creature, nothing in the way.
func hooked(session_seed := 7):
	var s = Session.new_session(session_seed)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	var r: Dictionary = live(s)
	r.y = float(Book.run_route(r).encounter_start) + 0.02; r.x = 5.5; r.vx = 0.0; r.steer = 0.0
	advance(s, 0.1)
	advance(s, float(Book.definition().encounter.arrive_seconds))
	live(s).x = Book.creature_centre(live(s)).x
	s.command({"type": "expedition_fire"})
	for i in range(80):
		if "hooked" in types(advance(s, 0.05)): break
	return s

func run() -> void:
	var rules: Dictionary = Book.definition().encounter
	var travel := float(Book.definition().forward_rows_per_second)

	# The route: ordinary terrain after the arena, long enough for a whole chase, and flyable.
	for seed_value in [SEED, 3, 7, 21, 99]:
		var path := Book.route(seed_value)
		var chase_rows := float(path.arena.y0)
		var needed := travel * float(rules.pursuit_speed_multiplier) * float(rules.resistance) / float(rules.resistance_drain_per_second)
		check(chase_rows >= needed - (float(rules.arena_rows) - travel * float(rules.window_seconds)), "seed %d leaves %d rows of terrain after the arena (a chase needs about %d)" % [seed_value, int(chase_rows), int(needed)])
		check(Route.ship_problems(path.rows).is_empty(), "seed %d: the whole version 4 route flies, arena seams included" % seed_value)
		check(path.shields.all(func(b): return b.y > float(path.encounter_edge)) and path.portals.all(func(p): return p.y > float(path.encounter_edge)), "seed %d: no shield or portal in the arena or the chase" % seed_value)

	# Pursuit: ship and creature speed up together; the cable has no range limit.
	var s = hooked()
	check(run_of(s).encounter.state == "hooked", "the run is hooked")
	var y0 := float(run_of(s).y)
	advance(s, float(rules.pursuit_ramp_seconds))
	var y1 := float(run_of(s).y)
	advance(s, 1.0)
	var pace := y1 - float(run_of(s).y)
	check(absf(pace - travel * float(rules.pursuit_speed_multiplier)) < 0.02, "after the ramp the chase runs at %.1f× travel speed (%.2f rows/s)" % [float(rules.pursuit_speed_multiplier), pace])
	check(y0 - y1 > travel * float(rules.pursuit_ramp_seconds), "the ramp already speeds up")
	var ahead := float(run_of(s).y) - Book.creature_centre(run_of(s)).y
	check(absf(ahead - float(rules.lead_rows)) < 0.01, "the creature keeps its lead: it speeds up with the ship")
	live(s).x = 1.0
	advance(s, 0.5)
	check(run_of(s).encounter.state == "hooked", "steering far from the creature never breaks the hook")
	check(s.command({"type": "expedition_fire"}).reason == "no_target", "only one harpoon: none fires during the pursuit")

	# Resistance drains steadily and never refills; collisions cost hull only.
	var r0 := float(run_of(s).encounter.resistance)
	advance(s, 2.0)
	var r1 := float(run_of(s).encounter.resistance)
	check(absf((r0 - r1) - 2.0 * float(rules.resistance_drain_per_second)) < 0.05, "resistance drains %.1f per second" % float(rules.resistance_drain_per_second))
	var rows: Array = Book.run_route(live(s)).rows
	var rock := Vector2(-1, -1)
	for ry in range(int(run_of(s).y) - 2, int(run_of(s).y) - 30, -1):
		for rx in range(1, 10):
			if Route.is_rock(str(rows[ry])[rx]) and not Route.is_rock(str(rows[ry + 1])[rx]): rock = Vector2(rx + .5, ry + .5); break
		if rock.x > 0: break
	live(s).x = rock.x; live(s).y = rock.y + .6; live(s).protection = 0.0
	var before := float(run_of(s).encounter.resistance)
	var hit := advance(s, 0.05)
	check("impact" in types(hit) and float(run_of(s).hull) < float(Book.definition().hull_max), "a collision during the pursuit dents the hull")
	check(float(run_of(s).encounter.resistance) <= before, "a collision never restores resistance")
	check(run_of(s).encounter.state == "hooked", "a collision keeps the creature hooked")

	# Save mid-pursuit: resistance, hull and timers reopen exactly.
	s.command({"type": "expedition_pause"})
	var reopened = roundtrip(s)
	check(run_of(reopened).encounter.resistance == run_of(s).encounter.resistance and run_of(reopened).hull == run_of(s).hull and run_of(reopened).encounter.chase_t == run_of(s).encounter.chase_t, "an unfinished pursuit reopens with its resistance, hull and timers")
	s.command({"type": "expedition_resume"})

	# The catch: zero resistance commits the discovery, then the run completes.
	var recipe := str(rules.recipe)
	check(not recipe in s.snapshot().recipe_book.discovered, "the eel's recipe starts undiscovered")
	# The steady drain was measured above; skip to its last moment.
	live(s).encounter.resistance = 1.0
	var salvage := int(run_of(s).salvage)
	var events := advance(s, 1.0)
	var caught: Array = events.filter(func(e): return e.type == "caught")
	var ended: Array = events.filter(func(e): return e.type == "ended")
	check(caught.size() == 1 and caught[0].first and types(events).find("caught") < types(events).find("ended"), "zero resistance lands the catch once, before the run ends")
	check(ended.size() == 1 and ended[0].result.outcome == "complete" and int(ended[0].result.bonus) == int(Book.definition().completion_bonus), "after the catch the ship finishes on its own: complete, with the completion bonus")
	check(ended[0].result.creature == {"id": str(rules.creature), "outcome": "caught", "recipe": recipe, "first": true}, "the receipt records the first catch and its recipe")
	check(int(ended[0].result.pickups) == salvage, "hazards end with the catch: no more travel or pickups")
	var book: Dictionary = s.snapshot().recipe_book
	check(recipe in book.discovered and recipe in book.new, "the recipe is discovered and marked NEW")
	check(run_of(s) == null, "the run is over: a completed catch never resumes as a pursuit")
	# Reopen during the cutscene, award or results: the discovery and outcome hold, once.
	reopened = roundtrip(s)
	check(run_of(reopened) == null and reopened.snapshot().expedition.result.creature.first, "reopening after the catch keeps the completed outcome")
	check(reopened.snapshot().recipe_book.discovered.count(recipe) == 1 and reopened.snapshot().recipe_book.new.count(recipe) == 1, "reopening never duplicates the discovery")
	check(reopened.command({"type": "expedition_acknowledge"}).ok and reopened.snapshot().recipe_book.new.has(recipe), "Continue past the results leaves the recipe NEW for the restaurant")

	# A repeat catch awards no new discovery.
	s.command({"type": "expedition_acknowledge"})
	# Inspected in the restaurant: NEW cleared.
	s._state.recipe_book.new.erase(recipe)
	s._state.expedition.charge = {"ready": true, "recharge_started": null}
	var r2 = s
	r2.command({"type": "expedition_start", "now": 5000.0, "seed": SEED})
	var rr: Dictionary = live(r2)
	rr.y = float(Book.run_route(rr).encounter_start) + 0.02; rr.x = 5.5
	advance(r2, 0.1); advance(r2, float(rules.arrive_seconds))
	live(r2).x = Book.creature_centre(live(r2)).x
	r2.command({"type": "expedition_fire"})
	for i in range(80):
		if "hooked" in types(advance(r2, 0.05)): break
	r2.command({"type": "expedition_cheat_catch"})
	events = advance(r2, 0.5)
	ended = events.filter(func(e): return e.type == "ended")
	check(ended.size() == 1 and ended[0].result.creature.first == false, "a repeat catch is not a first discovery")
	check(not r2.snapshot().recipe_book.new.has(recipe), "a repeat catch never re-marks the recipe NEW")

	# Zero hull during the pursuit: the creature escapes for good, no recipe.
	s = hooked(11)
	live(s).hull = float(Book.definition().impact_damage)
	rows = Book.run_route(live(s)).rows
	rock = Vector2(-1, -1)
	for ry in range(int(run_of(s).y) - 2, int(run_of(s).y) - 40, -1):
		for rx in range(1, 10):
			if Route.is_rock(str(rows[ry])[rx]) and not Route.is_rock(str(rows[ry + 1])[rx]): rock = Vector2(rx + .5, ry + .5); break
		if rock.x > 0: break
	live(s).x = rock.x; live(s).y = rock.y + .6; live(s).protection = 0.0
	events = advance(s, 0.1)
	ended = events.filter(func(e): return e.type == "ended")
	check("creature_lost" in types(events) and ended.size() == 1 and ended[0].result.outcome == "hull_depleted", "zero hull ends the pursuit as Hull depleted")
	check(ended[0].result.creature == {"id": str(rules.creature), "outcome": "escaped"} and int(ended[0].result.bonus) == 0, "the creature escapes: no recipe, no completion bonus")
	check(not recipe in s.snapshot().recipe_book.discovered, "no discovery after an escape")
	check(s.snapshot().expedition.run == null, "the only pursuit attempt is over: it cannot be rehooked")

	var data: Dictionary

	# Invalid saves are rejected.
	s = hooked(17)
	data = GameSession.flat_view(s.save_data())
	data.state.expedition.run.encounter.resistance = 150.0
	check(not Session.new().restore(data), "resistance above the creature's maximum is rejected")
	data = GameSession.flat_view(s.save_data())
	data.state.expedition.run.encounter.chase_t = -1.0
	check(not Session.new().restore(data), "a negative pursuit clock is rejected")

	print("Expedition pursuit tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() else 0)
