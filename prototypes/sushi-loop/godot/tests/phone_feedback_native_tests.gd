extends SceneTree
## Phone feedback on 0.20.1: the tea bubble itself is a tap target, the
## Workshop ship keeps its size across tabs, Shop rows never let a long
## description run into the stock line, and tapped goods show no square outline.
##   python3 tools/test_native.py --script tests/phone_feedback_native_tests.gd --visible --resolution 780x1688 --output <dir>
const Session = preload("res://scripts/session.gd")
const APP = preload("res://main.tscn")
var app
var checks := 0
var failures: Array[String] = []
var output := ""

func _initialize() -> void: call_deferred("run")

func check(value: bool, message: String) -> void:
	checks += 1
	if not value: failures.append(message); printerr("FAIL: " + message)

func frames(n := 3) -> void:
	for i in range(n): await process_frame

func settle() -> void:
	await frames(2)
	var guard := 0
	while app.transition.busy and guard < 600:
		await process_frame; guard += 1

func touch(at: Vector2, pressed: bool) -> void:
	var event := InputEventScreenTouch.new(); event.index = 21; event.position = app.get_viewport_transform() * at; event.pressed = pressed
	Input.parse_input_event(event); await frames()

func capture(name: String) -> void:
	if output.is_empty() or DisplayServer.get_name() == "headless": return
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(output.path_join(name + ".png"))

func run() -> void:
	output = OS.get_environment("SUSHI_LOOP_CAPTURE_OUTPUT")
	if not output.is_empty(): DirAccess.make_dir_recursive_absolute(output)
	var dims := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if dims.size() == 2 and DisplayServer.get_name() == "headless": root.size = Vector2i(int(dims[0]), int(dims[1]))
	app = APP.instantiate(); root.add_child(app)
	await process_frame
	app.performance_overlay.visible = false

	# Tea: a real touch on the bubble (above the guest's head) opens the pour.
	app.session = Session.new_session(41, {"starting_coins": 2000})
	app._refresh()
	for step in range(900): app.advance_time(0.05, false)
	var seated: Array = app.session._customers().filter(func(c): return c.phase == "waiting" and c.first_dish_received)
	for customer in app.session._customers():
		if customer.tea_phase in ["requested", "pouring"]: customer.tea_phase = "skipped"
	check(not seated.is_empty(), "a seated guest to ask for tea")
	var asking: Dictionary = seated[0]
	asking.preference_phase = "complete"; asking.tea_phase = "requested"; asking.tea_cup = "flask"; asking.tea_elapsed = 2.5
	app.simulation_enabled = false
	app._layout(); app._refresh(); await frames(4)
	var bubble: Vector2 = app.world.tea_bubble_centre(asking)
	check(app.world.tip_target_at(bubble).get("kind", "") == "tea", "the bubble centre is a tea target")
	await capture("01-tea-bubble")
	var screen: Vector2 = app.world.get_global_transform() * bubble
	await touch(screen, true); await touch(screen, false); await frames(6)
	check(app.tea_ui.visible, "tapping the bubble itself opens the pour sheet")
	app.tea_ui.cancel(); await frames(4)

	# Workshop: the ship keeps its size and place when the taller Power-ups tray opens.
	app.session = Session.new_session(19, {"starting_coins": 9180})
	for identity in ["armchair-west", "dock-access", "trash-8-5", "trash-9-4", "trash-10-6", "trash-10-8", "trash-10-9"]:
		app.session.command({"type": "clear_trash", "id": identity})
	app.session.command({"type": "reveal_dock"})
	app.session._state.expedition.salvage = 300
	app._refresh(); app._layout(); await frames()
	app._open_landmark("Workshop"); await settle()
	var ship_a: float = app.workshop_ui.ship.hull_px
	var cradle_a: Rect2 = app.workshop_ui.cradle.get_global_rect()
	var tray_a: float = app.workshop_ui.tray.get_global_rect().position.y
	await capture("02-workshop-equipment")
	app.workshop_ui.select_group("powerup"); await frames()
	check(is_equal_approx(app.workshop_ui.ship.hull_px, ship_a) and app.workshop_ui.cradle.get_global_rect().is_equal_approx(cradle_a), "switching tabs keeps the ship's size and place")
	check(app.workshop_ui.tray.get_global_rect().position.y <= tray_a + 0.5, "the Power-ups tray is never shorter, and grows over the floor instead of moving the ship")
	await capture("03-workshop-powerups")
	app.workshop_ui.leave(); await settle()

	# Shop: the sold-out tip jar's wrapped description stays clear of "Sold out".
	app.session._state.coins = 5000
	app._refresh()
	app._editor_command({"type": "set_mode", "mode": "edit"})
	app._refresh(); app._layout(); await frames()
	var bought: Dictionary = app.session.command({"type": "shop_purchase", "offer_id": "tip-jar", "expected_sequence": app.session.snapshot().shop.purchase_sequence})
	check(bought.get("ok", false), "bought the tip jar: %s" % bought)
	app.shop_ui.open(app.session.snapshot())
	app._layout(); await frames(4)
	var shop = app.shop_ui
	var jar: Dictionary = shop.rows.get("tip-jar", {})
	check(not jar.is_empty(), "the Shop lists the tip jar")
	if not jar.is_empty():
		var described: Rect2 = jar.description.get_global_rect()
		var lines: int = jar.description.get_line_count()
		var text_bottom: float = described.position.y + lines * jar.description.get_line_height()
		check(text_bottom <= jar.stock.get_global_rect().position.y + 1.0, "the description ends above the stock line (%d lines)" % lines)
		shop.catalog.scroll_vertical = int(shop.catalog.get_v_scroll_bar().max_value); await frames(4)
		await capture("04-shop-tip-jar-sold-out")
	shop.dismiss(); await frames()

	# Edit dock: pressed/focused goods draw no square ink outline.
	app._editor_command({"type": "editor_layer", "layer": "layout"})
	app._refresh(); app._layout(); await frames()
	var card: Button = app.editor_ui.cards[0]
	var outline: StyleBox = card.get_theme_stylebox("pressed")
	check(outline is StyleBoxEmpty, "Layout goods have no pressed outline")
	var ring: StyleBox = card.get_theme_stylebox("focus")
	check(ring is StyleBoxFlat and (ring as StyleBoxFlat).corner_radius_top_left > 0, "focus uses the rounded shared ring")
	var at: Vector2 = card.get_global_rect().get_center()
	await touch(at, true); await frames(2)
	await capture("05-goods-held")
	await touch(at, false); await frames(4)
	await capture("06-goods-tapped")
	outline = null; ring = null  # release StyleBox resources before quit

	# Let UI click cues finish so no audio stream is still playing at exit.
	await create_timer(0.8).timeout
	app.queue_free(); await frames(4)
	print("Phone feedback native: %d checks, %d failures" % [checks, failures.size()])
	quit(1 if failures.size() else 0)
