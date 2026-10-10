extends SceneTree
## Use tools/test_native.py to run this suite in an isolated user-data directory.
## Input travels through the actual viewport and native Control dispatch.

const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
const SAVE_FILES := ["session.json", "session.backup.json", "session.pending.json", "session.backup.pending.json"]
const REQUIRED_SPRITES := [
	"chef_up", "chef_down", "chef_hold_up", "guest_a_down",
	"guest_b_seated", "stool", "salmon_nigiri", "belt_horizontal",
	"belt_endpoint", "floor_wood", "plant", "lantern", "barrel", "crate", "entrance",
]
var checks := 0
var failures: Array[String] = []

func _init() -> void:
	call_deferred("_run")

func _run() -> void:
	# This suite deliberately damages saves to verify recovery. Never allow its
	# fault injection to run against an ordinary user's restaurant directory.
	if not str(ProjectSettings.get_setting("application/config/custom_user_dir_name", "")).begins_with("SushiLoopTicketsTest-"):
		printerr("Run native_app_tests.gd through tools/test_native.py for isolated save storage.")
		quit(1)
		return
	# Headless Godot ignores its --resolution option and starts with a 64px
	# window. The isolated runner supplies the same physical size explicitly.
	var requested_size := OS.get_environment("SUSHI_LOOP_TEST_SIZE").split("x")
	if requested_size.size() == 2 and requested_size[0].is_valid_int() and requested_size[1].is_valid_int():
		root.size = Vector2i(int(requested_size[0]), int(requested_size[1]))
	var app = APP.instantiate()
	app.simulation_enabled = false
	root.add_child(app)
	await _frames()
	print("Native UI viewport: window=%s canvas=%s transform=%s" % [root.size, app.size, app.get_viewport_transform()])
	_expect(not app.session.snapshot().is_empty(), "The actual main scene opens an operating public session")
	var stopped: Dictionary = app.session.snapshot()
	await _frames(4)
	_expect(_same(stopped, app.session.snapshot()), "The opt-in controlled clock prevents frame-driven simulation in tests")
	_test_geometry(app)
	await _test_configured_camera(app)
	await _test_touch_and_hud(app)
	var live_textures := _sprite_signatures(app)
	var renderer_script: Script = app.world.get_script()
	app = await _test_reopen(app)
	app.queue_free()
	await _frames()
	await _test_gallery(live_textures, renderer_script)
	await _test_save_recovery()
	if failures.is_empty():
		print("PASS: %s native app checks" % checks)
		quit(0)
	else:
		for failure in failures:
			printerr("FAIL: " + failure)
		printerr("%s of %s native app checks failed" % [failures.size(), checks])
		quit(1)

func _expect(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures.append(description)

func _frames(count: int = 3) -> void:
	for index in range(count):
		await process_frame

func _test_geometry(app) -> void:
	var portrait: Rect2 = app.world.portrait
	var canvas := Rect2(Vector2.ZERO, app.size)
	_expect(app.size.x > 0 and app.size.y > 0 and app.world.size.is_equal_approx(app.size), "Restaurant renderer fills the current native canvas")
	_expect(canvas.encloses(portrait) and is_equal_approx(portrait.get_center().x, canvas.get_center().x), "Portrait content is centered and contained in phone and wider windows")
	var clip = app.world.get_parent()
	_expect(clip is Control and clip.clip_contents and clip.get_global_rect().is_equal_approx(portrait), "The real parent clips adjoining restaurant floor to exactly the portrait rectangle")
	_expect(portrait.size.x <= portrait.size.y * 9.0 / 16.0 + 0.01, "Wider windows preserve the supported portrait composition")
	var base: Vector2 = app.world.cell_base(0, 0)
	var horizontal: Vector2 = app.world.cell_base(1, 0) - base
	var vertical: Vector2 = app.world.cell_base(0, 1) - base
	_expect(horizontal.is_equal_approx(Vector2(app.world.cell, 0)) and vertical.is_equal_approx(Vector2(0, app.world.cell)), "Actual restaurant cell centers have equal horizontal and vertical pitch")
	var transform: Transform2D = app.get_viewport_transform()
	var physical_horizontal := transform.basis_xform(horizontal)
	var physical_vertical := transform.basis_xform(vertical)
	# Godot rounds an expanded logical viewport to integer dimensions. The two
	# scale axes can consequently differ by a tiny fraction of one screen pixel.
	_expect(absf(physical_horizontal.length() - physical_vertical.length()) < 0.1, "Physical display scaling keeps cells square within subpixel viewport rounding")
	for button in [app.shop, app.edit, app.staff]:
		var rect: Rect2 = button.get_global_rect()
		var physical: Rect2 = transform * rect
		_expect(portrait.encloses(rect), "%s stays inside the portrait play area" % button.text)
		_expect(physical.size.x >= 44.0 and physical.size.y >= 44.0, "%s has a physical touch target of at least 44 pixels" % button.text)
		_expect(not button.accessibility_name.is_empty(), "%s retains a native accessible name" % button.text)
	_expect(app.coin.mouse_filter == Control.MOUSE_FILTER_IGNORE and app.money.mouse_filter == Control.MOUSE_FILTER_IGNORE, "Transparent earnings HUD does not intercept scene touches")
	var all_loaded := true
	var anchored := true
	for key in REQUIRED_SPRITES:
		var texture: Texture2D = app.world.art.get_texture(key)
		if texture == null:
			all_loaded = false
			continue
		var fitted: Rect2 = app.world.art.fit(key, Vector2(160, 230), Vector2(90, 140))
		anchored = anchored and is_equal_approx(fitted.get_center().x, 160.0) and is_equal_approx(fitted.end.y, 230.0)
		anchored = anchored and is_equal_approx(fitted.size.x / fitted.size.y, texture.get_width() / float(texture.get_height()))
	_expect(all_loaded, "Gameplay resolves all required finished chef, guest, food, belt and room sprites")
	_expect(all_loaded and anchored, "Production sprites retain their aspect ratio and bottom-center anchor")

func _test_configured_camera(app) -> void:
	var original: RefCounted = app.session
	app.session = load("res://scripts/session.gd").new_session(41, {"floor": {"viewport_columns": 6}})
	app._refresh()
	app._layout()
	await _frames()
	_expect(is_equal_approx(app.world.cell, (app.world.portrait.size.x - 48.0) / 6.0), "Configured visible column count determines the actual square cell pitch")
	app.session.command({"type": "set_camera", "x": 20.5, "y": 0.0})
	app._refresh()
	var start: Vector2 = app.world.portrait.position + app.world.portrait.size * Vector2(0.8, 0.6)
	var end := start - Vector2(app.world.cell * 2.0, 0)
	await _touch(app, start, true, 8)
	await _drag(app, start, end, 8)
	await _touch(app, end, false, 8)
	_expect(is_equal_approx(float(app.session.snapshot().camera.x), 21.0), "Actual touch panning uses the configured world-minus-visible extent rather than a hard-coded camera limit")
	app.session = original
	app._refresh()
	app._layout()
	app.save_now()
	await _frames()

func _test_touch_and_hud(app) -> void:
	app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
	await _frames()
	var before: Dictionary = app.session.snapshot()
	var hud := _hud_rects(app)
	var area: Rect2 = app.world.portrait
	var start := area.position + Vector2(area.size.x * 0.80, area.size.y * 0.62)
	var finish := start - Vector2(app.world.cell * 2.25, 0)
	await _touch(app, start, true)
	await _drag(app, start, finish)
	await _touch(app, finish, false)
	var moved: Dictionary = app.session.snapshot()
	_expect(float(moved.camera.x) > 1.0 and float(moved.camera.x) < 3.0, "A physical screen gesture pans the restaurant by the expected visible distance")
	_expect(moved.coins == before.coins and moved.elapsed == before.elapsed, "Panning does not alter coins or advance the controlled simulation")
	_expect(_same(hud, _hud_rects(app)), "Coin, reserved earnings area and Shop/Edit/Staff controls remain fixed while the world pans")
	var cancel_start := area.position + Vector2(area.size.x * 0.72, area.size.y * 0.50)
	var cancel_end := cancel_start - Vector2(app.world.cell * 0.7, 0)
	await _touch(app, cancel_start, true, 3)
	await _drag(app, cancel_start, cancel_end, 3)
	await _touch(app, cancel_end, false, 3, true)
	var cancelled: Dictionary = app.session.snapshot()
	await _drag(app, cancel_end, cancel_end - Vector2(app.world.cell * 2.0, 0), 3)
	_expect(_same(cancelled, app.session.snapshot()), "A canceled screen touch releases ownership and ignores later orphaned motion")
	await _touch(app, start, true, 4)
	await _drag(app, start, start + Vector2(app.world.cell * 0.5, 0), 4)
	await _touch(app, start + Vector2(app.world.cell * 0.5, 0), false, 4)
	_expect(float(app.session.snapshot().camera.x) < float(cancelled.camera.x), "A new gesture works immediately after cancellation")
	var before_buttons: Dictionary = app.session.snapshot()
	for button in [app.shop, app.edit, app.staff]:
		var center: Vector2 = button.get_global_rect().get_center()
		await _touch(app, center, true, 5)
		await _touch(app, center, false, 5)
	_expect(_same(before_buttons, app.session.snapshot()), "Unavailable future-feature buttons neither change coins nor pan the restaurant on tap")
	app.session.advance(60.0)
	await _frames()
	_expect(int(app.money.text) == int(app.session.snapshot().coins) and app.session.snapshot().coins > before.coins, "Controlled live service updates the native coin label")
	_expect(_same(hud, _hud_rects(app)), "Changing the coin balance does not shift Shop or the other fixed controls")

func _test_reopen(app):
	app.session.command({"type": "set_camera", "x": 4.25, "y": 0.0})
	app.session.advance(2.023456789)
	await _frames()
	var saved: Dictionary = app.session.snapshot()
	_expect(saved.stats.sales > 0 and not saved.customers.is_empty(), "Native reopen scenario includes credited sales and active customer progress")
	_expect(app.save_now() and app.save_error.is_empty(), "The actual app commits its live session through save_now")
	var uninterrupted: RefCounted = app.session
	app.queue_free()
	await _frames()
	var reopened = APP.instantiate()
	reopened.simulation_enabled = false
	root.add_child(reopened)
	await _frames()
	_expect(_same(saved, reopened.session.snapshot()), "A fresh main scene reopens coins, camera, chef progress, customer positions and belt food unchanged")
	_expect(_same(saved, reopened.world.state) and int(reopened.money.text) == saved.coins, "Restored transient state reaches the real renderer and coin HUD")
	var expected_events: Array = uninterrupted.advance(31.027777777)
	var actual_events: Array = reopened.session.advance(31.027777777)
	await _frames()
	_expect(_same(expected_events, actual_events) and _same(uninterrupted.snapshot(), reopened.session.snapshot()), "Reopened app continuation produces identical future sales, dish identities and visitor progress")
	return reopened

func _test_gallery(live_textures: Dictionary, renderer_script: Script) -> void:
	var gallery = APP.instantiate()
	gallery.simulation_enabled = false
	gallery.show_gallery = true
	root.add_child(gallery)
	await _frames()
	_expect(gallery.world.show_gallery and gallery.world.get_script() == renderer_script, "Shared-component gallery uses the production restaurant renderer")
	var gallery_textures := _sprite_signatures(gallery)
	_expect(live_textures.size() == REQUIRED_SPRITES.size() and _same(live_textures, gallery_textures), "Gameplay and gallery load the same finished sprite sources and atlas regions")
	_expect(gallery.gallery_buttons.size() == 3, "Gallery exposes the native Normal, Pressed and Disabled button states")
	if gallery.gallery_buttons.size() == 3:
		var normal: Button = gallery.gallery_buttons[0]
		var pressed: Button = gallery.gallery_buttons[1]
		var disabled: Button = gallery.gallery_buttons[2]
		_expect(not normal.disabled and not normal.button_pressed and pressed.button_pressed and disabled.disabled, "Review buttons exercise real native control states rather than painted labels")
		_expect(normal.get_theme_stylebox("normal").bg_color != pressed.get_theme_stylebox("pressed").bg_color and normal.get_theme_stylebox("normal").bg_color != disabled.get_theme_stylebox("disabled").bg_color, "Normal, pressed and disabled controls have distinct production styles")
		var fit := true
		for button in gallery.gallery_buttons:
			var physical: Rect2 = gallery.get_viewport_transform() * button.get_global_rect()
			fit = fit and gallery.world.portrait.encloses(button.get_global_rect()) and physical.size.x >= 44.0 and physical.size.y >= 44.0
		_expect(fit, "Gallery button targets remain contained and physically usable at the current window size")
		await _touch(gallery, normal.get_global_rect().get_center(), true, 6)
		_expect(normal.is_pressed(), "Physical screen input presses the actual enabled native gallery button")
		await _touch(gallery, normal.get_global_rect().get_center(), false, 6)
		_expect(not normal.is_pressed(), "Releasing a physical touch restores the native gallery button")
		await _touch(gallery, disabled.get_global_rect().get_center(), true, 7)
		_expect(not disabled.is_pressed(), "The disabled native review button rejects touch activation")
		await _touch(gallery, disabled.get_global_rect().get_center(), false, 7)
	gallery.queue_free()
	await _frames()

func _hud_rects(app) -> Dictionary:
	return {"coin": app.coin.get_global_rect(), "money": app.money.get_global_rect(), "shop": app.shop.get_global_rect(), "edit": app.edit.get_global_rect(), "staff": app.staff.get_global_rect()}

func _test_save_recovery() -> void:
	# Keep one authentic, operating save for the later repair. The second
	# fixture has a valid storage checksum but is not a restorable game session.
	var fixture = Store.new("user://native-recovery-fixture")
	var expected = Session.new_session(480)
	expected.advance(24.023456789)
	expected.command({"type": "set_camera", "x": 2.75, "y": 0.0})
	_expect(fixture.save_session(expected.save_data()), "Recovery fixture serializes a real operating restaurant")
	var repair_bytes := FileAccess.get_file_as_bytes("user://native-recovery-fixture/session.json")
	fixture.save_session({"version": 1, "coins": 999999})
	var invalid_domain_bytes := FileAccess.get_file_as_bytes("user://native-recovery-fixture/session.json")
	_write_bytes("user://session.json", "{truncated restaurant".to_utf8_buffer())
	_write_bytes("user://session.backup.json", invalid_domain_bytes)
	var damaged := _save_bytes()
	var blocked = APP.instantiate()
	# Leave the normal frame clock enabled: save recovery must stop it itself.
	root.add_child(blocked)
	await _frames()
	_expect(blocked.save_blocked and blocked.recovery != null and blocked.recovery.is_visible_in_tree(), "Unreadable primary and domain-invalid backup open the native recovery overlay")
	_expect(_same(damaged, _save_bytes()), "Recovery startup preserves every existing save byte instead of writing a starter restaurant")
	var frozen: Dictionary = blocked.session.snapshot()
	_expect(blocked.advance_time(120.0).is_empty() and not blocked.save_now(), "Blocked recovery refuses controlled advancement and explicit saving")
	await _frames(8)
	_expect(_same(frozen, blocked.session.snapshot()) and _same(damaged, _save_bytes()), "Normal app frames leave the blocked restaurant frozen and save files untouched")
	var retry_center: Vector2 = blocked.recovery_retry.get_global_rect().get_center()
	await _touch(blocked, retry_center, true, 9)
	await _touch(blocked, retry_center, false, 9)
	_expect(blocked.save_blocked and _same(damaged, _save_bytes()), "Retrying still-invalid data retains the recovery overlay and original files")
	# Exercise the same native close notification and teardown used by window
	# closing; activating the Close button would terminate this entire test tree.
	blocked.notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)
	blocked.queue_free()
	await _frames()
	_expect(_same(damaged, _save_bytes()), "Closing a blocked app preserves the invalid files through notification and teardown")
	var retry_app = APP.instantiate()
	retry_app.simulation_enabled = false
	root.add_child(retry_app)
	await _frames()
	_expect(retry_app.save_blocked, "Reopening damaged data continues to require recovery")
	_write_bytes("user://session.json", repair_bytes)
	var before_repair: Dictionary = expected.snapshot()
	retry_center = retry_app.recovery_retry.get_global_rect().get_center()
	await _touch(retry_app, retry_center, true, 10)
	await _touch(retry_app, retry_center, false, 10)
	_expect(not retry_app.save_blocked and retry_app.recovery == null and retry_app.save_error.is_empty(), "The actual native Retry button opens a repaired save and removes recovery")
	_expect(_same(before_repair, retry_app.session.snapshot()) and _same(before_repair, retry_app.world.state), "Repair restores exact coins, camera and meal progress without duplicating earlier sales")
	_expect(retry_app.save_now(), "Successful recovery re-enables ordinary persistence")
	var expected_events: Array = expected.advance(20.017)
	var actual_events: Array = retry_app.advance_time(20.017)
	_expect(_same(expected_events, actual_events) and _same(expected.snapshot(), retry_app.session.snapshot()), "Recovered play continues with the same future sales and transient state as the valid source")
	retry_app.queue_free()
	await _frames()
	# AudioServer releases stopped voices on its mixing thread. Headless frames
	# can run faster than one mixer buffer, so let teardown reach that thread.
	await create_timer(0.1).timeout

func _save_bytes() -> Dictionary:
	var result := {}
	for filename in SAVE_FILES:
		var path: String = "user://".path_join(filename)
		result[filename] = FileAccess.get_file_as_bytes(path) if FileAccess.file_exists(path) else null
	return result

func _write_bytes(path: String, bytes: PackedByteArray) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("Could not create recovery fault fixture: " + path)
		return
	file.store_buffer(bytes)
	file.close()

func _sprite_signatures(app) -> Dictionary:
	var result := {}
	for key in REQUIRED_SPRITES:
		var texture: Texture2D = app.world.art.get_texture(key)
		if texture is AtlasTexture:
			result[key] = {"source": texture.atlas.resource_path, "region": texture.region}
		elif texture != null:
			result[key] = {"source": texture.resource_path, "size": texture.get_size()}
	return result

func _touch(app, local_position: Vector2, down: bool, index: int = 0, cancelled: bool = false) -> void:
	var event := InputEventScreenTouch.new()
	event.index = index
	event.position = app.get_viewport_transform() * local_position
	event.pressed = down
	event.canceled = cancelled
	Input.parse_input_event(event)
	await _frames(2)

func _drag(app, from: Vector2, to: Vector2, index: int = 0) -> void:
	var event := InputEventScreenDrag.new()
	event.index = index
	var transform: Transform2D = app.get_viewport_transform()
	event.position = transform * to
	event.relative = transform.basis_xform(to - from)
	Input.parse_input_event(event)
	await _frames(2)

func _same(a: Variant, b: Variant) -> bool:
	if (a is int or a is float) and (b is int or b is float):
		return absf(float(a) - float(b)) < 0.000000001
	if a is Dictionary and b is Dictionary:
		if a.size() != b.size():
			return false
		for key in a:
			if not b.has(key) or not _same(a[key], b[key]):
				return false
		return true
	if a is Array and b is Array:
		if a.size() != b.size():
			return false
		for index in range(a.size()):
			if not _same(a[index], b[index]):
				return false
		return true
	return a == b
