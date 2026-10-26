extends SceneTree
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)
func config() -> Dictionary:
	return {"objects": [
		{"id": "chef", "kind": "chef", "x": 4, "y": 7, "facing": "east", "recipe_id": "salmon_nigiri", "art_id": "chef-lena"},
		{"id": "belt", "kind": "belt", "x": 5, "y": 7, "facing": "south"},
		{"id": "seat", "kind": "seat", "x": 5, "y": 6, "facing": "south"}],
		"recipes": {"salmon_nigiri": {"preparation_seconds": 0.2}},
		"service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "eating_seconds": 0.5, "sitting_seconds": 0.1, "standing_seconds": 0.1, "loading_seconds": 0.1},
		"customers": {"fullness_min": 1.0, "fullness_max": 1.0, "dish_fullness_min": 1.0, "dish_fullness_max": 1.0, "eating_jitter_seconds": 0.0}}
func guest(game: GameSession) -> Dictionary:
	var guests: Array = game.save_data().state.customers
	return guests[0] if not guests.is_empty() else {}
func reopen(game: GameSession) -> bool:
	var peer = Session.new_session(123)
	return peer.restore(JSON.parse_string(JSON.stringify(game.save_data(), "", true, true)))
func wait_for(game: GameSession, predicate: Callable, steps := 500) -> bool:
	for index in range(steps):
		if predicate.call(): return true
		game.advance(0.05)
	return predicate.call()
func place(game: GameSession, x: int) -> Dictionary:
	return game.command({"type": "editor_place", "inventory_id": "crate-wood", "x": x, "y": 3})
func _initialize() -> void:
	_test_actual_routes()
	_test_blocked_admission()
	_test_blocked_departure()
	if failures.is_empty():
		print("PASS: %s entrance route and blocking checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		quit(1)
func _test_actual_routes() -> void:
	var entries := {}
	var exits := {}
	var routes_valid := true
	var same_lane := true
	var visited_entry_apron := 0
	var visited_exit_apron := 0
	for seed_value in range(1, 25):
		var game = Session.new_session(seed_value, config())
		var entered := false
		var departed := false
		for step in range(500):
			game.advance(0.05)
			var visitor := guest(game)
			if visitor.is_empty():
				if departed: break
				continue
			if visitor.has("door_motion"): continue
			if visitor.phase == "walking" and float(visitor.y) > 3.1 and float(visitor.y) < 3.9:
				var lane := int(visitor.door_lane)
				entries[lane] = true
				same_lane = same_lane and is_equal_approx(float(visitor.x), float(lane))
				if not entered:
					visited_entry_apron += 1
					routes_valid = routes_valid and reopen(game)
					entered = true
			if visitor.phase == "leaving" and float(visitor.y) > 3.1 and float(visitor.y) < 3.9:
				var lane := int(visitor.door_lane)
				exits[lane] = true
				same_lane = same_lane and is_equal_approx(float(visitor.x), float(lane))
				if not departed:
					visited_exit_apron += 1
					routes_valid = routes_valid and reopen(game)
					departed = true
	check(entries.has(4) and entries.has(5) and visited_entry_apron == 24, "Real admitted guests walk through both front tiles on their way to a usable seat")
	check(exits.has(4) and exits.has(5) and visited_exit_apron == 24, "Real served guests approach both front tiles before leaving")
	check(same_lane, "Neither side is forced to merge into the left tile in front of the entrance")
	check(routes_valid, "Both sides' actual interior route segments survive save/reopen")
func _test_blocked_admission() -> void:
	var game = Session.new_session(7, config())
	game.command({"type": "set_mode", "mode": "edit"})
	var left := place(game, 4)
	var right := place(game, 5)
	check(left.ok and right.ok, "Objects can be placed on both front tiles, including the formerly reserved left tile")
	check(reopen(game), "A restaurant with both front tiles furnished saves and reopens")
	game.command({"type": "set_mode", "mode": "live"})
	game.advance(10.0)
	check(game.snapshot().customers.is_empty() and game.snapshot().stats.arrivals == 0, "A fully blocked entrance keeps new guests outside instead of spawning them inside objects")
	game.command({"type": "set_mode", "mode": "edit"})
	check(game.command({"type": "editor_remove", "id": right.get("id", "")}).ok, "Removing the right obstruction reopens that side")
	game.command({"type": "set_mode", "mode": "live"})
	game.advance(0.1)
	check(not guest(game).is_empty() and guest(game).x == 5 and guest(game).door_lane == 5, "With the left tile blocked, a guest enters through the right tile")
	check(reopen(game), "The one-sided entrance and active arrival save correctly")
	var invalid_rejected := true
	var peer = Session.new_session(123)
	for lane in [3, 6, 4.5, "5", null]:
		var invalid: Dictionary = JSON.parse_string(JSON.stringify(game.save_data(), "", true, true))
		invalid.state.customers[0].door_lane = lane
		invalid_rejected = invalid_rejected and not peer.restore(invalid)
	check(invalid_rejected, "Saved doorway lanes reject invalid types, fractions and out-of-opening values")
	var mirror = Session.new_session(8, config())
	mirror.command({"type": "set_mode", "mode": "edit"})
	check(place(mirror, 5).ok, "The right front tile also accepts an object on its own")
	mirror.command({"type": "set_mode", "mode": "live"})
	mirror.advance(0.1)
	check(not guest(mirror).is_empty() and guest(mirror).x == 4 and guest(mirror).door_lane == 4 and reopen(mirror), "With the right tile blocked, a guest uses the left tile and remains reopenable")
func _test_blocked_departure() -> void:
	var game = Session.new_session(9, config())
	if not wait_for(game, func(): return not guest(game).is_empty() and guest(game).phase == "eating"):
		check(false, "The obstruction fixture reaches a real meal")
		return
	game.command({"type": "set_mode", "mode": "edit"})
	var left := place(game, 4)
	var right := place(game, 5)
	check(left.ok and right.ok, "Both front tiles may be blocked while an admitted guest eats")
	game.command({"type": "set_mode", "mode": "live"})
	game.advance(5.0)
	check(not guest(game).is_empty() and guest(game).phase == "leaving" and guest(game).navigation_mode == "wander" and game.snapshot().stats.sales == 1, "A guest with no exit remains inside and completes payment only once")
	check(reopen(game), "A guest trapped by entrance furniture remains a valid saved visit")
	game.command({"type": "set_mode", "mode": "edit"})
	check(game.command({"type": "editor_remove", "id": right.get("id", "")}).ok, "Reopening the right front tile restores a valid route")
	check(guest(game).navigation_mode == "goal" and guest(game).door_lane == 5 and reopen(game), "The existing departure switches to the reopened right tile without resetting its visit")
	var offset: float = guest(game).door_exit_offset
	var rotated: Dictionary = game.command({"type": "editor_rotate", "id": left.id})
	check(rotated.ok and guest(game).door_exit_offset == offset and reopen(game), "Replanning around an unchanged obstruction preserves the selected crossing position")
	game.command({"type": "set_mode", "mode": "live"})
	check(wait_for(game, func(): return guest(game).is_empty()) and game.snapshot().stats.sales == 1 and game.snapshot().coins == 134, "The released guest uses the reopened entrance without another sale")
