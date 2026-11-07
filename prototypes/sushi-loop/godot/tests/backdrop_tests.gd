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
	a = GameSession.flat_view(a) if a is Dictionary and a.has("engine") else a
	b = GameSession.flat_view(b) if b is Dictionary and b.has("engine") else b
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
	await process_frame
	if failures.is_empty():
		print("PASS: %s backdrop checks" % checks)
		quit(0)
	else:
		for failure in failures: printerr("FAIL: "+failure)
		quit(1)
