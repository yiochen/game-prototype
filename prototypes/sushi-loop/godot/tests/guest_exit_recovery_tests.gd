extends SceneTree
## A blocked seat is different from a trapped visitor: a reachable entrance
## must let an already-admitted guest leave without payment or teleporting.
const Session = preload("res://scripts/session.gd")
const View = preload("res://scripts/restaurant_view.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_test_clear_entrance_and_edit_freeze()
	_test_old_wander_fractional_recovery()
	_test_true_trap_and_exit_reopening()
	_test_original_seat_priority()
	_test_already_at_entrance()
	_test_paid_departure()
	_test_departure_validation()
	if failures.is_empty():
		print("PASS: %s guest exit recovery checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		printerr("%s of %s guest exit recovery checks failed" % [failures.size(), checks])
		quit(1)

func _check(value: bool, description: String) -> void:
	checks += 1
	if not value: failures.append(description)

func _copy(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value, "", true, true))

func _same(left: Variant, right: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(left, "", true, true)) == JSON.parse_string(JSON.stringify(right, "", true, true))

func _same_continuation(left: Dictionary, right: Dictionary) -> bool:
	# The existing 1000-second arrival countdown can round-trip one ULP away
	# through JSON. Navigation, reactions, visit clocks, RNG and every other
	# saved field still require an exact match, as do all public exit events.
	if absf(float(left.state.arrival_remaining) - float(right.state.arrival_remaining)) > 0.000000001: return false
	var a := left.duplicate(true)
	var b := right.duplicate(true)
	a.state.erase("arrival_remaining")
	b.state.erase("arrival_remaining")
	return _same(a, b)

func _configuration(pocket := false, preparation := 1000.0) -> Dictionary:
	var objects: Array = [
		{"id": "chef", "kind": "chef", "x": 2, "y": 6, "facing": "east", "recipe_id": "salmon_nigiri", "art_id": "chef-lena"},
		{"id": "belt", "kind": "belt", "x": 3, "y": 6, "facing": "south"},
		{"id": "seat", "kind": "seat", "x": 3, "y": 5, "facing": "south"},
	]
	for y in ([1, 3] if pocket else [3]):
		for x in range(7):
			if x != 3: objects.append({"id": "wall-%s-%s" % [x, y], "kind": "decor", "art_id": "crate-wood", "x": x, "y": y, "facing": "south"})
	return {
		"floor": {"columns": 7, "rows": 7, "world_columns": 21, "viewport_columns": 7, "entrance": {"x": 3, "y": 0}},
		"recipes": {"salmon_nigiri": {"preparation_seconds": preparation}},
		"service": {"step_seconds": 0.05, "belt_seconds_per_cell": 0.2, "first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "walking_cells_per_second": 2.0, "eating_seconds": 0.5, "loading_seconds": 0.1, "sitting_seconds": 0.1, "standing_seconds": 0.1},
		"customers": {"preference_seconds": 0.8, "happy_seconds": 0.4, "restless_seconds": 1.5, "leave_seconds": 3.0, "fullness_min": 1.0, "fullness_max": 1.0, "dish_fullness_min": 1.0, "dish_fullness_max": 1.0, "eating_jitter_seconds": 0.0, "passing_offset": 0.24, "personal_space": 0.4},
		"objects": objects,
	}

func _guest(game: GameSession) -> Dictionary:
	var guests: Array = game.save_data().state.customers
	return guests[0].duplicate(true) if not guests.is_empty() else {}

func _snapshot_guest(game: GameSession) -> Dictionary:
	var guests: Array = game.snapshot().customers
	return guests[0] if not guests.is_empty() else {}

func _visit(customer: Dictionary) -> Dictionary:
	var result := customer.duplicate(true)
	for key in ["path", "path_index", "path_origin", "navigation_mode", "navigation_retry_elapsed", "wander_cursor", "wander_elapsed"]: result.erase(key)
	return result

func _edit(game: GameSession) -> void:
	_check(game.command({"type": "set_mode", "mode": "edit"}).ok, "public Edit pauses the escape scenario")

func _live(game: GameSession) -> void:
	_check(game.command({"type": "set_mode", "mode": "live"}).ok, "public Live resumes the escape scenario")

func _close(game: GameSession, y: int) -> String:
	var response := game.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 3, "y": y})
	_check(response.ok, "a permitted furnishing edit closes doorway y=%s" % y)
	return str(response.get("id", ""))

func _wait(game: GameSession, predicate: Callable, limit := 20.0) -> bool:
	for index in range(int(ceil(limit / 0.05))):
		if predicate.call(game): return true
		game.advance(0.05)
	return predicate.call(game)

func _feedback(game: GameSession) -> String:
	var view := View.new()
	var result := str(view.customer_feedback(_snapshot_guest(game)).get("object", ""))
	view.free()
	return result

func _test_clear_entrance_and_edit_freeze() -> void:
	var game := Session.new_session(61, _configuration())
	game.advance(0.675)
	_edit(game)
	var prior := game.save_data()
	_close(game, 3)
	_check(_same(_visit(prior.state.customers[0]), _visit(_guest(game))), "Edit keeps the exact walking phase, fractional position, visit and animation while replanning a blocked seat")
	var frozen := _copy(game.save_data())
	_check(game.advance(100.0).is_empty() and _same(frozen, game.save_data()), "a reachable exit does not cause an abandonment or clock change during Edit")
	var peer := Session.new_session(999)
	_check(peer.restore(frozen) and _same(frozen, peer.save_data()), "the undecided Edit visit reopens exactly without a restore-time departure")
	_live(game)
	var before := _guest(game)
	var random_state: String = game.save_data().random_state
	var events: Array = game.advance(0.025)
	var leaving := _guest(game)
	_check(leaving.phase == "leaving" and leaving.departure_reason == "seat_unreachable" and leaving.navigation_mode == "goal" and leaving.visual_phase == "walk", "the first Live fixed step chooses a real exit route and keeps the already-standing walk pose")
	_check(is_equal_approx(float(leaving.y), float(before.y) - 0.1) and is_equal_approx(float(leaving.x), float(before.x)) and is_zero_approx(float(leaving.wander_elapsed)), "the escaping guest moves from the exact fractional position at normal walking speed and clears the scare clock")
	_check(_feedback(game) != "bubble-panic" and game.save_data().random_state == random_state and game.snapshot().coins == 120 and game.snapshot().stats.sales == 0, "a reachable exit clears scared feedback without any RNG, sale or reward")
	var continued := Session.new_session(4)
	# Restore must preserve its decoded JSON input exactly. Comparing against
	# pre-serialization doubles instead would test the JSON parser's one-ULP
	# roundtrip for fractional offsets rather than this navigation behavior.
	var decoded_save := _copy(game.save_data())
	_check(continued.restore(decoded_save) and _same(decoded_save, continued.save_data()), "a partially walked seat-unreachable departure preserves its decoded save exactly")
	var deterministic := true
	for index in range(60):
		var actual: Array = game.advance(0.05)
		var expected: Array = continued.advance(0.05)
		events.append_array(actual)
		deterministic = deterministic and _same(actual, expected) and _same_continuation(game.save_data(), continued.save_data())
	_check(deterministic, "escape save continuation has identical public events and state across all sixty fixed steps")
	var departed: Array = events.filter(func(event): return event.type == "departed")
	_check(game.snapshot().customers.is_empty() and departed.size() == 1 and departed[0].reason == "seat_unreachable", "the blocked-seat visitor reaches the entrance and emits one honest departure")
	_check(events.filter(func(event): return event.type in ["sale", "eating_started"]).is_empty() and game.snapshot().coins == 120, "walking away from an unusable seat never invents a meal or payment")

func _test_old_wander_fractional_recovery() -> void:
	var source := Session.new_session(62, _configuration())
	source.advance(0.675)
	_edit(source)
	_close(source, 3)
	var old := _copy(source.save_data())
	old.state.mode = "live"
	old.state.customers[0].navigation_retry_elapsed = 0.35
	old.state.customers[0].wander_elapsed = 7.25
	var game := Session.new_session(6)
	_check(game.restore(old) and _same(old, game.save_data()), "an existing 0.4.7 wandering save with a clear exit restores byte-for-byte, including its partial retry clock")
	var origin := Vector2(float(_guest(game).x), float(_guest(game).y))
	game.advance(0.025)
	var leaving := _guest(game)
	_check(leaving.phase == "leaving" and leaving.departure_reason == "seat_unreachable" and leaving.navigation_mode == "goal" and is_zero_approx(float(leaving.navigation_retry_elapsed)), "an old wander state recovers on its first Live step without waiting for the remaining retry interval")
	_check(Vector2(float(leaving.x), float(leaving.y)).distance_to(origin) <= 0.100001 and float(leaving.y) < origin.y and _feedback(game) != "bubble-panic", "old-save recovery walks toward the door directly without an extra wandering step or teleport")

func _test_true_trap_and_exit_reopening() -> void:
	var game := Session.new_session(63, _configuration(true))
	game.advance(1.1)
	_edit(game)
	var entry := _close(game, 1)
	_close(game, 3)
	_live(game)
	var identity: String = _guest(game).id
	var events: Array = []
	var positions := {}
	for index in range(200):
		events.append_array(game.advance(0.05))
		var guest := _guest(game)
		if not guest.is_empty(): positions[Vector2i(roundi(float(guest.x)), roundi(float(guest.y)))] = true
	_check(not _guest(game).is_empty() and _guest(game).id == identity and _guest(game).phase == "walking" and _guest(game).navigation_mode == "wander" and positions.size() >= 3, "a guest cut off from both seat and entrance keeps wandering among real free-floor cells")
	_check(_feedback(game) == "bubble-panic" and not events.any(func(event): return event.type in ["sale", "departed"]), "only the genuinely trapped guest keeps the scared bubble and remains in the restaurant")
	_edit(game)
	var before := _guest(game)
	_check(game.command({"type": "editor_remove", "id": entry}).ok and _same(_visit(before), _visit(_guest(game))), "opening only the entrance during Edit preserves the trapped visit until Live")
	_live(game)
	game.advance(0.05)
	_check(_guest(game).phase == "leaving" and _guest(game).navigation_mode == "goal" and _feedback(game) != "bubble-panic", "opening only the exit lets a trapped guest stop being scared and leave even while the seat stays blocked")
	_check(_wait(game, func(session): return session.snapshot().customers.is_empty()) and game.snapshot().stats.sales == 0, "the released guest follows the reopened doorway to an unpaid exit")

func _test_original_seat_priority() -> void:
	var source := Session.new_session(64, _configuration())
	source.advance(0.675)
	_edit(source)
	var barrier := _close(source, 3)
	var old_guest := _guest(source)
	_check(source.command({"type": "editor_remove", "id": barrier}).ok, "the seat-priority fixture restores both original seat and entrance access")
	var old := _copy(source.save_data())
	old.state.mode = "live"
	old.state.customers[0] = old_guest
	var game := Session.new_session(7)
	_check(game.restore(old), "an older wandering route remains a valid save after both destinations become reachable")
	game.advance(0.025)
	_check(_guest(game).phase == "walking" and _guest(game).navigation_mode == "goal" and _guest(game).departure_reason == "" and float(_guest(game).y) > float(old_guest.y), "a reachable assigned seat takes priority over a reachable exit on the first resumed Live step")
	_check(_feedback(game) != "bubble-panic", "resuming the original seat also clears the trapped reaction")
	var pocket := Session.new_session(65, _configuration(true))
	pocket.advance(1.1)
	_edit(pocket)
	_close(pocket, 1)
	var front := _close(pocket, 3)
	_live(pocket)
	pocket.advance(0.25)
	_edit(pocket)
	_check(pocket.command({"type": "editor_remove", "id": front}).ok and _guest(pocket).phase == "walking" and _guest(pocket).navigation_mode == "goal", "opening only the seat route resumes the original visit even while the entrance is still blocked")
	_live(pocket)
	_check(_wait(pocket, func(session): return not _guest(session).is_empty() and _guest(session).phase == "waiting"), "a released seat-bound guest reaches the original stool normally")

func _test_already_at_entrance() -> void:
	var game := Session.new_session(66, _configuration())
	game.advance(0.1)
	_edit(game)
	_close(game, 3)
	_live(game)
	var events: Array = game.advance(0.05)
	var departures: Array = events.filter(func(event): return event.type == "departed")
	_check(game.snapshot().customers.is_empty() and departures.size() == 1 and departures[0].reason == "seat_unreachable", "an admitted guest already at the entrance can leave through a valid zero-length exit route")
	_check(game.advance(1.0).filter(func(event): return event.type == "departed").is_empty() and game.snapshot().coins == 120, "an entrance departure cannot replay or produce payment on later steps")

func _test_paid_departure() -> void:
	var game := Session.new_session(67, _configuration(false, 0.25))
	_check(_wait(game, func(session): return not _guest(session).is_empty() and _guest(session).phase == "eating"), "the paid-exit fixture reaches a real owned meal")
	_edit(game)
	var barrier := _close(game, 3)
	_live(game)
	var events: Array = game.advance(5.0)
	_check(_guest(game).phase == "leaving" and _guest(game).navigation_mode == "wander" and _guest(game).departure_reason == "satisfied" and _feedback(game) == "bubble-panic", "a paid guest with a genuinely blocked exit still wanders scared with the original departure reason")
	_check(events.filter(func(event): return event.type == "sale").size() == 1 and game.snapshot().coins == 134, "the stranded departure completes its original payment exactly once")
	_edit(game)
	_check(game.command({"type": "editor_remove", "id": barrier}).ok and _guest(game).navigation_mode == "goal" and _guest(game).departure_reason == "satisfied", "reopening an existing paid departure restores its exit without changing its visit reason")
	_live(game)
	_check(_wait(game, func(session): return session.snapshot().customers.is_empty()) and game.snapshot().coins == 134 and game.snapshot().stats.sales == 1, "the paid guest leaves through the restored exit without a second sale or reward")

func _test_departure_validation() -> void:
	var game := Session.new_session(68, _configuration())
	game.advance(0.675)
	_edit(game)
	_close(game, 3)
	_live(game)
	game.advance(0.025)
	var valid := _copy(game.save_data())
	var peer := Session.new_session(8)
	_check(peer.restore(valid) and _same(valid, peer.save_data()), "the explicit seat_unreachable departure reason is supported by strict saved-state validation")
	for reason in ["", "blocked", "no_seat", 1, null]:
		var invalid := _copy(valid)
		invalid.state.customers[0].departure_reason = reason
		_check(not peer.restore(invalid) and _same(valid, peer.save_data()), "a malformed or phase-incompatible departure reason is rejected atomically: %s" % str(reason))
	var inconsistent := _copy(valid)
	inconsistent.state.customers[0].phase = "walking"
	_check(not peer.restore(inconsistent) and _same(valid, peer.save_data()), "a walking guest cannot already have a departure reason")
