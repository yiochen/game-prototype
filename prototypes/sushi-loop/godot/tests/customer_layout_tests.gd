extends SceneTree
## #14 exercises preservation and recovery through command/time/save only.
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_carry_and_reseat()
	_standing_placement()
	_rescue_and_guards()
	_trapped_standing_meal()
	_belt_clock()
	_migration_and_corruption()
	if failures.is_empty():
		print("PASS: %s customer layout and rescue checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		quit(1)

func check(value: bool, message: String) -> bool:
	checks += 1
	if not value: failures.append(message)
	return value

func same(a: Variant, b: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(a, "", true, true)) == JSON.parse_string(JSON.stringify(b, "", true, true))

func same_continuation(a: Dictionary, b: Dictionary) -> bool:
	# Match the existing wandering suite's 1 ns tolerance only for the raw
	# binary-float arrival countdown. Every visit/meal/navigation field is exact.
	if absf(float(a.state.arrival_remaining)-float(b.state.arrival_remaining)) > 0.000000001: return false
	a = a.duplicate(true)
	b = b.duplicate(true)
	a.state.erase("arrival_remaining")
	b.state.erase("arrival_remaining")
	return same(a,b)

func guest(game: GameSession) -> Dictionary:
	return game.save_data().state.customers[0] if not game.snapshot().customers.is_empty() else {}

func progress(customer: Dictionary) -> Dictionary:
	var result := {}
	for key in ["id", "appearance", "meal_dish", "meal_elapsed", "meal_duration", "meal_fullness", "first_dish_received", "preferred_recipe_id", "preference_phase", "preference_elapsed", "preference_phase_elapsed", "happy_elapsed", "waiting_elapsed", "fullness", "appetite_target", "restless"]:
		result[key] = customer[key]
	return result

func edit(game: GameSession) -> void:
	check(game.command({"type":"set_mode","mode":"edit"}).ok, "Edit pauses the scenario")

func reopen(game: GameSession) -> GameSession:
	var peer := Session.new()
	check(peer.restore(JSON.parse_string(JSON.stringify(game.save_data(), "", true, true))), "The exact current save validates after JSON encoding")
	check(same(peer.save_data(),game.save_data()), "Reopening preserves the exact visit, food, layout, RNG and clocks")
	return peer

func eating() -> GameSession:
	var game := Session.new_session(1414, {"service":{"first_arrival_seconds":0.1,"arrival_seconds":1000.0,"arrival_jitter_seconds":0.0,"eating_seconds":8.0},"customers":{"fullness_min":1.0,"fullness_max":1.0,"dish_fullness_min":1.0,"dish_fullness_max":1.0,"eating_jitter_seconds":0.0}})
	for index in range(600):
		game.advance(0.05)
		if not guest(game).is_empty() and guest(game).phase == "eating": break
	check(not guest(game).is_empty() and guest(game).phase == "eating", "A real visit naturally receives its first meal")
	game.advance(0.25)
	edit(game)
	return game

func reject(game: GameSession, request: Dictionary, reason := "") -> void:
	var before := game.save_data()
	var result := game.command(request)
	check(not result.ok and (reason.is_empty() or result.get("reason") == reason) and same(before,game.save_data()), "Rejected %s preserves every saved field (%s)" % [request.type,reason])

func _carry_and_reseat() -> void:
	var game := eating()
	var before := guest(game).duplicate(true)
	var random_state: String = game.save_data().random_state
	var coins: int = game.snapshot().coins
	var seat_id: String = before.seat_id
	check(game.command({"type":"editor_move","id":seat_id,"x":0,"y":10}).ok, "An occupied seat may move to a clear cell")
	check(guest(game).x == 0 and guest(game).y == 10 and same(progress(before),progress(guest(game))), "The same eating customer is carried with their exact unfinished meal and preference")
	check(guest(game).visual_elapsed == before.visual_elapsed and guest(game).visual_phase == before.visual_phase, "Carrying retains the exact animation frame")
	check(game.command({"type":"editor_rotate","id":seat_id}).ok and same(progress(before),progress(guest(game))), "Rotating an occupied seat preserves visit progress")
	reopen(game)
	check(game.command({"type":"editor_remove","id":seat_id}).ok, "Returning an occupied seat is accepted")
	check(guest(game).phase == "standing" and guest(game).seat_id == "" and guest(game).x == 0 and guest(game).y == 10 and same(progress(before),progress(guest(game))), "Seat removal leaves the customer at the seat's cell with the entire meal intact")
	check(guest(game).layout_pending and game.advance(100.0).is_empty(), "New reactions and all service clocks remain deferred in Edit")
	check(game.save_data().random_state == random_state and game.snapshot().coins == coins, "Editing consumes neither service RNG nor revenue")
	var peer := reopen(game)
	game.command({"type":"set_mode","mode":"live"})
	peer.command({"type":"set_mode","mode":"live"})
	var sales := 0
	var walked_with_meal := false
	var resumed := false
	var deterministic := true
	for index in range(700):
		var events := game.advance(0.05)
		deterministic = deterministic and same(events,peer.advance(0.05)) and same(game.save_data(),peer.save_data())
		sales += events.filter(func(event): return event.type == "sale").size()
		if not guest(game).is_empty():
			walked_with_meal = walked_with_meal or (guest(game).phase == "walking" and guest(game).meal_dish != null)
			resumed = resumed or guest(game).phase == "eating"
	check(walked_with_meal and resumed, "Live finds replacement seating and resumes the same carried meal")
	check(deterministic and sales == 1 and game.snapshot().stats.sales == 1 and game.snapshot().coins == coins+14, "Reopened recovery sells the unfinished dish exactly once with deterministic continuation")

func _standing_placement() -> void:
	var game := eating()
	var old := guest(game).duplicate(true)
	check(game.command({"type":"editor_remove","id":old.seat_id}).ok, "The placement fixture releases a seated guest")
	check(game.command({"type":"editor_place","inventory_id":"stool-plain","x":old.x,"y":old.y,"facing":"south"}).ok, "A suitable stool can be placed on a standing guest")
	check(guest(game).phase == "eating" and same(progress(old),progress(guest(game))), "Placement immediately seats the same customer and resumes the exact unfinished meal")
	reopen(game)
	game.command({"type":"editor_remove","id":guest(game).seat_id})
	var displaced := game.command({"type":"editor_place","inventory_id":"crate-wood","x":old.x,"y":old.y})
	check(displaced.ok and guest(game).phase == "standing" and same(progress(old),progress(guest(game))), "Another object visibly displaces the standing guest without changing their meal")
	check(Vector2(guest(game).x,guest(game).y).distance_to(Vector2(old.x,old.y)) == 1.0, "Displacement chooses a nearest empty cell")
	check(not game.snapshot().objects.any(func(object): return object.x == guest(game).x and object.y == guest(game).y), "A displaced customer never overlaps the new object")
	reopen(game)
	# Fill all floor except the entrance and the customer's cell in a custom
	# valid source configuration. No overlapping intermediate state is saved.
	var config := {"floor":{"columns":3,"rows":2,"world_columns":3,"viewport_columns":7,"entrance":{"x":0,"y":0}},"objects":[{"id":"chef","kind":"chef","x":0,"y":1,"facing":"east","recipe_id":"salmon_nigiri","art_id":"chef-lena"},{"id":"belt","kind":"belt","x":1,"y":1,"facing":"east"},{"id":"seat","kind":"seat","x":1,"y":0,"facing":"south"},{"id":"decor","kind":"decor","x":2,"y":0,"facing":"south","art_id":"crate-wood"},{"id":"decor2","kind":"decor","x":2,"y":1,"facing":"south","art_id":"crate-wood"}],"service":{"first_arrival_seconds":0.05,"arrival_seconds":1000.0,"arrival_jitter_seconds":0.0,"eating_seconds":8.0},"customers":{"eating_jitter_seconds":0.0}}
	var full := Session.new_session(1,config)
	for index in range(300):
		full.advance(0.05)
		if not guest(full).is_empty() and guest(full).phase == "eating": break
	edit(full)
	check(full.command({"type":"editor_remove","id":"seat"}).ok, "A guest can stand in the only nonentrance free cell")
	reject(full,{"type":"editor_place","inventory_id":"plant-angular","x":1,"y":0},"no_customer_space")
	reopen(full)

func _rescue_and_guards() -> void:
	var game := eating()
	var seated := guest(game).duplicate(true)
	game.command({"type":"editor_layer","layer":"people"})
	reject(game,{"type":"editor_select","id":seated.id},"seated_customer")
	game.command({"type":"editor_remove","id":seated.seat_id})
	var standing := guest(game).duplicate(true)
	game.command({"type":"editor_layer","layer":"people"})
	check(game.command({"type":"editor_select","id":standing.id}).ok, "People can select a standing guest")
	check(game.command({"type":"editor_move","id":standing.id,"x":0,"y":11}).ok and same(progress(standing),progress(guest(game))), "A direct rescue needs no route and preserves visit and meal progress")
	check(guest(game).layout_pending and game.snapshot().editor.selected_id == standing.id, "A floor rescue stays selected and defers reactions")
	reopen(game)
	reject(game,{"type":"editor_move","id":standing.id,"x":4,"y":3},"entrance")
	reject(game,{"type":"editor_move","id":standing.id,"x":-1,"y":3},"invalid_position")
	reject(game,{"type":"editor_move","id":standing.id,"x":1,"y":7},"occupied")
	reject(game,{"type":"editor_remove","id":standing.id},"seated_customer")
	reject(game,{"type":"editor_rotate","id":standing.id},"seated_customer")
	game.command({"type":"editor_layer","layer":"layout"})
	reject(game,{"type":"editor_move","id":standing.id,"x":0,"y":10},"people_required")
	game.command({"type":"editor_layer","layer":"people"})
	var free: Dictionary = game.snapshot().objects.filter(func(object): return object.kind == "seat")[0]
	check(game.command({"type":"editor_move","id":standing.id,"x":free.x,"y":free.y}).ok, "A standing customer can be rescued directly onto any free seat")
	check(guest(game).phase == "eating" and same(progress(standing),progress(guest(game))), "Direct reseating resumes the exact meal without a new visit or preference")
	reopen(game)

func _trapped_standing_meal() -> void:
	var objects: Array = [{"id":"chef","kind":"chef","art_id":"chef-lena","recipe_id":"salmon_nigiri","x":2,"y":6,"facing":"east"},{"id":"belt","kind":"belt","x":3,"y":6,"facing":"south"},{"id":"seat","kind":"seat","x":3,"y":5,"facing":"south"}]
	for x in range(7):
		if x != 3: objects.append({"id":"wall-%s" % x,"kind":"decor","art_id":"crate-wood","x":x,"y":3,"facing":"south"})
	var game := Session.new_session(1,{"floor":{"columns":7,"rows":7,"world_columns":21,"viewport_columns":7,"entrance":{"x":3,"y":0}},"objects":objects,"service":{"first_arrival_seconds":0.05,"arrival_seconds":1000.0,"arrival_jitter_seconds":0.0,"eating_seconds":8.0},"customers":{"eating_jitter_seconds":0.0}})
	for index in range(400):
		game.advance(0.05)
		if not guest(game).is_empty() and guest(game).phase == "eating": break
	if not check(not guest(game).is_empty() and guest(game).phase == "eating", "The trapped-standing fixture starts with a real unfinished meal"): return
	game.advance(0.25)
	edit(game)
	var before := guest(game).duplicate(true)
	game.command({"type":"editor_remove","id":"seat"})
	var wall := game.command({"type":"editor_place","inventory_id":"crate-wood","x":3,"y":3})
	check(wall.ok, "Layout can seal the only exit behind a seatless customer")
	game.command({"type":"set_mode","mode":"live"})
	game.advance(1.2)
	check(guest(game).phase == "standing" and guest(game).navigation_mode == "wander" and guest(game).meal_dish == before.meal_dish and guest(game).meal_elapsed == before.meal_elapsed, "A trapped standing guest wanders with their exact plate while eating stays frozen")
	var peer := reopen(game)
	var actual := game.advance(2.0)
	var expected := peer.advance(2.0)
	check(same(actual,expected) and same_continuation(game.save_data(),peer.save_data()), "Saved standing panic and wandering continue deterministically without a duplicate sale")
	edit(game)
	check(game.command({"type":"editor_remove","id":wall.id}).ok, "Removing the barrier restores the standing guest's exit access")
	game.command({"type":"set_mode","mode":"live"})
	game.advance(0.05)
	check(guest(game).navigation_mode == "goal" and guest(game).visual_phase == "stand" and guest(game).meal_dish == before.meal_dish and guest(game).meal_elapsed == before.meal_elapsed, "Restored access clears panic while retaining the unfinished visit and meal")

func _belt_clock() -> void:
	var game := Session.new_session(1)
	game.command({"type":"set_entrance_open","open":false})
	game.advance(4.55)
	edit(game)
	var tiles: Array = game.save_data().state.objects.filter(func(object): return object.kind == "belt" and object.dish != null and object.travel_elapsed > 0)
	if not check(not tiles.is_empty(), "The belt fixture has a partially transferred real dish"): return
	var tile: Dictionary = tiles[0].duplicate(true)
	check(game.command({"type":"editor_move","id":tile.id,"x":0,"y":10}).ok, "A loaded belt can move")
	var after: Dictionary = game.save_data().state.objects.filter(func(object): return object.id == tile.id)[0]
	check(after.dish == tile.dish and after.travel_elapsed == tile.travel_elapsed, "The moved tile carries its exact dish and frozen progress")
	reopen(game)
	game.command({"type":"set_mode","mode":"live"})
	game.advance(0.2)
	after = game.save_data().state.objects.filter(func(object): return object.id == tile.id)[0]
	check(after.dish == tile.dish and after.travel_elapsed == tile.travel_elapsed, "A disconnected loaded endpoint keeps its plate and clock when service resumes")
	edit(game)
	game.command({"type":"editor_select","id":tile.id})
	check(game.command({"type":"editor_belt_extend","x":1,"y":10}).ok, "The carried tile can reconnect to a new neighboring belt")
	after = game.save_data().state.objects.filter(func(object): return object.id == tile.id)[0]
	check(after.dish == tile.dish and after.travel_elapsed == tile.travel_elapsed, "Reconnection retains the carried dish's unfinished transfer clock")
	reopen(game)

func _migration_and_corruption() -> void:
	var game := eating()
	var old := game.save_data()
	old.erase("customer_layout_version")
	for customer in old.state.customers:
		customer.erase("layout_pending")
		customer.erase("standing_elapsed")
	var migrated := Session.new()
	check(migrated.restore(old) and same(progress(guest(migrated)),progress(guest(game))), "Earlier shipped saves acquire neutral layout fields without replaying a visit")
	var corrupt := game.save_data()
	corrupt.state.customers[0].layout_pending = "yes"
	var peer := Session.new()
	check(not peer.restore(corrupt), "Malformed reaction state is rejected")
	corrupt = game.save_data()
	corrupt.customer_layout_version = 999
	check(not peer.restore(corrupt), "Unknown future customer-layout versions are rejected")
