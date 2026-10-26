extends SceneTree
const Session = preload("res://scripts/session.gd")
const View = preload("res://scripts/restaurant_view.gd")
const Curtain = preload("res://scripts/entrance_curtain.gd")
const Doorway = preload("res://scripts/doorway.gd")
var checks := 0
var failures: Array[String] = []

func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)

func decoded(value: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(value))

func same(a: Variant, b: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(a, "", true, true)) == JSON.parse_string(JSON.stringify(b, "", true, true))

func same_continuation(a: Dictionary, b: Dictionary) -> bool:
	# JSON may round the legacy arrival countdown by one ULP. Visits, portal
	# positions, RNG, meal clocks and public events must remain exactly equal.
	if absf(float(a.state.arrival_remaining) - float(b.state.arrival_remaining)) > 0.000000001: return false
	a = a.duplicate(true)
	b = b.duplicate(true)
	a.state.erase("arrival_remaining")
	b.state.erase("arrival_remaining")
	return same(a, b)

func _initialize() -> void:
	call_deferred("run")

func reach_exit_motion(game: GameSession) -> bool:
	for index in range(80):
		var guests: Array = game.save_data().state.customers
		if not guests.is_empty() and guests[0].get("door_motion", {}).get("direction") == "exit": return true
		game.advance(0.05)
	return false

func _test_random_width() -> void:
	var entry_samples := []
	var exit_samples := []
	var any_fractional := false
	var distinct_directions := false
	var all_valid := true
	var legacy := true
	for seed_value in range(1, 33):
		var game = Session.new_session(seed_value, {"objects": [], "service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0}})
		game.advance(0.1)
		var saved: Dictionary = decoded(game.save_data())
		var entry: Dictionary = saved.state.customers[0].door_motion
		entry_samples.append(float(entry.offset_x))
		any_fractional = any_fractional or (float(entry.offset_x) > 0.1 and float(entry.offset_x) < 0.9)
		# Existing in-progress APK saves have no offset: preserve their exact path.
		var old := saved.duplicate(true)
		old.state.customers[0].door_motion.erase("offset_x")
		old.state.customers[0].erase("door_lane")
		old.state.customers[0].x = 4.0
		old.state.customers[0].path_origin.x = 4.0
		var peer = Session.new_session(9)
		legacy = legacy and peer.restore(old) and peer.snapshot().customers[0].x == 4.0
		game.advance(4.5)
		if not reach_exit_motion(game):
			check(false, "The unseated visitor reaches a doorway exit")
			return
		saved = decoded(game.save_data())
		var outward: Dictionary = saved.state.customers[0].door_motion
		exit_samples.append(float(outward.offset_x))
		distinct_directions = distinct_directions or not is_equal_approx(float(entry.offset_x), float(outward.offset_x))
		all_valid = all_valid and peer.restore(saved)
		for invalid_offset in [-0.01, 1.01, "right", null]:
			var bad := saved.duplicate(true)
			bad.state.customers[0].door_motion.offset_x = invalid_offset
			all_valid = all_valid and not peer.restore(bad)
	check(entry_samples.min() < 0.15 and entry_samples.max() > 0.85, "Arrivals span both tiles of the doorway")
	check(exit_samples.min() < 0.15 and exit_samples.max() > 0.85, "Departures independently span both tiles of the doorway")
	check(any_fractional and distinct_directions, "Door crossings use continuous random positions and resample the departure")
	check(all_valid and legacy, "Random positions validate strictly and old in-progress crossings remain compatible")
	var guest := {"x": 4.0, "y": 3.0, "door_motion": {"direction": "enter", "distance": 0.0, "offset_x": 1.0}}
	var previous := Vector2(5.0, 3.0 - Doorway.TRAVEL)
	var continuous := true
	for index in range(1, 101):
		guest.door_motion.distance = Doorway.TRAVEL * index / 100.0
		var visible := {}
		Doorway.present(visible, guest, 2.5)
		var position := Vector2(visible.x, visible.y)
		continuous = continuous and position.x >= 4.0 and position.x <= 5.0 and position.distance_to(previous) < 0.03
		previous = position
	check(continuous and previous.is_equal_approx(Vector2(4, 3)), "Even the far-right crossing joins the indoor route continuously without a jump")
	var stream = RandomNumberGenerator.new()
	stream.seed = 17
	var original_state: int = stream.state
	Doorway.motion("enter", "customer-1", stream.state)
	check(stream.state == original_state, "Doorway variety never changes the service RNG stream")

func run() -> void:
	_test_random_width()
	var game = Session.new_session(41, {"service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0}})
	game.advance(0.1)
	var arrival: Dictionary = game.snapshot().customers[0]
	check(arrival.y < 2.04 and arrival.door_alpha == 0.0 and arrival.visual_phase == "walk" and arrival.facing == "south", "Arrival begins invisible in the dark with southbound walking pose")
	game.advance(0.15)
	var emerging: Dictionary = game.snapshot().customers[0]
	check(emerging.y > arrival.y and emerging.y < 3.0 and emerging.door_alpha > 0.0, "The feet move continuously out of the darkness")
	game.command({"type": "set_mode", "mode": "edit"})
	var frozen: Dictionary = decoded(game.save_data())
	game.advance(100.0)
	check(same(frozen, decoded(game.save_data())), "Edit freezes the entire entrance traversal")
	var peer = Session.new_session(7)
	check(peer.restore(frozen) and same(frozen, decoded(peer.save_data())), "An in-progress arrival reopens exactly")
	game.command({"type": "set_mode", "mode": "live"})
	peer.command({"type": "set_mode", "mode": "live"})
	var deterministic := true
	var valid := true
	var saw_exit := false
	var exit_frames := 0
	var departures := 0
	var previous_exit_y := 3.0
	for step in range(2200):
		var events: Array = game.advance(0.05)
		deterministic = deterministic and same(events, peer.advance(0.05)) and same_continuation(decoded(game.save_data()), decoded(peer.save_data()))
		departures += events.filter(func(event): return event.type == "departed").size()
		var saved: Dictionary = decoded(game.save_data())
		var restored = Session.new_session(9)
		valid = valid and restored.restore(saved) and same(saved, decoded(restored.save_data()))
		var guests: Array = game.snapshot().customers
		if not guests.is_empty() and saved.state.customers[0].get("door_motion", {}).get("direction") == "exit":
			saw_exit = true
			exit_frames += 1
			check(guests[0].y <= previous_exit_y and guests[0].facing == "north" and guests[0].visual_phase == "walk", "Departing guest walks north into darkness before removal")
			previous_exit_y = guests[0].y
		if departures > 0: break
	check(valid, "Every arrival, service, departure and darkness save point reopens exactly")
	check(deterministic, "Save continuation preserves identical events and state")
	check(saw_exit and exit_frames > 4 and departures == 1 and game.snapshot().customers.is_empty(), "A served visit completes one visible doorway traversal and one departure")
	check(game.snapshot().stats.sales > 0, "The full visit still pays for actual meals")
	var empty = Session.new_session(42, {"objects": [], "service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0, "arrival_jitter_seconds": 0.0}})
	empty.advance(0.6)
	check(empty.snapshot().customers[0].phase == "entrance_wait" and empty.snapshot().customers[0].entrance_wait_elapsed < 0.1, "The four-second no-seat wait starts after walking inside")
	empty.advance(4.0)
	check(reach_exit_motion(empty), "The unseated visitor walks to its selected exit lane")
	var leaving: Dictionary = decoded(empty.save_data())
	check(leaving.state.customers[0].departure_reason == "no_seat" and leaving.state.customers[0].door_motion.direction == "exit", "An unseated visitor walks back out after the full admission wait")
	check(peer.restore(leaving), "No-seat doorway departures are valid saved visits")
	empty.command({"type": "set_mode", "mode": "edit"})
	var exit_frozen: Dictionary = decoded(empty.save_data())
	empty.advance(10.0)
	check(same(exit_frozen, decoded(empty.save_data())), "Edit also freezes the outward traversal")
	empty.command({"type": "set_mode", "mode": "live"})
	var no_seat_events: Array = empty.advance(1.0)
	check(empty.snapshot().customers.is_empty() and no_seat_events.filter(func(event): return event.type == "departed" and event.reason == "no_seat").size() == 1 and empty.snapshot().coins == 120, "The no-seat exit emits one departure without money")
	for bad in [{"direction": "sideways", "distance": 0.2}, {"direction": "exit", "distance": -1.0}, {"direction": "exit", "distance": 1.15}, null]:
		var invalid := leaving.duplicate(true)
		invalid.state.customers[0].door_motion = bad
		check(not peer.restore(invalid), "Malformed doorway motion is rejected atomically")
	var world = View.new()
	world.size = Vector2(450,800)
	root.add_child(world)
	world.state = game.snapshot()
	world.update_layout()
	var foot_y := 3.0 + Doorway.CURTAIN_OFFSET
	for offset in [-0.02, 0.02]:
		world.state.customers = [{"id": "probe", "y": foot_y, "render_offset_y": offset}]
		var plan: Array = world.render_plan()
		var guest_index := -1
		var curtain_index := -1
		for index in range(plan.size()):
			if plan[index].kind == "customer": guest_index = index
			if plan[index].kind == "curtain": curtain_index = index
		check((guest_index < curtain_index) == (offset < 0.0), "Curtain order uses the actual foot root including render offsets")
	var gate_rect: Rect2 = world.art.registered_rect("backdrop-entrance", world.cell_base(4.5, 2.5), world.cell)
	var source_scale := gate_rect.size / Vector2(1728, 1344)
	var cloth := gate_rect.position + Vector2(610, 660) * source_scale
	var seam := gate_rect.position + Vector2(737, 660) * source_scale
	check(Curtain.covers(world, cloth, world.cell_base(4.5, 2.5)) and not Curtain.covers(world, seam, world.cell_base(4.5, 2.5)), "The curtain clips its actual cloth while leaving its seams open")
	world.state.customers[0].render_offset_y = -0.02
	check(world._curtain_hides_hit({"owner_id": "probe"}, cloth), "Hidden parts of a guest behind the curtain cannot be picked through the cloth")
	world.state.customers[0].render_offset_y = 0.02
	check(not world._curtain_hides_hit({"owner_id": "probe"}, cloth), "A guest in front remains pickable over the same curtain pixels")
	world.queue_free()
	var rescued = Session.new_session(43, {"objects": [], "service": {"first_arrival_seconds": 0.1, "arrival_seconds": 1000.0}})
	rescued.advance(0.25)
	rescued.command({"type": "set_mode", "mode": "edit"})
	var identity: String = rescued.snapshot().customers[0].id
	check(rescued.command({"type": "editor_pickup", "id": identity}).ok and rescued.command({"type": "editor_move", "id": identity, "x": 3, "y": 5}).ok, "A guest crossing the doorway retains the existing People rescue behavior")
	check(not rescued.save_data().state.customers[0].has("door_motion") and peer.restore(decoded(rescued.save_data())), "A deliberate rescue cancels doorway movement and saves the dropped visit")
	if failures.is_empty():
		print("PASS: %s doorway checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		quit(1)
