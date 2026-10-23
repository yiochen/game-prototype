extends SceneTree
## Issue #11 scenarios use the public session command/time/snapshot/save seam.
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_test_current_starter_and_connections()
	_test_enclosed_assigned_chef()
	_test_seat_choice_and_directed_menus()
	_test_matching_first_dish()
	_test_preference_expiry_and_later_dishes()
	_test_fullness_and_recipe_timing()
	_test_unfed_departure()
	_test_guests_pass_through_each_other()
	_test_crossings_and_saved_passing()
	_test_default_service_stays_healthy()
	_test_saved_visit_phases()
	_test_default_save_continuation()
	_test_issue10_save_upgrade()
	_test_invalid_visit_saves()
	if failures.is_empty():
		print("PASS: %s customer visit checks" % checks)
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		printerr("%s of %s customer visit checks failed" % [failures.size(), checks])
		quit(1)

func _check(value: bool, description: String) -> void:
	checks += 1
	if not value:
		failures.append(description)

func _merge(base: Dictionary, changes: Dictionary) -> Dictionary:
	var result := base.duplicate(true)
	for key in changes:
		result[key] = _merge(result[key], changes[key]) if result.get(key) is Dictionary and changes[key] is Dictionary else changes[key]
	return result

func _base(changes: Dictionary = {}) -> Dictionary:
	return _merge({
		"floor": {"columns": 7, "rows": 7, "world_columns": 21, "viewport_columns": 7, "entrance": {"x": 3, "y": 0}},
		"recipes": {"salmon_nigiri": {"name": "Salmon nigiri", "price": 14, "preparation_seconds": 0.5}, "cucumber_maki": {"name": "Cucumber maki", "price": 10, "preparation_seconds": 0.5}},
		"service": {"step_seconds": 0.05, "belt_seconds_per_cell": 0.2, "first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0, "walking_cells_per_second": 4.0, "eating_seconds": 1.0, "loading_seconds": 0.1, "sitting_seconds": 0.1, "standing_seconds": 0.1},
		"customers": {"preference_seconds": 0.8, "happy_seconds": 0.4, "restless_seconds": 1.5, "leave_seconds": 3.0, "fullness_min": 1.0, "fullness_max": 1.0, "dish_fullness_min": 1.0, "dish_fullness_max": 1.0, "eating_jitter_seconds": 0.0, "passing_offset": 0.24, "personal_space": 0.4},
		"objects": [
			{"id": "chef", "kind": "chef", "x": 1, "y": 4, "facing": "north", "recipe_id": "salmon_nigiri"},
			{"id": "b1", "kind": "belt", "x": 1, "y": 3, "facing": "east"},
			{"id": "b2", "kind": "belt", "x": 2, "y": 3, "facing": "east"},
			{"id": "b3", "kind": "belt", "x": 3, "y": 3, "facing": "east"},
			{"id": "seat", "kind": "seat", "x": 3, "y": 2, "facing": "south"},
		],
	}, changes)

func _json_copy(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value, "", true, true))

func _same(left: Variant, right: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(left, "", true, true)) == JSON.parse_string(JSON.stringify(right, "", true, true))

func _object(scene: Dictionary, identity: String) -> Dictionary:
	for object in scene.objects:
		if object.id == identity:
			return object
	return {}

func _events(events: Array, kind: String) -> Array:
	return events.filter(func(event): return event.type == kind)

func _wait(game: GameSession, predicate: Callable, limit: float = 15.0) -> bool:
	for tick in range(int(ceil(limit / 0.05))):
		if predicate.call(game.snapshot()):
			return true
		game.advance(0.05)
	return predicate.call(game.snapshot())

func _first(scene: Dictionary) -> Dictionary:
	return scene.customers[0] if not scene.customers.is_empty() else {}

func _seed_food(game: GameSession, belt_id: String, recipe: String) -> bool:
	var data := _json_copy(game.save_data())
	for object in data.state.objects:
		if object.id == belt_id:
			if object.dish != null:
				return false
			object.dish = {"id": "dish-%s" % int(data.state.next_dish_id), "recipe_id": recipe}
			object.travel_elapsed = 0.0
			data.state.next_dish_id += 1
			return game.restore(data)
	return false

func _test_current_starter_and_connections() -> void:
	var game := Session.new_session(17)
	var scene: Dictionary = game.snapshot()
	_check(scene.floor.viewport_columns == 7 and scene.floor.columns == 7 and scene.floor.rows == 13, "fresh #11 restaurant retains the approved seven-column composition")
	_check(scene.recipes.has("salmon_nigiri") and scene.recipes.has("cucumber_maki"), "current starter has two identifiable recipes")
	var chefs: Array = scene.objects.filter(func(object): return object.kind == "chef")
	var seats: Array = scene.objects.filter(func(object): return object.kind == "seat")
	_check(chefs.filter(func(chef): return chef.active).size() == 2 and chefs.filter(func(chef): return not chef.active).size() == 1, "current starter shows two connected chefs and one dormant chef")
	_check(seats.filter(func(seat): return seat.active).size() == 4 and seats.filter(func(seat): return not seat.active).size() == 1, "current starter shows four useful seats and one dormant seat")
	game.advance(20.0)
	var inactive: Dictionary = game.snapshot().objects.filter(func(object): return object.kind == "chef" and not object.active)[0]
	_check(inactive.visual_phase == "idle" and inactive.preparation == 0.0 and inactive.held_dish == null, "disconnected chef visibly stays idle without preparing unusable food")
	_check(not scene.customers.any(func(customer): return customer.has("fullness") or customer.has("appetite_target") or customer.has("remaining_dishes")), "observable customers expose no fullness meter or remaining-plate count")

func _test_enclosed_assigned_chef() -> void:
	var configuration := _base()
	# A counter surrounds this stationary chef. Customer aisles lead directly
	# to the seat, but no empty-floor route can enter the chef's own cell.
	configuration.objects.append_array([
		{"id": "counter-w", "kind": "belt", "x": 0, "y": 4, "facing": "west"},
		{"id": "counter-e", "kind": "belt", "x": 2, "y": 4, "facing": "east"},
		{"id": "counter-s", "kind": "belt", "x": 1, "y": 5, "facing": "south"},
	])
	var game := Session.new_session(32, configuration)
	_check(_object(game.snapshot(), "chef").active and _object(game.snapshot(), "seat").active, "a stationary chef enclosed behind a valid counter still supplies a customer-accessible seat")
	var events: Array = game.advance(8.0)
	_check(not _events(events, "prepared").is_empty() and not _events(events, "loaded").is_empty(), "an enclosed assigned chef automatically prepares and loads food without a walking route")
	_check(_events(events, "sale").size() == 1 and game.snapshot().coins == 134, "an enclosed kitchen serves the reachable customer and credits the ordinary fixed-price sale")

func _test_seat_choice_and_directed_menus() -> void:
	var configuration := _base({"objects": [
		{"id": "salmon-chef", "kind": "chef", "x": 1, "y": 4, "facing": "north", "recipe_id": "salmon_nigiri"},
		{"id": "salmon-belt", "kind": "belt", "x": 1, "y": 3, "facing": "east"},
		{"id": "salmon-end", "kind": "belt", "x": 2, "y": 3, "facing": "east"},
		{"id": "salmon-seat", "kind": "seat", "x": 2, "y": 2, "facing": "south"},
		{"id": "cucumber-chef", "kind": "chef", "x": 4, "y": 4, "facing": "north", "recipe_id": "cucumber_maki"},
		{"id": "cucumber-belt", "kind": "belt", "x": 4, "y": 3, "facing": "east"},
		{"id": "cucumber-end", "kind": "belt", "x": 5, "y": 3, "facing": "east"},
		{"id": "cucumber-seat", "kind": "seat", "x": 5, "y": 2, "facing": "south"},
		{"id": "wrong-way", "kind": "belt", "x": 0, "y": 3, "facing": "west"},
		{"id": "wrong-way-seat", "kind": "seat", "x": 0, "y": 2, "facing": "south"},
	]})
	var seen := {}
	var all_useful := true
	for seed_value in range(1, 13):
		var game := Session.new_session(seed_value, configuration)
		game.advance(0.1)
		var visitor := _first(game.snapshot())
		if visitor.is_empty():
			all_useful = false
			continue
		seen[visitor.preferred_recipe_id] = true
		all_useful = all_useful and visitor.seat_id == ("salmon-seat" if visitor.preferred_recipe_id == "salmon_nigiri" else "cucumber-seat")
		all_useful = all_useful and not _object(game.snapshot(), "wrong-way-seat").active
	_check(all_useful and seen.size() == 2, "seeded preferences choose matching reachable chef boards and ignore a nearby belt pointing away from supply")
	var preferred_ready := 0
	var ready_choices_correct := true
	for seed_value in range(1, 13):
		var ready := Session.new_session(seed_value, configuration)
		ready_choices_correct = ready_choices_correct and _seed_food(ready, "cucumber-end", "salmon_nigiri")
		ready.advance(0.1)
		var visitor := _first(ready.snapshot())
		if visitor.preferred_recipe_id == "salmon_nigiri":
			preferred_ready += 1
			ready_choices_correct = ready_choices_correct and visitor.seat_id == "cucumber-seat"
	_check(preferred_ready > 0 and ready_choices_correct, "an immediately available matching dish takes precedence over a matching distant chef board")
	var inaccessible := _base({"objects": [
		{"id": "chef", "kind": "chef", "x": 4, "y": 6, "facing": "east", "recipe_id": "salmon_nigiri"},
		{"id": "front", "kind": "belt", "x": 5, "y": 6, "facing": "east"},
		{"id": "seat", "kind": "seat", "x": 5, "y": 5, "facing": "south"},
		{"id": "wall-w", "kind": "belt", "x": 4, "y": 5, "facing": "north"},
		{"id": "wall-n", "kind": "belt", "x": 5, "y": 4, "facing": "north"},
		{"id": "wall-e", "kind": "belt", "x": 6, "y": 5, "facing": "north"},
	]})
	var blocked := Session.new_session(3, inaccessible)
	blocked.advance(5.0)
	_check(_object(blocked.snapshot(), "seat").inactive_reason == "no_access" and blocked.snapshot().customers.all(func(customer): return customer.phase == "entrance_wait" and customer.seat_id == ""), "a supplied seat surrounded by furniture remains inactive; any unadmitted visitor stays at the entrance instead of walking to it")

func _test_matching_first_dish() -> void:
	var game := Session.new_session(6, _base())
	var matched: Array = []
	for tick in range(200):
		matched.append_array(_events(game.advance(0.05), "preference_matched"))
		if not matched.is_empty():
			break
	var visitor := _first(game.snapshot())
	_check(matched.size() == 1 and visitor.preference_phase == "satisfied" and visitor.phase == "eating", "a matching first dish emits one happy reaction while the same customer begins eating")
	_check(visitor.preferred_recipe_id == visitor.meal_dish.recipe_id and visitor.happy_elapsed == 0.0, "happy state names the actual preferred dish and starts its saved clock at zero")
	var later: Array = game.advance(10.0)
	_check(_events(later, "preference_matched").is_empty() and _events(later, "sale").size() == 1, "the fulfilled preference runs once and the meal pays its fixed price once")

func _expiry_game() -> GameSession:
	var configuration := _base({"recipes": {"cucumber_maki": {"preparation_seconds": 100.0}}, "objects": [
		{"id": "chef", "kind": "chef", "x": 1, "y": 4, "facing": "north", "recipe_id": "cucumber_maki"},
		{"id": "b1", "kind": "belt", "x": 1, "y": 3, "facing": "east"},
		{"id": "b2", "kind": "belt", "x": 2, "y": 3, "facing": "east"},
		{"id": "b3", "kind": "belt", "x": 3, "y": 3, "facing": "east"},
		{"id": "seat", "kind": "seat", "x": 3, "y": 2, "facing": "south"},
	]})
	for seed_value in range(1, 30):
		var game := Session.new_session(seed_value, configuration)
		_seed_food(game, "b3", "salmon_nigiri")
		game.advance(0.1)
		if _first(game.snapshot()).preferred_recipe_id == "cucumber_maki":
			return game
	return null

func _test_preference_expiry_and_later_dishes() -> void:
	var game := _expiry_game()
	_check(game != null, "controlled seeds produce a cucumber preference over an available salmon dish")
	if game == null:
		return
	_check(_wait(game, func(scene): return not _first(scene).is_empty() and _first(scene).preference_phase == "active"), "first preference becomes visible with a timer after sitting")
	var before := _first(game.snapshot())
	_check(before.preference_progress > 0.0 and before.preference_progress <= 1.0 and _object(game.snapshot(), "b3").dish.recipe_id == "salmon_nigiri", "unmatched food stays on the stopped facing tile while the preference timer runs")
	var events: Array = game.advance(4.0)
	_check(_events(events, "preference_expired").size() == 1 and _events(events, "preference_matched").is_empty() and _events(events, "sale").size() == 1, "expiry accepts the stopped nonmatching dish without an undeserved happy reaction")
	var multiple := Session.new_session(9, _base({"recipes": {"salmon_nigiri": {"preparation_seconds": 100.0}}, "customers": {"fullness_min": 2.0, "fullness_max": 2.0}}))
	_check(_seed_food(multiple, "b3", "salmon_nigiri"), "multi-dish fixture begins with one genuine dish")
	_check(_wait(multiple, func(scene): return scene.stats.sales == 1 and _first(scene).phase == "waiting"), "a not-yet-full visitor waits for another plate after the first completed meal")
	_check(_seed_food(multiple, "b3", "cucumber_maki"), "second plate has a different identity from the original preference")
	var second: Array = multiple.advance(0.05)
	_check(_events(second, "eating_started").size() == 1 and _first(multiple.snapshot()).meal_dish.recipe_id == "cucumber_maki" and _first(multiple.snapshot()).preference_phase == "complete", "later dishes are accepted immediately without a second preference cycle")
	var finish: Array = multiple.advance(5.0)
	_check(_events(finish, "sale").size() == 1 and multiple.snapshot().coins == 120 + 14 + 10 and _events(finish, "preference_matched").is_empty(), "each recipe pays its own price with no turnover reward on a multi-dish visit")

func _test_fullness_and_recipe_timing() -> void:
	var plate_counts := {}
	var total_sales := 0
	var times: Array = []
	for recipe in ["salmon_nigiri", "cucumber_maki"]:
		for seed_value in range(1, 13):
			var configuration := _base({"customers": {"fullness_min": 1.3, "fullness_max": 2.8, "dish_fullness_min": 0.8, "dish_fullness_max": 1.2, "eating_jitter_seconds": 0.15}})
			configuration.objects[0].recipe_id = recipe
			var game := Session.new_session(seed_value, configuration)
			var began := -1.0
			var count := 0
			for tick in range(500):
				var events: Array = game.advance(0.05)
				if not _events(events, "eating_started").is_empty():
					began = float(game.snapshot().elapsed)
				if not _events(events, "sale").is_empty():
					count += 1
					times.append(float(game.snapshot().elapsed) - began)
			plate_counts[count] = true
			total_sales += count
	_check(plate_counts.size() >= 2 and not plate_counts.has(0) and total_sales > 24, "hidden continuous fullness produces varied multi-plate visits instead of a fixed dish count")
	_check(times.all(func(seconds): return seconds >= 0.85 - 0.000001 and seconds <= 1.2 + 0.000001), "both recipes share broadly similar eating durations independently of price and preparation")
	var visible := Session.new_session(2, _base())
	visible.advance(1.0)
	_check(visible.snapshot().customers.all(func(customer): return not customer.has("fullness") and not customer.has("appetite_target") and not customer.has("meal_fullness")), "fullness and per-dish appetite contributions remain hidden from the presentation")

func _test_unfed_departure() -> void:
	var game := Session.new_session(4, _base({"recipes": {"salmon_nigiri": {"preparation_seconds": 1000.0}}}))
	var events: Array = game.advance(10.0)
	_check(_events(events, "customer_restless").size() == 1 and _events(events, "visit_abandoned").size() == 1 and _events(events, "departed").size() == 1, "an unfed customer visibly becomes restless and then leaves autonomously")
	_check(game.snapshot().coins == 120 and game.snapshot().stats.sales == 0 and _events(events, "sale").is_empty(), "abandonment applies no fine, recurring fee, sales reward or reputation penalty")
	_check(not game.save_data().state.has("reputation"), "failed service stores no lasting reputation damage")

func _feet_are_clear(scene: Dictionary) -> bool:
	for customer in scene.customers:
		var cell := Vector2i(floori(float(customer.x) + float(customer.render_offset_x) + 0.5), floori(float(customer.y) + float(customer.render_offset_y) + 0.5))
		if cell.x < 0 or cell.y < 0 or cell.x >= int(scene.floor.columns) or cell.y >= int(scene.floor.rows):
			return false
		for object in scene.objects:
			if Vector2i(object.x, object.y) == cell and not (object.kind == "seat" and object.id == customer.seat_id):
				return false
	return true

func _corner_traffic_save() -> Dictionary:
	var objects: Array = [{"id": "chef", "kind": "chef", "x": 1, "y": 5, "facing": "north", "recipe_id": "salmon_nigiri"}]
	for x in range(1, 6):
		objects.append({"id": "b%s" % x, "kind": "belt", "x": x, "y": 4, "facing": "east"})
	for x in [4, 5]:
		objects.append({"id": "s%s" % x, "kind": "seat", "x": x, "y": 3, "facing": "south"})
	objects.append({"id": "obstacle", "kind": "decor", "art_id": "crate-wood", "x": 5, "y": 1, "facing": "south"})
	var game := Session.new_session(1, _base({"floor": {"entrance": {"x": 1, "y": 0}}, "objects": objects}))
	game.advance(0.1)
	var saved := _json_copy(game.save_data())
	var turning: Dictionary = saved.state.customers[0].duplicate(true)
	turning.seat_id = "s4"
	turning.x = 4.0
	turning.y = 0.125
	turning.render_offset_x = 0.48
	turning.facing = "south"
	turning.path = [{"x": 2, "y": 0}, {"x": 3, "y": 0}, {"x": 4, "y": 0}, {"x": 4, "y": 1}, {"x": 4, "y": 2}, {"x": 4, "y": 3}]
	turning.path_index = 3
	turning.yielding = true
	var crossing := turning.duplicate(true)
	crossing.id = "customer-2"
	crossing.seat_id = "s5"
	crossing.x = 4.25
	crossing.y = 0.0
	crossing.render_offset_x = 0.0
	crossing.render_offset_y = 0.48
	crossing.facing = "east"
	crossing.path = [{"x": 2, "y": 0}, {"x": 3, "y": 0}, {"x": 4, "y": 0}, {"x": 5, "y": 0}, {"x": 6, "y": 0}, {"x": 6, "y": 1}, {"x": 6, "y": 2}, {"x": 6, "y": 3}, {"x": 5, "y": 3}]
	saved.state.customers = [turning, crossing]
	saved.state.next_customer_id = 3
	saved.state.stats.arrivals = 2
	saved.state.entrance_open = false
	return saved

func _movement(customer: Dictionary) -> Dictionary:
	var result := {}
	for field in ["x", "y", "facing", "render_offset_x", "render_offset_y", "yielding"]:
		result[field] = customer[field]
	return result

func _test_guests_pass_through_each_other() -> void:
	# Two valid saved routes cross at a bend, with both guests already yielding.
	# Each guest must make exactly the same progress as when walking alone.
	var saved := _corner_traffic_save()
	var game := Session.new_session(1)
	var alone: Array = []
	_check(game.restore(saved), "a saved pair stuck across each other's lanes remains loadable")
	_check(_same(game.save_data(), saved), "loading an older yielding pair preserves its positions and visit clocks")
	for customer in saved.state.customers:
		var single := _json_copy(saved)
		single.state.customers = [customer.duplicate(true)]
		var peer := Session.new_session(1)
		_check(peer.restore(single), "the independent walking comparison starts from the same saved guest")
		alone.append(peer)
	var independent := true
	var crossed := false
	for tick in range(8):
		game.advance(0.05)
		var customers: Array = game.snapshot().customers
		for index in range(alone.size()):
			alone[index].advance(0.05)
			independent = independent and _same(_movement(customers[index]), _movement(alone[index].snapshot().customers[0]))
		var a := Vector2(customers[0].x + customers[0].render_offset_x, customers[0].y + customers[0].render_offset_y)
		var b := Vector2(customers[1].x + customers[1].render_offset_x, customers[1].y + customers[1].render_offset_y)
		crossed = crossed or a.distance_to(b) < 0.4
	_check(independent and crossed, "guests pass through each other at a corner without slowing either route")
	_check(_feet_are_clear(game.snapshot()), "nonblocking guests still avoid furniture and floor boundaries")
	_roundtrip(game, "guests crossing at a corner")
	game.advance(20.0)
	_check(game.snapshot().customers.is_empty() and game.snapshot().stats.sales == 2, "both formerly yielding guests finish their meals and leave normally")

func _test_crossings_and_saved_passing() -> void:
	var game := Session.new_session(23, _base({"service": {"first_arrival_seconds": 0.1, "arrival_seconds": 0.3, "walking_cells_per_second": 2.5, "eating_seconds": 0.45}, "customers": {"restless_seconds": 5.0, "leave_seconds": 10.0}, "objects": [
		{"id": "chef", "kind": "chef", "x": 1, "y": 5, "facing": "north", "recipe_id": "salmon_nigiri"},
		{"id": "b1", "kind": "belt", "x": 1, "y": 4, "facing": "east"},
		{"id": "b2", "kind": "belt", "x": 2, "y": 4, "facing": "east"},
		{"id": "b3", "kind": "belt", "x": 3, "y": 4, "facing": "east"},
		{"id": "b4", "kind": "belt", "x": 4, "y": 4, "facing": "east"},
		{"id": "s1", "kind": "seat", "x": 2, "y": 3, "facing": "south"},
		{"id": "s2", "kind": "seat", "x": 3, "y": 3, "facing": "south"},
		{"id": "s3", "kind": "seat", "x": 4, "y": 3, "facing": "south"},
	]}))
	var feet_clear := true
	var departed := 0
	var passing_save: Dictionary = {}
	var passing_snapshot: Dictionary = {}
	for tick in range(1800):
		var events: Array = game.advance(0.05)
		departed += _events(events, "departed").size()
		var scene: Dictionary = game.snapshot()
		feet_clear = feet_clear and _feet_are_clear(scene)
		for customer in scene.customers:
			if absf(float(customer.render_offset_x)) + absf(float(customer.render_offset_y)) > 0.05 and passing_save.is_empty():
				passing_save = _json_copy(game.save_data())
				passing_snapshot = scene
	_check(feet_clear, "passing keeps feet on valid floor or the visitor's own seat, away from other furniture")
	_check(departed >= 12 and game.snapshot().stats.sales >= 12, "nonblocking crossings keep repeated service productive")
	_check(not passing_save.is_empty(), "busy service exercises a real passing offset")
	if not passing_save.is_empty():
		var first := Session.new_session(1)
		var second := Session.new_session(2)
		_check(first.restore(passing_save) and second.restore(passing_save) and _same(first.snapshot(), passing_snapshot), "a passing visitor reopens at the saved route and offset")
		_check(_same(first.advance(20.0), second.advance(20.0)) and _same(first.snapshot(), second.snapshot()), "reopened passing continues with deterministic future sales and departures")

func _test_default_service_stays_healthy() -> void:
	var feet_clear := true
	var no_deadlock := true
	for seed_value in range(1, 9):
		var game := Session.new_session(seed_value)
		var departed := 0
		for tick in range(2400):
			departed += _events(game.advance(0.05), "departed").size()
			var scene: Dictionary = game.snapshot()
			feet_clear = feet_clear and _feet_are_clear(scene)
		no_deadlock = no_deadlock and departed >= 4 and game.snapshot().stats.sales >= 8
	_check(feet_clear, "all eight demo runs keep passing offsets within usable floor cells")
	_check(no_deadlock, "the actual two-menu demo keeps selling and releasing seats across eight seeded two-minute runs")

func _roundtrip(game: GameSession, description: String) -> void:
	var before: Dictionary = game.snapshot()
	var restored := Session.new_session(998)
	_check(restored.restore(_json_copy(game.save_data())) and _same(before, restored.snapshot()), description + " reopens without moving or resetting its visible clocks")
	var expected: Array = game.advance(12.0)
	var actual: Array = restored.advance(12.0)
	_check(_same(expected, actual) and _same(game.snapshot(), restored.snapshot()), description + " continues with the same rewards and no replay")

func _test_saved_visit_phases() -> void:
	for phase in ["pending", "satisfied"]:
		var game := Session.new_session(8, _base())
		_check(_wait(game, func(scene): return not _first(scene).is_empty() and _first(scene).preference_phase == phase), phase + " preference save fixture reaches its intended phase")
		_roundtrip(game, phase + " preference")
	var active := _expiry_game()
	_wait(active, func(scene): return not _first(scene).is_empty() and _first(scene).preference_phase == "active")
	active.advance(0.15)
	_roundtrip(active, "partly elapsed first preference")
	for target in ["expired", "restless", "stand-up", "leaving"]:
		var game := Session.new_session(11, _base({"recipes": {"salmon_nigiri": {"preparation_seconds": 1000.0}}}))
		_check(_wait(game, func(scene):
			var customer := _first(scene)
			return not customer.is_empty() and (customer.preference_phase == "expired" if target == "expired" else customer.restless and customer.phase == "waiting" if target == "restless" else customer.visual_phase == "stand-up" if target == "stand-up" else customer.phase == "leaving" and customer.visual_phase == "walk")
		), target + " save fixture reaches its intended phase")
		_roundtrip(game, target + " visit")
	var meal := Session.new_session(12, _base({"customers": {"fullness_min": 2.0, "fullness_max": 2.0}}))
	_wait(meal, func(scene): return scene.stats.sales == 1 and _first(scene).phase == "eating")
	meal.advance(0.2)
	_roundtrip(meal, "second partly eaten dish")

func _test_default_save_continuation() -> void:
	var restored_all := true
	var identical_all := true
	for seed_value in [1, 4, 11]:
		for elapsed in [9.117, 23.117, 48.117]:
			var game := Session.new_session(seed_value)
			game.advance(elapsed)
			var restored := Session.new_session(999)
			restored_all = restored_all and restored.restore(_json_copy(game.save_data())) and _same(game.snapshot(), restored.snapshot())
			var expected: Array = game.advance(30.0)
			var actual: Array = restored.advance(30.0)
			identical_all = identical_all and _same(expected, actual) and _same(game.snapshot(), restored.snapshot())
	_check(restored_all, "nine actual-demo save points preserve mixed visit phases and sampled eating durations exactly")
	_check(identical_all, "mixed seeded demo saves continue with identical dishes, reactions, sales and future visitor choices")

func _test_issue10_save_upgrade() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/legacy-0.2.0-session.json"))
	var game := Session.new_session(91)
	_check(fixture.source_commit == "d30f3cbe" and game.restore(fixture.save_data), "the actual merged #10 save upgrades into the new visit engine")
	var observed: Dictionary = game.snapshot()
	for key in ["mode", "editor", "inventory"]:
		observed.erase(key)
	for object in observed.objects:
		object.erase("active")
		object.erase("inactive_reason")
		# #13 adds explicit route descriptors; the legacy fixture predates them.
		for key in ["next_id", "input_facing", "incoming_id"]: object.erase(key)
	for index in range(observed.customers.size()):
		var previous: Dictionary = fixture.snapshot.customers[index]
		for key in observed.customers[index].keys():
			if not previous.has(key):
				observed.customers[index].erase(key)
	var expected: Dictionary = fixture.snapshot.duplicate(true)
	expected.floor.backdrop_rows = 3
	expected.floor.entrance = {"x": 4, "y": 3}
	for index in range(expected.customers.size()):
		if float(expected.customers[index].y) < 3:
			_check(float(observed.customers[index].y) >= 3, "A visitor crossing the retired doorway moves onto clear floor below the new backdrop")
			expected.customers[index].x = observed.customers[index].x
			expected.customers[index].y = observed.customers[index].y
	_check(_same(observed, expected), "backdrop migration preserves the old floor extent, camera, coins, furniture, dishes and every in-flight action clock")
	_check(game.save_data().random_state == fixture.save_data.random_state, "upgrade does not reroll old visitors or advance the random generator")
	game.command({"type": "set_entrance_open", "open": false})
	var events: Array = game.advance(60.0)
	var counts := {}
	for event in _events(events, "sale"):
		counts[event.customer_id] = int(counts.get(event.customer_id, 0)) + 1
	_check(counts.values().all(func(count): return count <= 1) and _events(events, "preference_matched").is_empty(), "existing #10 visitors finish their saved single-meal visits without a replayed preference or bonus plate")
	game.command({"type": "set_entrance_open", "open": true})
	_check(_wait(game, func(scene): return not scene.customers.is_empty() and _first(scene).preference_phase == "pending"), "new visitors after an old-save upgrade receive the current one-time preference cycle")

func _test_invalid_visit_saves() -> void:
	var game := Session.new_session(41, _base())
	game.advance(0.4)
	var valid := _json_copy(game.save_data())
	for field in ["preference_elapsed", "appetite_target", "meal_duration"]:
		var bad := _json_copy(valid)
		bad.state.customers[0][field] = -1.0
		_check(not game.restore(bad) and _same(game.save_data(), valid), "invalid " + field + " cannot replace a valid saved visit")
	var missing := _json_copy(valid)
	missing.state.customers[0].erase("first_dish_received")
	_check(not game.restore(missing), "a malformed current-format visit cannot masquerade as a legacy migration")
	var bad_offset := _json_copy(valid)
	bad_offset.state.customers[0].render_offset_x = INF
	_check(not game.restore(bad_offset), "nonfinite saved passing offsets cannot enter the live renderer")
	bad_offset = _json_copy(valid)
	bad_offset.state.customers[0].render_offset_y = 0.9
	_check(not game.restore(bad_offset), "saved passing offsets cannot exceed the safe within-cell range")
	var finished_timer := _json_copy(valid)
	finished_timer.state.customers[0].preference_phase = "active"
	finished_timer.state.customers[0].preference_elapsed = finished_timer.configuration.customers.preference_seconds
	_check(not game.restore(finished_timer), "a completed saved timer cannot masquerade as a still-active preference and replay its expiry")
	var duplicate_preference := _json_copy(valid)
	duplicate_preference.state.customers[0].first_dish_received = true
	duplicate_preference.state.customers[0].preference_phase = "active"
	_check(not game.restore(duplicate_preference), "a received first dish cannot restart its one-time preference cycle")
