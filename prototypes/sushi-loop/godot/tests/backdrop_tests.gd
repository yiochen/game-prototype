extends SceneTree
const Session = preload("res://scripts/session.gd")
const World = preload("res://scripts/restaurant_view.gd")
var failures: Array[String] = []
var checks := 0
func _init() -> void:
	call_deferred("run")
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)
func same(a: Variant, b: Variant) -> bool:
	return JSON.stringify(JSON.parse_string(JSON.stringify(a)), "", true) == JSON.stringify(JSON.parse_string(JSON.stringify(b)), "", true)
func run() -> void:
	var game = Session.new_session(41)
	var snapshot: Dictionary = game.snapshot()
	check(snapshot.floor.backdrop_rows == 3 and snapshot.floor.entrance.x == 4 and snapshot.floor.entrance.y == 3, "Backdrop reserves three rows; guests enter the two-tile opening in columns four and five")
	game.command({"type":"set_mode","mode":"edit"})
	var before: Dictionary = game.save_data()
	for y in range(3):
		var response: Dictionary = game.command({"type":"editor_move","id":"chef-1","x":0,"y":y})
		check(not response.ok and response.reason == "invalid_position" and same(before,game.save_data()), "Reserved backdrop rows reject object placement atomically")
	var world = World.new()
	world.size = Vector2(720,1280)
	root.add_child(world)
	world.state = snapshot
	world.update_layout()
	var pieces: Array = world.backdrop_plan()
	check(pieces.size() == 18, "Twenty-one columns contain seventeen blank modules and one four-tile gate")
	check(pieces.slice(0,3).all(func(piece): return piece.key == "backdrop-wall"), "Three blank modules precede the entrance")
	check(pieces[3].key == "backdrop-entrance" and pieces[3].x == 3 and pieces[3].width == 4, "The gate occupies columns three through six")
	check(pieces[4].x == 7 and pieces[-1].x == 20 and pieces.slice(4).all(func(piece): return piece.key == "backdrop-wall"), "All remaining world columns use the blank wall")
	check(not world.art.objects.has("entry-finished"), "Old entrance is absent from runtime catalog")
	for piece in pieces:
		var box: Rect2 = world.art.registered_rect(piece.key,piece.base,world.cell)
		var content := Rect2(box.position + Vector2.ONE * 32 * world.cell / 128, Vector2(piece.width,3)*world.cell)
		check(content.position.is_equal_approx(world.floor_origin+Vector2(piece.x,0)*world.cell), "Authored padded frames align to exact tile edges")
	world.state.camera = {"x":9.0,"y":1.0}
	var shifted: Array = world.backdrop_plan()
	check(shifted[3].base.is_equal_approx(pieces[3].base-Vector2(9,1)*world.cell), "Backdrop follows both camera axes with no stretching")
	world.queue_free()
	var legacy: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://tests/fixtures/legacy-0.2.0-session.json")).save_data
	var restored = Session.new_session(9)
	check(restored.restore(legacy), "An existing active restaurant can adopt the new backdrop")
	var upgraded: Dictionary = restored.save_data()
	check(upgraded.configuration.floor.backdrop_rows == 3 and upgraded.configuration.floor.entrance == {"x":4,"y":3}, "Legacy arrival cell moves into the approved doorway")
	check(upgraded.state.coins == legacy.state.coins and same(upgraded.state.stats,legacy.state.stats) and upgraded.random_state == legacy.random_state, "Migration neither grants rewards nor advances random state")
	for old in legacy.state.customers:
		var customer: Dictionary = upgraded.state.customers.filter(func(c): return c.id == old.id)[0]
		check(customer.phase == old.phase and customer.meal_elapsed == old.meal_elapsed, "Existing visits and meal clocks survive")
		check(customer.y >= 3, "Existing visitors remain below the backdrop")
	var reopened = Session.new_session(8)
	var reopened_ok: bool = reopened.restore(JSON.parse_string(JSON.stringify(upgraded)))
	check(reopened_ok and same(reopened.save_data(),upgraded), "Upgraded saves validate and reopen idempotently")
	var crowded: Dictionary = game.save_data()
	crowded.erase("expansion_version");crowded.state.erase("expansion")
	crowded.configuration.floor.erase("backdrop_rows")
	crowded.configuration.floor.entrance = {"x":3,"y":2}
	crowded.configuration.content_version = 2
	crowded.configuration.objects[0].y = 1
	crowded.state.objects[0].y = 1
	var old_rows: int = crowded.configuration.floor.rows
	var moved = Session.new_session(1)
	check(moved.restore(crowded), "An old edited layout using the reserved rows is retained")
	var migrated: Dictionary = moved.save_data()
	check(migrated.configuration.floor.rows == old_rows+3 and migrated.state.objects[0].y == 4, "Occupied old top rows shift the whole connected layout and extend the floor")
	var verify = Session.new_session(2)
	check(verify.restore(JSON.parse_string(JSON.stringify(migrated))), "Relocated furniture, inventory and navigation remain valid saves")
	var compatible := true
	for seed_value in [1,41,118]:
		var old_game = Session.new_session(seed_value,{"content_version":2,"floor":{"backdrop_rows":0,"entrance":{"x":3,"y":2}}})
		for moment in [0.0,0.8,0.85,1.0,2.0,4.0,7.0,10.0,15.0,30.0,60.0]:
			old_game.advance(moment-float(old_game.snapshot().elapsed))
			var saved: Dictionary = JSON.parse_string(JSON.stringify(old_game.save_data()))
			saved.configuration.floor.erase("backdrop_rows")
			var adopted = Session.new_session(9)
			compatible = compatible and adopted.restore(saved)
			var again = Session.new_session(10)
			compatible = compatible and again.restore(JSON.parse_string(JSON.stringify(adopted.save_data())))
			compatible = compatible and adopted.snapshot().coins == old_game.snapshot().coins and same(adopted.snapshot().stats,old_game.snapshot().stats)
	check(compatible,"Thirty-three seeded legacy save points retain valid visits, economy and reopenable routes")
	# Real room dimensions: the 0.4.8 save can be Live yet still waiting for
	# its first step to turn a blocked-seat wander into an exit route.
	var exit_game = Session.new_session(41,{"content_version":2,"floor":{"backdrop_rows":0,"entrance":{"x":3,"y":2}}})
	exit_game.advance(0.85)
	exit_game.command({"type":"set_mode","mode":"edit"})
	var visitor: Dictionary = exit_game.snapshot().customers[0]
	var seat: Dictionary = exit_game.snapshot().objects.filter(func(o): return o.id == visitor.seat_id)[0]
	for delta in [Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP,Vector2i.DOWN]:
		var point: Vector2i = Vector2i(int(seat.x),int(seat.y))+delta
		if exit_game.snapshot().objects.any(func(o): return int(o.x)==point.x and int(o.y)==point.y): continue
		var stock: Dictionary = exit_game.snapshot().inventory.filter(func(item): return item.kind == "decor" and item.count > 0)[0]
		check(exit_game.command({"type":"editor_place","inventory_id":stock.id,"x":point.x,"y":point.y}).ok,"Old review fixture can block its assigned seat")
	exit_game.command({"type":"set_mode","mode":"live"})
	var old_exit: Dictionary = JSON.parse_string(JSON.stringify(exit_game.save_data()))
	old_exit.configuration.floor.erase("backdrop_rows")
	var upgraded_exit = Session.new_session(4)
	check(upgraded_exit.restore(old_exit),"A blocked-seat 0.4.8 room adopts the new backdrop")
	check(upgraded_exit.snapshot().customers[0].phase == "walking","Restore keeps the existing visit phase until Live advances")
	upgraded_exit.advance(0.05)
	check(upgraded_exit.snapshot().customers[0].phase == "leaving","First Live step retains the released reachable-exit recovery")
	await process_frame
	if failures.is_empty():
		print("PASS: %s backdrop checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: "+failure)
		quit(1)
