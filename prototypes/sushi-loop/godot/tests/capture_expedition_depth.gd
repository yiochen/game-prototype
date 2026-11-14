extends SceneTree
## Native evidence for dive layering: the hull draws behind any row whose base is
## south of the hull's base, so it slips behind a rock it passes north of and
## covers the rock once it is south of it.
## Run through tools/test_native.py --visible with an output folder.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
var app
var destination := ""

func _initialize() -> void: call_deferred("run")

func capture(name: String) -> void:
	await process_frame
	if destination.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(destination.path_join(name + ".png"))

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await process_frame
	var s = Session.new_session(24, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	app.session = s; app._refresh(); app._layout()
	if app.performance_overlay != null: app.performance_overlay.hide()
	var ui = app.expedition_ui
	var view = ui.view
	app._open_landmark("Submarine")
	for i in range(600):
		if ui.mode == "prep" and not app.transition.visible: break
		await process_frame
	await create_timer(0.4).timeout
	ui.start()
	await create_timer(0.3).timeout
	# A lone rock away from the start, with open water north and south of it.
	var rock := Vector2i(-1, -1)
	var solid: Dictionary = {}
	for b in view.scene.collision: solid[b] = true
	for index in view.world.path.reef_cells: solid[Vector2i(int(index) % 11, int(index) / 11)] = true
	for b in view.scene.collision:
		if b.y < 12 or b.x < 2 or b.x > 8: continue
		var around := [Vector2i(0, -1), Vector2i(0, -2), Vector2i(0, 1), Vector2i(0, 2), Vector2i(-1, -1), Vector2i(1, -1), Vector2i(-1, 1), Vector2i(1, 1)]
		if around.all(func(d): return not solid.has(b + d)):
			rock = b; break
	if rock.x < 0: print("Depth captures: no lone rock"); quit(1); return
	app.set_process(false)
	for shot in [["01-north-behind", -0.35], ["02-south-in-front", 1.35]]:
		view.ship = Vector2(rock.x + .5, rock.y + float(shot[1]))
		view.cam_x = rock.x + .5
		view.queue_redraw()
		await capture(shot[0])
	print("Depth captures at rock %s" % str(rock))
	quit(0)
