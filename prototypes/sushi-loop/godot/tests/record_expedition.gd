extends SceneTree
## Issue #21 review video: drives the real game with injected touches at a
## fixed frame rate and writes every rendered frame to the output folder.
##
##   python3 tools/test_native.py --script tests/record_expedition.gd --visible --fixed-fps 30 \
##       --resolution 390x844 --timeout 900 --output <frames-dir>
##   ffmpeg -framerate 30 -i <frames-dir>/frame-%05d.png -c:v libx264 -pix_fmt yuv420p video.mp4
##
## A translucent ring marks the simulated finger. The ship cruises the launch
## lead-in on the preparation screen; pressing the water starts the dive. The
## finger works the joystick toward gold, lifts whenever the ship is lined up
## (it runs straight), clips a rock wall once for the damage flash, then
## pauses and resumes.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const TOUCH := 21

var app
var destination := ""
var frame_index := 0
var finger := Vector2.ZERO
var finger_down := false
var marker: Control
var press_at := Vector2.ZERO
var failures: Array[String] = []

class Marker extends Control:
	var owner_script
	func _draw() -> void:
		if owner_script.finger_down:
			draw_circle(owner_script.finger, 26, Color(1, 1, 1, .28))
			draw_arc(owner_script.finger, 26, 0, TAU, 40, Color(1, 1, 1, .85), 3, true)

func _initialize() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value: failures.append(message); printerr("FAIL: " + message)

func frame() -> void:
	marker.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	if destination.is_empty(): return
	root.get_texture().get_image().save_png(destination.path_join("frame-%05d.png" % frame_index))
	frame_index += 1

func hold(seconds: float, each: Callable = Callable()) -> void:
	for i in range(int(round(seconds * 30))):
		if each.is_valid(): each.call()
		await frame()

func touch(at: Vector2, down: bool) -> void:
	var event := InputEventScreenTouch.new(); event.index = TOUCH; event.position = app.get_viewport_transform() * at; event.pressed = down
	finger = at; finger_down = down; Input.parse_input_event(event)

func drag(at: Vector2) -> void:
	var event := InputEventScreenDrag.new(); event.index = TOUCH; event.position = app.get_viewport_transform() * at
	event.relative = at - finger; finger = at; Input.parse_input_event(event)

func tap(control: Control) -> void:
	var at := control.get_global_rect().get_center()
	touch(at, true); await hold(.15); touch(at, false); await hold(.1)

func revealed_session(seed_value: int):
	var s = Session.new_session(seed_value, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	return s

## Lateral target: stay clear of rock ahead and lean toward uncollected gold.
func target(prefer_wall := false) -> float:
	var run = Book.snapshot(app.session._state).run
	if run == null: return 5.5
	var rows: Array = Book.route(int(run.seed)).rows
	var collected := {}
	for i in run.collected: collected[int(i)] = true
	var pickups: Array = app.expedition_ui.view.scene.get("pickups", [])
	var best := float(run.x); var best_score := INF
	for i in range(1, 22):
		var x := i * .5
		var score := absf(x - float(run.x)) * .02
		for ahead in [0.0, .3, .6, 1.0, 1.4, 2.0]:
			if Book._overlaps(rows, x, float(run.y) - ahead, Vector2(.32, .44)): score += (-6.0 if prefer_wall and ahead < .7 else 10.0) / (1.0 + ahead)
		for j in range(pickups.size()):
			var p: Dictionary = pickups[j]
			var dy := float(run.y) - float(p.y)
			if collected.has(j) or dy < .2 or dy > 3.5: continue
			if absf(float(p.x) - x) < .45: score -= 2.5 / (1.0 + dy)
		if score < best_score: best_score = score; best = x
	return best

## Work the stick: push toward the target column, lift once lined up.
func steer(prefer_wall := false) -> void:
	var ui = app.expedition_ui
	if ui.mode != "travel" or ui.overlay != "none": return
	var run = Book.snapshot(app.session._state).run
	var error := target(prefer_wall) - float(run.x)
	if not finger_down:
		if absf(error) > .35 or prefer_wall: touch(press_at, true)
		return
	if absf(error) < .12 and absf(float(run.vx)) < .5 and not prefer_wall:
		touch(finger, false); return
	# Braking-aware: never more sideways speed than can stop at the target.
	var rules: Dictionary = Book.definition()
	var stick := signf(error) * minf(1.0, sqrt(2.0 * float(rules.lateral_acceleration) * absf(error)) * .85 / float(rules.lateral_columns_per_second))
	var reach: float = ui.view._reach()
	var offset := 0.0 if absf(stick) < .05 else signf(stick) * (reach * .12 + absf(stick) * reach * .88)
	var at := Vector2(ui.view._drag_anchor + offset, finger.y)
	if absf(at.x - finger.x) > .5: drag(at)

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	app = load("res://main.tscn").instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	var layer := CanvasLayer.new(); layer.layer = 120; root.add_child(layer)
	marker = Marker.new(); marker.owner_script = self; marker.mouse_filter = Control.MOUSE_FILTER_IGNORE
	marker.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); layer.add_child(marker)
	await process_frame
	app.session = revealed_session(21); app._refresh(); app._layout()
	if app.performance_overlay != null: app.performance_overlay.hide()
	var ui = app.expedition_ui
	await hold(1.0)
	app._open_landmark("Submarine")
	check(ui.mode == "prep", "dock opens the on-screen preparation")
	await hold(4.5)
	check(ui._prep_y < float(Book.launch(ui._prep_seed).bottom) - 3.0, "the ship cruises the launch lead-in before Start")
	# Press the water: the dive starts there and the same touch becomes the stick.
	press_at = Vector2(ui.area.get_center().x, ui.area.end.y - 150)
	touch(press_at, true)
	await hold(.1)
	check(ui.mode == "travel", "pressing the water starts the dive")
	await hold(13.0, steer)
	# Clip the canyon wall once for the damage flash, then recover.
	var hull := float(Book.snapshot(app.session._state).run.hull_fraction)
	var guard := 0
	while ui.mode == "travel" and float(Book.snapshot(app.session._state).run.hull_fraction) >= hull and guard < 120:
		steer(true); await frame(); guard += 1
	check(guard < 120, "steering into rock shows an impact")
	await hold(4.0, steer)
	touch(finger, false); await hold(.3)
	await tap(ui.pause_button)
	check(ui.overlay == "paused", "Pause opens")
	await hold(1.2)
	await tap(ui.cards.paused.buttons[1])
	await hold(3.3)
	await hold(4.0, steer)
	touch(finger, false); await hold(.3)
	print("Recorded %d frames, %d failures" % [frame_index, failures.size()])
	quit(1 if failures.size() else 0)
