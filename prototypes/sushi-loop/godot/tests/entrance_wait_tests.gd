extends SceneTree
## New visitors may wait at the door, but may not use the trapped-guest wander
## policy until a real seat has admitted them. Fixtures use only public APIs.
const Session = preload("res://scripts/session.gd")
const View = preload("res://scripts/restaurant_view.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_test_missing_and_unusable_seats()
	_test_full_restaurant_and_door_capacity()
	_test_retry_before_deadline()
	_test_exact_timeout_and_exit_accounting()
	_test_pause_save_and_closed_door()
	_test_saved_admission_validation()
	_test_legacy_46_continuation()
	_test_existing_trapped_guests()
	_test_production_feedback()
	if failures.is_empty():
		print("PASS: %s entrance waiting checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		printerr("%s of %s entrance waiting checks failed" % [failures.size(), checks])
		quit(1)

func _check(value: bool, description: String) -> void:
	checks += 1
	if not value: failures.append(description)

func _copy(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value, "", true, true))

func _same(left: Variant, right: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(left, "", true, true)) == JSON.parse_string(JSON.stringify(right, "", true, true))

func _configuration() -> Dictionary:
	return {
		"floor": {"columns": 7, "rows": 7, "world_columns": 21, "viewport_columns": 7, "entrance": {"x": 3, "y": 0}},
		"recipes": {"salmon_nigiri": {"preparation_seconds": 1000.0}},
		"service": {"step_seconds": 0.05, "belt_seconds_per_cell": 0.2, "first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "walking_cells_per_second": 4.0, "eating_seconds": 0.5, "loading_seconds": 0.1, "sitting_seconds": 0.1, "standing_seconds": 0.1},
		"customers": {"preference_seconds": 0.8, "happy_seconds": 0.4, "restless_seconds": 30.0, "leave_seconds": 60.0, "fullness_min": 1.0, "fullness_max": 1.0, "dish_fullness_min": 1.0, "dish_fullness_max": 1.0, "eating_jitter_seconds": 0.0, "passing_offset": 0.24, "personal_space": 0.4},
		"objects": [
			{"id": "chef", "kind": "chef", "x": 2, "y": 6, "facing": "east", "recipe_id": "salmon_nigiri", "art_id": "chef-lena"},
			{"id": "belt", "kind": "belt", "x": 3, "y": 6, "facing": "south"},
			{"id": "seat", "kind": "seat", "x": 3, "y": 5, "facing": "south"},
		],
	}

func _unreachable() -> Dictionary:
	var config := _configuration()
	for x in range(7):
		config.objects.append({"id": "wall-%s" % x, "kind": "decor", "art_id": "crate-wood", "x": x, "y": 3, "facing": "south"})
	return config

func _trapped_configuration() -> Dictionary:
	var config := _configuration()
	for y in [1, 3]:
		for x in range(7):
			if x != 3: config.objects.append({"id": "wall-%s-%s" % [x, y], "kind": "decor", "art_id": "crate-wood", "x": x, "y": y, "facing": "south"})
	return config

func _customer(game: GameSession, identity := "") -> Dictionary:
	for guest in game.snapshot().customers:
		if identity.is_empty() or guest.id == identity: return guest
	return {}

func _waiting(game: GameSession) -> Dictionary:
	for guest in game.snapshot().customers:
		if guest.phase == "entrance_wait": return guest
	return {}

func _wait(game: GameSession, predicate: Callable, limit := 12.0) -> bool:
	for index in range(int(ceil(limit / 0.05))):
		if predicate.call(game): return true
		game.advance(0.05)
	return predicate.call(game)

func _door_stationary(guest: Dictionary, entrance: Dictionary) -> bool:
	return not guest.is_empty() and guest.phase == "entrance_wait" and guest.seat_id == "" and guest.navigation_mode == "goal" and guest.visual_phase == "stand" and is_equal_approx(float(guest.x), float(entrance.x)) and is_equal_approx(float(guest.y), float(entrance.y)) and is_zero_approx(float(guest.render_offset_x)) and is_zero_approx(float(guest.render_offset_y))

func _no_money(events: Array, game: GameSession) -> bool:
	return not events.any(func(event): return event.type in ["sale", "eating_started"]) and game.snapshot().coins == 120 and game.snapshot().stats.sales == 0 and game.snapshot().stats.served == 0

func _test_missing_and_unusable_seats() -> void:
	var absent := _configuration()
	absent.objects = []
	var no_belt := _configuration()
	no_belt.objects = no_belt.objects.filter(func(object): return object.kind == "seat")
	var no_supply := _configuration()
	no_supply.objects = no_supply.objects.filter(func(object): return object.kind != "chef")
	for fixture in [{"name": "no furniture", "config": absent}, {"name": "seat with no belt", "config": no_belt}, {"name": "belt with no food supply", "config": no_supply}, {"name": "supplied seat across a sealed aisle", "config": _unreachable()}]:
		var game := Session.new_session(51, fixture.config)
		var arrived: Array = game.advance(0.1)
		var guest := _customer(game)
		_check(_door_stationary(guest, game.snapshot().floor.entrance) and game.snapshot().stats.arrivals == 1, "%s admits one visible stationary doorstep visitor" % fixture.name)
		_check(float(guest.get("entrance_wait_elapsed", -1)) == 0.0 and float(guest.get("entrance_wait_total", -1)) == 4.0 and guest.preferred_recipe_id == "" and guest.preference_phase == "pending", "%s begins a four-second puzzled wait without a seat or premature meal request" % fixture.name)
		var identity := str(guest.get("id", "missing"))
		var stationary := true
		var events: Array = arrived.duplicate(true)
		for index in range(60):
			events.append_array(game.advance(0.05))
			stationary = stationary and _door_stationary(_customer(game, identity), game.snapshot().floor.entrance)
		_check(stationary and is_zero_approx(float(_customer(game, identity).get("waiting_elapsed", -1))), "%s never walks, wanders, yields, becomes restless or starts seat patience while outside" % fixture.name)
		_check(_no_money(events, game), "%s cannot receive food or generate earnings" % fixture.name)

func _test_full_restaurant_and_door_capacity() -> void:
	var config := _configuration()
	config.service.arrival_seconds = 0.2
	var game := Session.new_session(62, config)
	_check(_wait(game, func(session): return not _waiting(session).is_empty(), 2.0), "a second guest appears at the entrance when the only useful seat is reserved")
	var waiter := _waiting(game)
	var first_id := str(_customer(game).get("id", ""))
	var waiting_id := str(waiter.get("id", ""))
	var unique := true
	var stationary := true
	for index in range(65):
		game.advance(0.05)
		var scene := game.snapshot()
		var at_door: Array = scene.customers.filter(func(guest): return Vector2(float(guest.x), float(guest.y)).distance_to(Vector2(float(scene.floor.entrance.x), float(scene.floor.entrance.y))) < 0.4)
		unique = unique and at_door.size() == 1 and _waiting(game).id == waiting_id and scene.customers.size() == 2
		stationary = stationary and _door_stationary(_customer(game, waiting_id), scene.floor.entrance)
	_check(unique and stationary and game.snapshot().stats.arrivals == 2, "repeated due arrivals cannot pile up on the one waiting guest or reroll their identity")
	_check(not first_id.is_empty() and _customer(game, first_id).seat_id == "seat" and _customer(game, first_id).phase == "waiting", "the admitted guest retains the sole seat while the newcomer waits outside")

func _test_retry_before_deadline() -> void:
	var config := _configuration()
	config.objects = config.objects.filter(func(object): return object.kind != "belt")
	var game := Session.new_session(73, config)
	game.advance(1.875)
	var before := _customer(game)
	_check(_door_stationary(before, game.snapshot().floor.entrance), "seat-availability fixture starts as a real doorstep wait")
	game.command({"type": "set_mode", "mode": "edit"})
	var placed := game.command({"type": "editor_place", "inventory_id": "belt-tile", "x": 3, "y": 6})
	_check(placed.ok, "public furnishing command connects the waiting visitor's seat before their deadline")
	var paused := game.save_data()
	_check(game.advance(100.0).is_empty() and _same(paused, game.save_data()), "connecting a seat during Edit does not consume entrance patience or choose a meal")
	game.command({"type": "set_mode", "mode": "live"})
	var events: Array = game.advance(0.05)
	var admitted := _customer(game, str(before.get("id", "")))
	_check(not admitted.is_empty() and admitted.phase == "walking" and admitted.seat_id == "seat" and admitted.navigation_mode == "goal", "the same waiting guest takes the newly usable seat on the next Live step")
	_check(admitted.preferred_recipe_id == "salmon_nigiri" and admitted.preference_phase == "pending" and game.snapshot().stats.arrivals == 1 and not events.any(func(event): return event.type in ["departed", "sale"]), "admission chooses one real recipe without counting a second arrival, sale or departure")
	_check(_wait(game, func(session): return _customer(session, str(before.id)).phase == "waiting", 3.0), "an admitted newcomer walks to the real stool and sits instead of remaining puzzled")
	var last_chance := Session.new_session(75, config)
	last_chance.advance(4.05)
	var late_id := str(_customer(last_chance).get("id", ""))
	last_chance.command({"type": "set_mode", "mode": "edit"})
	var late_placement := last_chance.command({"type": "editor_place", "inventory_id": "belt-tile", "x": 3, "y": 6})
	last_chance.command({"type": "set_mode", "mode": "live"})
	var late_events: Array = last_chance.advance(0.05)
	_check(late_placement.ok and not _customer(last_chance, late_id).is_empty() and _customer(last_chance, late_id).phase == "walking" and not late_events.any(func(event): return event.type == "departed"), "a seat available on the deadline step wins over the no-seat timeout")
	# A separately occupied seat must also become available through ordinary Live service.
	var busy := _configuration()
	busy.recipes.salmon_nigiri.preparation_seconds = 0.1
	busy.service.arrival_seconds = 0.2
	busy.service.walking_cells_per_second = 10.0
	busy.service.eating_seconds = 0.3
	var occupied := Session.new_session(74, busy)
	_check(_wait(occupied, func(session): return not _waiting(session).is_empty(), 2.0), "occupied-seat retry fixture first creates a real waiting newcomer")
	var waiting_id := str(_waiting(occupied).get("id", ""))
	_check(_wait(occupied, func(session): return not _customer(session, waiting_id).is_empty() and _customer(session, waiting_id).phase == "walking", 3.0), "a seat released by a real paying guest admits the waiting newcomer before patience expires")
	_check(occupied.snapshot().stats.sales >= 1 and _customer(occupied, waiting_id).seat_id == "seat", "natural seat release preserves the first guest's sale and the newcomer's own identity")

func _test_exact_timeout_and_exit_accounting() -> void:
	var config := _configuration()
	config.objects = []
	var game := Session.new_session(84, config)
	game.advance(0.1)
	var identity := str(_customer(game).get("id", ""))
	var events: Array = game.advance(3.95)
	_check(_door_stationary(_customer(game, identity), game.snapshot().floor.entrance) and is_equal_approx(float(_customer(game, identity).get("entrance_wait_elapsed", -1)), 3.95), "the guest remains visibly at the door until the full four-second admission wait has elapsed")
	_check(not events.any(func(event): return event.type == "departed"), "the patience deadline never departs a guest one simulation step early")
	var deadline: Array = game.advance(0.05)
	var departures := deadline.filter(func(event): return event.type == "departed")
	_check(_customer(game, identity).is_empty() and departures.size() == 1 and departures[0].customer_id == identity and departures[0].reason == "no_seat", "the exact deadline removes the unadmitted guest at the entrance with one no-seat departure")
	var future: Array = game.advance(30.0)
	_check(not future.any(func(event): return event.type == "departed") and _no_money(events + deadline + future, game), "a rejected visit never replays its departure, receives a dish or earns money later")
	var tuned := _configuration()
	tuned.objects = []
	tuned.customers.entrance_wait_seconds = 0.35
	var short := Session.new_session(85, tuned)
	short.advance(0.4)
	_check(not _customer(short).is_empty() and float(_customer(short).get("entrance_wait_total", -1)) == 0.35, "admission patience is a separate content tuneable rather than seated hunger patience")
	_check(short.advance(0.05).any(func(event): return event.type == "departed") and short.snapshot().customers.is_empty(), "a custom admission patience duration ends at its own fixed-step deadline")

func _test_pause_save_and_closed_door() -> void:
	var config := _configuration()
	config.objects = []
	var game := Session.new_session(95, config)
	game.advance(1.375)
	game.command({"type": "set_mode", "mode": "edit"})
	var paused := _copy(game.save_data())
	var peer := Session.new_session(1)
	_check(peer.restore(paused) and _same(paused, peer.save_data()), "a fractional doorstep patience clock and remainder reopen exactly through the public save boundary")
	_check(game.advance(1000.0).is_empty() and peer.advance(1000.0).is_empty() and _same(paused, game.save_data()) and _same(paused, peer.save_data()), "Edit freezes admission animation and patience in both the original and reopened restaurant")
	game.command({"type": "set_mode", "mode": "live"})
	peer.command({"type": "set_mode", "mode": "live"})
	var expected: Array = []
	var actual: Array = []
	var identical := true
	for index in range(75):
		expected.append_array(game.advance(0.05))
		actual.append_array(peer.advance(0.05))
		identical = identical and _same_continuation(game.save_data(), peer.save_data())
	_check(identical and _same(expected, actual) and actual.filter(func(event): return event.type == "departed").size() == 1, "reopened patience expires at the identical frame with identical departure and future state")
	var closed := Session.new_session(96, config)
	closed.command({"type": "set_entrance_open", "open": false})
	closed.advance(20.0)
	_check(closed.snapshot().customers.is_empty() and closed.snapshot().stats.arrivals == 0, "a closed restaurant never creates a doorstep visitor")
	closed.command({"type": "set_entrance_open", "open": true})
	closed.advance(0.1)
	var identity := str(_customer(closed).get("id", ""))
	closed.command({"type": "set_entrance_open", "open": false})
	var departures: Array = closed.advance(10.0).filter(func(event): return event.type == "departed")
	_check(departures.size() == 1 and departures[0].customer_id == identity and closed.snapshot().customers.is_empty() and closed.snapshot().stats.arrivals == 1, "closing arrivals during a wait lets that existing guest finish and leave, without replacing them")

func _test_saved_admission_validation() -> void:
	var config := _configuration()
	config.objects = []
	var game := Session.new_session(107, config)
	game.advance(1.375)
	var pristine := _copy(game.save_data())
	_check(pristine.get("customer_admission_version") == 1, "the save explicitly declares its admission-state schema")
	for mutation in [["entrance_wait_elapsed", -0.05], ["entrance_wait_elapsed", "1.25"], ["entrance_wait_elapsed", 4.0], ["seat_id", "fake-seat"], ["preferred_recipe_id", "salmon_nigiri"], ["phase", "walking"], ["navigation_mode", "wander"], ["visual_phase", "walk"], ["x", 2.0], ["render_offset_y", 0.2], ["waiting_elapsed", 0.1], ["first_dish_received", true], ["wander_elapsed", -0.1], ["wander_elapsed", "0"], ["wander_elapsed", 0.1]]:
		var corrupt := _copy(pristine)
		corrupt.state.customers[0][mutation[0]] = mutation[1]
		_check(not game.restore(corrupt) and _same(pristine, game.save_data()), "malformed doorstep state is rejected atomically: %s = %s" % [mutation[0], str(mutation[1])])
	for field in ["entrance_wait_elapsed", "wander_elapsed"]:
		var missing := _copy(pristine)
		missing.state.customers[0].erase(field)
		_check(not game.restore(missing) and _same(pristine, game.save_data()), "current admission saves cannot silently reset a missing reaction clock: %s" % field)
	for value in [-1, 0, "4"]:
		var tune := _copy(pristine)
		tune.configuration.customers.entrance_wait_seconds = value
		_check(not game.restore(tune) and _same(pristine, game.save_data()), "invalid admission patience tuning is rejected atomically: %s" % str(value))
	var future := _copy(pristine)
	future.customer_admission_version = 999
	_check(not game.restore(future) and _same(pristine, game.save_data()), "a future admission schema cannot overwrite the running restaurant")
	var duplicate := _copy(pristine)
	var second: Dictionary = duplicate.state.customers[0].duplicate(true)
	second.id = "customer-2"
	duplicate.state.customers.append(second)
	duplicate.state.next_customer_id = 3
	duplicate.state.stats.arrivals = 2
	_check(not game.restore(duplicate) and _same(pristine, game.save_data()), "saved restaurants cannot hide two waiting visitors in the same entrance cell")

func _test_legacy_46_continuation() -> void:
	var current := Session.new_session(118, _configuration())
	current.advance(0.625)
	var expected := _copy(current.save_data())
	var old := _copy(expected)
	old.erase("customer_admission_version")
	old.configuration.customers.erase("entrance_wait_seconds")
	for guest in old.state.customers:
		guest.erase("entrance_wait_elapsed")
		guest.erase("wander_elapsed")
	var restored := Session.new_session(1)
	_check(restored.restore(old), "a real 0.4.6 admitted walking save migrates without restarting its visit")
	_check(_same(expected, restored.save_data()), "legacy migration only adds neutral admission metadata and retains the exact seat, route, animation, visit, RNG and fractional remainder")
	_check(_same(current.advance(12.0), restored.advance(12.0)) and _same(current.save_data(), restored.save_data()), "a migrated admitted guest has identical subsequent service and departure behavior")
	var corrupt := _copy(old)
	corrupt.state.customers[0].path[0] = {"x": 0, "y": 6}
	var baseline := restored.save_data()
	_check(not restored.restore(corrupt) and _same(baseline, restored.save_data()), "legacy admission migration still validates the original walking route before accepting it")

func _test_existing_trapped_guests() -> void:
	var game := Session.new_session(129, _trapped_configuration())
	game.advance(0.6)
	var identity := str(_customer(game).get("id", ""))
	game.command({"type": "set_mode", "mode": "edit"})
	_check(game.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 1}).ok, "the trapped admission fixture closes the entrance behind an inside guest")
	var blockage := game.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3})
	_check(blockage.ok and _customer(game, identity).navigation_mode == "wander", "an already-admitted guest behind a new furnishing blockage still enters the established wander policy")
	game.command({"type": "set_mode", "mode": "live"})
	var positions := {}
	var retained := true
	for index in range(1200):
		game.advance(0.05)
		var guest := _customer(game, identity)
		retained = retained and not guest.is_empty() and guest.phase == "walking" and guest.navigation_mode == "wander" and guest.seat_id == "seat" and is_zero_approx(float(guest.get("entrance_wait_elapsed", -1)))
		if not guest.is_empty(): positions[Vector2i(roundi(float(guest.x)), roundi(float(guest.y)))] = true
	_check(retained and positions.size() >= 3, "the admission timeout never removes an inside trapped guest, who continues wandering among actual free tiles for a minute")

func _test_production_feedback() -> void:
	var view := View.new()
	view.art.reload()
	var config := _configuration()
	config.objects = []
	var door := Session.new_session(140, config)
	door.advance(0.4)
	var puzzled: Dictionary = view.customer_feedback(_customer(door))
	_check(puzzled.get("object") == "bubble-puzzled" and view.customer_clip(_customer(door)) == "stand", "the real feedback renderer selects approved puzzled 2D art and a standing pose for a doorstep visitor")
	var frame: Dictionary = view.art.frame_data(str(puzzled.get("object", "")), str(puzzled.get("clip", "")), "S", float(puzzled.get("seconds", 0)))
	_check(not frame.is_empty() and int(frame.get("frames", 0)) >= 6, "the production puzzled bubble resolves to a real multi-frame shipping atlas")
	var trapped := Session.new_session(141, _trapped_configuration())
	trapped.advance(0.6)
	trapped.command({"type": "set_mode", "mode": "edit"})
	_check(trapped.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 1}).ok, "the scared feedback fixture closes the entrance behind the guest")
	var result := trapped.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3})
	trapped.command({"type": "set_mode", "mode": "live"})
	trapped.advance(0.375)
	var guest := _customer(trapped)
	var panic: Dictionary = view.customer_feedback(guest)
	_check(result.ok and panic.get("object") == "bubble-panic" and is_equal_approx(float(guest.get("wander_elapsed", -1)), 0.35), "trapped admitted guests get the approved scared 2D bubble driven by their own saved Live wander clock")
	var panic_frame: Dictionary = view.art.frame_data(str(panic.get("object", "")), str(panic.get("clip", "")), "S", float(panic.get("seconds", 0)))
	_check(not panic_frame.is_empty() and int(panic_frame.get("frames", 0)) >= 6, "the production scared reaction resolves to a real multi-frame shipping atlas")
	trapped.command({"type": "set_mode", "mode": "edit"})
	var saved := _copy(trapped.save_data())
	var peer := Session.new_session(1)
	_check(peer.restore(saved) and _same(saved, peer.save_data()) and _same(panic, view.customer_feedback(_customer(peer))), "a scared reaction reopens on the identical animated frame with its fractional simulation remainder")
	trapped.advance(100.0)
	_check(_same(saved, trapped.save_data()) and _same(panic, view.customer_feedback(_customer(trapped))), "Edit pauses the scared bubble clock together with the trapped visitor")
	trapped.command({"type": "editor_remove", "id": result.get("id", "")})
	_check(_customer(trapped).navigation_mode == "goal" and is_zero_approx(float(_customer(trapped).get("wander_elapsed", -1))) and view.customer_feedback(_customer(trapped)).get("object", "") != "bubble-panic", "opening the route clears the scared reaction and resets its clock without restarting the visit")
	view.free()

func _same_continuation(left: Dictionary, right: Dictionary) -> bool:
	# The old arrival countdown subtracts binary floats. JSON round-tripping
	# may move that unrelated 1000-second countdown by one IEEE-754 ULP. All
	# admission/reaction clocks, RNG, events and other saved fields stay exact.
	if absf(float(left.state.arrival_remaining) - float(right.state.arrival_remaining)) > 0.000000001: return false
	var a := left.duplicate(true)
	var b := right.duplicate(true)
	a.state.erase("arrival_remaining")
	b.state.erase("arrival_remaining")
	return _same(a, b)
