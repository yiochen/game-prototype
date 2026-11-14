extends SceneTree
## Issue #70 rules: the Inkfin Cuttlefish's ink blackout, through the public
## command/time/save boundary with a controlled clock. Covers which species a
## dive meets, the sight check that keeps the ink fair, one burst per ink zone
## (warn, seep in, hold, linger into the next chunk, lift), that ink never
## hurts or changes collision, the catch and its recipe, and save/restore.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
const Sight = preload("res://scripts/expedition/sight.gd")
const INKFIN := "inkfin-cuttlefish"
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

func copy(s):
	var restored = Session.new()
	restored.restore(JSON.parse_string(JSON.stringify(s.save_data(), "", true, true)))
	return restored

## An Inkfin run hooked in the arena, at full chase speed.
func hooked(route_seed := SEED):
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": route_seed, "creature": INKFIN})
	var r: Dictionary = live(s)
	r.y = float(Book.run_route(r).encounter_start) + 0.02; r.x = 5.5; r.vx = 0.0; r.steer = 0.0
	advance(s, 0.1)
	advance(s, float(Book.definition().encounter.arrive_seconds))
	for shot in range(6):
		live(s).x = Book.creature_centre(live(s)).x; live(s).vx = 0.0
		s.command({"type": "expedition_fire"})
		for i in range(60):
			if "hooked" in types(advance(s, 0.05)): return s
			if live(s).encounter.harpoon == null and float(live(s).encounter.cooldown) <= 0.0: break
	return s

## Hooked, at the entry of the run's `which` ink zone, kept out of harm's way.
func at_zone(route_seed: int, which: int):
	var s = hooked(route_seed)
	advance(s, float(Book.definition().encounter.pursuit_ramp_seconds) + 0.1)
	var r: Dictionary = live(s)
	var zone: Dictionary = Book.run_route(r).ink_zones[which]
	r.y = float(zone.y1) + 1.2; r.x = Book._centre_of(str(Book.run_route(r).rows[int(zone.y1)])); r.vx = 0.0
	r.encounter.resistance = 1e6
	return s

## Put the test's helping hands back within what a real save may hold.
func tidy(s) -> void:
	live(s).encounter.resistance = 50.0; live(s).protection = 1.0

## Fly on, keeping the ship in open water and the creature alive, until `done` holds.
func fly(s, done: Callable, limit := 60.0) -> Array:
	var events: Array = []
	var t := 0.0
	while t < limit and run_of(s) != null and not done.call():
		var r: Dictionary = live(s)
		r.protection = 5.0; r.encounter.resistance = 1e6
		var rows: Array = Book.run_route(r).rows
		r.x = Book._centre_of(str(rows[clampi(int(floor(float(r.y) - 0.6)), 0, rows.size() - 1)])); r.vx = 0.0
		events.append_array(advance(s, 0.05)); t += 0.05
	return events

func run() -> void:
	var rules := Book.definition()
	var k: Dictionary = rules.encounter.ink

	# --- species
	check(Book.creatures() == ["storm-eel", INKFIN, "boulderhead-parrotfish"] and str(Book.species(INKFIN).recipe) == "ika_nigiri", "the catalog lists the eel, the Inkfin with its recipe and the parrotfish")
	var fresh = Session.new_session(7)
	var seen := {}
	for i in range(40):
		fresh._state.expedition.sequence = i
		seen[Book.next_creature(fresh._state)] = true
	check(seen.size() == 3, "with nothing caught, dives meet any species")
	fresh._state.recipe_book.discovered.append("eel_roll")
	fresh._state.recipe_book.discovered.append("budai_sashimi")
	var only := true
	for i in range(40):
		fresh._state.expedition.sequence = i
		if Book.next_creature(fresh._state) != INKFIN: only = false
	check(only, "once the others are caught, dives meet the uncaught Inkfin")
	fresh._state.recipe_book.discovered.append("ika_nigiri")
	seen = {}
	for i in range(40):
		fresh._state.expedition.sequence = i
		seen[Book.next_creature(fresh._state)] = true
	check(seen.size() == 3, "with all caught, any species returns")
	var plain = Session.new_session(7)
	plain.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	check(Book.creature_of(live(plain)) == "storm-eel", "a chosen seed without a species meets the Storm Eel")
	check(not Session.new_session(7).command({"type": "expedition_start", "now": 1000.0, "seed": SEED, "creature": "kraken"}).ok, "an unknown species is refused")

	# --- sight check
	check(Sight.shift_per_row(rules) == 1, "at chase handling the ship moves one column per row")
	var open: Array = []
	for i in range(8): open.append("#.........#")
	check(Sight.problems(open, rules).is_empty(), "open water is fair")
	var trap: Array = ["####.######", "####.######", "####.######", "#...#.....#", "#...#.....#", "#...#.....#", "#...#.....#", "#...#.....#", "#.........#", "#.........#"]
	check(not Sight.problems(trap, rules).is_empty(), "a deep dead-end branch is not fair")
	var by_id := {}
	for c in Book.library(): by_id[c.id] = c
	check(by_id.has("fork-ruin-split") and not Sight.problems(by_id["fork-ruin-split"].rows, rules).is_empty(), "Ruin Split fails the sight check")
	var normals: Array = Book.library().filter(func(c): return c.kind == "normal")
	check(normals.size() >= 10 and normals.all(func(c): return Book.ink_fair(c)), "every ordinary chunk passes at %s clear rows" % str(k.clear_rows))

	# --- routes
	for seed_value in [3, 7, 23, 101, 2026]:
		var path := Book.route(seed_value, INKFIN)
		check(path.zones.is_empty() and path.ink_zones.size() == 3 and path.ink_zones.all(func(z): return z.y1 < path.arena.y0), "seed %d: three ink zones after the arena, no eel zones" % seed_value)
		check(path.spans.all(func(sp): return sp.kind != "creature"), "seed %d: no eel chunks on an Inkfin route" % seed_value)
		for z in path.ink_zones:
			var chunk: Dictionary = by_id[z.id]
			check(Book.ink_fair(chunk), "seed %d: ink zone %s passes the sight check" % [seed_value, z.id])
			check(int(z.y0) - int(z.end) == mini(int(k.linger_rows), int(path.spans[int(z.span) + 1].y1) - int(path.spans[int(z.span) + 1].y0) + 1), "seed %d: the ink lingers into the next ordinary chunk" % seed_value)
		check(Book.route(seed_value).ink_zones.is_empty() and Book.route(seed_value).zones.size() == 3, "seed %d: the eel's route keeps its zones and has no ink" % seed_value)

	# --- one burst
	var s = at_zone(SEED, 0)
	var zone: Dictionary = Book.run_route(live(s)).ink_zones[0]
	check(live(s).encounter.ink == null, "no ink before the zone")
	var events := fly(s, func(): return live(s).encounter.ink != null)
	check("ink_warn" in types(events) and live(s).encounter.ink.phase == "warn" and Book.ink_cover(live(s)) == 0.0, "entering the zone starts the warning with the sea still in view")
	check(float(live(s).y) < float(zone.y1) + 1.0 - float(k.entry_rows) + 0.2, "the warning starts as the ship enters")
	var hull := float(live(s).hull)
	events = fly(s, func(): return live(s).encounter.ink.phase != "warn")
	check("ink_spread" in types(events) and absf(float(live(s).encounter.ink.t)) < 0.06, "after %s s the ink starts to spread" % str(k.warn_seconds))
	advance(s, float(k.spread_seconds) * 0.5)
	var half := Book.ink_cover(live(s))
	check(half > 0.4 and half < 0.6, "half-way through the spread about half the sea is covered")
	fly(s, func(): return live(s).encounter.ink.phase == "hold")
	check(Book.ink_cover(live(s)) == 1.0, "then the ink holds at full cover")
	tidy(s)
	var restored = copy(s)
	check(restored.snapshot().expedition.run != null and restored._state.expedition.run.encounter.ink.phase == "hold" and restored._state.expedition.run.creature == INKFIN, "a save restores the ink and the species")
	var a := types(advance(s, 1.0))
	var b := types(advance(restored, 1.0))
	check(a == b and absf(float(live(s).y) - float(restored._state.expedition.run.y)) < 0.0001, "the restored run plays on identically")
	fly(s, func(): return float(live(s).y) < float(zone.y0) - 1.0)
	check(live(s).encounter.ink != null and live(s).encounter.ink.phase == "hold", "the ink lingers past the zone into the next chunk")
	events = fly(s, func(): return live(s).encounter.ink == null or live(s).encounter.ink.phase == "lift")
	check("ink_lift" in types(events) and absf(float(live(s).y) - float(zone.end) - float(k.clear_rows)) < 0.3, "it lifts once the ship's clear sight reaches where the ink ends")
	events = fly(s, func(): return live(s).encounter.ink == null)
	check("ink_end" in types(events) and Book.ink_cover(live(s)) == 0.0, "after %s s it is gone" % str(k.lift_seconds))
	check(float(live(s).hull) == hull and int(live(s).impacts) == 0, "ink never costs hull")
	check(int(zone.y0) in live(s).encounter.inked, "the zone is spent")
	var second: Dictionary = Book.run_route(live(s)).ink_zones[1]
	# A short chunk between the zones can be inked end to end; no new burst starts before the second zone.
	events = fly(s, func(): return float(live(s).y) < float(second.y1) + 1.5)
	check(not "ink_warn" in types(events), "one burst per zone")
	events = fly(s, func(): return live(s).encounter.ink != null or float(live(s).y) < float(second.y0))
	check(live(s).encounter.ink != null and float(live(s).y) >= float(second.y0), "the second zone starts its own burst")

	# --- collision under ink is the terrain's own
	var c = at_zone(SEED, 0)
	fly(c, func(): return live(c).encounter.ink != null and live(c).encounter.ink.phase == "hold")
	var rows: Array = Book.run_route(live(c)).rows
	var blocked := 0
	var same := true
	for y in range(int(zone.y0), int(zone.y1) + 1):
		for x in range(Route.COLUMNS):
			if Book._collides(rows, x + 0.5, y + 0.5, float(rules.ship_radius)): blocked += 1
			if Book._collides(rows, x + 0.5, y + 0.5, float(rules.ship_radius)) != Book._collides(Book.route(SEED, INKFIN).rows, x + 0.5, y + 0.5, float(rules.ship_radius)): same = false
	check(blocked > 0 and same, "ink changes nothing about what blocks the ship")

	# --- the catch clears it and awards the recipe once
	var d = at_zone(SEED, 0)
	fly(d, func(): return live(d).encounter.ink != null and live(d).encounter.ink.phase == "hold")
	live(d).encounter.resistance = 0.5
	var ending := advance(d, 1.0)
	check("caught" in types(ending) and run_of(d) == null, "a catch under the ink ends the run")
	var result: Dictionary = d.snapshot().expedition.result
	check(result.outcome == "complete" and result.creature.id == INKFIN and result.creature.recipe == "ika_nigiri" and result.creature.first, "it records the Inkfin and its first Ika nigiri")
	check("ika_nigiri" in d._state.recipe_book.discovered and not "eel_roll" in d._state.recipe_book.discovered, "only the Inkfin's recipe is discovered")
	check(copy(d).snapshot().expedition.result.creature.id == INKFIN, "the result survives a save")

	# --- hull loss under ink loses the creature
	var e = at_zone(SEED, 0)
	fly(e, func(): return live(e).encounter.ink != null and live(e).encounter.ink.phase == "hold")
	live(e).hull = 1.0; live(e).protection = 0.0
	var rows_e: Array = Book.run_route(live(e)).rows
	var lost: Array = []
	for i in range(400):
		if run_of(e) == null: break
		var r: Dictionary = live(e)
		r.encounter.resistance = 1e6; r.protection = 0.0
		# Steer into the nearest rock ahead.
		var row := str(rows_e[clampi(int(floor(float(r.y) - 0.6)), 0, rows_e.size() - 1)])
		for x in range(Route.COLUMNS):
			if Route.is_rock(row[x]) and x > 0 and x < Route.COLUMNS - 1: r.x = x + 0.5
		lost.append_array(advance(e, 0.05))
	check("creature_lost" in types(lost) and e.snapshot().expedition.result.creature.outcome == "escaped" and e.snapshot().expedition.result.creature.id == INKFIN, "zero hull under the ink loses the Inkfin")

	# --- invalid saves
	var f = at_zone(SEED, 0)
	fly(f, func(): return live(f).encounter.ink != null and live(f).encounter.ink.phase == "hold")
	tidy(f)
	check(Session.new().restore(JSON.parse_string(JSON.stringify(f.save_data(), "", true, true))), "the untouched save restores")
	for edit in [func(ink): ink.phase = "boil", func(ink): ink.t = -1.0, func(ink): ink.zone = 99, func(ink): ink.end = int(ink.end) + 1]:
		var data = JSON.parse_string(JSON.stringify(f.save_data(), "", true, true))
		var found = _find(data, "ink")
		edit.call(found.ink)
		var broken = Session.new()
		check(found != null and not broken.restore(data), "a save with impossible ink is refused")
	var other = JSON.parse_string(JSON.stringify(f.save_data(), "", true, true))
	_find(other, "ink").inked = [1]
	check(not Session.new().restore(other), "a save with an unknown spent zone is refused")

	print("Expedition ink tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() > 0 else 0)

## The dictionary holding `field` somewhere in a save (the run's encounter).
func _find(value: Variant, field: String) -> Variant:
	if value is Dictionary:
		if value.has(field) and value.has("resistance"): return value
		for v in value.values():
			var found = _find(v, field)
			if found != null: return found
	elif value is Array:
		for v in value:
			var found = _find(v, field)
			if found != null: return found
	return null
