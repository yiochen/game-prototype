extends SceneTree
## Issue #25 rules: the Storm Eel's discharge in its own creature chunks,
## through the public command/time/save boundary with a controlled clock.
## Beyond the rules themselves, it demonstrates fair routes: from many ship
## positions at each windup, a real steering input (after a reaction delay)
## gets the ship through the strike without a lightning hit.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Route = preload("res://scripts/expedition/route.gd")
const Discharge = preload("res://scripts/expedition/discharge.gd")
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

## A run hooked in the arena (as the pursuit tests do), then held at full chase speed.
func hooked(route_seed := SEED):
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": route_seed})
	var r: Dictionary = live(s)
	r.y = float(Book.run_route(r).encounter_start) + 0.02; r.x = 5.5; r.vx = 0.0; r.steer = 0.0
	advance(s, 0.1)
	advance(s, float(Book.definition().encounter.arrive_seconds))
	# Aim under the creature and fire until it is hooked.
	for shot in range(6):
		live(s).x = Book.creature_centre(live(s)).x; live(s).vx = 0.0
		s.command({"type": "expedition_fire"})
		for i in range(60):
			if "hooked" in types(advance(s, 0.05)): return s
			if live(s).encounter.harpoon == null and float(live(s).encounter.cooldown) <= 0.0: break
	return s

## Hooked with full resistance at the entry of the run's `which` creature chunk.
func at_zone(route_seed: int, which: int):
	var s = hooked(route_seed)
	advance(s, float(Book.definition().encounter.pursuit_ramp_seconds) + 0.1)
	var zones: Array = Book.run_route(live(s)).zones
	var zone: Dictionary = zones[which]
	var r := live(s)
	r.y = float(zone.y1) + 0.6; r.x = 5.5; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	r.encounter.resistance = float(Book.definition().encounter.resistance); r.encounter.discharge = null; r.encounter.discharge_cooldown = 0.0
	return s

func advance_until_windup(s, limit := 6.0) -> Variant:
	var t := 0.0
	while t < limit and run_of(s) != null:
		live(s).encounter.resistance = 100.0
		var events := advance(s, 0.05)
		t += 0.05
		for e in events: if e.type == "discharge_windup": return e
	return null

## From the windup in `s`, put the ship at `x` and, after the reaction delay,
## steer to one `side` (0 holds) until `margin` columns clear of the strip's
## edge, then let go. `strike` false removes the strike first (terrain only).
## {zapped, impacts}.
func dodge(s, x: float, side: float, margin: float, strike := true) -> Dictionary:
	var b = copy(s)
	var r := live(b)
	r.x = x; r.vx = 0.0; r.steer = 0.0; r.protection = 0.0
	var d: Dictionary = Book.definition().encounter.discharge
	var shape: Dictionary = r.encounter.discharge
	var centre := float(shape.x0) + float(shape.w) / 2.0
	if not strike: r.encounter.discharge = null; r.encounter.discharge_cooldown = 9.0
	var events := advance(b, float(d.fairness.reaction_seconds))
	var t := float(d.fairness.reaction_seconds)
	while t < float(d.warn_seconds) + float(d.active_seconds) + 0.2 and run_of(b) != null:
		var clear := absf(float(live(b).x) - centre) >= float(shape.w) / 2.0 + margin
		b.command({"type": "expedition_steer", "input": 0.0 if clear else side})
		events.append_array(advance(b, 0.05)); t += 0.05
	return {"zapped": "zapped" in types(events), "impacts": types(events).count("impact")}

const POLICIES := [[0.0, 0.0], [-1.0, 0.4], [1.0, 0.4], [-1.0, 0.9], [1.0, 0.9]]

## Some steering gets through cleanly (no lightning, no rock); null when the
## terrain alone would hit from here whatever the ship does.
func dodgeable(s, x: float) -> Variant:
	for p in POLICIES:
		var out := dodge(s, x, p[0], p[1])
		if not out.zapped and out.impacts == 0: return true
	for p in POLICIES:
		if dodge(s, x, p[0], p[1], false).impacts == 0: return false
	return null

func run() -> void:
	var rules := Book.definition()
	var d: Dictionary = rules.encounter.discharge

	# The library: each eel chunk carries an up-to-date, accepted table of fair strikes.
	var eel: Array = Book.library().filter(func(c): return c.kind == "creature" and str(c.creature) == "storm-eel")
	check(eel.map(func(c): return c.id) == ["eel-island-lanes", "eel-open-basin", "eel-opening-funnel", "eel-pillar-basin"], "four Storm Eel chunks join the library: %s" % [eel.map(func(c): return c.id)])
	for c in eel:
		check(c.creature == "storm-eel" and Discharge.table_problems(c, Book._doc(c.id).chunk.discharge, rules).is_empty(), "%s: its discharge table is current and accepted" % c.id)
		check(c.discharge.strikes.all(func(s): return s.fair.size() >= int(d.fairness.min_choices)), "%s: every strike row offers at least %d fair strips" % [c.id, int(d.fairness.min_choices)])
	# The stored table is exactly what the fairness search finds (one chunk; ~0.5 s).
	var basin: Dictionary = eel[1]
	var fresh := Discharge.analyze(basin.rows, basin.attack_rows, rules, func(x: float, y: float) -> bool: return Book._collides(basin.rows, x, y, float(rules.ship_radius)))
	check(fresh.strikes.map(func(s): return [s.row, s.fair]) == basin.discharge.strikes.map(func(s): return [s.row, s.fair]), "the stored Open Basin table matches a fresh fairness search")
	# A designer edit (a reef squeezing the strike rows into one lane) is rejected.
	var squeezed: Array = basin.rows.duplicate()
	for y in range(6, 11): squeezed[y] = "####...####"
	var verdict := Discharge.analyze(squeezed, basin.attack_rows, rules, func(x: float, y: float) -> bool: return Book._collides(squeezed, x, y, float(rules.ship_radius)))
	check(not verdict.accepted, "a reef squeezing the strike rows is rejected: %s" % [verdict.problems])
	check(not Discharge.table_problems({"rows": squeezed, "attack_rows": basin.attack_rows}, basin.discharge, rules).is_empty(), "an edited chunk's old table is stale and leaves it out")

	# The route: version 5 alternates ordinary and eel chunks after the arena; version 4 has none.
	for seed_value in [SEED, 1, 22, 777]:
		var path := Book.route(seed_value)
		check(path.zones.size() == 3 and path.zones.all(func(z): return z.y1 < path.arena.y0) and path.zones[0].y0 > path.zones[1].y0 and path.zones[1].y0 > path.zones[2].y0, "seed %d: three eel zones in the pursuit, listed in the order the ship meets them" % seed_value)
		check(Route.ship_problems(path.rows).is_empty(), "seed %d: the version 5 route flies" % seed_value)

	# Aiming stays attack-free; a hooked chase through ordinary chunks too.
	var s = Session.new_session(7)
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	live(s).y = float(Book.run_route(live(s)).encounter_start) + 0.02; live(s).x = 5.5
	var events := advance(s, 6.0)
	check(not "discharge_windup" in types(events) and live(s).encounter.state == "aiming", "aiming is attack-free")
	s = hooked()
	var path := Book.run_route(live(s))
	events = []
	while run_of(s) != null and float(live(s).y) > float(path.zones[0].y1) + 1.0:
		live(s).protection = 5.0; live(s).hull = 100.0; live(s).encounter.resistance = 100.0
		events.append_array(advance(s, 0.05))
	check(not "discharge_windup" in types(events), "no discharge in the ordinary chunk before the first eel chunk")

	# In an eel chunk: one fixed strip from the table, a warning, then a live strike.
	s = at_zone(SEED, 0)
	var windup = advance_until_windup(s)
	check(windup != null, "the eel winds up inside its chunk")
	var strike: Dictionary = live(s).encounter.discharge
	var zone: Dictionary = Book.run_route(live(s)).zones.filter(func(z): return int(z.span) == int(strike.zone))[0]
	var entry: Array = zone.strikes.filter(func(e): return float(e.row) == float(strike.row))
	check(entry.size() == 1 and entry[0].fair.has([int(strike.x0), int(strike.w)]), "the strip is one of that strike row's fair choices")
	s.command({"type": "expedition_steer", "input": 1.0})
	events = advance(s, float(d.warn_seconds) - 0.1)
	check(live(s).encounter.discharge.x0 == strike.x0 and live(s).encounter.discharge.phase == "windup" and not "zapped" in types(events), "the strip stays put while the ship steers (no tracking), and the warning does no damage")
	events = advance(s, 0.15)
	check("discharge_strike" in types(events) and live(s).encounter.discharge.phase == "strike", "after %.1f s the strip goes live" % float(d.warn_seconds))
	events = advance(s, float(d.active_seconds) + 0.05)
	check("discharge_end" in types(events) and live(s).encounter.discharge == null and float(live(s).encounter.discharge_cooldown) >= float(d.cooldown_seconds[0]) - 0.1, "it ends after %.1f s and cools down" % float(d.active_seconds))

	# Standing in the strip: hull only, once, with no knock-back and no resistance change.
	s = at_zone(SEED, 0)
	advance_until_windup(s)
	strike = live(s).encounter.discharge
	live(s).x = float(strike.x0) + float(strike.w) / 2.0
	advance(s, float(d.warn_seconds) - 0.1)
	var before: Dictionary = run_of(s)
	var zap_events: Array = []
	while not "zapped" in types(zap_events) and live(s).encounter.discharge != null:
		live(s).vx = 0.0; live(s).steer = 0.0
		before = run_of(s)
		zap_events = advance(s, 0.05)
	var after: Dictionary = run_of(s)
	check("zapped" in types(zap_events) and float(before.hull) - float(after.hull) == float(d.damage), "a ship in the live strip loses %d hull" % int(d.damage))
	check(absf(float(after.x) - float(before.x)) < 0.001, "no knock-back from lightning")
	check(absf((float(before.encounter.resistance) - float(after.encounter.resistance)) - float(rules.encounter.resistance_drain_per_second) * 0.05) < 0.001, "the hit neither restores nor drains extra resistance")
	# Saved mid-strike right after the hit: the restored run does not hit again.
	var restored = copy(s)
	check(restored.snapshot().expedition.run.encounter.discharge != null, "a save keeps the live strike")
	events = advance(restored, float(d.active_seconds))
	check(types(events).count("zapped") == 0 and float(run_of(restored).hull) == float(after.hull), "hit protection carries over: a restored strike cannot hit twice")

	# Pause and save during the warning keep it exactly.
	s = at_zone(SEED, 1)
	advance_until_windup(s)
	advance(s, 0.4)
	s.command({"type": "expedition_pause"})
	var held: Dictionary = run_of(s).encounter.discharge
	advance(s, 2.0)
	check(run_of(s).encounter.discharge == held, "paused, the warning and its remaining time hold still")
	restored = copy(s)
	var back: Dictionary = run_of(restored).encounter.discharge
	check(back.phase == held.phase and back.x0 == held.x0 and back.w == held.w and absf(float(back.t) - float(held.t)) < 1e-6 and run_of(restored).paused, "save/reopen restores the warning and its remaining time behind Paused")

	# A catch or zero hull mid-strike ends the run: no strike survives it.
	s = at_zone(SEED, 0)
	advance_until_windup(s)
	advance(s, float(d.warn_seconds) + 0.05)
	live(s).encounter.resistance = 0.01
	events = advance(s, 0.1)
	check("caught" in types(events) and run_of(s) == null and s.snapshot().expedition.result.outcome == "complete", "catching the eel mid-strike ends the run as complete")
	s = at_zone(SEED, 0)
	advance_until_windup(s)
	strike = live(s).encounter.discharge
	live(s).x = float(strike.x0) + float(strike.w) / 2.0; live(s).hull = float(d.damage)
	events = advance(s, float(d.warn_seconds) + 0.2)
	check("creature_lost" in types(events) and s.snapshot().expedition.result.outcome == "hull_depleted" and s.snapshot().expedition.result.creature.outcome == "escaped", "a lightning hit to zero hull snaps the cable: the eel escapes")

	# Saves: bad discharge fields are rejected.
	s = at_zone(SEED, 0)
	advance_until_windup(s)
	var data: Dictionary = JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))
	var bad: Dictionary = data.duplicate(true)
	_encounter_in(bad).discharge.phase = "sparkle"
	check(not Session.new().restore(bad), "a save with an unknown discharge phase is rejected")
	bad = data.duplicate(true)
	_encounter_in(bad).discharge.x0 = 9
	check(not Session.new().restore(bad), "a save whose strip leaves the route is rejected")

	# Fair routes: at each windup in both eel chunks of several routes, from
	# every clear position across the chunk, steering one way or the other after
	# the reaction delay comes through without a lightning hit.
	var started := Time.get_ticks_msec()
	var trials := 0
	var unfair: Array = []
	for seed_value in [SEED, 1, 22]:
		for which in [0, 1]:
			s = at_zone(seed_value, which)
			for n in range(2):
				var w = advance_until_windup(s)
				if w == null: break
				var rows: Array = Book.run_route(live(s)).rows
				var y := float(live(s).y)
				var x := 1.0
				while x <= 10.0:
					if not Book._collides(rows, x, y, float(rules.ship_radius) + 0.05):
						var ok = dodgeable(s, x)
						if ok != null: trials += 1
						if ok == false: unfair.append("seed %d zone %d strike %d: x %.1f vs strip %d+%d" % [seed_value, which, n, x, int(w.x0), int(w.w)])
					x += 0.5
				# Carry on along the chase: dodge this one from where the ship is.
				var centre := float(w.x0) + float(w.w) / 2.0
				s.command({"type": "expedition_steer", "input": 1.0 if float(live(s).x) >= centre else -1.0})
				advance(s, 0.6)
				s.command({"type": "expedition_steer", "input": 0.0})
				live(s).encounter.resistance = 100.0
				advance(s, float(d.warn_seconds) + float(d.active_seconds))
				if run_of(s) == null: break
				# Back towards the middle for the next one.
				live(s).protection = 5.0; live(s).hull = 100.0
	check(trials > 60 and unfair.is_empty(), "%d windup positions all have a clean way out: %s" % [trials, unfair])
	print("fair-route trials: %d in %d ms" % [trials, Time.get_ticks_msec() - started])
	print("Expedition discharge tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() else 0)

func _encounter_in(save: Dictionary) -> Dictionary:
	return _find(save, "discharge")

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
