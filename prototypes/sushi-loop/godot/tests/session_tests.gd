extends SceneTree
## Run: godot --headless --path prototypes/sushi-loop/godot --script tests/session_tests.gd
## Scenarios use only GameSession's public commands, elapsed time and save API.

const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_test_starter()
	_test_autonomous_service()
	_test_completed_meal_price()
	_test_full_belt_and_resume()
	_test_timing_and_seed()
	_test_save_during_walk()
	_test_save_during_meal()
	_test_save_held_and_belt_food()
	_test_camera_and_public_copies()
	_test_invalid_input_and_save()
	if failures.is_empty():
		print("PASS: %s GameSession checks" % checks)
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		printerr("%s of %s GameSession checks failed" % [failures.size(), checks])
		quit(1)

func _check(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures.append(description)

func _objects(snapshot: Dictionary, kind: String) -> Array:
	return snapshot.objects.filter(func(item): return item.kind == kind)

func _object(snapshot: Dictionary, object_id: String) -> Dictionary:
	for item in snapshot.objects:
		if item.id == object_id:
			return item
	return {}

func _events(events: Array, kind: String) -> Array:
	return events.filter(func(event): return event.type == kind)

func _customer(snapshot: Dictionary, phase: String) -> Dictionary:
	for customer in snapshot.customers:
		if customer.phase == phase:
			return customer
	return {}

func _advance_until(session: RefCounted, condition: Callable, limit: float = 60.0) -> bool:
	var elapsed := 0.0
	while elapsed < limit:
		if condition.call(session.snapshot()):
			return true
		session.advance(0.05)
		elapsed += 0.05
	return condition.call(session.snapshot())

func _json_copy(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value, "", true, true))

func _same(left: Variant, right: Variant) -> bool:
	# Comparing parsed JSON also exercises the persistence-compatible public data
	# without treating a JSON number's int/float representation as a difference.
	return JSON.parse_string(JSON.stringify(left, "", true, true)) == JSON.parse_string(JSON.stringify(right, "", true, true))

func _single_visit_config() -> Dictionary:
	return {"service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0}}

func _test_starter() -> void:
	var game := Session.new_session(17)
	var scene: Dictionary = game.snapshot()
	_check(scene.floor.columns == 9 and scene.floor.rows == 16 and scene.floor.world_columns == 27, "starter exposes a rectangular workable floor inside the future wider world")
	_check(_objects(scene, "chef").size() == 1 and _objects(scene, "seat").size() == 3, "starter has one chef and three seats")
	_check(_objects(scene, "belt").size() == 4, "starter uses a short four-cell belt")
	var occupied := {}
	var distinct := true
	var adjacent := true
	var offsets := {"north": Vector2i(0, -1), "east": Vector2i(1, 0), "south": Vector2i(0, 1), "west": Vector2i(-1, 0)}
	for object in scene.objects:
		var cell := Vector2i(object.x, object.y)
		distinct = distinct and not occupied.has(cell)
		occupied[cell] = object.kind
	for object in scene.objects:
		if object.kind in ["chef", "seat"]:
			adjacent = adjacent and occupied.get(Vector2i(object.x, object.y) + offsets[object.facing]) == "belt"
	_check(distinct and adjacent, "every assigned object occupies one cell and chef/seats each face one adjacent belt tile")
	_check(_object(scene, "chef-1").recipe_id == "salmon_nigiri" and scene.recipes.salmon_nigiri.price == 14, "starter chef knows the content-defined salmon recipe")
	game.advance(1.0)
	_check(_object(game.snapshot(), "chef-1").preparation > 0.0, "chef prepares without an action from the player")

func _test_autonomous_service() -> void:
	var game := Session.new_session(42)
	var initial_coins: int = game.snapshot().coins
	var events: Array = game.advance(180.0)
	var scene: Dictionary = game.snapshot()
	var sales := _events(events, "sale")
	_check(sales.size() >= 20, "starter service remains productive through sustained autonomous play")
	_check(not _events(events, "arrived").is_empty() and not _events(events, "departed").is_empty(), "customers enter, find seats, finish and leave")
	var served_seats := {}
	var dishes_sold := {}
	var unique_sales := true
	for event in sales:
		served_seats[event.seat_id] = true
		unique_sales = unique_sales and not dishes_sold.has(event.dish_id)
		dishes_sold[event.dish_id] = true
	_check(served_seats.size() == 3, "all three starter seats are reachable and can receive food")
	_check(unique_sales, "each consumed dish emits exactly one sale")
	_check(scene.coins == initial_coins + sales.size() * 14 and scene.stats.sales == sales.size(), "balance changes only by fixed recipe prices, with no turnover bonus or operating fee")
	_check(sales.all(func(event): return event.has("x") and event.has("y") and event.has("customer_id")), "sale events provide the local position needed for a coin pop")

func _test_completed_meal_price() -> void:
	var config := _single_visit_config()
	config["recipes"] = {"salmon_nigiri": {"price": 23}}
	var game := Session.new_session(3, config)
	var initial: int = game.snapshot().coins
	_check(_advance_until(game, func(scene): return not _customer(scene, "eating").is_empty()), "a single visitor reaches a seat and takes a dish")
	_check(game.snapshot().coins == initial, "taking a plate does not pay before eating finishes")
	var interim: Array = game.advance(3.0)
	_check(game.snapshot().coins == initial and _events(interim, "sale").is_empty(), "a partially eaten meal gives no partial or early payment")
	var events: Array = game.advance(3.0)
	_check(_events(events, "sale").size() == 1 and game.snapshot().coins == initial + 23, "eating completion credits the separate content price exactly once")
	game.advance(30.0)
	_check(game.snapshot().coins == initial + 23 and game.snapshot().stats.served == 1, "departure and continued cooking add no extra payment")

func _test_full_belt_and_resume() -> void:
	var game := Session.new_session(29)
	_check(game.command({"type": "set_entrance_open", "open": false}).ok, "public environmental command closes arrivals")
	game.advance(7.0)
	var endpoint: Dictionary = _object(game.snapshot(), "belt-4")
	_check(endpoint.dish != null, "a dish reaches the open endpoint")
	var endpoint_dish: String = endpoint.dish.id if endpoint.dish != null else "missing"
	game.advance(90.0)
	var blocked: Dictionary = game.snapshot()
	_check(_object(blocked, "belt-4").dish.id == endpoint_dish, "open endpoint retains the same dish indefinitely without disposal")
	_check(_objects(blocked, "belt").all(func(tile): return tile.dish != null), "waiting food creates visible local backpressure across the four tiles")
	var chef: Dictionary = _object(blocked, "chef-1")
	_check(chef.held_dish != null and chef.preparation == 1.0, "blocked chef holds one finished dish")
	var held_id: String = chef.held_dish.id if chef.held_dish != null else "missing"
	var waiting: Array = game.advance(60.0)
	_check(_object(game.snapshot(), "chef-1").held_dish.id == held_id and _events(waiting, "prepared").is_empty(), "chef never stockpiles or replaces held food while loading remains blocked")
	_check(game.snapshot().coins == blocked.coins, "belt congestion never drains existing coins")
	game.command({"type": "set_entrance_open", "open": true})
	var resumed: Array = game.advance(35.0)
	_check(not _events(resumed, "sale").is_empty() and not _events(resumed, "loaded").is_empty(), "new customers can take stopped dishes and release backpressure")
	_check(_events(resumed, "loaded").any(func(event): return event.dish_id == held_id), "chef loads the previously held dish after space opens")

func _test_timing_and_seed() -> void:
	var continuous := Session.new_session(771)
	var fragmented := Session.new_session(771)
	var single_events: Array = continuous.advance(51.017)
	var many_events: Array = []
	for index in range(3001):
		many_events.append_array(fragmented.advance(0.017))
	_check(_same(continuous.snapshot(), fragmented.snapshot()), "simulation outcome is independent of frame-time partitioning")
	_check(_same(single_events, many_events), "seeded customer choices and observable events are frame-rate independent")
	var other_seed := Session.new_session(772)
	other_seed.advance(51.017)
	_check(not _same(continuous.snapshot().customers, other_seed.snapshot().customers), "injected seed controls visitor variation")

func _test_save_during_walk() -> void:
	var original := Session.new_session(81)
	original.advance(2.017)
	_check(not _customer(original.snapshot(), "walking").is_empty(), "walk-save scenario captures a visitor between the entrance and their seat")
	var saved := _json_copy(original.save_data())
	var restored := Session.new_session(999)
	_check(restored.restore(saved), "JSON save made while walking restores successfully")
	_check(_same(original.snapshot(), restored.snapshot()), "restore preserves positions, preparation, layout, coins and elapsed time immediately")
	var expected: Array = original.advance(90.0)
	var actual: Array = restored.advance(90.0)
	_check(_same(expected, actual) and _same(original.snapshot(), restored.snapshot()), "saved path, fractional clock and random state continue identically after reopening")

func _test_save_during_meal() -> void:
	var original := Session.new_session(46, _single_visit_config())
	_advance_until(original, func(scene): return not _customer(scene, "eating").is_empty())
	original.advance(2.017)
	var before: Dictionary = original.snapshot()
	var meal := _customer(before, "eating")
	_check(not meal.is_empty() and meal.meal_progress > 0.0 and meal.meal_progress < 1.0, "meal-save scenario contains a partly eaten dish")
	var saved := _json_copy(original.save_data())
	var restored := Session.new_session(1)
	_check(restored.restore(saved) and _same(before, restored.snapshot()), "mid-meal restoration preserves the actual dish and eating progress")
	var repeat_ok := true
	for repeat in range(5):
		repeat_ok = repeat_ok and restored.restore(saved) and restored.snapshot().coins == before.coins
	_check(repeat_ok and restored.advance(0.0).is_empty(), "repeated restoration and zero elapsed time cannot replay a sale or grant offline income")
	var future: Array = restored.advance(20.0)
	_check(_events(future, "sale").size() == 1 and restored.snapshot().coins == before.coins + 14, "restored in-progress meal pays once on its eventual completion")
	var completed_save := _json_copy(restored.save_data())
	var completed: Dictionary = restored.snapshot()
	for repeat in range(5):
		restored.restore(completed_save)
	var later: Array = restored.advance(40.0)
	_check(_events(later, "sale").is_empty() and restored.snapshot().coins == completed.coins, "restoring a completed sale cannot credit it again")

func _test_save_held_and_belt_food() -> void:
	var original := Session.new_session(109)
	original.command({"type": "set_entrance_open", "open": false})
	original.advance(40.017)
	var saved := _json_copy(original.save_data())
	var restored := Session.new_session(1)
	_check(restored.restore(saved) and _same(original.snapshot(), restored.snapshot()), "full belt and the chef's held plate survive a JSON save round trip")
	var original_snapshot: Dictionary = original.snapshot()
	var food_ids: Array = []
	for tile in _objects(original_snapshot, "belt"):
		food_ids.append(tile.dish.id)
	food_ids.append(_object(original_snapshot, "chef-1").held_dish.id)
	original.command({"type": "set_entrance_open", "open": true})
	restored.command({"type": "set_entrance_open", "open": true})
	var expected: Array = original.advance(90.0)
	var actual: Array = restored.advance(90.0)
	_check(_same(expected, actual) and _same(original.snapshot(), restored.snapshot()), "reopened congestion clears identically, preserving dish identities and future arrivals")
	var sold_ids: Array = _events(actual, "sale").map(func(event): return event.dish_id)
	_check(food_ids.all(func(dish_id): return sold_ids.has(dish_id)), "all four saved belt plates and the held plate can eventually be eaten")

func _test_camera_and_public_copies() -> void:
	var game := Session.new_session(88)
	game.advance(5.0)
	_check(game.command({"type": "set_camera", "x": -2.5, "y": 0.75}).ok, "camera changes are accepted at the public session boundary")
	var saved := _json_copy(game.save_data())
	var reopened := Session.new_session(1)
	reopened.restore(saved)
	_check(reopened.snapshot().camera == {"x": -2.5, "y": 0.75}, "saved restaurant reopens at the same camera position")
	var visible: Dictionary = game.snapshot()
	visible.coins = 999999
	visible.objects[0].x = 100
	_check(game.snapshot().coins != visible.coins and game.snapshot().objects[0].x != 100, "observable snapshots cannot mutate the running session")
	saved.state.coins = 0
	_check(game.snapshot().coins != 0 and reopened.snapshot().coins != 0, "save payload and restored state have independent ownership")

func _test_invalid_input_and_save() -> void:
	var game := Session.new_session(12)
	game.advance(10.0)
	var before: Dictionary = game.snapshot()
	_check(not game.command({"type": "grant_coins", "amount": 999}).ok, "unknown commands cannot bypass game rules")
	_check(not game.command({"type": "set_camera", "x": INF, "y": 0}).ok, "nonfinite camera input is rejected")
	_check(not game.command({"type": "set_entrance_open", "open": "yes"}).ok, "entrance command validates its value")
	_check(game.advance(-5.0).is_empty() and game.advance(NAN).is_empty() and _same(before, game.snapshot()), "invalid elapsed time and rejected commands leave service unchanged")
	_check(not game.restore({"version": 999}) and _same(before, game.snapshot()), "unsupported or incomplete saves do not replace a valid session")
	var invalid := _json_copy(game.save_data())
	invalid.state.objects[0].x = invalid.state.objects[1].x
	invalid.state.objects[0].y = invalid.state.objects[1].y
	_check(not game.restore(invalid) and _same(before, game.snapshot()), "a malformed save with overlapping floor objects is rejected atomically")
