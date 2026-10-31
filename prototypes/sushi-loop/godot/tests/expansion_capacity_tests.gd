extends SceneTree
## Capacity must equal usable placement cells for every independent floor/save.
const Book = preload("res://scripts/expansion_book.gd")
const Session = preload("res://scripts/session.gd")
var checks := 0
var failures: Array[String] = []
func _init() -> void: call_deferred("run")
func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message);printerr("FAIL: "+message)
func count_cells(state: Dictionary, floor_data: Dictionary) -> int:
	var result := 0
	for y in range(int(floor_data.backdrop_rows),int(floor_data.rows)):
		for x in range(Book.columns(floor_data)):
			if Book.usable(state,floor_data,Vector2i(x,y),true): result += 1
	return result
func run() -> void:
	var identities: Array = Book.definition().patches.map(func(p):return p.id)
	var floors: Array = []
	for width in [7,9,12]:
		for rows in [9,13,16]: floors.append({"columns":width,"world_columns":width+14,"rows":rows,"backdrop_rows":3})
	floors.append({"columns":7,"world_columns":30,"rows":16,"backdrop_rows":3})
	floors.append({"columns":4,"world_columns":4,"rows":6,"backdrop_rows":0})
	var masks: Array = [[],identities,identities.slice(0,7),identities.slice(9,25),["dock-access"],["dock-access","dock-access"],["unknown"]]
	for floor_data in floors:
		var initial := count_cells({"expansion":{"cleared":[]}},floor_data)
		for cleared in masks:
			var state := {"expansion":{"cleared":cleared.duplicate(),"revealed":false}}
			var expected := count_cells(state,floor_data)
			check(Book.area(state,floor_data)==expected,"capacity matches actual usable cells across native/legacy/clipped/extra-row floors")
			check(Book.base_area(floor_data)==initial,"base area is independent of the other restaurant's cleared objects")
			check(is_equal_approx(Book.arrival_multiplier(state,floor_data),float(expected)/maxi(1,initial)),"arrival rate uses the same usable floor")
			check(Book.staff_bonus(state,floor_data)==maxi(0,(expected-initial)/9),"staff slots use the same ordinary area")
			state.expansion.revealed = true
			check(Book.area(state,floor_data)==expected,"revealing the reserved dock never adds placement capacity")
			state.expansion.cleared = []
			check(Book.area(state,floor_data)==initial,"restoring or resetting clearance reads current session state")
	var session := Session.new_session(19,{"starting_coins":100000})
	var original: Dictionary = session.save_data()
	var first: Dictionary = session.snapshot().expansion
	first.patches[0].price = -1
	first.cleared.append("changed-by-renderer")
	check(session.snapshot().expansion == Book.snapshot(original.configuration,original.state),"mutating a returned snapshot cannot alter the cached map")
	session.advance(1.0)
	check(session.snapshot().expansion == Book.snapshot(original.configuration,original.state),"service clocks reuse the unchanged clearance map")
	var available: Dictionary = session.snapshot().expansion.patches.filter(func(p):return p.available)[0]
	check(session.command({"type":"clear_trash","id":available.id}).ok,"the clearance cache fixture uses a real paid command")
	var cleared: Dictionary = session.save_data()
	check(session.snapshot().expansion == Book.snapshot(cleared.configuration,cleared.state),"clearing immediately updates availability, capacity and shade data")
	cleared.state.expansion.cleared = identities.duplicate()
	check(session.restore(cleared),"an all-cleared restaurant restores through domain validation")
	check(session.snapshot().expansion.dock_ready and not session.snapshot().expansion.dock_open,"restoring clearance updates the ready cover without revealing it")
	check(session.command({"type":"reveal_dock"}).ok and session.snapshot().expansion.dock_open,"explicit reveal invalidates the cached covered presentation")
	var legacy := Session.new_session(21,{"floor":{"columns":9,"world_columns":23,"rows":16,"backdrop_rows":3}})
	check(session.restore(legacy.save_data()) and session.snapshot().expansion == legacy.snapshot().expansion,"restoring a different floor does not retain another room's map")
	check(session.restore(original) and session.snapshot().expansion == Book.snapshot(original.configuration,original.state),"restoring the original room resets cached clearance and geometry")
	print("Expansion capacity: %s checks; %s failures" % [checks,failures.size()]);quit(0 if failures.is_empty() else 1)
