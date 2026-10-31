extends SceneTree
## #12 exercises accepted/rejected edits and persisted continuation only through
## GameSession's public command, time, snapshot and save boundaries.
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	_pause_and_resume()
	_layers_and_selection()
	_moves_rotation_and_stock()
	_loaded_belt_ownership()
	_unassigned_chef_continuation()
	_customer_protection()
	_persistence_and_migration()
	_four_slot_page_migration()
	_invalid_commands_and_saves()
	if failures.is_empty():
		print("PASS: %s restaurant editor checks" % checks)
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		quit(1)

func _check(value: bool, description: String) -> void:
	checks += 1
	if not value:
		failures.append(description)

func _same(left: Variant, right: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(left, "", true, true)) == JSON.parse_string(JSON.stringify(right, "", true, true))

func _json(data: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(data, "", true, true))

func _object(scene: Dictionary, identity: String) -> Dictionary:
	for object in scene.objects:
		if object.id == identity:
			return object
	return {}

func _stock(scene: Dictionary, identity: String) -> Dictionary:
	for entry in scene.inventory:
		if entry.id == identity:
			return entry
	return {}

func _edit(game: GameSession) -> void:
	_check(game.command({"type": "set_mode", "mode": "edit"}).ok, "Edit is a public persisted mode")

func _reject_unchanged(game: GameSession, request: Dictionary, reason: String = "") -> void:
	var before := game.save_data()
	var result := game.command(request)
	_check(not result.ok and (reason.is_empty() or result.get("reason") == reason) and _same(before, game.save_data()), "rejected %s preserves every owned object, clock, stock item, camera, coin and selection (%s)" % [request.type, reason])

func _reopen(game: GameSession) -> GameSession:
	var copy := Session.new_session(999)
	_check(copy.restore(_json(game.save_data())) and _same(copy.snapshot(), game.snapshot()), "accepted editor state reopens at the exact arrangement and visual frame")
	return copy

func _pause_and_resume() -> void:
	var game := Session.new_session(41)
	var peer := Session.new_session(41)
	_check(game.snapshot().mode == "live" and game.snapshot().editor.layer == "layout", "new restaurants start Live with the Layout layer remembered")
	_reject_unchanged(game, {"type": "editor_move", "id": "belt-1", "x": 1, "y": 4}, "edit_required")
	game.advance(7.025)
	peer.advance(7.025)
	_edit(game)
	var before := game.save_data()
	_check(game.advance(600.0).is_empty() and _same(before, game.save_data()), "Edit freezes chefs, customers, belts, preferences, RNG, arrival clocks and fractional simulation time")
	var reopened := _reopen(game)
	_check(reopened.advance(1.0).is_empty() and _same(before, reopened.save_data()), "reopening in Edit remains paused rather than simulating hidden elapsed time")
	_check(game.command({"type": "set_mode", "mode": "live"}).ok, "Live resumes without a Save or Done phase")
	game.advance(12.975)
	peer.advance(12.975)
	_check(_same(game.save_data(), peer.save_data()), "resumed service is identical to the uninterrupted controlled timeline, including fractional remainder and future choices")

func _layers_and_selection() -> void:
	var game := Session.new_session(3)
	var content: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/editor.json"))
	_check(_same(content.page_sizes, {"people": 3, "layout": 4, "floor": 3}), "the drawer content has four Layout goods while People and Floor retain three slots")
	_check(game.save_data().editor_version == 3, "new saves declare editor version 3 for four-item Layout paging")
	_edit(game)
	_check(game.command({"type": "editor_select", "id": "chef-1"}).ok and game.snapshot().editor.layer == "people", "selecting an existing chef activates People")
	_check(game.command({"type": "editor_toggle_tray"}).ok and not game.snapshot().editor.tray_open and game.snapshot().editor.selected_id == "chef-1", "collapsing the selected layer tray retains selection and the named layer")
	_check(game.command({"type": "editor_layer", "layer": "layout"}).ok and game.snapshot().editor.tray_open, "changing layers opens the new tray")
	_check(game.command({"type": "editor_page", "page": 1}).ok and game.snapshot().editor.page == 1, "the four-item Layout drawer can reach its final compact page")
	_check(game.command({"type": "editor_layer", "layer": "people"}).ok and game.snapshot().editor.page == 0, "People has its independent three-profile page")
	_check(game.command({"type": "editor_layer", "layer": "layout"}).ok and game.snapshot().editor.page == 1, "switching layers restores the remembered compact page")
	_check(game.command({"type": "editor_layer", "layer": "floor"}).ok and _stock(game.snapshot(), "floor-cream").available == false, "Floor can be reviewed without implementing the later finish-painting ticket")
	_check(game.command({"type": "set_camera", "x": 13.125, "y": -0.375}).ok, "the camera supports continuous fractional fixed-scale panning across the three-panel world")
	var reopened := _reopen(game)
	_check(reopened.snapshot().editor.layer == "floor" and reopened.snapshot().camera.x == 13.125, "mode, selection, layer, tray, page and exact camera survive reopening")
	_check(game.command({"type": "editor_select", "id": null}).ok and game.snapshot().editor.selected_id.is_empty(), "a public deselect lets the same outside gesture pan")

func _moves_rotation_and_stock() -> void:
	var game := Session.new_session(5)
	_edit(game)
	var coins: int = game.snapshot().coins
	_check(game.command({"type": "editor_select", "id": "seat-5"}).ok, "an existing object can be selected")
	_check(game.command({"type": "editor_move", "id": "seat-5", "x": 5, "y": 11}).ok and _object(game.snapshot(), "seat-5").x == 5 and game.snapshot().editor.selected_id == "seat-5", "accepted drag moves immediately and retains selection")
	_check(game.command({"type": "editor_rotate", "id": "seat-5"}).ok and _object(game.snapshot(), "seat-5").facing == "east", "local rotation advances the selected object's facing")
	_check(game.command({"type": "editor_rotate", "id": "seat-5", "clockwise": false}).ok and _object(game.snapshot(), "seat-5").facing == "north", "counterclockwise rotation uses the same public command")
	_reject_unchanged(game, {"type": "editor_move", "id": "seat-5", "x": 2, "y": 6}, "occupied")
	_check(game.command({"type": "editor_move", "id": "seat-5", "x": 4, "y": 3}).ok and _object(game.snapshot(), "seat-5").x == 4 and _object(game.snapshot(), "seat-5").y == 3, "the left front entrance tile accepts ordinary furniture")
	_reopen(game)
	_reject_unchanged(game, {"type": "editor_move", "id": "seat-5", "x": 21, "y": 11}, "invalid_position")
	_reject_unchanged(game, {"type": "editor_move", "id": "seat-5", "x": 7, "y": 11}, "uncleared_floor")
	_check(game.command({"type": "editor_remove", "id": "seat-5"}).ok and _object(game.snapshot(), "seat-5").is_empty() and _stock(game.snapshot(), "stool-plain").count == 5 and game.snapshot().editor.selected_id.is_empty(), "removing owned furniture returns exactly one item to inventory and clears its selection")
	var placed := game.command({"type": "editor_place", "inventory_id": "stool-plain", "x": 5, "y": 11, "facing": "south"})
	_check(placed.ok and _object(game.snapshot(), placed.id).facing == "south" and _stock(game.snapshot(), "stool-plain").count == 4 and game.snapshot().editor.selected_id == placed.id, "an inventory drop consumes one owned item and selects the resulting placed object")
	var plant := game.command({"type": "editor_place", "inventory_id": "plant-angular", "x": 0, "y": 11})
	_check(plant.ok and _object(game.snapshot(), plant.id).art_id == "plant-angular", "catalog decorations use the same placement and occupancy rules as furniture")
	_reject_unchanged(game, {"type": "editor_place", "inventory_id": "crate-wood", "x": 0, "y": 11}, "occupied")
	_check(game.command({"type": "editor_remove", "id": plant.id}).ok and _stock(game.snapshot(), "plant-angular").count == 2, "a removed decoration returns to its original catalog stock")
	for x in range(6):
		_check(game.command({"type": "editor_place", "inventory_id": "belt-tile", "x": x, "y": 12}).ok, "single inventory belt drops are supported without adding #13 route drawing")
	_reject_unchanged(game, {"type": "editor_place", "inventory_id": "belt-tile", "x": 6, "y": 12}, "no_stock")
	_check(game.snapshot().coins == coins, "starting supplies, accepted edits and returned stock never debit or refund coins")
	var reopened := _reopen(game)
	var placed_after_reopen := reopened.command({"type": "editor_place", "inventory_id": "crate-wood", "x": 0, "y": 11})
	_check(placed_after_reopen.ok and placed_after_reopen.id.begins_with("editor-object-") and not placed_after_reopen.id.contains("."), "JSON reopening normalizes the monotonic object counter before the next inventory drop")
	_reopen(reopened)

func _loaded_belt_ownership() -> void:
	var game := Session.new_session(6)
	game.command({"type": "set_entrance_open", "open": false})
	game.advance(20.0)
	_edit(game)
	var loaded: Array = game.snapshot().objects.filter(func(object): return object.kind == "belt" and object.dish != null)
	_check(not loaded.is_empty(), "the edit scenario uses naturally prepared live food")
	if loaded.is_empty():
		return
	var identity: String = loaded[0].id
	var dish: Dictionary = loaded[0].dish
	var coins: int = game.snapshot().coins
	var stock: int = _stock(game.snapshot(), "belt-tile").count
	_check(game.command({"type": "editor_move", "id": identity, "x": 0, "y": 10}).ok and _object(game.snapshot(), identity).dish == dish and _object(game.snapshot(), identity).travel_progress == 0.0, "moving a loaded belt carries its exact owned dish at the new tile root")
	_reopen(game)
	_check(game.command({"type": "editor_remove", "id": identity}).ok and _stock(game.snapshot(), "belt-tile").count == stock + 1, "removing a loaded belt returns the tile but discards its plate exactly once")
	_check(game.snapshot().coins == coins and game.save_data().state.discarded_dishes == 1, "discarded food produces no sale, bonus or coin refund")
	var reopened := _reopen(game)
	game.command({"type": "set_mode", "mode": "live"})
	reopened.command({"type": "set_mode", "mode": "live"})
	game.advance(10.0)
	reopened.advance(10.0)
	_check(_same(game.save_data(), reopened.save_data()), "a restaurant with discarded food continues identically after reopening")

func _unassigned_chef_continuation() -> void:
	var game := Session.new_session(9)
	game.command({"type": "set_entrance_open", "open": false})
	game.advance(30.0)
	_edit(game)
	var chef := _object(game.snapshot(), "chef-1")
	_check(chef.held_dish != null, "the roster scenario starts with a naturally held chef dish")
	_check(game.command({"type": "editor_remove", "id": "chef-1"}).ok and not _stock(game.snapshot(), "chef-1").assigned and _stock(game.snapshot(), "chef-1").count == 1, "removing an assigned chef returns that person to the shared roster, without hiring or firing")
	_reopen(game)
	_reject_unchanged(game, {"type": "editor_place", "inventory_id": "chef-1", "x": 0, "y": 11}, "no_belt")
	_check(game.command({"type": "editor_place", "inventory_id": "chef-1", "x": 1, "y": 7}).ok and _stock(game.snapshot(), "chef-1").assigned, "the unassigned roster portrait places the same chef at a usable counter")
	var after := _object(game.snapshot(), "chef-1")
	_check(after.held_dish == chef.held_dish and after.preparation == chef.preparation and after.visual_elapsed == chef.visual_elapsed and after.recipe_id == chef.recipe_id, "unassign/reassign preserves recipe, prepared food, work and animation progress without rerolling or paying")
	_check(game.snapshot().inventory.filter(func(entry): return entry.kind == "chef").size() == 3, "the editor contains only the existing three chefs, with no hiring fixture or free extra staff")
	_reopen(game)

func _customer_protection() -> void:
	var game := Session.new_session(41)
	game.advance(4.0)
	_edit(game)
	_check(not game.snapshot().customers.is_empty(), "customer-protection checks use ordinary in-flight visitors")
	if game.snapshot().customers.is_empty():
		return
	var visitor: Dictionary = game.snapshot().customers[0]
	_check(game.command({"type": "editor_move", "id": visitor.seat_id, "x": 0, "y": 11}).ok, "#14 moves occupied or reserved seating while retaining the visitor")
	_check(game.command({"type": "editor_remove", "id": visitor.seat_id}).ok and game.snapshot().customers[0].phase == "standing", "#14 returns seating and preserves its standing visitor")
	var standing: Dictionary = game.snapshot().customers[0]
	_check(game.command({"type": "editor_place", "inventory_id": "crate-wood", "x": int(round(standing.x)), "y": int(round(standing.y))}).ok, "#14 displaces a standing visitor safely when another object is placed")
	var walking := Session.new_session(41)
	walking.advance(0.85)
	_edit(walking)
	var path: Array = walking.save_data().state.customers[0].path
	var blocked_a_future_cell := false
	for point in path:
		var current: Dictionary = walking.snapshot().customers[0]
		if _object(walking.snapshot(), current.seat_id).x == point.x and _object(walking.snapshot(), current.seat_id).y == point.y:
			continue
		if Vector2(point.x, point.y).distance_to(Vector2(current.x, current.y)) > 0.75:
			var result := walking.command({"type": "editor_place", "inventory_id": "crate-wood", "x": point.x, "y": point.y})
			_check(result.ok, "furniture may occupy the guest's former future route; navigation can reroute or wander")
			blocked_a_future_cell = result.ok
			break
	_check(blocked_a_future_cell, "a paused visitor no longer reserves every tile of their remaining aisle path")
	var before: Array = _customer_visit_values(game.save_data().state.customers)
	_check(game.command({"type": "editor_place", "inventory_id": "plant-angular", "x": 6, "y": 12}).ok and _same(before, _customer_visit_values(game.save_data().state.customers)), "a safe edit leaves every customer's preference, meal, position and visit progress intact while navigation may replan")
	_reopen(game)
	game.command({"type": "set_mode", "mode": "live"})
	_check(not game.advance(20.0).is_empty(), "Live service resumes normally with customer-safe changed arrangements")

func _customer_visit_values(customers: Array) -> Array:
	var values := customers.duplicate(true)
	for customer in values:
		for key in ["path", "path_index", "path_origin", "navigation_mode", "navigation_retry_elapsed", "wander_cursor"]:
			customer.erase(key)
	return values

func _persistence_and_migration() -> void:
	var game := Session.new_session(15)
	var path := "user://editor-tests-%s" % OS.get_process_id()
	var store := Store.new(path)
	store.clear_session()
	var validator := func(data):
		var probe := Session.new_session(1)
		return probe.restore(data)
	store.load_session(validator)
	for request in [
		{"type": "set_mode", "mode": "edit"},
		{"type": "editor_select", "id": "seat-5"},
		{"type": "editor_move", "id": "seat-5", "x": 5, "y": 11},
		{"type": "editor_rotate", "id": "seat-5"},
		{"type": "editor_layer", "layer": "people"},
		{"type": "editor_toggle_tray"},
		{"type": "set_camera", "x": 4.375, "y": 0.125},
	]:
		_check(game.command(request).ok and store.save_session(game.save_data()), "each accepted public change can persist immediately without a separate Save/Done transaction")
		var reopened := Session.new_session(111)
		_check(reopened.restore(store.load_session(validator)) and _same(reopened.save_data(), game.save_data()), "the latest accepted change, including selection/tray/camera, is the durable primary generation")
	store.clear_session()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	var legacy := _json(game.save_data())
	legacy.erase("editor_version")
	legacy.erase("staff_version");legacy.state.erase("staff")
	for key in ["mode", "editor", "inventory", "next_object_id", "discarded_dishes"]:
		legacy.state.erase(key)
	var migrated := Session.new_session(99)
	_check(migrated.restore(legacy) and migrated.snapshot().mode == "live", "pre-editor saves receive a one-time compatible Live editor-state migration")
	_check(_same(migrated.snapshot().objects, game.snapshot().objects) and _same(migrated.snapshot().stats, game.snapshot().stats) and migrated.snapshot().coins == game.snapshot().coins and _same(migrated.snapshot().camera, game.snapshot().camera), "migration retains every previous arrangement, service clock, sale, coin and camera")

func _four_slot_page_migration() -> void:
	var game := Session.new_session(115)
	game.advance(4.025)
	_edit(game)
	game.command({"type": "editor_select", "id": "seat-5"})
	game.command({"type": "editor_toggle_tray"})
	game.command({"type": "set_camera", "x": 4.375, "y": 0.125})
	var restored := Session.new_session(99)
	for example in [
		[1, 0, 0, "layout"],
		[1, 1, 0, "layout"],
		[1, 2, 1, "layout"],
		[2, 0, 0, "layout"],
		[2, 1, 0, "layout"],
		[1, 2, 1, "people"],
		[2, 1, 0, "floor"],
	]:
		var legacy := _json(game.save_data())
		legacy.editor_version = example[0]
		legacy.state.editor.layer = example[3]
		legacy.state.editor.pages.layout = example[1]
		legacy.state.editor.page = legacy.state.editor.pages[example[3]]
		var expected := _json(legacy)
		expected.editor_version = 3
		expected.state.editor.pages.layout = example[2]
		expected.state.editor.page = expected.state.editor.pages[example[3]]
		_check(restored.restore(legacy) and _same(restored.save_data(), expected), "v%s Layout page %s migrates to page %s with %s active; every other saved field is preserved" % example)
		_reopen(restored)
	_check(restored.command({"type": "editor_layer", "layer": "layout"}).ok and not restored.command({"type": "editor_page", "page": 2}).ok and restored.command({"type": "editor_page", "page": 1}).ok, "four-item Layout paging accepts its second page and rejects a third page")
	for old_version in [1, 2]:
		var legacy := _json(game.save_data())
		legacy.editor_version = old_version
		legacy.state.editor.page = 1
		legacy.state.editor.pages.layout = 1
		var before := restored.save_data()
		for layer in ["people", "layout", "floor"]:
			var old_page_count := (3 if old_version == 1 else 2) if layer == "layout" else 1
			for bad_page in [-1, old_page_count, 999, 0.5, "0", true, null]:
				var invalid := _json(legacy)
				invalid.state.editor.pages[layer] = bad_page
				if layer == "layout": invalid.state.editor.page = bad_page
				_check(not restored.restore(invalid) and _same(before, restored.save_data()), "v%s rejects malformed or out-of-range old %s pages atomically" % [old_version, layer])
			var missing := _json(legacy)
			missing.state.editor.pages.erase(layer)
			_check(not restored.restore(missing) and _same(before, restored.save_data()), "v%s rejects a missing remembered %s page" % [old_version, layer])
		var mismatched := _json(legacy)
		mismatched.state.editor.page = 0
		_check(not restored.restore(mismatched) and _same(before, restored.save_data()), "v%s rejects an active page that disagrees with its remembered layer before both could map to zero" % old_version)
		for corruption in ["tray", "selection", "inventory", "mode"]:
			var invalid := _json(legacy)
			match corruption:
				"tray": invalid.state.editor.tray_open = "yes"
				"selection": invalid.state.editor.selected_id = "missing"
				"inventory": invalid.state.inventory[0].count += 1
				"mode": invalid.state.mode = "shop"
			_check(not restored.restore(invalid) and _same(before, restored.save_data()), "v%s paging migration still rejects corrupt %s data without changing the session" % [old_version, corruption])

func _invalid_commands_and_saves() -> void:
	var game := Session.new_session(19)
	_edit(game)
	for request in [
		{"type": "set_mode", "mode": "pause"},
		{"type": "editor_layer", "layer": "shop"},
		{"type": "editor_page", "page": -1},
		{"type": "editor_page", "page": 99},
		{"type": "editor_select", "id": "not-owned"},
		{"type": "editor_rotate", "id": "belt-1", "clockwise": "yes"},
		{"type": "editor_place", "inventory_id": "floor-cream", "x": 0, "y": 11},
		{"type": "editor_place", "inventory_id": "belt-tile", "x": 0.5, "y": 11},
		{"type": "editor_place", "inventory_id": "belt-tile", "x": 0, "y": 11, "facing": "diagonal"},
		{"type": "editor_place", "inventory_id": "not-owned", "x": 0, "y": 11},
	]:
		_reject_unchanged(game, request)
	var saved := _json(game.save_data())
	var corruptions: Array = []
	var invalid := _json(saved)
	invalid.state.mode = "shop"
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.editor.tray_open = "yes"
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.editor.selected_id = "missing"
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.editor.pages.layout = 999
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.inventory[0].count = -1
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.inventory[0].count += 1
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.inventory.append(invalid.state.inventory[0].duplicate(true))
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.inventory.pop_front()
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.state.discarded_dishes = 100
	corruptions.append(invalid)
	invalid = _json(saved)
	invalid.editor_version = 999
	corruptions.append(invalid)
	for damaged in corruptions:
		_check(not game.restore(damaged) and _same(game.save_data(), saved), "invalid editor saves are rejected atomically without damaging a playable restaurant")
