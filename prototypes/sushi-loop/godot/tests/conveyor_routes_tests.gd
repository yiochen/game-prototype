extends SceneTree
## #13: observable construction, stock, food and reopening through the public
## GameSession boundary; render contracts are checked against authored ports.
const Session = preload("res://scripts/session.gd")
const View = preload("res://scripts/restaurant_view.gd")
var checks := 0
var failures: Array[String] = []
const LOOP := [Vector2i(1,3), Vector2i(2,3), Vector2i(3,3), Vector2i(3,4), Vector2i(2,4), Vector2i(1,4)]

func _initialize() -> void:
	_construction_and_zero_stock()
	_reuse_and_return()
	_simultaneous_loop()
	_endpoint_and_consumption()
	_validation_and_upgrade()
	_authored_turns()
	if failures.is_empty():
		print("PASS: %s conveyor route checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: " + failure)
		quit(1)

func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message)

func json(data: Dictionary) -> Dictionary:
	return JSON.parse_string(JSON.stringify(data, "", true, true))

func same(a: Variant, b: Variant) -> bool:
	return JSON.parse_string(JSON.stringify(a, "", true, true)) == JSON.parse_string(JSON.stringify(b, "", true, true))

func fresh(objects: Array = []) -> GameSession:
	var game := Session.new_session(1313, {"floor": {"columns": 9, "rows": 10, "world_columns": 27, "entrance": {"x": 0, "y": 0}}, "objects": objects, "service": {"belt_seconds_per_cell": 1.0}})
	game.command({"type": "set_entrance_open", "open": false})
	game.command({"type": "set_mode", "mode": "edit"})
	return game

func object(game: GameSession, identity: String) -> Dictionary:
	for tile in game.snapshot().objects:
		if tile.id == identity: return tile
	return {}

func stock(game: GameSession) -> int:
	return int(game.snapshot().inventory.filter(func(item): return item.id == "belt-tile")[0].count)

func reopen(game: GameSession) -> GameSession:
	var peer := Session.new()
	check(peer.restore(json(game.save_data())) and same(peer.snapshot(), game.snapshot()), "JSON reopening preserves exact routes, path cursor, stock, food and clocks")
	return peer

func reject(game: GameSession, request: Dictionary, reason: String) -> void:
	var before := game.save_data()
	var result := game.command(request)
	check(not result.ok and result.reason == reason and same(before, game.save_data()), "Rejected %s (%s) changes no accepted state" % [request.type, reason])

func build_loop() -> GameSession:
	var game := fresh()
	var start := game.command({"type": "editor_place", "inventory_id": "belt-tile", "x": LOOP[0].x, "y": LOOP[0].y})
	check(start.ok, "An inventory drop starts a route")
	for cell in LOOP.slice(1): check(game.command({"type": "editor_belt_extend", "x": cell.x, "y": cell.y}).ok, "An empty neighbor extends the route")
	check(game.command({"type": "editor_belt_extend", "x": LOOP[0].x, "y": LOOP[0].y}).get("closed", false), "Tapping the starting tile closes a valid six-tile loop")
	return game

func seed_food(game: GameSession) -> void:
	var data := game.save_data()
	var index := 1
	for tile in data.state.objects:
		if tile.kind == "belt":
			tile.dish = {"id": "dish-%s" % index, "recipe_id": "salmon_nigiri"}
			tile.travel_elapsed = 0.0
			index += 1
	data.state.next_dish_id = index
	check(game.restore(json(data)), "A controlled full-food fixture passes the public restore boundary")

func _construction_and_zero_stock() -> void:
	var game := fresh()
	var start := game.command({"type": "editor_place", "inventory_id": "belt-tile", "x": 1, "y": 3})
	check(start.ok and stock(game) == 5 and game.snapshot().editor.belt_path == [start.id], "The first drop spends exactly one tile and saves the construction cursor")
	check(game.snapshot().editor.belt_targets.size() == 4, "Construction exposes the four neighboring cells")
	reject(game, {"type": "editor_belt_extend", "x": 3, "y": 3}, "invalid_position")
	for cell in LOOP.slice(1): check(game.command({"type": "editor_belt_extend", "x": cell.x, "y": cell.y}).ok, "A new route supports both straight and corner extensions")
	check(stock(game) == 0, "Six placed tiles exhaust the six owned supplies without debiting coins")
	var targets: Array = game.snapshot().editor.belt_targets
	check(targets.any(func(t): return t.kind == "close" and t.valid) and targets.any(func(t): return not t.valid and t.reason == "no_belt_tiles"), "Zero stock keeps closure usable and marks only empty extensions unavailable")
	reject(game, {"type": "editor_belt_extend", "x": 0, "y": 4}, "no_belt_tiles")
	var peer := reopen(game)
	check(peer.command({"type": "editor_rotate", "id": peer.snapshot().editor.selected_id}).ok and stock(peer) == 0, "Latest-tile rotation remains available at zero stock")
	check(game.command({"type": "editor_belt_extend", "x": 1, "y": 3}).get("closed", false) and stock(game) == 0 and game.snapshot().editor.belt_path.is_empty(), "Loop closure reuses its starting tile for free and exits construction")
	check(game.command({"type": "editor_select", "id": start.id}).ok and game.command({"type": "editor_belt_extend", "x": 2, "y": 3}).get("reused", false) and stock(game) == 0, "Selecting an existing belt permits free neighboring reuse at zero stock")
	check(game.command({"type": "editor_belt_end"}).ok and game.snapshot().mode == "edit" and game.snapshot().editor.belt_path.is_empty() and game.snapshot().editor.tray_open, "Inventory exit keeps accepted routes and opens the drawer in paused Edit")
	reopen(game)

func _reuse_and_return() -> void:
	var game := fresh([
		{"id":"a","kind":"belt","x":1,"y":3,"facing":"east"},
		{"id":"b","kind":"belt","x":2,"y":3,"facing":"east"},
		{"id":"c","kind":"belt","x":3,"y":3,"facing":"east"},
		{"id":"old-input","kind":"belt","x":2,"y":5,"facing":"north"},
		{"id":"d","kind":"belt","x":2,"y":4,"facing":"east"},
		{"id":"e","kind":"belt","x":3,"y":4,"facing":"east"},
	])
	seed_food(game)
	var before := game.snapshot()
	game.command({"type":"editor_select","id":"b"})
	var result := game.command({"type":"editor_belt_extend","x":2,"y":4})
	check(result.ok and result.reused and stock(game) == 6 and game.snapshot().objects.size() == before.objects.size(), "Neighboring reuse spends no stock and retains every existing tile")
	check(object(game,"b").next_id == "d" and object(game,"old-input").next_id == "" and object(game,"c").incoming_id == "", "Reshaping a turn replaces its old edges without creating a split or merge")
	check(object(game,"c").dish == before.objects[2].dish and object(game,"old-input").dish == before.objects[3].dish, "Disconnected old segments retain their exact food")
	var coins: int = game.snapshot().coins
	check(game.command({"type":"editor_remove","id":"d"}).ok and stock(game) == 7 and game.snapshot().editor.belt_path == ["b"], "Return stores the latest tile and restores the preceding path cursor")
	check(game.snapshot().coins == coins and game.save_data().state.discarded_dishes == 1 and object(game,"b").next_id == "", "Returning an occupied tile discards one dish without a sale or refund")
	reopen(game)

func _simultaneous_loop() -> void:
	var game := build_loop()
	seed_food(game)
	game.command({"type":"set_mode","mode":"live"})
	var before := game.snapshot()
	var peer := reopen(game)
	var reordered := json(game.save_data())
	reordered.state.objects.reverse()
	var reverse := Session.new()
	check(reverse.restore(reordered), "Object storage order is independent of route topology")
	game.advance(0.45)
	check(game.snapshot().objects.all(func(tile): return tile.travel_progress > 0.4 and tile.travel_progress < 0.5), "A completely full loop moves every plate visibly together")
	var partial := reopen(game)
	var events := game.advance(0.55)
	peer.advance(1.0)
	reverse.advance(1.0)
	partial.advance(0.55)
	check(events.filter(func(event): return event.type == "belt_moved").size() == LOOP.size(), "All full-loop dishes transfer simultaneously once per cell duration")
	var identities := {}
	for tile in before.objects:
		var destination := object(game, tile.next_id)
		check(destination.dish == tile.dish and object(reverse, tile.next_id).dish == tile.dish, "A full-loop transfer preserves unique dish ownership regardless of object order")
		identities[destination.dish.id] = true
	check(identities.size() == LOOP.size() and same(game.save_data(), peer.save_data()) and same(game.save_data(), partial.save_data()), "Full-loop time partitioning and partial-crossing reopening neither duplicate nor lose food")

func _endpoint_and_consumption() -> void:
	var game := fresh([
		{"id":"a","kind":"belt","x":2,"y":3,"facing":"east"},
		{"id":"b","kind":"belt","x":3,"y":3,"facing":"east"},
		{"id":"c","kind":"belt","x":4,"y":3,"facing":"east"},
		{"id":"seat","kind":"seat","x":4,"y":4,"facing":"north"},
	])
	seed_food(game)
	game.command({"type":"set_mode","mode":"live"})
	var before := game.snapshot()
	game.advance(20.0)
	check(game.snapshot().objects.filter(func(tile): return tile.kind == "belt").all(func(tile): return tile.travel_progress == 0.0) and object(game,"c").dish == before.objects[2].dish and game.snapshot().coins == before.coins, "An open endpoint retains food and stops its upstream train without draining coins")
	game.command({"type":"set_entrance_open","open":true})
	var peer := reopen(game)
	var events := game.advance(25.0)
	peer.advance(25.0)
	check(events.any(func(event): return event.type == "sale") and events.any(func(event): return event.type == "belt_moved" and event.from_id == "a"), "Eating a stopped endpoint plate releases the local blockage automatically")
	check(same(peer.save_data(), game.save_data()), "A released queue resumes the same sales, visits, RNG and remaining food after reopening")

func _validation_and_upgrade() -> void:
	var game := build_loop()
	var good := game.save_data()
	for change in ["dangling", "merge", "nonneighbor", "cursor", "future"]:
		var bad := json(good)
		match change:
			"dangling": bad.state.objects[0].next_id = "absent"
			"merge": bad.state.objects[2].next_id = bad.state.objects[0].next_id
			"nonneighbor": bad.state.objects[0].facing = "west"
			"cursor": bad.state.editor.belt_path = ["absent"]
			"future": bad.belt_route_version = 2
		check(not game.restore(bad) and same(good, game.save_data()), "Malformed route save (%s) is rejected atomically" % change)
	var legacy := fresh([{ "id":"a","kind":"belt","x":1,"y":3,"facing":"east" }, { "id":"b","kind":"belt","x":2,"y":3,"facing":"east" }])
	seed_food(legacy)
	var old := legacy.save_data()
	old.erase("belt_route_version")
	old.state.editor.erase("belt_path")
	for tile in old.state.objects:
		tile.erase("next_id")
		tile.erase("input_facing")
	var migrated := Session.new()
	check(migrated.restore(json(old)) and object(migrated,"a").next_id == "b" and object(migrated,"b").next_id == "" and stock(migrated) == stock(legacy), "Pre-route saves acquire their existing adjacency links without spending stock")
	check(object(migrated,"a").dish == object(legacy,"a").dish and migrated.snapshot().coins == legacy.snapshot().coins, "Legacy route migration preserves food and economy")

func _authored_turns() -> void:
	var view := View.new()
	view.native_composition_enabled = false
	view.art.reload()
	view.cell = 128.0
	for incoming in Session.DIRECTIONS:
		for outgoing in Session.DIRECTIONS:
			if Vector2(Session.DIRECTIONS[incoming]).dot(Vector2(Session.DIRECTIONS[outgoing])) != 0: continue
			var center := Vector2i(4,4)
			var a: Vector2i = center - Session.DIRECTIONS[incoming]
			var b: Vector2i = center + Session.DIRECTIONS[outgoing]
			var game := fresh([
				{"id":"in","kind":"belt","x":a.x,"y":a.y,"facing":incoming},
				{"id":"turn","kind":"belt","x":4,"y":4,"facing":outgoing},
				{"id":"out","kind":"belt","x":b.x,"y":b.y,"facing":outgoing},
			])
			view.state = game.snapshot()
			var turn := object(game,"turn")
			var identity := view.belt_clip(turn)
			var facing := view.belt_direction(turn)
			check(identity.begins_with("belt-corner-") and view.art.objects.has(identity), "Every turn uses an approved native corner atlas (%s to %s)" % [incoming,outgoing])
			var ports: Dictionary = view.art.objects[identity].ports[facing]
			var deck: Vector2 = view.art.socket(identity,"deck",facing)
			check((Vector2(ports.incoming[0],ports.incoming[1])-deck).is_equal_approx(view.belt_path_point(turn,0)*128) and (Vector2(ports.outgoing[0],ports.outgoing[1])-deck).is_equal_approx(view.belt_path_point(turn,1)*128), "Curved food motion meets the exact authored inlet and outlet ports")
			turn.travel_progress = 1.0
			var next := object(game,"out")
			check(view.dish_base(turn).distance_to(view.dish_base(next)) < 0.001 and view.belt_path_point(turn,0.5).length() > 0.1, "A dish follows the quarter-circle and crosses ownership boundaries continuously")
	view.free()
