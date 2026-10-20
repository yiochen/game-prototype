extends SceneTree
## #12 allows route-blocking edits. Real guests keep their visit and find free
## floor to wander until the same seat/exit becomes reachable again.
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_test_old_route_and_guards()
	_test_alternative_route()
	_test_blocked_walking_continuation()
	_test_seated_history_and_paid_departure()
	_test_legacy_navigation()
	_test_invalid_navigation_saves()
	if failures.is_empty():
		print("PASS: %s blocked guest wandering checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		printerr("%s of %s blocked guest wandering checks failed" % [failures.size(), checks])
		quit(1)

func _check(value: bool, description: String) -> void:
	checks += 1
	if not value: failures.append(description)

func _same(left: Variant, right: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(left, "", true, true)) == JSON.parse_string(JSON.stringify(right, "", true, true))

func _copy(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value, "", true, true))

func _configuration(alternate := false, preparation := 0.25) -> Dictionary:
	var objects: Array = [
		{"id": "chef", "kind": "chef", "x": 2, "y": 6, "facing": "east", "recipe_id": "salmon_nigiri", "art_id": "chef-lena"},
		{"id": "belt", "kind": "belt", "x": 3, "y": 6, "facing": "south"},
		{"id": "seat", "kind": "seat", "x": 3, "y": 5, "facing": "south"},
	]
	for x in range(7):
		if x == 3 or (alternate and x == 4): continue
		objects.append({"id": "wall-%s" % x, "kind": "decor", "art_id": "crate-wood", "x": x, "y": 3, "facing": "south"})
	return {
		"floor": {"columns": 7, "rows": 7, "world_columns": 21, "viewport_columns": 7, "entrance": {"x": 3, "y": 0}},
		"recipes": {"salmon_nigiri": {"preparation_seconds": preparation}},
		"service": {"step_seconds": 0.05, "belt_seconds_per_cell": 0.2, "first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "walking_cells_per_second": 2.0, "eating_seconds": 0.5, "loading_seconds": 0.1, "sitting_seconds": 0.1, "standing_seconds": 0.1},
		"customers": {"preference_seconds": 0.8, "happy_seconds": 0.4, "restless_seconds": 1.5, "leave_seconds": 3.0, "fullness_min": 1.0, "fullness_max": 1.0, "dish_fullness_min": 1.0, "dish_fullness_max": 1.0, "eating_jitter_seconds": 0.0, "passing_offset": 0.24, "personal_space": 0.4},
		"objects": objects,
	}

func _first(game: GameSession) -> Dictionary:
	var guests: Array = game.snapshot().customers
	return guests[0] if not guests.is_empty() else {}

func _guest_save(game: GameSession) -> Dictionary:
	var guests: Array = game.save_data().state.customers
	return guests[0].duplicate(true) if not guests.is_empty() else {}

func _visit_fields(customer: Dictionary) -> Dictionary:
	var result := customer.duplicate(true)
	for key in ["path", "path_index", "path_origin", "navigation_mode", "navigation_retry_elapsed", "wander_cursor"]: result.erase(key)
	return result

func _edit(game: GameSession) -> void:
	_check(game.command({"type": "set_mode", "mode": "edit"}).ok, "public Edit pauses the blocked-guest scenario")

func _seal(game: GameSession) -> String:
	var before := game.save_data()
	var result := game.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 3})
	_check(result.ok, "a furnishing may close the only future guest route")
	_check(_same(_visit_fields(before.state.customers[0]), _visit_fields(_guest_save(game))), "route-blocking placement keeps the same guest, position, meal, preference, animation and visit clocks")
	_check(game.save_data().random_state == before.random_state and game.save_data().remainder == before.remainder, "navigation changes spend no service RNG or fractional time while Edit is frozen")
	return str(result.get("id", ""))

func _live(game: GameSession) -> void:
	_check(game.command({"type": "set_mode", "mode": "live"}).ok, "public Live resumes the existing blocked visit")

func _wait(game: GameSession, predicate: Callable, limit := 20.0) -> bool:
	for index in range(int(ceil(limit / 0.05))):
		if predicate.call(game): return true
		game.advance(0.05)
	return predicate.call(game)

func _feet_clear(scene: Dictionary) -> bool:
	for guest in scene.customers:
		var foot := Vector2(float(guest.x) + float(guest.render_offset_x), float(guest.y) + float(guest.render_offset_y))
		if not is_finite(foot.x) or not is_finite(foot.y): return false
		var cell := Vector2i(floori(foot.x + 0.5), floori(foot.y + 0.5))
		if cell.x < 0 or cell.y < 0 or cell.x >= scene.floor.columns or cell.y >= scene.floor.rows: return false
		for object in scene.objects:
			if Vector2i(object.x, object.y) == cell and not (object.kind == "seat" and object.id == guest.seat_id): return false
	return true

func _test_old_route_and_guards() -> void:
	var game := Session.new_session(41, _configuration())
	game.advance(0.6)
	_edit(game)
	_check(_first(game).phase == "walking" and absf(float(_first(game).y) - 1.0) < 0.000001, "the edit begins with an ordinary guest a full two cells before the door")
	var prior := game.save_data()
	for request in [
		{"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 0},
		{"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": 1},
		{"type": "editor_place", "inventory_id": "crate-wood", "x": 0, "y": 3},
		{"type": "editor_place", "inventory_id": "crate-wood", "x": 7, "y": 2},
		{"type": "editor_move", "id": "seat", "x": 5, "y": 5},
	]:
		var result := game.command(request)
		_check(not result.ok and _same(prior, game.save_data()), "route freedom preserves entrance, direct guest-foot overlap, occupied-cell, floor bounds and assigned-seat guards: %s" % request)
	var history := Session.new_session(41, _configuration())
	history.advance(1.1)
	_edit(history)
	var past: Dictionary = _guest_save(history)
	var past_drop := history.command({"type": "editor_place", "inventory_id": "plant-angular", "x": 3, "y": 1})
	_check(past_drop.ok and _same(_visit_fields(past), _visit_fields(_guest_save(history))) and _first(history).navigation_mode == "goal", "a walking guest does not reserve a tile already passed on its old route")
	var closed := _seal(game)
	_check(not closed.is_empty() and _first(game).navigation_mode == "wander", "closing the one-cell doorway enters wander mode without rejecting the edit")
	var frozen := game.save_data()
	_check(game.advance(600.0).is_empty() and _same(frozen, game.save_data()), "Edit freezes even a guest whose route is newly blocked")
	var reopened := Session.new_session(999)
	_check(reopened.restore(_copy(frozen)) and _same(frozen, reopened.save_data()), "blocked Edit state reopens byte-for-byte through the public save boundary")

func _test_alternative_route() -> void:
	var game := Session.new_session(41, _configuration(true))
	game.advance(0.6)
	_edit(game)
	_seal(game)
	_check(_first(game).navigation_mode == "goal" and _guest_save(game).path.any(func(point): return int(point.x) == 4 and int(point.y) == 3), "a blocked old aisle reroutes through the remaining opening rather than wandering")
	_live(game)
	var clear := true
	var saw_alternate := false
	for index in range(130):
		game.advance(0.05)
		clear = clear and _feet_clear(game.snapshot())
		var guest := _first(game)
		if not guest.is_empty() and absf(float(guest.x) - 4.0) < 0.000001 and absf(float(guest.y) - 3.0) < 0.11: saw_alternate = true
	_check(clear and saw_alternate and game.snapshot().stats.sales == 1, "the real guest walks the free alternate door, sits, eats and pays once")

func _test_blocked_walking_continuation() -> void:
	var game := Session.new_session(41, _configuration())
	game.advance(0.625)
	_edit(game)
	var blocked_id := _seal(game)
	var identity: String = _first(game).id
	_live(game)
	var peer := Session.new_session(2)
	_check(peer.restore(_copy(game.save_data())), "the first blocked Live state is a valid save")
	var clear := true
	var stayed := true
	var moving := false
	var no_jump := true
	var positions := {}
	var previous := Vector2(float(_first(game).x), float(_first(game).y))
	var events: Array = []
	for index in range(3600):
		var actual: Array = game.advance(0.05)
		var expected: Array = peer.advance(0.05)
		clear = clear and _feet_clear(game.snapshot())
		stayed = stayed and _same(actual, expected) and _same(game.save_data(), peer.save_data())
		events.append_array(actual)
		var guest := _first(game)
		if guest.is_empty():
			stayed = false
			break
		var current := Vector2(float(guest.x), float(guest.y))
		no_jump = no_jump and current.distance_to(previous) <= 0.100001
		moving = moving or current.distance_to(previous) > 0.001
		positions[Vector2i(roundi(current.x), roundi(current.y))] = true
		stayed = stayed and guest.id == identity and guest.phase == "walking" and guest.navigation_mode == "wander" and float(guest.y) < 2.500001 and guest.visual_phase == "walk"
		previous = current
	_check(stayed and game.snapshot().elapsed > 180.0, "a sealed guest keeps the same walking visit for three minutes with deterministic saved continuation")
	_check(clear and no_jump and moving and positions.size() >= 3, "wandering uses multiple real free-floor cells at the ordinary walking speed, without furniture clipping or teleporting")
	_check(events.filter(func(event): return event.type in ["sale", "departed", "visit_abandoned", "eating_started"]).is_empty() and game.snapshot().coins == 120 and game.snapshot().stats.sales == 0, "a blocked guest never disappears, abandons, steals food, pays or changes coins")
	_edit(game)
	var before := _guest_save(game)
	_check(game.command({"type": "editor_remove", "id": blocked_id}).ok, "the player can reopen the doorway after arbitrarily long wandering")
	_check(_first(game).navigation_mode == "goal" and _same(_visit_fields(before), _visit_fields(_guest_save(game))), "unblocking restores the same guest's intended seat without resetting their visit or position")
	_live(game)
	_check(_wait(game, func(session): return session.snapshot().customers.is_empty(), 20.0) and game.snapshot().stats.sales == 1 and game.snapshot().coins == 134, "the formerly trapped guest resumes, eats, pays exactly once and leaves after the door opens")

func _test_seated_history_and_paid_departure() -> void:
	var game := Session.new_session(7, _configuration(false, 1000.0))
	_check(_wait(game, func(session): return not _first(session).is_empty() and _first(session).phase == "waiting"), "historic-path fixture seats an ordinary unfed guest")
	_edit(game)
	var before := _guest_save(game)
	var historic := game.command({"type": "editor_place", "inventory_id": "plant-angular", "x": 3, "y": 1})
	_check(historic.ok and _same(_visit_fields(before), _visit_fields(_guest_save(game))), "furniture may occupy the aisle a seated guest already walked without forcing that guest to stand or resetting hunger")
	var reopened := Session.new_session(1)
	_check(reopened.restore(_copy(game.save_data())) and _same(game.save_data(), reopened.save_data()), "seated historic-route edits retain valid exact saved continuation")
	var paid := Session.new_session(7, _configuration())
	_check(_wait(paid, func(session): return not _first(session).is_empty() and _first(session).phase == "eating"), "paid-exit fixture reaches a real owned meal")
	_edit(paid)
	var meal_before := _guest_save(paid)
	var closed_id := _seal(paid)
	_check(_same(meal_before.meal_dish, _guest_save(paid).meal_dish) and _first(paid).phase == "eating", "closing the exit preserves the in-progress plate and seated eat animation")
	_live(paid)
	var events: Array = paid.advance(90.0)
	_check(not _first(paid).is_empty() and _first(paid).phase == "leaving" and _first(paid).navigation_mode == "wander", "after finishing the meal, a blocked departing guest wanders on its side of the barrier")
	_check(events.filter(func(event): return event.type == "sale").size() == 1 and events.filter(func(event): return event.type == "departed").is_empty() and paid.snapshot().coins == 134 and paid.snapshot().stats.sales == 1, "a stranded departure retains the completed one-time payment without fake departure or repeat rewards")
	var peer := Session.new_session(3)
	var restored := peer.restore(_copy(paid.save_data()))
	var peer_events: Array = peer.advance(30.0) if restored else []
	var paid_events: Array = paid.advance(30.0) if restored else []
	_check(restored and _same(peer_events, paid_events) and _same_continuation(peer.save_data(), paid.save_data()), "paid wandering departures reopen with identical future events, visit, navigation and clocks")
	_edit(paid)
	_check(paid.command({"type": "editor_remove", "id": closed_id}).ok, "the paid guest's exit can be restored later")
	_live(paid)
	_check(_wait(paid, func(session): return session.snapshot().customers.is_empty()) and paid.snapshot().coins == 134 and paid.snapshot().stats.sales == 1, "restoring the exit departs the same guest without replaying a sale")

func _test_legacy_navigation() -> void:
	var current := Session.new_session(41, _configuration())
	current.advance(0.625)
	var legacy := _copy(current.save_data())
	legacy.erase("customer_navigation_version")
	legacy.configuration.customers.erase("wander_retry_seconds")
	legacy.configuration.customers.erase("wander_speed_multiplier")
	for customer in legacy.state.customers:
		for field in ["navigation_mode", "path_origin", "navigation_retry_elapsed", "wander_cursor"]: customer.erase(field)
	var reopened := Session.new_session(99)
	_check(reopened.restore(legacy), "a real pre-navigation walking save migrates through the public restore boundary")
	_check(_same(_visit_fields(current.save_data().state.customers[0]), _visit_fields(_guest_save(reopened))) and reopened.save_data().random_state == legacy.random_state and reopened.save_data().remainder == legacy.remainder, "navigation migration retains old guest positions, visits, animation, RNG and fractional time")
	_check(_same(current.advance(12.0), reopened.advance(12.0)) and _same(current.save_data(), reopened.save_data()), "an unedited legacy restaurant continues identically to the new navigation schema")
	var corrupt := _copy(legacy)
	corrupt.state.customers[0].path[0] = {"x": 0, "y": 3}
	var before := reopened.save_data()
	_check(not reopened.restore(corrupt) and _same(before, reopened.save_data()), "legacy migration validates the old route before adding navigation fields")

func _test_invalid_navigation_saves() -> void:
	var game := Session.new_session(41, _configuration())
	game.advance(0.6)
	_edit(game)
	_seal(game)
	_live(game)
	game.advance(0.35)
	var pristine := _copy(game.save_data())
	_check(pristine.get("customer_navigation_version") == 1, "the save declares the blocked-route navigation schema")
	for field_and_value in [["navigation_mode", "teleport"], ["navigation_retry_elapsed", -0.1], ["navigation_retry_elapsed", "0"], ["wander_cursor", -1], ["wander_cursor", 0.5], ["path_origin", {"x": -100, "y": 0}], ["path_origin", {"x": 0, "y": "0"}]]:
		var corrupt := _copy(pristine)
		corrupt.state.customers[0][field_and_value[0]] = field_and_value[1]
		_check(not game.restore(corrupt) and _same(pristine, game.save_data()), "malformed saved navigation is rejected atomically: %s" % field_and_value[0])
	for field in ["navigation_mode", "navigation_retry_elapsed", "wander_cursor", "path_origin"]:
		var missing := _copy(pristine)
		missing.state.customers[0].erase(field)
		_check(not game.restore(missing) and _same(pristine, game.save_data()), "current navigation saves require every declared field atomically: %s" % field)
	for setting in [["wander_retry_seconds", 0.0], ["wander_retry_seconds", -0.8], ["wander_speed_multiplier", 0.0], ["wander_speed_multiplier", 1.1]]:
		var bad_configuration := _copy(pristine)
		bad_configuration.configuration.customers[setting[0]] = setting[1]
		_check(not game.restore(bad_configuration) and _same(pristine, game.save_data()), "invalid wandering tuneables are rejected without altering the running guest")
	var illegal_path := _copy(pristine)
	illegal_path.state.customers[0].path = [{"x": 0, "y": 3}]
	illegal_path.state.customers[0].path_index = 0
	_check(not game.restore(illegal_path) and _same(pristine, game.save_data()), "saved wandering cannot cross a solid crate barrier")
	var version := _copy(pristine)
	version.customer_navigation_version = 999
	_check(not game.restore(version) and _same(pristine, game.save_data()), "future navigation schema is rejected without changing the current restaurant")

func _same_continuation(left: Dictionary, right: Dictionary) -> bool:
	# The unchanged arrival clock subtracts binary floats each fixed step. A
	# 1000-second isolated arrival interval may round-trip through JSON with
	# sub-picosecond drift; no other persisted field receives this tolerance.
	if absf(float(left.state.arrival_remaining) - float(right.state.arrival_remaining)) > 0.000000001: return false
	var a := left.duplicate(true)
	var b := right.duplicate(true)
	a.state.erase("arrival_remaining")
	b.state.erase("arrival_remaining")
	return _same(a, b)
