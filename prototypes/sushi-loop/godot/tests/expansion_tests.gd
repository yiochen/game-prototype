extends SceneTree
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expansion_book.gd")
var count := 0
var failures: Array[String] = []
func _init() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	count += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func run() -> void:
	var game = Session.new_session(19,{"starting_coins":10000})
	check(game != null,"approved starter constructs")
	if game == null: quit(1);return
	var initial: Dictionary = game.snapshot()
	check(initial.expansion.enabled and initial.expansion.patches.size() == 41,"41 actual trash objects")
	check(initial.expansion.usable_area == 70,"70 starter cells")
	check(initial.expansion.patches.filter(func(p):return p.available).map(func(p):return p.id) == ["sofa-west","armchair-west","dock-access","shelves-west"],"chosen-order adjacent clearances")
	var occupied := {}
	for value in Book.definition().patches:
		for y in range(int(value.y),int(value.y)+int(value.h)):
			for x in range(int(value.x),int(value.x)+int(value.w)):
				check(not occupied.has(Vector2i(x,y)),"no overlapping trash mask")
				occupied[Vector2i(x,y)] = true
	check(occupied.size() == 131,"exact 131-cell future masks")
	var before: Dictionary = game.save_data()
	check(not game.command({"type":"clear_trash","id":"trash-20-12"}).ok and game.save_data() == before,"unknown/far clear cannot mutate")
	check(not game.command({"type":"dock_access","destination":"Submarine"}).ok and game.save_data() == before,"covered submarine rejects without mutation")
	check(not game.command({"type":"reveal_dock"}).ok and game.save_data() == before,"reveal rejects before all surrounding trash is removed")
	var result: Dictionary = game.command({"type":"clear_trash","id":"dock-access"})
	check(result.ok and result.changed and game.snapshot().coins == 9820,"single object debit")
	check(not game.snapshot().expansion.dock_open and game.snapshot().expansion.dock_blockers.size() == 6,"car alone cannot reveal dock")
	check(game.snapshot().expansion.usable_area == 76,"only the car's six cells are gained")
	before = game.save_data()
	check(game.command({"type":"clear_trash","id":"dock-access"}).ok and game.save_data() == before,"repeated confirmation never debits twice")
	var loaded = Session.new_session(2)
	check(loaded.restore(JSON.parse_string(JSON.stringify(before))),"partial clear roundtrips")
	check(loaded.snapshot().expansion.cleared == ["dock-access"] and not loaded.snapshot().expansion.dock_open,"partial reload remains covered")
	var required := ["armchair-west","dock-access","trash-9-4","trash-8-5","trash-10-6","trash-10-8","trash-10-9"]
	for missing in required:
		var fixture: Dictionary = Session.new_session(3).save_data()
		fixture.state.expansion.cleared = required.filter(func(id):return id != missing)
		check(loaded.restore(fixture) and not loaded.snapshot().expansion.dock_open,"every side/corner object is required: "+missing)
		check(not loaded.command({"type":"dock_access","destination":"Workshop"}).ok,"Workshop shares complete prerequisite")
	var poor = Session.new_session(19,{"starting_coins":0})
	before = poor.save_data()
	check(not poor.command({"type":"clear_trash","id":"armchair-west"}).ok and poor.save_data() == before,"insufficient funds are atomic")
	game = Session.new_session(19)
	var seconds := 0
	while game.snapshot().coins < 820 and seconds < 1200:
		game.advance(2);seconds += 2
	check(game.snapshot().coins >= 820 and game.snapshot().stats.sales > 0,"real starter service funds all seven without expansion")
	print("Starter funds all neighbors after %s simulation seconds / %s real sales" % [seconds,game.snapshot().stats.sales])
	var camera: Dictionary = game.snapshot().camera
	var order := ["armchair-west","dock-access","trash-8-5","trash-9-4","trash-10-6","trash-10-8","trash-10-9"]
	for id in order:
		var prior_coins: int = game.snapshot().coins
		check(game.command({"type":"clear_trash","id":id}).get("changed",false),"reachable before uncovering: "+id)
		check(game.snapshot().coins == prior_coins-int(Book.patch(id).price),"exact configured price: "+id)
		check(game.snapshot().camera == camera,"clear leaves camera fixed")
		check(not game.snapshot().expansion.dock_open and game.snapshot().expansion.dock_ready == (id == order[-1]),"clearing only enables inspection; it never reveals automatically")
	before = game.save_data()
	check(not game.command({"type":"dock_access","destination":"Submarine"}).ok and game.save_data() == before,"ready cover still blocks destination access")
	check(loaded.restore(JSON.parse_string(JSON.stringify(before))) and loaded.snapshot().expansion.dock_ready and not loaded.snapshot().expansion.dock_open,"ready but unconfirmed cover survives reload")
	var old: Dictionary = before.duplicate(true);old.expansion_version = 1;old.state.expansion.version = 1;old.state.expansion.erase("revealed")
	check(loaded.restore(old) and loaded.snapshot().expansion.dock_open and loaded.snapshot().coins == before.state.coins,"0.11.2 already-revealed progress migrates without replay or new charges")
	old.state.expansion.cleared = ["dock-access"]
	check(loaded.restore(old) and not loaded.snapshot().expansion.dock_open,"0.11.2 partial clearance migrates as still covered")
	check(game.command({"type":"reveal_dock"}).get("changed",false) and game.snapshot().expansion.dock_open,"explicit reveal confirmation unlocks the destinations")
	check(game.snapshot().coins == before.state.coins and game.snapshot().camera == before.state.camera and game.save_data().random_state == before.random_state,"reveal preserves coins, camera and RNG")
	before = game.save_data()
	check(not game.command({"type":"reveal_dock"}).changed and game.save_data() == before,"repeated reveal is idempotent")
	check(game.command({"type":"dock_access","destination":"Submarine"}).ok and game.command({"type":"dock_access","destination":"Workshop"}).ok,"both destinations accessible")
	check(game.snapshot().expansion.usable_area == 94 and game.snapshot().staff.capacity == 6,"area drives real staff capacity")
	check(game.snapshot().expansion.arrival_multiplier > 1.0,"area drives arrival cadence")
	game.advance(30)
	game.command({"type":"set_mode","mode":"edit"});game.command({"type":"editor_layer","layer":"layout"})
	check(game.command({"type":"editor_place","inventory_id":"stool-plain","x":7,"y":5}).ok,"cleared cells accept inventory")
	check(game.command({"type":"shop_purchase","offer_id":"belt","expected_sequence":0}).ok and game.command({"type":"shop_purchase","offer_id":"belt","expected_sequence":1}).ok,"real service funds conveyor tiles from Shop")
	check(game.command({"type":"editor_place","inventory_id":"belt-tile","x":7,"y":9}).ok,"cleared floor accepts conveyor construction")
	check(game.snapshot().editor.belt_targets.any(func(t):return t.x == 8 and t.y == 9 and t.valid),"conveyor targets extend through cleared future cells")
	game.command({"type":"editor_belt_end"})
	check(not game.command({"type":"editor_place","inventory_id":"stool-plain","x":8,"y":7}).ok,"platform remains reserved")
	check(not game.command({"type":"editor_place","inventory_id":"stool-plain","x":20,"y":12}).ok,"uncleared floor rejects placement")
	var area: int = game.snapshot().expansion.usable_area
	before = game.save_data();game.advance(60)
	check(game.save_data() == before and game.snapshot().expansion.usable_area == area,"Edit freezes service; occupancy does not shrink floor capacity")
	check(loaded.restore(JSON.parse_string(JSON.stringify(game.save_data()))),"expanded placement and service state roundtrip")
	var legacy: Dictionary = Session.new_session(4,{"starting_coins":432}).save_data()
	legacy.erase("expansion_version");legacy.state.erase("expansion")
	check(loaded.restore(legacy),"old save receives neutral expansion state")
	check(loaded.snapshot().coins == 432 and JSON.parse_string(JSON.stringify(loaded.save_data().state.objects)) == JSON.parse_string(JSON.stringify(legacy.state.objects)),"migration preserves owned objects and coins across JSON number normalization")
	var wide: Dictionary = Session.new_session(5).save_data();wide.erase("expansion_version");wide.state.erase("expansion");wide.configuration.floor.columns = 9
	for object in wide.state.objects:
		if object.id == "chef-disconnected": object.x = 8;object.y = 7
	check(loaded.restore(wide),"legacy nine-column owned layout loads without dock collision")
	check(loaded.snapshot().floor.world_columns == 23 and loaded.snapshot().expansion.offset_x == 2,"future layout moves beyond the legacy starter footprint")
	check(loaded.snapshot().objects.any(func(o):return o.id == "chef-disconnected" and o.x == 8 and o.y == 7),"legacy owned furniture and staff stay in place")
	var rescued = Session.new_session(19,{"starting_coins":10000})
	rescued.advance(1)
	rescued.command({"type":"clear_trash","id":"armchair-west"})
	rescued.command({"type":"set_mode","mode":"edit"})
	rescued.command({"type":"editor_layer","layer":"people"})
	var guest: Dictionary = rescued.snapshot().customers[0]
	check(rescued.command({"type":"editor_pickup","id":guest.id}).ok and rescued.command({"type":"editor_move","id":guest.id,"x":7,"y":5}).ok,"a real guest can be rescued onto cleared floor")
	var fresh = Session.new_session(1)
	check(fresh.restore(JSON.parse_string(JSON.stringify(rescued.save_data()))),"expanded guest save validates against its saved clearance, independent of the open restaurant")
	var locked: Dictionary = rescued.save_data();locked.state.expansion.cleared = []
	check(not fresh.restore(locked),"a guest standing on uncleared floor rejects even when the open restaurant has that patch clear")
	var complete = Session.new_session(19,{"starting_coins":10000})
	for i in range(41):
		var choices: Array = complete.snapshot().expansion.patches.filter(func(p):return p.available)
		if choices.is_empty(): break
		check(complete.command({"type":"clear_trash","id":choices[-1].id}).get("changed",false),"chosen-order clearance remains reachable across the entire room")
	check(complete.snapshot().expansion.patches.is_empty() and complete.snapshot().expansion.usable_area == 201,"all 41 masks free exactly 131 ordinary cells without counting the dock")
	check(Session.new().restore(JSON.parse_string(JSON.stringify(complete.save_data()))),"complete cleanup roundtrips through the public save boundary")
	for damage in ["missing","type","premature","future"]:
		var invalid: Dictionary = Session.new_session(19).save_data()
		match damage:
			"missing": invalid.state.expansion.erase("revealed")
			"type": invalid.state.expansion.revealed = "yes"
			"premature": invalid.state.expansion.revealed = true
			"future": invalid.expansion_version = 99
		check(not loaded.restore(invalid),"invalid reveal state rejects atomically: "+damage)
	var corrupt: Dictionary = loaded.save_data();corrupt.state.expansion.cleared = ["invented"]
	before = loaded.save_data();check(not loaded.restore(corrupt) and loaded.save_data() == before,"malformed clearance save rejects atomically")
	print("Expansion domain: %s checks; %s failures" % [count,failures.size()])
	quit(0 if failures.is_empty() else 1)
