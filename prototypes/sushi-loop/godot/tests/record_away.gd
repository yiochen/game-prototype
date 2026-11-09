extends SceneTree
## Issue #29 review video: the real game with injected touches at a fixed frame
## rate. A live restaurant dives, the restaurant freezes, the dive returns and
## credits its time away once (cue + rolling balance), Edit/Shop red dot for
## the rotated stock, then a closed app reopens and credits its absence.
## Long absences are produced by moving the saved interval start back, a
## test-only clock skip that the caption announces.
##
##   python3 tools/test_native.py --script tests/record_away.gd --visible --fixed-fps 30 \
##       --resolution 390x844 --timeout 900 --output <frames-dir>
##   ffmpeg -framerate 30 -i <frames-dir>/frame-%05d.png -c:v libx264 -pix_fmt yuv420p video.mp4
const Session = preload("res://scripts/session.gd")
const TOUCH := 29

var app
var destination := ""
var frame_index := 0
var finger := Vector2.ZERO
var finger_down := false
var marker: Control
var caption: Label
var failures: Array[String] = []
## The restaurant as the newest app instance loaded it, before its first frame.
var opened_view: Variant

class Marker extends Control:
	var owner_script
	func _draw() -> void:
		if owner_script.finger_down:
			draw_circle(owner_script.finger, 26, Color(1, 1, 1, .28))
			draw_arc(owner_script.finger, 26, 0, TAU, 40, Color(1, 1, 1, .85), 3, true)

func _initialize() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	if not value: failures.append(message); printerr("FAIL: " + message)
	else: print("ok: " + message)

func frame() -> void:
	marker.queue_redraw()
	await process_frame
	await RenderingServer.frame_post_draw
	if destination.is_empty(): return
	root.get_texture().get_image().save_png(destination.path_join("frame-%05d.png" % frame_index))
	frame_index += 1

func hold(seconds: float) -> void:
	for i in range(int(round(seconds * 30))): await frame()

func say(text: String) -> void:
	caption.text = text
	caption.visible = not text.is_empty()

func touch(at: Vector2, down: bool) -> void:
	var event := InputEventScreenTouch.new(); event.index = TOUCH; event.position = app.get_viewport_transform() * at; event.pressed = down
	finger = at; finger_down = down; Input.parse_input_event(event)

func tap(control: Control) -> void:
	var at := control.get_global_rect().get_center()
	touch(at, true); await hold(.15); touch(at, false); await hold(.1)

## Test-only clock skip: the saved time-away history moves `seconds` earlier.
func skip_clock(seconds: float) -> void:
	var away: Dictionary = app.session._state.away
	for field in ["started", "credited_through"]:
		if away[field] != null: away[field] = float(away[field]) - seconds

func restaurant() -> Variant:
	var view: Dictionary = app.session.snapshot()
	return JSON.parse_string(JSON.stringify({"customers": view.customers, "objects": view.objects}))

func open_app() -> void:
	app = load("res://main.tscn").instantiate()
	root.add_child(app)
	root.move_child(app, 0)
	opened_view = restaurant()
	await process_frame
	if app.performance_overlay != null: app.performance_overlay.hide()

func run() -> void:
	destination = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not destination.is_empty(): DirAccess.make_dir_recursive_absolute(destination)
	var layer := CanvasLayer.new(); layer.layer = 120; root.add_child(layer)
	marker = Marker.new(); marker.owner_script = self; marker.mouse_filter = Control.MOUSE_FILTER_IGNORE
	marker.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT); layer.add_child(marker)
	caption = Label.new(); caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	caption.add_theme_font_size_override("font_size", 19); caption.add_theme_color_override("font_color", Color.WHITE)
	var backing := StyleBoxFlat.new(); backing.bg_color = Color(0.05, 0.08, 0.14, 0.82); backing.set_corner_radius_all(10); backing.content_margin_left = 10; backing.content_margin_right = 10; backing.content_margin_top = 6; backing.content_margin_bottom = 6
	caption.add_theme_stylebox_override("normal", backing)
	caption.anchor_left = 0; caption.anchor_right = 1; caption.anchor_top = 1; caption.anchor_bottom = 1
	caption.offset_left = 12; caption.offset_right = -12; caption.offset_top = -132; caption.offset_bottom = -92
	layer.add_child(caption)
	await open_app()
	# A revealed dock with a bought plant, so the rotation visibly restocks it.
	var s = Session.new_session(29, {"starting_coins": 4000})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]: s.command({"type": "clear_trash", "id": identity})
	s.command({"type": "reveal_dock"})
	s.command({"type": "set_mode", "mode": "edit"})
	s.command({"type": "shop_purchase", "offer_id": "barrel", "expected_sequence": s.snapshot().shop.purchase_sequence})
	s.command({"type": "set_mode", "mode": "live"})
	for i in range(400): s.advance(0.1)
	app.session = s; app._refresh(); app._layout()
	app.save_now()
	say("Restaurant running live")
	await hold(2.5)
	# ---- Expedition: Start freezes the restaurant.
	var ui = app.expedition_ui
	finger = app._landmark_point("Submarine"); finger_down = true; await hold(.15); finger_down = false
	app._open_landmark("Submarine")
	say("Tap the submarine, then touch to dive")
	await hold(2.6)
	var frozen: Variant = restaurant()
	var coins: int = app.session.snapshot().coins
	touch(Vector2(ui.area.get_center().x, ui.area.end.y - 150), true); await hold(.1); touch(finger, false)
	check(ui.mode == "travel", "pressing the water starts the dive")
	check(app.session._state.away.started != null, "Start opens the time-away interval")
	say("Diving: the restaurant is frozen (no ticks, no sound)")
	await hold(3.0)
	check(restaurant() == frozen, "restaurant did not tick during the dive")
	# Test-only clock skip: the dive began 20 minutes ago.
	skip_clock(1200.0)
	var expected: int = app.session.away_estimate(1200.0 + 4.0)
	say("Clock skip (test only): the dive took 20 minutes")
	await hold(1.6)
	await tap(ui.pause_button)
	await hold(.6)
	await tap(ui.cards.paused.buttons[0])
	check(ui.mode == "results", "Give up shows the results")
	say("Results: the restaurant stays frozen behind them")
	await hold(2.0)
	check(restaurant() == frozen, "restaurant still frozen on results")
	check(app.session.snapshot().shop.fresh, "the ended run rotated Shop stock")
	var returned := {}
	ui.returned_to_restaurant.connect(func(): returned.view = restaurant(), CONNECT_ONE_SHOT)
	await tap(ui.cards.results.buttons[0])
	say("Back at the bar: time-away income credited once")
	await hold(1.2)
	var credited: int = app.session.snapshot().coins - coins
	check(credited > 0 and absi(credited - expected) <= expected / 20 + 2, "return credited the 20-minute estimate once (%d vs %d)" % [credited, expected])
	check(app.away_notice.visible and app.away_notice.label.text == "+%d while away" % credited, "while-away cue shows the credit")
	check(returned.get("view") == frozen, "the restored restaurant is exactly the one left at Start")
	await hold(4.0)
	# ---- Rotated stock: Edit and Shop show a red dot until Shop is entered.
	say("New Shop stock: red dot on Edit")
	check(app.edit_dot.visible, "Edit carries the new-stock dot")
	await hold(1.6)
	await tap(app.edit)
	say("…and on the Shop action")
	check(app.shop_dot.is_visible_in_tree(), "Shop action carries the dot in Edit")
	await hold(1.8)
	await tap(app.editor_ui.shop)
	say("Entering Shop clears it; the barrel is restocked")
	await hold(2.8)
	check(not app.session.snapshot().shop.fresh, "entering Shop clears the dot")
	await tap(app.shop_ui.close_button)
	await hold(1.0)
	check(not app.shop_dot.is_visible_in_tree(), "dot gone after Shop")
	await tap(app.editor_ui.live)
	await hold(1.2)
	# ---- Close the app, reopen two hours later.
	say("Close the app…")
	await hold(1.2)
	var before_close: int = app.session.snapshot().coins
	app._begin_away(); app.save_now()
	skip_clock(7200.0)
	app.save_now()
	var closed: Variant = restaurant()
	var reopen_expected: int = app.session.away_estimate(7200.0)
	app.queue_free(); await process_frame
	say("…reopen 2 hours later (clock skip, test only)")
	await hold(1.0)
	await open_app()
	check(opened_view == closed, "reopen restores the saved restaurant without fast-forwarding")
	var reopened: int = app.session.snapshot().coins - before_close
	check(reopened > 0 and absi(reopened - reopen_expected) <= reopen_expected / 50 + 2, "reopen credited the absence once (%d vs %d)" % [reopened, reopen_expected])
	say("Reopen: credited automatically, no Claim step")
	await hold(4.5)
	say("")
	await hold(1.0)
	print("Recorded %d frames, %d failures" % [frame_index, failures.size()])
	quit(1 if failures.size() else 0)
