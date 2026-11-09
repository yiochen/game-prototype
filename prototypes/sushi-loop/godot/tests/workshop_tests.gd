extends SceneTree
## Issue #28 rules: the Workshop spends banked salvage on independent Hull,
## Harpoon, Collector and power-up levels, and new departures fly with that
## gear. Through the public command/time/save boundary with a controlled clock;
## equivalent runs compare each benefit.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const Workshop = preload("res://scripts/workshop_book.gd")
const SEED := 23
var count := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func _initialize() -> void: call_deferred("run")

func live(s) -> Dictionary: return s._state.expedition.run
func types(events: Array) -> Array: return events.map(func(e): return e.type)
func track(s, id: String) -> Dictionary:
	for row in s.snapshot().workshop.tracks:
		if row.id == id: return row
	return {}

func advance(s, seconds: float) -> Array:
	var events: Array = []
	var t := 0.0
	while t < seconds - 0.0001 and s.snapshot().expedition.run != null:
		events.append_array(s.command({"type": "expedition_advance", "elapsed": 0.05, "now": 2000.0 + t}).get("events", []))
		t += 0.05
	return events

func roundtrip(s):
	var restored = Session.new()
	check(restored.restore(JSON.parse_string(JSON.stringify(s.save_data(), "", true, true))), "JSON save restores")
	return restored

## A session with banked salvage and the given levels bought through the command boundary.
func equipped(levels: Dictionary, salvage := 5000):
	var s = Session.new_session(7)
	s._state.expedition.salvage = salvage # test-only bank
	var n := 0
	for id in levels:
		while int(track(s, id).level) < int(levels[id]):
			n += 1
			check(s.command({"type": "workshop_upgrade", "id": id, "token": "setup-%d" % n}).ok, "setup upgrade %s" % id)
	return s

## A run hooked in the arena, ship under the creature (as in the #24 tests).
func hooked(s):
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
	# Fresh restaurants start every track at level 1 with base gear.
	var s = Session.new_session(7)
	var view: Dictionary = s.snapshot().workshop
	check(view.tracks.size() == 6 and view.tracks.all(func(t): return t.level == 1), "six tracks start at level 1")
	check(is_equal_approx(float(view.gear.hull), 100.0) and is_equal_approx(float(view.gear.launch), 0.0), "base gear: 100 hull, no launch shield")

	# Insufficient salvage: nothing changes (the UI disables Upgrade; no shortage modal).
	var r: Dictionary = s.command({"type": "workshop_upgrade", "id": "hull", "token": "a"})
	check(not r.ok and r.reason == "insufficient_salvage" and track(s, "hull").level == 1, "an unaffordable upgrade is rejected")

	# One affordable upgrade pays exactly one level.
	s._state.expedition.salvage = 200
	r = s.command({"type": "workshop_upgrade", "id": "hull", "token": "t1"})
	check(r.ok and track(s, "hull").level == 2 and s.snapshot().expedition.salvage == 140, "an upgrade pays 60 and raises one level")
	check(track(s, "hull").cost == 110 and is_equal_approx(float(track(s, "hull").next_value), 150.0), "the next cost and value update in place")
	# Repeated input with the same token never pays twice, also after a save and reopen.
	r = s.command({"type": "workshop_upgrade", "id": "hull", "token": "t1"})
	check(r.ok and r.get("replayed", false) and track(s, "hull").level == 2 and s.snapshot().expedition.salvage == 140, "a replayed token is accepted without paying")
	s = roundtrip(s)
	r = s.command({"type": "workshop_upgrade", "id": "hull", "token": "t1"})
	check(track(s, "hull").level == 2 and s.snapshot().expedition.salvage == 140, "the token survives save/reopen")
	check(not s.command({"type": "workshop_upgrade", "id": "hull"}).ok, "an upgrade needs a token")
	check(not s.command({"type": "workshop_upgrade", "id": "sonar", "token": "x"}).ok, "unknown tracks are rejected")

	# Coins and salvage never exchange.
	var coins: int = s.snapshot().coins
	s.command({"type": "workshop_upgrade", "id": "collector", "token": "c1"})
	check(s.snapshot().coins == coins, "salvage upgrades never touch coins")

	# Looks: crossing a look level marks NEW until the Workshop is left.
	s = equipped({"hull": 2})
	r = s.command({"type": "workshop_upgrade", "id": "hull", "token": "look"})
	check(r.new_look and track(s, "hull").new and track(s, "hull").tier == 2, "level 3 swaps the hull look and marks it NEW")
	s.command({"type": "workshop_seen"})
	check(not track(s, "hull").new and track(s, "hull").tier == 2, "leaving acknowledges NEW; the look stays")

	# Caps: MAX keeps the final value and refuses more.
	s = equipped({"collector": 4})
	check(track(s, "collector").max and track(s, "collector").cost == -1, "Collector caps at level 4 (modest reach)")
	check(not s.command({"type": "workshop_upgrade", "id": "collector", "token": "over"}).ok, "a capped track rejects Upgrade")

	# New departures use the full upgraded hull; a run keeps the gear it left with.
	s = equipped({"hull": 5, "launch": 2})
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	var run_view: Dictionary = s.snapshot().expedition.run
	check(is_equal_approx(float(run_view.hull), 200.0) and is_equal_approx(float(run_view.hull_fraction), 1.0), "a new departure has the full upgraded hull")
	check(float(run_view.shield) > 0.0, "Shield at start launches already shielded")
	s._state.expedition.salvage = 5000
	s.command({"type": "workshop_upgrade", "id": "harpoon", "token": "mid"})
	check(is_equal_approx(float(live(s).gear.harpoon), 1.0), "an upgrade bought mid-run waits for the next departure")
	s = roundtrip(s)
	check(is_equal_approx(float(s.snapshot().expedition.run.hull), 200.0), "the run's gear survives save/reopen")

	# Equivalent runs: the same hooked chase drains resistance faster with a stronger harpoon.
	var base = hooked(Session.new_session(7))
	var strong = hooked(equipped({"harpoon": 5}))
	check(live(base).encounter.state == "hooked" and live(strong).encounter.state == "hooked", "both equivalent runs are hooked")
	var before_base := float(live(base).encounter.resistance)
	var before_strong := float(live(strong).encounter.resistance)
	advance(base, 1.0); advance(strong, 1.0)
	var drop_base := before_base - float(live(base).encounter.resistance)
	var drop_strong := before_strong - float(live(strong).encounter.resistance)
	check(absf(drop_strong / drop_base - 1.8) < 0.05, "Harpoon level 5 drains resistance 1.8× as fast (%.2f vs %.2f)" % [drop_strong, drop_base])
	check(is_equal_approx(float(Book.definition().encounter.resistance), 100.0), "the creature's resistance itself does not scale with equipment")

	# Equivalent runs: Collector reach collects a pickup the base reach misses.
	var near := Session.new_session(7)
	near.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	var far = equipped({"collector": 4})
	far.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	var pickup: Vector2 = Book.run_route(live(near)).pickups[0]
	for one in [near, far]:
		var rr: Dictionary = live(one)
		rr.x = pickup.x + 1.2; rr.y = pickup.y + 0.05; rr.vx = 0.0; rr.steer = 0.0
	var near_events := types(advance(near, 0.05))
	var far_events := types(advance(far, 0.05))
	check(not "pickup" in near_events and "pickup" in far_events, "a pickup 1.2 tiles away is drawn in only with a long Collector")
	check(int(live(far).salvage) == live(far).collected.size() * int(Book.definition().salvage_per_pickup), "attraction never multiplies pickup value")

	# Equivalent runs: Hull level survives more rock hits.
	check(Workshop.value("hull", 5) / float(Book.definition().impact_damage) > Workshop.value("hull", 1) / float(Book.definition().impact_damage), "more hull survives more hits")

	# Power-ups: shield pickups last longer; the passage ride is longer.
	s = equipped({"shield": 5, "passage": 4})
	s.command({"type": "expedition_start", "now": 1000.0, "seed": SEED})
	var path := Book.run_route(live(s))
	if not path.shields.is_empty():
		var b: Vector2 = path.shields[0]
		live(s).x = b.x; live(s).y = b.y + 0.02
		advance(s, 0.05)
		check(float(s.snapshot().expedition.run.shield) > float(Book.definition().shield_seconds), "an upgraded shield pickup lasts longer than the base")
	check(Book.passage(SEED, 0, int(live(s).gear.passage)).rows.size() > Book.passage(SEED, 0).rows.size(), "an upgraded passage ride is longer")

	# Invalid saves are rejected.
	var data: Dictionary = GameSession.flat_view(equipped({"hull": 2}).save_data())
	data.state.workshop.levels.hull = 9
	check(not Session.new().restore(data), "a level above the cap is rejected")
	data = GameSession.flat_view(equipped({"hull": 2}).save_data())
	data.state.workshop.levels.erase("hull")
	check(not Session.new().restore(data), "a missing track is rejected")
	# Saves from before #28 (no workshop slice) open with every level at 1.
	data = GameSession.flat_view(Session.new_session(7).save_data())
	data.state.erase("workshop")
	var older = Session.new()
	check(older.restore(data) and older.snapshot().workshop.tracks.all(func(t): return t.level == 1), "a pre-Workshop save opens at level 1")

	print("Workshop tests: %d checks, %d failures" % [count, failures.size()])
	quit(1 if failures.size() else 0)
