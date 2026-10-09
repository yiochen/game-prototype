extends SceneTree
## Render-only QA: does not load Main or read/write game saves.

func _initialize() -> void:
	call_deferred("capture")

func capture() -> void:
	root.size = Vector2i(720, 1280)
	var dive = load("res://scripts/expedition.gd").new()
	dive.setup(0, {})
	root.add_child(dive)
	dive.set_process(false)
	dive.elapsed = 21.0
	dive.travel = 21.0
	dive.sea_scroll = 5460.0
	dive.pickups = 24
	dive.notice_left = 0.0
	dive.objects = [
		{"kind":"portal", "x":175.0, "y":420.0},
		{"kind":"rock", "x":510.0, "y":565.0, "radius":53.0},
		{"kind":"salvage", "x":380.0, "y":650.0},
		{"kind":"salvage", "x":355.0, "y":745.0},
		{"kind":"salvage", "x":375.0, "y":815.0},
	]
	await take(dive, "travel")
	dive.objects = []
	dive.phase = "aim"
	dive.species = "salmon"
	dive.creature_x = 411.0
	dive.shots = [{"x":390.0,"y":640.0}]
	await take(dive, "aim")
	dive.phase = "pursuit"
	dive.species = "eel"
	dive.shots = []
	dive.ship_x = 371.0
	dive.resistance = 63.0
	dive.attack_x = 467.0
	dive.attack_warning = 1.1
	await take(dive, "pursuit")
	dive.suspend()
	await take(dive, "pause")
	dive.paused = false
	dive.lesson = "shoot"
	dive.lesson_step = 2
	await take(dive, "lesson")
	print("Captured five expedition states at /tmp/sushi-v2-dive-*.png")
	quit()

func take(dive: Control, label: String) -> void:
	dive.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/sushi-v2-dive-" + label + ".png")
