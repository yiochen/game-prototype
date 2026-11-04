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
## finger holds the left or right arrow toward gold, lifts whenever the ship
## is lined up (it runs straight), clips a rock wall once for the damage
## flash, then pauses and resumes.
##
## Issue #22 (default): after the dive the video cuts ahead to each feature in
## route order: a lateral current field (the finger lets go to show the push),
## the portal and the automatic passage ride back to the main route, then a
## shield pickup that bumps through rock without damage. Pass `--issue21` for
## the original sequence.
const Session = preload("res://scripts/session.gd")
const Book = preload("res://scripts/expedition/expedition_book.gd")
const TOUCH := 21

var app
var destination := ""
var frame_index := 0
var finger := Vector2.ZERO
var finger_down := false
var marker: Control
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

func tap(control: Control) -> void:
	var at := control.get_global_rect().get_center()
	touch(at, true); await hold(.15); touch(at, false); await hold(.1)

func revealed_session(seed_value: int):
	var s = Session.new_session(seed_value, {"starting_coins": 10000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	return s

## Lateral target: stay clear of rock ahead and lean toward uncollected gold,
## detouring onto an unspent portal or shield just ahead.
func target(prefer_wall := false) -> float:
	var run = Book.snapshot(app.session._state).run
	if run == null or run.passage != null: return 5.5
	var path := Book.run_route(run)
	for i in range(path.portals.size()):
		var portal: Dictionary = path.portals[i]
		if not i in run.portals_used and float(run.y) - float(portal.y) > 0.0 and float(run.y) - float(portal.y) < 6.0: return float(portal.x)
	for i in range(path.shields.size()):
		var b: Vector2 = path.shields[i]
		if not i in run.shields_taken and float(run.y) - b.y > 0.0 and float(run.y) - b.y < 4.0: return b.x
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

## Hold the arrow toward the target column; lift to brake once close or lined up.
func steer(prefer_wall := false) -> void:
	var ui = app.expedition_ui
	if ui.mode != "travel" or ui.overlay != "none": return
	var run = Book.snapshot(app.session._state).run
	# The passage current steers: keep the finger off the arrows.
	if run.passage != null or ui.view.transitioning():
		if finger_down: touch(finger, false)
		return
	var error := target(prefer_wall) - float(run.x)
	var rules: Dictionary = Book.definition()
	var want := 0.0
	if prefer_wall or absf(error) > .12:
		# Braking-aware: let go while faster than can stop at the target.
		var stop_speed := sqrt(2.0 * float(rules.lateral_acceleration) * absf(error)) * .85
		if prefer_wall or signf(float(run.vx)) != signf(error) or absf(float(run.vx)) < stop_speed: want = signf(error)
	var side := 0.0 if not finger_down else (-1.0 if finger.x < ui.area.get_center().x else 1.0)
	if want == side: return
	if finger_down: touch(finger, false)
	if want != 0.0: touch(ui.view.get_global_transform() * ui.view._button_rect(want).get_center(), true)

## Cut ahead (a test-only move of the saved run) to `rows` before `y`.
func cut_to(ui, y: float, x: float) -> void:
	if finger_down: touch(finger, false)
	var run: Dictionary = app.session._state.expedition.run
	run.y = y; run.x = x; run.vx = 0.0; run.steer = 0.0; run.protection = 0.0
	ui.update({"expedition": Book.snapshot(app.session._state)}, 0.0)
	ui.view.snap_camera()
	await hold(.1)

func features(ui) -> void:
	var path := Book.run_route(Book.snapshot(app.session._state).run)
	await hold(4.0, steer)
	# 1. A current field: let go inside it and the push carries the ship sideways.
	var crossing: Dictionary = path.spans.filter(func(span): return span.kind == "current")[0]
	await cut_to(ui, float(crossing.y1) + 1.0, Book._centre_of(path.rows[int(crossing.y1)]))
	var x0 := float(Book.snapshot(app.session._state).run.x)
	await hold(3.0)
	check(absf(float(Book.snapshot(app.session._state).run.x) - x0) > 1.0, "a released ship drifts with the current")
	await hold(3.5, steer)
	# 2. The portal: steer onto it, ride the passage, rejoin the main route.
	var portal: Dictionary = path.portals[0]
	await cut_to(ui, float(portal.y) + 7.0, Book._centre_of(path.rows[int(portal.y) + 7]))
	var guard := 0
	while Book.snapshot(app.session._state).run.passage == null and guard < 300:
		steer(); await frame(); guard += 1
	check(guard < 300, "steering onto the portal enters the passage")
	guard = 0
	while (Book.snapshot(app.session._state).run.passage != null or ui.view.transitioning()) and guard < 600:
		steer(); await frame(); guard += 1
	check(guard < 600 and int(Book.snapshot(app.session._state).run.passage_pickups) > 0, "the passage ride collects salvage and rejoins the route")
	await hold(3.0, steer)
	# 3. The shield: pick it up, then plough through rock without damage.
	var shield: Vector2 = path.shields[0]
	await cut_to(ui, shield.y + 5.0, shield.x)
	guard = 0
	while float(Book.snapshot(app.session._state).run.shield) <= 0.0 and guard < 200:
		steer(); await frame(); guard += 1
	var hull := float(Book.snapshot(app.session._state).run.hull)
	await hold(1.2)
	await hold(1.8, func(): steer(true))
	check(float(Book.snapshot(app.session._state).run.hull) == hull, "the shield blocks collision damage")
	await hold(3.5, steer)
	if finger_down: touch(finger, false)
	await tap(ui.pause_button)
	await hold(1.0)
	await tap(ui.cards.paused.buttons[1])
	await hold(3.3)
	await hold(2.0, steer)
	if finger_down: touch(finger, false)
	await hold(.3)

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
	# Press the water: the dive starts there and runs straight until an arrow is held.
	touch(Vector2(ui.area.get_center().x, ui.area.end.y - 150), true)
	await hold(.1)
	check(ui.mode == "travel", "pressing the water starts the dive")
	touch(finger, false)
	if not OS.get_cmdline_user_args().has("--issue21"):
		await features(ui)
		print("Recorded %d frames, %d failures" % [frame_index, failures.size()])
		quit(1 if failures.size() else 0)
		return
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
