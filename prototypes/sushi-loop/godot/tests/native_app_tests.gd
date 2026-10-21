extends SceneTree
## Use tools/test_native.py to run this suite in an isolated user-data directory.
## Input travels through the actual viewport and native Control dispatch.

const APP = preload("res://main.tscn")
const Session = preload("res://scripts/session.gd")
const Store = preload("res://scripts/save_store.gd")
const SAVE_FILES := ["session.json", "session.backup.json", "session.pending.json", "session.backup.pending.json"]
const REQUIRED_SPRITES := [
	"chef-lena", "chef-omar", "chef-blackboard", "customer-rosa", "customer-ellis",
	"customer-samir", "customer-june", "stool-wood", "dish-salmon", "dish-cucumber",
	"bubble-preference", "bubble-happy",
	"belt-straight-e", "belt-start-e", "belt-end-e", "floor-cream",
	"plant-angular", "lantern-gold", "barrel-wood", "crate-wood", "backdrop-entrance", "backdrop-wall",
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
	_test_camera_clearance(app)
	_test_skin(app)
	await _test_configured_camera(app)
	await _test_touch_and_hud(app)
	await _test_editor(app)
	_test_active_clock_and_resume(app)
	await _test_reaction_restore(app)
	var live_textures := _sprite_signatures(app)
	var renderer_script: Script = app.world.get_script()
	app = await _test_reopen(app)
	app.queue_free()
	await _frames()
	await _test_gallery(live_textures, renderer_script)
	await _test_editor_gallery()
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

func _skin_source(surface: StyleBox) -> Array:
	if surface is StyleBoxFlat or surface is StyleBoxTexture or surface is StyleBoxEmpty: return []
	return [surface.texture.resource_path, surface.region]

func _button_surface(button: Button) -> StyleBox:
	return button.get_meta("visual_surface").get_theme_stylebox("panel") if button.has_meta("visual_surface") else button.get_theme_stylebox("normal")

func _skin_calibrated(surface: StyleBox, skin, unit: float) -> bool:
	if _skin_source(surface).is_empty(): return false
	for raw in skin.manifest.styles.values():
		var candidates: Array = [raw]
		for treatment in raw.get("states", {}).values():
			if treatment is Dictionary:
				var variant: Dictionary = raw.duplicate(true)
				variant.merge(treatment, true)
				candidates.append(variant)
		for entry in candidates:
			var source: Array = entry.region
			if not surface.region.is_equal_approx(Rect2(float(source[0]), float(source[1]), float(source[2]), float(source[3]))): continue
			var matches := true
			for side in [SIDE_LEFT, SIDE_TOP, SIDE_RIGHT, SIDE_BOTTOM]:
				matches = matches and is_equal_approx(surface.get_margin(side), float(entry.content[side]) * unit)
				matches = matches and is_equal_approx(float(surface.edges[side]), float(entry.edge[side]) * unit)
			if matches: return true
	return false

func _test_skin(app) -> void:
	# Exercise every material in its real screen role, including passive B
	# containers. Fixed corners and content insets follow their manifest roles.
	var editor = app.editor_ui
	var unit: float = app.world.portrait.size.x / 720.0
	var surfaces: Array = [_button_surface(app.shop), _button_surface(app.edit), _button_surface(app.staff), editor.live.get_meta("visual_surface").get_theme_stylebox("panel"), editor.tray.get_theme_stylebox("panel"), editor.context_bubble.get_theme_stylebox("panel"), editor.inspection_panel.get_theme_stylebox("panel"), editor.inspection_preview_panel.get_theme_stylebox("panel"), editor.rejection.get_theme_stylebox("normal"), editor.category_rod.get_theme_stylebox("panel"), editor.bottom_dock.get_theme_stylebox("panel")]
	surfaces.append(app.coin_panel.get_theme_stylebox("panel"))
	surfaces.append(app.editing_panel.get_theme_stylebox("panel"))
	var generated := true
	var calibrated := true
	for surface in surfaces:
		generated = generated and not _skin_source(surface).is_empty()
		calibrated = calibrated and _skin_calibrated(surface, editor.skin, unit)
	_expect(generated, "Every rendered HUD control, hanging rod, bottom dock, drawer, context capsule, profile well, modal and toast uses the coordinated generated B family")
	_expect(calibrated, "Generated surfaces retain their documented fixed corner edges and content insets at the actual viewport scale")
	_expect(_skin_source(surfaces[0]) == _skin_source(editor.skin.style("control-wood", unit, "disabled")) and _skin_source(surfaces[1]) == _skin_source(editor.skin.style("control-wood", unit)) and _skin_source(surfaces[2]) == _skin_source(editor.skin.style("control-wood", unit, "disabled")), "Shop, Edit and Staff share the neutral ceramic family with its generated disabled treatment")
	_expect(_skin_source(editor.live.get_meta("visual_surface").get_theme_stylebox("panel")) != _skin_source(_button_surface(app.edit)), "Live has the distinct generated vermilion primary surface")
	_expect(editor.previous.size.is_equal_approx(editor.next.size), "Both inventory pagers keep matching undistorted touch targets")
	_expect(_skin_source(editor.category_rod.get_theme_stylebox("panel")) == _skin_source(editor.skin.style("noren-rod", unit)) and _skin_source(editor.bottom_dock.get_theme_stylebox("panel")) == _skin_source(editor.skin.style("noren-dock", unit)), "The shared rod and bottom dock render their dedicated generated materials")
	_expect(app.coin.stretch_mode == TextureRect.STRETCH_KEEP_ASPECT_CENTERED and app.coin.texture is AtlasTexture, "The generated coin preserves its aspect ratio in the transparent HUD")
	var full_pill_minimums := true
	for role in ["control-wood", "control-pressed", "control-green", "control-green-pressed", "control-slate", "toast-error", "context-bubble", "coin-panel"]:
		for treatment in ["normal", "pressed", "disabled"]:
			full_pill_minimums = full_pill_minimums and editor.skin.style(role, unit, treatment).get_minimum_size().y >= 100 * unit - 0.01
	_expect(full_pill_minimums, "Every rounded pill material enforces a 100-unit minimum height in normal, pressed and disabled states")
	var full_pill_frames := true
	for control in [app.coin_panel, app.editing_panel, editor.live.get_meta("visual_surface"), editor.shop.get_meta("visual_surface"), editor.inspection_close.get_meta("visual_surface")]:
		full_pill_frames = full_pill_frames and control.size.y >= 100 * unit - 0.01
	for button in [app.shop, app.edit, app.staff, editor.live, editor.shop, editor.inspection_close]:
		full_pill_frames = full_pill_frames and button.size.y >= 100 * unit - 0.01
	_expect(full_pill_frames, "Actual pill frames and native button targets retain the full rounded ends instead of compressing below their material minimum")
	var refuses_flattening := true
	for control in [app.coin_panel, app.editing_panel, editor.live.get_meta("visual_surface"), editor.shop.get_meta("visual_surface"), editor.inspection_close.get_meta("visual_surface"), app.shop, app.edit, app.staff, editor.live, editor.shop, editor.inspection_close]:
		var original_size: Vector2 = control.size
		control.size = Vector2(original_size.x, 40 * unit)
		refuses_flattening = refuses_flattening and control.size.y >= 100 * unit - 0.01
		control.size = original_size
	_expect(refuses_flattening, "Rendered pill panels and native targets reject a future undersized assignment that would flatten their rounded ends")

func _test_geometry(app) -> void:
	var portrait: Rect2 = app.world.portrait
	var canvas := Rect2(Vector2.ZERO, app.size)
	_expect(app.size.x > 0 and app.size.y > 0 and app.world.size.is_equal_approx(app.size), "Restaurant renderer fills the current native canvas")
	_expect(canvas.encloses(portrait) and is_equal_approx(portrait.get_center().x, canvas.get_center().x), "Portrait content is centered and contained in phone and wider windows")
	var clip = app.world.get_parent()
	_expect(clip is Control and clip.clip_contents and clip.get_global_rect().is_equal_approx(portrait), "The real parent clips adjoining restaurant floor to exactly the portrait rectangle")
	_expect(portrait.size.x <= portrait.size.y * 9.0 / 16.0 + 0.01, "Wider windows preserve the supported portrait composition")
	_expect(app.world.floor_origin.is_equal_approx(app.world.hud_area().position) and is_equal_approx(app.world.cell * float(app.session.snapshot().floor.viewport_columns), portrait.size.x), "Restaurant fills both phone sides below its camera-clearance sky")
	_expect(app.world.sky_height >= 80.0 * portrait.size.x / 720.0 and app.coin_panel.position.y >= app.world.hud_area().position.y, "Generated night sky reserves a quiet top strip and all HUD content starts below it")
	var base: Vector2 = app.world.cell_base(0, 0)
	_expect(base.is_equal_approx(app.world.floor_origin + Vector2(0.5, 0.5) * app.world.cell), "Feet register at the actual center of the occupied square tile")
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
		if not app.world.art.objects.has(key):
			all_loaded = false
			continue
		var entry: Dictionary = app.world.art.objects[key]
		var clip_id: String = "static" if entry.clips.has("static") else str(entry.clips.keys()[0])
		var clip_record: Dictionary = entry.clips[clip_id]
		var direction: String = "S" if clip_record.directions.has("S") else str(clip_record.directions.keys()[0])
		var texture: Texture2D = app.world.art.get_texture(key, clip_id, direction, 0.0)
		if texture == null:
			all_loaded = false
			continue
		var fitted: Rect2 = app.world.art.registered_rect(key, Vector2(160, 230), 90.0, clip_id, direction)
		var registration: Dictionary = app.world.art.registration(key, clip_id, direction)
		var anchor: Array = registration.root
		var registered := fitted.position + Vector2(float(anchor[0]), float(anchor[1])) * (90.0 / 128.0)
		anchored = anchored and registered.is_equal_approx(Vector2(160, 230))
		anchored = anchored and is_equal_approx(fitted.size.x / fitted.size.y, texture.get_width() / float(texture.get_height()))
		anchored = anchored and fitted.size.is_equal_approx(Vector2(float(registration.frame_size[0]), float(registration.frame_size[1])) * (90.0 / 128.0))
	_expect(all_loaded, "Gameplay resolves all required finished chef, guest, food, belt and room sprites")
	_expect(all_loaded and anchored, "Catalog sprites preserve the complete frame, uniform tile scale and registered foot/deck/plate root")

func _test_camera_clearance(app) -> void:
	var before: Dictionary = app.session.save_data()
	var footer: Vector2 = app.edit.position
	var physical := Transform2D(Vector2(0.5, 0), Vector2(0, 0.5), Vector2.ZERO)
	var layout = load("res://scripts/screen_layout.gd")
	_expect(is_equal_approx(layout.top_inset(Rect2(0, 40, 390, 804), [], physical, 844), 80.0), "Physical safe-area pixels convert to logical canvas units")
	_expect(is_equal_approx(layout.top_inset(Rect2(0, 40, 390, 804), [Rect2(175, 16, 40, 36)], physical, 844), 104.0), "A hole-punch bottom beyond the reported safe area expands the clearance")
	_expect(is_zero_approx(layout.top_inset(Rect2(0, 0, 390, 844), [Rect2(0, 0, 20, 844), Rect2(175, 800, 40, 44)], physical, 844)), "Side and bottom cutouts do not reserve the whole display as a top strip")
	app._layout_for_safe_top(180.0)
	var sky_bottom: float = app.world.hud_area().position.y
	var clear: bool = sky_bottom >= 180.0 + 12.0 * app.editor_ui.unit
	for control in [app.coin_panel, app.editing_panel, app.editor_ui.live, app.shop]:
		clear = clear and control.get_global_rect().position.y >= sky_bottom
	_expect(clear and app.world.sky_texture != null, "A large simulated camera clears Coins, Editing, Live and Shop over the generated sky")
	_expect(not app._floor_drop(Vector2(app.world.portrait.get_center().x, sky_bottom * 0.5)) and app.world.object_at(Vector2(app.world.portrait.get_center().x, sky_bottom * 0.5)).is_empty(), "The quiet sky cannot select sprites or accept an editor drop")
	_expect(app.edit.position.is_equal_approx(footer) and _same(before, app.session.save_data()), "Camera clearance preserves bottom controls and the exact saved restaurant")
	app._layout()

func _test_configured_camera(app) -> void:
	var original: RefCounted = app.session
	app.session = load("res://scripts/session.gd").new_session(41, {"floor": {"viewport_columns": 6, "rows": 30}})
	app._refresh()
	app._layout()
	await _frames()
	_expect(is_equal_approx(app.world.cell, app.world.portrait.size.x / 6.0), "Configured visible column count determines the actual square cell pitch")
	var horizontal_limit := float(app.session.snapshot().floor.world_columns) - 6.0
	app.session.command({"type": "set_camera", "x": horizontal_limit - 0.5, "y": 0.0})
	app._refresh()
	var start: Vector2 = app.world.portrait.position + app.world.portrait.size * Vector2(0.8, 0.6)
	var end := start - Vector2(app.world.cell * 2.0, 0)
	await _touch(app, start, true, 8)
	await _drag(app, start, end, 8)
	await _touch(app, end, false, 8)
	_expect(is_equal_approx(float(app.session.snapshot().camera.x), horizontal_limit), "Actual touch panning uses the configured world-minus-visible extent rather than a hard-coded camera limit")
	var hud := _hud_rects(app)
	var vertical_end := start - Vector2(0, app.world.cell * 2.0)
	await _touch(app, start, true, 8)
	await _drag(app, start, vertical_end, 8)
	await _touch(app, vertical_end, false, 8)
	_expect(is_equal_approx(float(app.session.snapshot().camera.y), 2.0), "A vertical drag reaches rows outside a short viewport without distorting tile scale")
	_expect(_same(hud, _hud_rects(app)), "Vertical scene panning leaves the transparent HUD and Shop stationary")
	app.session = original
	app._refresh()
	app._layout()
	app.save_now()
	await _frames()

func _test_touch_and_hud(app) -> void:
	await _test_optical_pairs(app, [_button_ink_pair(app.shop), _button_ink_pair(app.edit), _button_ink_pair(app.staff)])
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
	for button in [app.shop, app.staff]:
		var center: Vector2 = button.get_global_rect().get_center()
		await _touch(app, center, true, 5)
		await _touch(app, center, false, 5)
	_expect(_same(before_buttons, app.session.snapshot()), "Unavailable future-feature buttons neither change coins nor pan the restaurant on tap")
	app.session.advance(60.0)
	await _frames()
	_expect(int(app.money.text) == int(app.session.snapshot().coins) and app.session.snapshot().coins > before.coins, "Controlled live service updates the native coin label")
	_expect(_same(hud, _hud_rects(app)), "Changing the coin balance does not shift Shop or the other fixed controls")

func _tap(app, at: Vector2, index := 11) -> void:
	await _touch(app, at, true, index)
	await _touch(app, at, false, index)
	await create_timer(0.23).timeout

func _object(scene: Dictionary, identity: String) -> Dictionary:
	for item in scene.objects:
		if str(item.id) == identity: return item
	return {}

func _test_editor(app) -> void:
	var original: RefCounted = app.session
	app.session = Session.new_session(41)
	app._refresh()
	app._layout()
	await _frames()
	await _tap(app, app.edit.get_global_rect().get_center())
	_expect(app.session.snapshot().mode == "edit" and app.editor_ui.visible and app.editing_cue.visible and not app.shop.visible and not app.edit.visible and not app.staff.visible, "Actual Edit touch opens the shared native editor, shows Editing and moves Shop into the category rail")
	_expect(not quit_on_go_back and auto_accept_quit, "The native app owns Android Back while retaining normal window-close behavior")
	var coin_capsule: Rect2 = app.coin_panel.get_global_rect()
	var editing_capsule: Rect2 = app.editing_panel.get_global_rect()
	var live_capsule: Rect2 = app.editor_ui.live.get_meta("visual").get_global_rect()
	_expect(app.coin_panel.is_visible_in_tree() and coin_capsule.encloses(app.coin.get_global_rect()) and coin_capsule.encloses(app.money.get_global_rect()) and app.money.get_minimum_size().x <= app.money.size.x + 1, "The cream coin capsule contains its generated coin and measured earnings text")
	_expect(app.editing_panel.is_visible_in_tree() and app.editing_icon.is_visible_in_tree() and editing_capsule.encloses(app.editing_icon.get_global_rect()) and editing_capsule.encloses(app.editing_cue.get_global_rect()) and not coin_capsule.intersects(editing_capsule) and not editing_capsule.intersects(live_capsule), "The Editing capsule contains its icon and label with clear gaps from the coin and Live capsules")
	await _test_large_balance_capsule(app)
	var paused: Dictionary = app.session.snapshot()
	app.advance_time(20.0)
	_expect(_same(paused, app.session.snapshot()), "The editor pauses actual customer, chef and conveyor simulation")
	var camera_before_probe: Dictionary = app.session.save_data()
	app._pan(Vector2(0, -app.world.cell * 100.0))
	var final_row: Vector2 = app.world.cell_base(0.0, float(app.session.snapshot().floor.rows) - 1.0)
	_expect(final_row.y + app.world.cell * 0.5 <= app.editor_ui.occlusion_top() + 0.01 and final_row.y - app.world.cell * 0.5 >= app.world.hud_area().position.y + 145.0 * app.editor_ui.unit, "Editor vertical panning reveals the entire final floor row above the rail, including in tall windows")
	_expect(app.session.restore(camera_before_probe), "The camera-boundary probe restores the same paused restaurant")
	app._refresh()
	var controls: Array = [app.editor_ui.live, app.editor_ui.previous, app.editor_ui.next, app.editor_ui.shop]
	for button in app.editor_ui.layers.values(): controls.append(button)
	var editor_fit := true
	for button in controls:
		var physical: Rect2 = app.get_viewport_transform() * button.get_global_rect()
		editor_fit = editor_fit and app.world.portrait.encloses(button.get_global_rect()) and physical.size.x >= 44 and physical.size.y >= 44 and not button.accessibility_name.is_empty()
	_expect(editor_fit, "Editor Live, layer and paging controls remain contained with native names and at least 44 physical pixel targets")
	var rail_rect: Rect2 = app.editor_ui.category_rail.get_global_rect()
	var prior_right := rail_rect.position.x
	var horizontal := true
	for layer in ["people", "layout", "floor"]:
		var button: Button = app.editor_ui.layers[layer]
		var rect: Rect2 = button.get_global_rect()
		horizontal = horizontal and rail_rect.encloses(rect) and rect.position.x >= prior_right and button.text == str(layer).capitalize()
		prior_right = rect.end.x
	var shop_face: Rect2 = app.editor_ui.skin.face_rect("control-wood", app.editor_ui.shop.get_meta("visual").get_global_rect(), app.editor_ui.unit)
	var curtain_face: Rect2 = app.editor_ui.skin.face_rect("tab-idle", app.editor_ui.layers.people.get_meta("visual").get_global_rect(), app.editor_ui.unit)
	_expect(horizontal and app.world.portrait.encloses(app.editor_ui.shop.get_global_rect()) and app.editor_ui.shop.get_global_rect().position.x >= prior_right and absf(shop_face.get_center().y - curtain_face.get_center().y) < 0.1, "People, Layout, Floor and quiet Shop retain clear horizontal targets and align their visible material faces")
	_expect(app.editor_ui.tray.get_global_rect().position.y >= rail_rect.end.y - 0.01, "The compact cream drawer begins below the separate hanging category panels")
	_test_compact_inventory(app)
	await _test_restored_rail(app)
	await _test_visible_ink_alignment(app)
	await _test_curtain_feedback(app)
	await _test_curtain_lifecycle(app)
	var before_shop: Dictionary = app.session.save_data()
	var before_shop_bytes: Dictionary = _save_bytes()
	await _tap(app, app.editor_ui.shop.get_global_rect().get_center())
	_expect(_same(before_shop, app.session.save_data()) and _same(before_shop_bytes, _save_bytes()) and app.editor_ui.rejection.visible and "Shop" in app.editor_ui.rejection.text, "The editor Shop shortcut shows unavailable feedback while preserving the paused restaurant and both saves")
	await _tap(app, app.editor_ui.layers.people.get_global_rect().get_center())
	_expect(app.editor_ui.layers.people.text == "People" and app.editor_ui.layers.layout.text == "Layout" and app.editor_ui.layers.floor.text == "Floor", "Every category keeps its visible name when People is active")
	_expect(app.editor_ui.cards.size() == 3 and app.editor_ui.previous.disabled and app.editor_ui.next.disabled, "The compact People rail shows three existing staff with disabled boundary carets")
	_expect(_skin_source(app.editor_ui.cards[0].get_theme_stylebox("normal")) != _skin_source(app.editor_ui.layers.people.get_theme_stylebox("normal")) and app.editor_ui.cards[0].get_theme_color("font_color") == Color("233d58"), "Roster cards use generated cream mats and navy ink beside the indigo category rail")
	var before_profile: Dictionary = app.session.save_data()
	var profile_tap: Vector2 = app.editor_ui.cards[0].get_global_rect().get_center()
	await _touch(app, profile_tap, true, 19)
	await _drag(app, profile_tap, profile_tap + Vector2(2, 1), 19)
	await _touch(app, profile_tap + Vector2(2, 1), false, 19)
	await create_timer(0.23).timeout
	_expect(app.editor_ui.inspection.visible and not app.editor_ui.inspection_preview.entry.is_empty() and "Salmon nigiri" in app.editor_ui.inspection_details.text and app.armed_item.is_empty() and _same(before_profile, app.session.save_data()), "A roster profile tap opens real recipe/preparation details without arming, moving or changing its chef")
	_expect(app.editor_ui.inspection_close.has_focus() and app.editor_ui.inspection_close.get_theme_color("font_focus_color") == Color("233d58") and app.editor_ui.live.get_theme_color("font_focus_color") == Color("fff3db"), "Focused staff-detail Close remains navy on cream, and Live retains cream focus text on vermilion")
	_expect(app.editor_ui.inspection_panel.get_global_rect().encloses(app.editor_ui.inspection_close.get_global_rect()) and not app.editor_ui.inspection_close.get_global_rect().intersects(app.editor_ui.inspection_details.get_global_rect()), "The full-height rounded staff Close control stays inside its modal without covering recipe details")
	app.notification(Node.NOTIFICATION_WM_GO_BACK_REQUEST)
	_expect(not app.editor_ui.inspection.visible and _same(before_profile, app.session.save_data()), "System Back closes staff details and returns to the same saved editor")
	await _tap(app, app.editor_ui.cards[0].get_global_rect().get_center())
	await _tap(app, app.world.portrait.position + Vector2(12, 140))
	_expect(not app.editor_ui.inspection.visible, "A touch outside staff details closes the local popup without changing scenes")
	var profile_from: Vector2 = app.editor_ui.cards[0].get_global_rect().get_center()
	var profile_to: Vector2 = app.world.cell_base(4, 7)
	await _touch(app, profile_from, true, 15)
	await _drag(app, profile_from, profile_to, 15)
	await _touch(app, profile_to, false, 15)
	_expect(not app.editor_ui.inspection.visible and int(_object(app.session.snapshot(), "chef-1").x) == 4, "Dragging a roster profile moves its existing chef without opening the inspection popup")
	app._editor_command({"type": "editor_select", "id": null})
	await _tap(app, app.editor_ui.layers.layout.get_global_rect().get_center())
	_expect(app.session.snapshot().editor.layer == "layout" and app.session.snapshot().editor.tray_open and app.editor_ui.cards.size() == 4, "Switching to Layout opens the compact drawer with four inventory slots")
	await _touch(app, app.editor_ui.layers.layout.get_global_rect().get_center(), true)
	await _touch(app, app.editor_ui.layers.layout.get_global_rect().get_center(), false)
	var moving_backing: Rect2 = app.editor_ui.inventory_backing.get_global_rect()
	var covered_floor: Vector2 = moving_backing.end - Vector2(4, 78) * app.editor_ui.unit
	_expect(app.editor_ui.inventory_backing.is_visible_in_tree() and moving_backing.has_point(covered_floor) and not app._floor_drop(covered_floor), "The visible full-width cream backdrop blocks exposed floor drops while the category row moves")
	var before_backing_gesture: Dictionary = app.session.save_data()
	await _touch(app, covered_floor, true, 26)
	await _drag(app, covered_floor, covered_floor + Vector2(app.world.cell * 0.35, 0), 26)
	await _touch(app, covered_floor + Vector2(app.world.cell * 0.35, 0), false, 26)
	_expect(_same(before_backing_gesture, app.session.save_data()), "A real touch and drag beginning on the exposed cream backdrop cannot pan or select the covered floor")
	await create_timer(0.23).timeout
	_expect(not app.session.snapshot().editor.tray_open and not app.editor_ui.tray.visible and app.editor_ui.category_rail.visible and app.editor_ui.shop.visible, "Tapping the active layer collapses the drawer and keeps the category rail and Shop available")
	_expect(app.editor_ui.inventory_backing.is_visible_in_tree() and app.editor_ui.inventory_backing.get_global_rect().encloses(app.editor_ui.category_rail.get_global_rect()) and app.editor_ui.inventory_backing.get_global_rect().encloses(app.editor_ui.bottom_dock.get_global_rect()) and app.editor_ui.category_rail.get_theme_stylebox("panel") is StyleBoxEmpty, "Collapsed curtains retain the same unframed cream backdrop continuously through the bottom dock")
	_expect(app.editor_ui.category_rail.get_global_rect().end.y <= app.editor_ui.bottom_dock.get_global_rect().position.y + 0.01, "The collapsed curtain row reserves space above the bottom dock so the selected underline remains visible")
	await _tap(app, app.editor_ui.layers.layout.get_global_rect().get_center())
	var seat := _object(app.session.snapshot(), "seat-1")
	if seat.is_empty():
		for candidate in app.session.snapshot().objects:
			if candidate.kind == "seat": seat = candidate; break
	var seat_id: String = str(seat.id)
	var at: Vector2 = _sprite_point(app, seat_id)
	await _touch(app, at, true, 16)
	await _drag(app, at, at - Vector2(app.world.cell, 0), 16)
	await _touch(app, at - Vector2(app.world.cell, 0), false, 16)
	_expect(int(_object(app.session.snapshot(), seat_id).x) == int(seat.x) and float(app.session.snapshot().camera.x) > 0 and str(app.session.snapshot().editor.selected_id).is_empty(), "Dragging an unselected object pans instead of moving it or selecting it")
	app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
	app._refresh()
	await _tap(app, at)
	_expect(app.session.snapshot().editor.selected_id == seat_id and app.editor_ui.rotate.visible and app.editor_ui.remove.visible and app.editor_ui.context_bubble.visible and app.editor_ui.context_bubble.get_global_rect().encloses(app.editor_ui.rotate.get_global_rect()) and app.editor_ui.context_bubble.get_global_rect().encloses(app.editor_ui.remove.get_global_rect()) and app.editor_ui.rotate.text == "Rotate" and app.editor_ui.remove.text == "Return", "Tapping a floor object exposes labelled Rotate and Return in one contextual ceramic capsule")
	await _test_optical_pairs(app, [_button_ink_pair(app.editor_ui.rotate), _button_ink_pair(app.editor_ui.remove)])
	var pointer: Rect2 = app.editor_ui.context_pointer.get_global_rect()
	var capsule: Rect2 = app.editor_ui.context_bubble.get_global_rect()
	_expect(pointer.position.y >= capsule.end.y - 28 * app.editor_ui.unit and pointer.end.y <= capsule.end.y + 1 * app.editor_ui.unit, "The context pointer occupies the capsule's lower material edge instead of floating beneath its bounds")
	var destination: Vector2 = app.world.cell_base(3, 5) + at - app.world.cell_base(float(seat.x), float(seat.y))
	await _touch(app, at, true, 12)
	await _drag(app, at, destination, 12)
	_expect(not app.world.editor_preview.is_empty() and app.world.editor_preview.valid, "An actual selected-object drag shows a valid registered tile preview")
	await _touch(app, destination, false, 12)
	var moved := _object(app.session.snapshot(), seat_id)
	_expect(int(moved.x) == 3 and int(moved.y) == 5 and app.session.snapshot().editor.selected_id == seat_id, "Releasing the selected-object drag moves it and leaves it selected")
	destination = _sprite_point(app, seat_id)
	var before_rejection: Dictionary = app.session.save_data()
	var blocked: Vector2 = app.world.cell_base(3, 6) + destination - app.world.cell_base(3, 5)
	await _touch(app, destination, true, 12)
	await _drag(app, destination, blocked, 12)
	_expect(not app.world.editor_preview.is_empty() and not app.world.editor_preview.valid, "Dragging onto a real conveyor shows an invalid placement preview")
	await _touch(app, blocked, false, 12)
	_expect(_same(before_rejection, app.session.save_data()) and app.editor_ui.rejection.visible, "Rejected object drop restores the exact arrangement and shows brief feedback")
	await _test_rejected_overlay_release(app, destination, app.world.cell_base(1, 12), "the open inventory tray")
	await _test_rejected_overlay_release(app, destination, app.editor_ui.layers.people.get_global_rect().get_center(), "a visible People layer control")
	var capsule_target: Vector2 = _valid_underlay(app, app.editor_ui.context_bubble.get_global_rect(), seat_id)
	await _test_rejected_overlay_release(app, destination, capsule_target, "the contextual Rotate/Return capsule")
	app.session.command({"type": "set_camera", "x": 1.0, "y": 0.0})
	app._refresh()
	var outside_portrait: Vector2 = Vector2(app.world.portrait.position.x - 2.0, app.world.cell_base(0, 4).y)
	await _test_rejected_overlay_release(app, _sprite_point(app, seat_id), outside_portrait, "outside the portrait over an otherwise valid world tile")
	app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
	app._refresh()
	var facing: String = str(moved.facing)
	await _tap(app, app.editor_ui.rotate.get_global_rect().get_center())
	_expect(_object(app.session.snapshot(), seat_id).facing != facing and app.session.snapshot().editor.selected_id == seat_id, "The native Rotate button turns the selected object without losing selection")
	await _tap(app, app.editor_ui.cards[0].get_global_rect().get_center())
	_expect(str(app.session.snapshot().editor.selected_id).is_empty() and not app.armed_item.is_empty() and not app.editor_ui.rotate.visible and not app.editor_ui.remove.visible, "Arming Layout inventory clears the old floor selection so object tools cannot target a different object")
	await _tap(app, app.editor_ui.layers.people.get_global_rect().get_center())
	await _tap(app, app.editor_ui.layers.layout.get_global_rect().get_center())
	await _tap(app, _sprite_point(app, seat_id))
	var coins: int = int(app.session.snapshot().coins)
	await _tap(app, app.editor_ui.remove.get_global_rect().get_center())
	_expect(_object(app.session.snapshot(), seat_id).is_empty() and int(app.session.snapshot().coins) == coins, "The native return-to-inventory control removes purchased furniture without a refund")
	var item_card: Button = app.editor_ui.cards[1]
	var item_start: Vector2 = item_card.get_global_rect().get_center()
	var new_cell: Vector2 = app.world.cell_base(3, 4)
	await _touch(app, item_start, true, 13)
	await _drag(app, item_start, new_cell, 13)
	_expect(not app.world.editor_preview.is_empty(), "Dragging native inventory artwork onto the actual floor exposes the same placement preview")
	await _touch(app, new_cell, false, 13)
	var placed_id: String = str(app.session.snapshot().editor.selected_id)
	var placed := _object(app.session.snapshot(), placed_id)
	_expect(not placed.is_empty() and placed.kind == "seat" and int(placed.x) == 3 and int(placed.y) == 4, "Inventory touch drag places the requested native chair at the released tile")
	var outside: Vector2 = app.world.cell_base(5, 3)
	var camera_before := float(app.session.snapshot().camera.x)
	await _touch(app, outside, true, 14)
	await _drag(app, outside, outside - Vector2(app.world.cell, 0), 14)
	await _touch(app, outside - Vector2(app.world.cell, 0), false, 14)
	_expect(str(app.session.snapshot().editor.selected_id).is_empty() and float(app.session.snapshot().camera.x) > camera_before, "A swipe outside the selection deselects and pans in that same gesture")
	var full_goods_width: float = app.editor_ui.tray.size.x
	await _tap(app, app.editor_ui.next.get_global_rect().get_center())
	_expect(int(app.session.snapshot().editor.page) == 1 and app.editor_ui.page_announcement.accessibility_name == "Layout page 2 of 2" and not app.editor_ui.previous.disabled and app.editor_ui.next.disabled and app.editor_ui.cards.size() == 1 and app.editor_ui.cards[0].get_meta("entry").id == "barrel-wood", "The edge caret reaches the fifth good on the final page with correct boundaries and an accessible announcement")
	_expect(app.editor_ui.tray.size.x < full_goods_width * 0.6 and absf(app.editor_ui.tray.get_global_rect().get_center().x - app.world.portrait.get_center().x) < 1, "The final one-good page shrinks its cream drawer around the actual item instead of leaving empty inventory space")
	await _tap(app, app.editor_ui.previous.get_global_rect().get_center())
	_expect(app.session.snapshot().editor.page == 0 and app.editor_ui.cards.size() == 4 and app.editor_ui.previous.disabled and not app.editor_ui.next.disabled and app.editor_ui.cards[3].get_meta("entry").id == "crate-wood", "The previous caret restores the first four goods without skipping or duplicating an entry")
	await _tap(app, app.editor_ui.layers.floor.get_global_rect().get_center())
	_expect(app.editor_ui.cards.size() == 1 and app.editor_ui.cards[0].disabled and app.editor_ui.layers.floor.text == "Floor", "Floor keeps its approved tray composition and shows the current floor without adding future painting mechanics")
	_expect(app.editor_ui.cards[0].get_meta("preview").goods.has("floor-cream"), "The current floor inventory preview resolves the separate Blender slab render")
	app._editor_command({"type": "editor_select", "id": "chef-1"})
	var working_store = app.store
	_write_bytes("user://editor-write-obstacle", "A file blocks this directory".to_utf8_buffer())
	app.store = Store.new("user://editor-write-obstacle")
	app._editor_command({"type": "editor_rotate", "id": "chef-1"})
	var pending: Dictionary = app.session.save_data()
	_expect(app.save_blocked and app.pending_edit_save and app.recovery.visible and "saving" in app.recovery_title.text, "An immediate edit write failure opens a blocking, readable retry instead of silently losing the accepted arrangement")
	_expect(app.recovery.get_global_rect().encloses(app.recovery_retry.get_global_rect()) and app.recovery.get_global_rect().encloses(app.recovery_close.get_global_rect()) and app.recovery_message.get_global_rect().end.y <= app.recovery_retry.get_global_rect().position.y + 0.01, "Full-height recovery pills stay inside their modal below the readable recovery message")
	_expect(app.recovery_retry.get_theme_color("font_focus_color") == Color("fff3db") and app.recovery_close.get_theme_color("font_focus_color") == Color("233d58") and app.edit.get_theme_color("font_focus_color") == Color("233d58"), "HUD and recovery focus colors preserve the same primary and neutral text contrast")
	_expect(_skin_calibrated(app.recovery.get_theme_stylebox("panel"), app.skin, app.editor_ui.unit) and _skin_source(_button_surface(app.recovery_retry)) == _skin_source(app.skin.style("control-green", app.editor_ui.unit)) and _skin_source(_button_surface(app.recovery_close)) == _skin_source(app.skin.style("control-wood", app.editor_ui.unit)) and app.recovery_title.get_theme_color("font_color") == Color("233d58"), "Save retry uses the same calibrated cream recovery panel, navy type and vermilion primary as the editor")
	await _test_optical_pairs(app, [_button_ink_pair(app.recovery_retry), _button_ink_pair(app.recovery_close)])
	_expect(not app._editor_command({"type": "editor_remove", "id": "chef-1"}).ok and _same(pending, app.session.save_data()), "A pending editor save blocks further mutations while preserving the exact in-memory arrangement")
	await _tap(app, app.recovery_retry.get_global_rect().get_center())
	_expect(app.save_blocked and _same(pending, app.session.save_data()), "Retrying while storage is unavailable keeps the accepted in-memory edit intact")
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://editor-write-obstacle"))
	await _tap(app, app.recovery_retry.get_global_rect().get_center())
	_expect(not app.save_blocked and not app.pending_edit_save and app.recovery == null and _same(pending, app.store.load_session()), "Retry writes the same pending arrangement once storage recovers and re-enables the editor")
	app.store = working_store
	app._editor_command({"type": "editor_layer", "layer": "floor"})
	var edit_saved: Dictionary = app.session.snapshot()
	var restored = Session.new()
	_expect(app.save_now() and restored.restore(app.store.load_session()) and _same(edit_saved, restored.snapshot()), "Every accepted editor change immediately persists mode, camera, layer and tray state through the actual save store")
	await _tap(app, app.editor_ui.live.get_global_rect().get_center())
	_expect(app.session.snapshot().mode == "live" and not app.editor_ui.visible and app.edit.visible and app.shop.visible and not app.editing_cue.visible, "Top-right Live returns directly to service without Save, Done, Cancel or Undo")
	var elapsed_before := float(app.session.snapshot().elapsed)
	app.advance_time(1.0)
	_expect(float(app.session.snapshot().elapsed) > elapsed_before, "Returning to Live resumes the actual operating simulation")
	app.session = original
	app._refresh()
	app._layout()
	app.save_now()
	await _frames()

func _test_large_balance_capsule(app) -> void:
	var original: Dictionary = app.session.save_data()
	var earned: Dictionary = original.duplicate(true)
	earned.state.coins = 123456789
	_expect(app.session.restore(earned), "The high-balance HUD probe uses a valid saved restaurant")
	app._refresh()
	app._layout()
	await _frames()
	var coin_capsule: Rect2 = app.coin_panel.get_global_rect()
	var money_ink: Vector2 = app.money.get_theme_font("font").get_string_size(app.money.text, HORIZONTAL_ALIGNMENT_LEFT, -1, app.money.get_theme_font_size("font_size"))
	_expect(app.money.text == "123456789" and coin_capsule.encloses(app.money.get_global_rect()) and money_ink.x <= app.money.size.x + 0.1 and not coin_capsule.intersects(app.editing_panel.get_global_rect()), "A nine-digit earned balance stays fully readable inside its coin capsule without reaching Editing")
	# The save contract caps exact currency at 2^53-1. Its largest legal value
	# still needs a readable caption, with the exact full amount accessible.
	earned.state.coins = 9007199254740991
	_expect(app.session.restore(earned), "The compact-currency probe restores the largest valid exact saved amount")
	app._refresh()
	app._layout()
	await _frames()
	_expect(app.money.text == "9Qa" and app.money.accessibility_description == "9007199254740991 coins" and int(app.session.snapshot().coins) == 9007199254740991 and coin_capsule.encloses(app.money.get_global_rect()) and app.money.get_theme_font_size("font_size") >= int(20 * app.editor_ui.unit), "The maximum legal balance uses a readable compact caption while preserving exact saved and accessible currency")
	# Also guard the HUD formatter's native layout at the signed-64-bit limit.
	# This synchronous presentation fixture never reaches a simulation frame or
	# the save store; the domain correctly continues to reject such save values.
	var real_session: RefCounted = app.session
	var currency: RefCounted = Session.new_session(41)
	currency._state.coins = 9223372036854775807
	app.session = currency
	app._layout_hud(app.world.hud_area(), app.editor_ui.unit)
	var defensive_caption: String = app.money.text
	var defensive_description: String = app.money.accessibility_description
	var defensive_bounds: Rect2 = app.money.get_global_rect()
	var defensive_font_size: int = app.money.get_theme_font_size("font_size")
	app.session = real_session
	_expect(defensive_caption == "9.2Qi" and defensive_description == "9223372036854775807 coins" and coin_capsule.encloses(defensive_bounds) and defensive_font_size >= int(20 * app.editor_ui.unit), "A defensive nineteen-digit HUD fixture retains full accessibility text and fits the existing capsule at a readable font size")
	_expect(app.session.restore(original), "The large-balance HUD probe restores the exact paused restaurant")
	app._refresh()
	app._layout()
	await _frames()

func _test_compact_inventory(app) -> void:
	var editor = app.editor_ui
	var unit: float = editor.unit
	var tray_bounds: Rect2 = editor.tray.get_global_rect()
	var dock_bounds: Rect2 = editor.bottom_dock.get_global_rect()
	var backing: Rect2 = editor.inventory_backing.get_global_rect()
	_expect(editor.cards.size() == 4 and editor.inventory_backing.is_visible_in_tree() and editor.inventory_backing.mouse_filter == Control.MOUSE_FILTER_STOP and backing.encloses(editor.category_rail.get_global_rect()) and backing.encloses(tray_bounds) and is_equal_approx(backing.position.x, app.world.portrait.position.x) and is_equal_approx(backing.size.x, app.world.portrait.size.x) and is_equal_approx(backing.end.y, app.world.portrait.end.y) and editor.inventory_backing.color.a > 0.99 and editor.category_rail.get_theme_stylebox("panel") is StyleBoxEmpty, "One opaque full-width beige backdrop covers the unframed category rail and compact drawer through the footer, with native input shielding")
	_expect(editor.tray.size.x < app.world.portrait.size.x * 0.8 and editor.bottom_dock.is_visible_in_tree() and app.world.portrait.encloses(dock_bounds) and dock_bounds.size.y >= 48 * unit, "The inventory panel hugs its goods while a substantial bottom dock stays inside the portrait")
	var captions := ["Belt", "Stool", "Plant", "Crate"]
	var goods_ready := true
	var compact := true
	var accessible := true
	var independent := true
	var transform: Transform2D = app.get_viewport_transform()
	for index in range(editor.cards.size()):
		var card: Button = editor.cards[index]
		var bounds := card.get_global_rect()
		var preview: Control = card.get_meta("preview")
		var label: Label = card.get_meta("name_label")
		var stock: Label = card.get_meta("stock")
		var item: Dictionary = card.get_meta("entry")
		var physical: Rect2 = transform * bounds
		goods_ready = goods_ready and preview.goods_texture != null and preview.goods_texture.resource_path == "res://assets/ui/editor-goods/atlas.png" and preview.goods.has(str(item.art_id))
		compact = compact and preview.size.y <= 128 * unit and bounds.encloses(preview.get_global_rect()) and bounds.encloses(label.get_global_rect()) and bounds.encloses(stock.get_global_rect()) and label.get_global_rect().end.y <= stock.get_global_rect().position.y + 1 * unit
		compact = compact and bounds.end.y - stock.get_global_rect().end.y >= 14 * unit - 0.1 and dock_bounds.position.y - stock.get_global_rect().end.y >= 20 * unit - 0.1
		accessible = accessible and physical.size.x >= 44 and physical.size.y >= 44 and label.text == captions[index] and card.accessibility_name == str(item.name)
		for pager in [editor.previous, editor.next]:
			independent = independent and not bounds.intersects(pager.get_global_rect())
	_expect(goods_ready, "Every visible Layout good loads its dedicated Blender atlas region instead of a live-scene sprite")
	_expect(compact and accessible, "Four smaller goods retain readable captions, padded stock labels above the dock and 44-pixel targets")
	for pager in [editor.previous, editor.next]:
		var visual: Control = pager.get_meta("visual")
		var material: Panel = pager.get_meta("visual_surface")
		var icon: TextureRect = pager.get_meta("visual_icon")
		var physical: Rect2 = transform * pager.get_global_rect()
		independent = independent and physical.size.x >= 44 and physical.size.y >= 44 and pager.get_global_rect().encloses(icon.get_global_rect()) and icon.size.x <= 24 * unit and material.get_theme_stylebox("panel") is StyleBoxEmpty and visual.is_visible_in_tree()
	_expect(independent, "Unbacked narrow chevrons retain independent 44-pixel native targets without covering any good")
	var previous_end: float = editor.category_rail.get_global_rect().position.x
	var separated := true
	for layer in ["people", "layout", "floor"]:
		var button: Button = editor.layers[layer]
		var visual: Control = button.get_meta("visual")
		var surface: Control = button.get_meta("visual_surface")
		var rect := surface.get_global_rect()
		separated = separated and button.is_visible_in_tree() and visual.is_visible_in_tree() and button.self_modulate.a == 0 and visual.modulate.a > 0 and visual.get_global_rect().encloses(rect) and rect.position.x > previous_end
		previous_end = rect.end.x
	_expect(separated and editor.category_rod.is_visible_in_tree() and editor.category_rod.size.y >= 32 * unit, "Separate curtains hang from one substantial shared rod with open gaps between them")
	var backing_blocks := false
	for blocked: Rect2 in editor.blocked_rects():
		backing_blocks = backing_blocks or blocked.encloses(backing)
	_expect(backing_blocks, "The entire visible beige backdrop shields scene gestures, including space beside the narrower goods drawer")
	for button in [editor.live, editor.shop]:
		var visual: Control = button.get_meta("visual")
		_expect(button.get_global_rect().encloses(visual.get_global_rect()) and is_equal_approx(visual.size.y, button.size.y) and visual.size.y >= 100 * unit - 0.01, "%s renders the full-height rounded capsule within its native touch target" % button.text)

func _test_restored_rail(app) -> void:
	var editor = app.editor_ui
	var unit: float = editor.unit
	var area: Rect2 = app.world.portrait
	var rod_face: Rect2 = editor.skin.face_rect("noren-rod", editor.category_rod.get_global_rect(), unit)
	_expect(absf(rod_face.position.x - area.position.x) < 0.1 and absf(rod_face.end.x - area.end.x) < 0.1, "The rod's visible wood face reaches both portrait edges rather than stopping at its transparent source margins")
	if DisplayServer.get_name() == "headless": return
	var previous_mode: int = app.process_mode
	app.process_mode = Node.PROCESS_MODE_DISABLED
	await _frames()
	await RenderingServer.frame_post_draw
	var pixels: Image = root.get_texture().get_image()
	app.process_mode = previous_mode
	_expect(pixels != null, "The restored curtain/backdrop composite is checked in the rendered native viewport")
	if pixels == null: return
	var transform: Transform2D = app.get_viewport_transform()
	var physical_rod: Rect2 = transform * rod_face
	var row := clampi(int(roundf(physical_rod.get_center().y)), 0, pixels.get_height() - 1)
	var physical_area: Rect2 = transform * area
	var left := pixels.get_pixel(clampi(int(ceilf(physical_area.position.x)), 0, pixels.get_width() - 1), row)
	var right := pixels.get_pixel(clampi(int(floorf(physical_area.end.x)) - 1, 0, pixels.get_width() - 1), row)
	_expect(_wood_pixel(left) and _wood_pixel(right), "Visible brown wood crosses the complete portrait width at the rod center, including the first and last screen pixels")
	var seam_samples: Array[Vector2] = []
	var previous_rect := Rect2()
	for layer in ["people", "layout", "floor"]:
		var visual: Control = editor.layers[layer].get_meta("visual")
		var bounds := visual.get_global_rect()
		var physical: Rect2 = transform * bounds
		var runs: Array[int] = []
		var run_width := 0
		for x in range(maxi(0, int(ceilf(physical.position.x))), mini(pixels.get_width(), int(floorf(physical.end.x)))):
			var navy := _navy_pixel(pixels.get_pixel(x, row))
			if navy: run_width += 1
			elif run_width > 0:
				runs.append(run_width)
				run_width = 0
		if run_width > 0: runs.append(run_width)
		var navy_width := 0
		for width in runs: navy_width += width
		_expect(runs.size() == 2 and navy_width < physical.size.x * 0.45, "%s original solid straps meet the rendered wood as two distinct navy bands with wood between them (runs=%s)" % [str(layer).capitalize(), runs])
		if previous_rect.has_area():
			var face: Rect2 = editor.skin.face_rect("tab-idle", bounds, unit)
			seam_samples.append(Vector2((previous_rect.end.x + bounds.position.x) * 0.5, face.get_center().y))
		previous_rect = bounds
	var tray_bounds: Rect2 = editor.tray.get_global_rect()
	seam_samples.append(Vector2(area.position.x + 3 * unit, tray_bounds.position.y + 50 * unit))
	seam_samples.append(Vector2(area.end.x - 3 * unit, tray_bounds.position.y + 50 * unit))
	seam_samples.append(Vector2(area.get_center().x, editor.category_rail.get_global_rect().end.y - 3 * unit))
	seam_samples.append(Vector2(area.position.x + 2 * unit, area.end.y - 2 * unit))
	seam_samples.append(Vector2(area.end.x - 2 * unit, area.end.y - 2 * unit))
	var uninterrupted := true
	var expected: Color = editor.inventory_backing.color
	for sample in seam_samples:
		var at := transform * sample
		var pixel := pixels.get_pixel(clampi(int(roundf(at.x)), 0, pixels.get_width() - 1), clampi(int(roundf(at.y)), 0, pixels.get_height() - 1))
		uninterrupted = uninterrupted and absf(pixel.r - expected.r) < 0.04 and absf(pixel.g - expected.g) < 0.04 and absf(pixel.b - expected.b) < 0.04
	_expect(uninterrupted, "Rendered beige remains continuous through curtain seams, beside the narrow goods drawer and at both footer corners")

func _wood_pixel(color: Color) -> bool:
	return color.r > 0.3 and color.r > color.g * 1.2 and color.g > color.b * 1.2

func _navy_pixel(color: Color) -> bool:
	return color.r < 0.3 and color.g < 0.35 and color.b > 0.14 and color.b > color.r * 1.25

func _difference_ink_bounds(pixels: Image, background: Image, logical: Rect2, transform: Transform2D) -> Rect2:
	var physical: Rect2 = transform * logical
	var clip := Rect2i(Vector2i(physical.position.floor()), Vector2i(physical.size.ceil())).intersection(Rect2i(Vector2i.ZERO, pixels.get_size()))
	var first := Vector2i(pixels.get_width(), pixels.get_height())
	var last := Vector2i(-1, -1)
	for y in range(clip.position.y, clip.end.y):
		for x in range(clip.position.x, clip.end.x):
			var color := pixels.get_pixel(x, y)
			var underneath := background.get_pixel(x, y)
			if maxf(absf(color.r - underneath.r), maxf(absf(color.g - underneath.g), absf(color.b - underneath.b))) <= 0.015: continue
			first = Vector2i(mini(first.x, x), mini(first.y, y))
			last = Vector2i(maxi(last.x, x), maxi(last.y, y))
	if last.x < first.x: return Rect2()
	return Rect2(Vector2(first), Vector2(last - first + Vector2i.ONE))

func _button_ink_pair(button: Button) -> Dictionary:
	return {"name": button.text, "button": button, "icon": button.get_meta("visual_icon"), "caption": button.get_meta("visual_label"), "frame": button.get_meta("visual"), "role": str(button.get_meta("skin_role", "control-wood")), "stacked": bool(button.get_meta("visual_stacked", false))}

func _test_visible_ink_alignment(app) -> void:
	var pairs: Array = [{"name": "Editing", "icon": app.editing_icon, "caption": app.editing_cue, "frame": app.editing_panel, "role": "control-wood"}, {"name": "Coins", "icon": app.coin, "caption": app.money, "frame": app.coin_panel, "role": "coin-panel"}]
	for button in [app.editor_ui.live, app.editor_ui.shop, app.editor_ui.layers.people, app.editor_ui.layers.layout, app.editor_ui.layers.floor]: pairs.append(_button_ink_pair(button))
	await _test_optical_pairs(app, pairs, app.editor_ui.cards)

func _test_optical_pairs(app, pairs: Array, stock_cards: Array = []) -> void:
	if DisplayServer.get_name() == "headless": return
	# Freeze only this isolated scene during two GPU captures. Taking the real
	# foreground away gives an exact ink mask independent of generated color,
	# antialiasing, transparent padding, shadows, and disabled-state opacity.
	var previous_mode: int = app.process_mode
	app.process_mode = Node.PROCESS_MODE_DISABLED
	var foreground: Array[Control] = []
	for pair in pairs:
		for key in ["icon", "caption"]:
			var control: Control = pair[key]
			if control.is_visible_in_tree(): foreground.append(control)
	for card in stock_cards:
		var stock: Label = card.get_meta("stock")
		if stock.is_visible_in_tree(): foreground.append(stock)
	await _frames()
	await RenderingServer.frame_post_draw
	var pixels: Image = root.get_texture().get_image()
	for control in foreground: control.hide()
	await _frames()
	await RenderingServer.frame_post_draw
	var background: Image = root.get_texture().get_image()
	for control in foreground: control.show()
	app.process_mode = previous_mode
	await _frames()
	_expect(pixels != null and background != null, "Native optical alignment reads real foreground and background GPU frames")
	if pixels == null or background == null: return
	var transform: Transform2D = app.get_viewport_transform()
	var unit: float = app.editor_ui.unit
	var physical_unit: float = (transform.basis_xform(Vector2(0, unit))).length()
	for pair in pairs:
		var icon: TextureRect = pair.icon
		var caption: Label = pair.caption
		var icon_ink := _difference_ink_bounds(pixels, background, icon.get_global_rect(), transform)
		var text_ink := _difference_ink_bounds(pixels, background, caption.get_global_rect(), transform)
		var stacked: bool = pair.get("stacked", false)
		var aligned := icon_ink.end.y + 6 * physical_unit - 1 <= text_ink.position.y if stacked else absf(icon_ink.get_center().y - text_ink.get_center().y) <= 2.1
		_expect(icon_ink.has_area() and text_ink.has_area() and aligned, "%s rendered text and icon keep their intended optical alignment (icon=%s, text=%s, stacked=%s)" % [pair.name, icon_ink, text_ink, stacked])
		if not icon_ink.has_area() or not text_ink.has_area(): continue
		var treatment := "normal"
		if pair.has("button"):
			var button: Button = pair.button
			treatment = "disabled" if button.disabled else "pressed" if button.get_meta("visual_pressed", false) or (button.toggle_mode and button.button_pressed) else "normal"
			if pair.role in ["tab-idle", "tab-active", "context-action"] and not button.disabled: treatment = "normal"
		var logical_face: Rect2 = app.skin.face_rect(pair.role, pair.frame.get_global_rect(), unit, treatment)
		if stacked:
			var bubble_face: Rect2 = app.skin.face_rect("context-bubble", app.editor_ui.context_bubble.get_global_rect(), unit)
			logical_face.position.y = bubble_face.position.y
			logical_face.size.y = bubble_face.size.y
		var face: Rect2 = transform * logical_face
		var group := icon_ink.merge(text_ink)
		var padding_units := 10.0 if pair.name in ["Editing", "Coins"] else 8.0
		var minimum_padding: float = (transform.basis_xform(Vector2(padding_units * unit, 0))).length()
		var centered_horizontally: bool = pair.name == "Coins" or absf(group.get_center().x - face.get_center().x) <= 2.1
		_expect(face.grow(0.5).encloses(group) and group.position.x - face.position.x >= minimum_padding - 1 and face.end.x - group.end.x >= minimum_padding - 1 and centered_horizontally and absf(group.get_center().y - face.get_center().y) <= 2.1, "%s rendered foreground fits its material face with horizontal padding (face=%s, foreground=%s)" % [pair.name, face, group])
	if stock_cards.is_empty(): return
	var stock_clearance := true
	var stock_details: Array[String] = []
	var dock: Rect2 = transform * app.editor_ui.bottom_dock.get_global_rect()
	for card in stock_cards:
		var stock: Label = card.get_meta("stock")
		var actual_ink := _difference_ink_bounds(pixels, background, stock.get_global_rect(), transform)
		var face: Rect2 = transform * app.skin.face_rect("slot-paper", card.get_global_rect(), unit)
		stock_details.append("%s ink=%s face=%s dock=%s" % [str(card.get_meta("entry").id), actual_ink, face, dock])
		stock_clearance = stock_clearance and actual_ink.has_area() and face.end.y - actual_ink.end.y >= 10 * physical_unit - 1 and dock.position.y - actual_ink.end.y >= 24 * physical_unit - 1
	_expect(stock_clearance, "Rendered stock text leaves at least ten logical units inside each mat face and twenty-four before the bottom dock: " + "; ".join(stock_details))

func _test_curtain_feedback(app) -> void:
	var editor = app.editor_ui
	var button: Button = editor.layers.floor
	var visual: Control = button.get_meta("visual")
	var bounds := button.get_global_rect()
	var rod: Rect2 = editor.category_rod.get_global_rect()
	var rail: Rect2 = editor.category_rail.get_global_rect()
	var before: Dictionary = app.session.save_data()
	var saved := _save_bytes()
	var original_motion: bool = app.world.reduced_motion
	await _touch(app, bounds.get_center(), true, 24)
	await create_timer(0.20).timeout
	await _frames()
	_expect(visual.scale.x < 1.0 and visual.scale.x >= 0.97 and button.get_global_rect() == bounds and editor.category_rod.get_global_rect() == rod and editor.category_rail.get_global_rect() == rail and _same(before, app.session.save_data()), "Pointer down presses only the curtain artwork while keeping its target, rod, rail and saved restaurant fixed")
	_expect(_skin_source(button.get_meta("visual_surface").get_theme_stylebox("panel")) == _skin_source(editor.skin.style("tab-idle", editor.unit)), "Holding an inactive curtain preserves its current material without adding the active underline")
	var focus_shadow: StyleBox = button.get_meta("visual_focus").get_theme_stylebox("panel")
	_expect(focus_shadow is StyleBoxFlat and focus_shadow.bg_color.a == 0 and focus_shadow.get_border_width(SIDE_LEFT) == 0 and focus_shadow.shadow_size > 0, "The curtain focus cue is a transparent soft shadow that cannot paint another selection underline")
	await _touch(app, bounds.get_center(), false, 24, true)
	await create_timer(0.20).timeout
	await _frames()
	_expect(visual.scale.is_equal_approx(Vector2.ONE) and _same(before, app.session.save_data()) and _same(saved, _save_bytes()), "A canceled curtain touch restores its artwork without switching category or writing either save")
	app.world.reduced_motion = true
	app._refresh()
	await _touch(app, bounds.get_center(), true, 25)
	_expect(visual.scale.is_equal_approx(Vector2.ONE * 0.975) and button.get_global_rect() == bounds and _same(before, app.session.save_data()), "Reduced motion applies the curtain's static pressed state immediately with stable native geometry")
	await _touch(app, bounds.get_center(), false, 25)
	_expect(visual.scale.is_equal_approx(Vector2.ONE) and app.session.snapshot().editor.layer == "floor" and editor.cards.size() == 1, "Reduced-motion release restores the artwork and activates the existing Floor action")
	await _tap(app, editor.layers.layout.get_global_rect().get_center(), 25)
	app.world.reduced_motion = original_motion
	app._refresh()
	_expect(app.session.snapshot().editor.layer == "layout" and editor.cards.size() == 4, "The same category control returns to the four-good Layout page after press feedback")

func _test_curtain_lifecycle(app) -> void:
	var editor = app.editor_ui
	for probe in [{"layer": "floor", "out": Node.NOTIFICATION_APPLICATION_PAUSED, "inside": Node.NOTIFICATION_APPLICATION_RESUMED, "name": "application pause"}, {"layer": "people", "out": Node.NOTIFICATION_WM_WINDOW_FOCUS_OUT, "inside": Node.NOTIFICATION_WM_WINDOW_FOCUS_IN, "name": "window focus loss"}]:
		app.save_now()
		app.save_now()
		var before: Dictionary = app.session.save_data()
		var saved := _save_bytes()
		var button: Button = editor.layers[probe.layer]
		var visual: Control = button.get_meta("visual")
		var target := button.get_global_rect().get_center()
		await _touch(app, target, true, 27)
		app.propagate_notification(int(probe.out))
		_expect(not bool(button.get_meta("visual_pressed", false)) and visual.scale.is_equal_approx(Vector2.ONE) and not button.disabled and not button.button_pressed and editor.layers.layout.button_pressed and _same(before, app.session.save_data()), "%s immediately cancels a held inactive curtain's native press and artwork while preserving the selected category" % str(probe.name).capitalize())
		app.propagate_notification(int(probe.inside))
		await _touch(app, target, false, 27)
		_expect(_same(before, app.session.save_data()) and _same(saved, _save_bytes()) and visual.scale.is_equal_approx(Vector2.ONE), "An orphan release after %s cannot switch category or change either saved copy" % probe.name)
		await _tap(app, target, 27)
		_expect(app.session.snapshot().editor.layer == probe.layer and editor.cards.size() == (1 if probe.layer == "floor" else 3), "A fresh curtain press works normally after %s" % probe.name)
		await _tap(app, editor.layers.layout.get_global_rect().get_center(), 27)

func _sprite_point(app, identity: String) -> Vector2:
	var object := _object(app.session.snapshot(), identity)
	var ground: Vector2 = app.world.cell_base(float(object.x), float(object.y))
	var best := Vector2(INF, INF)
	var distance := INF
	for record in app.world.sprite_hits():
		if str(record.owner_id) != identity: continue
		var pixels: Image = record.texture.get_image()
		if pixels.is_compressed(): pixels.decompress()
		var region: Rect2 = record.region
		var bounds: Rect2 = record.rect
		for y in range(3, int(region.size.y), 8):
			for x in range(3, int(region.size.x), 8):
				if pixels.get_pixelv(Vector2i(region.position) + Vector2i(x, y)).a < 0.9: continue
				var point := bounds.position + (Vector2(x, y) + Vector2(0.5, 0.5)) / region.size * bounds.size
				if point.distance_squared_to(ground) >= distance or not app._floor_drop(point): continue
				if app.world.object_at(point).get("id") != identity: continue
				best = point
				distance = point.distance_squared_to(ground)
	_expect(best.is_finite(), "The %s gesture starts on a visible opaque owned sprite pixel outside protected UI" % identity)
	return best

func _valid_underlay(app, rect: Rect2, identity: String) -> Vector2:
	# Prefer the capsule's pointer/padding outside either action button.
	var samples := [Vector2(0.5, 0.94), Vector2(0.02, 0.5), Vector2(0.98, 0.5)]
	for y in [0.15, 0.5, 0.85]:
		for x in [0.15, 0.5, 0.85]: samples.append(Vector2(x, y))
	for sample in samples:
		var target: Vector2 = rect.position + rect.size * sample
		var object := _object(app.session.snapshot(), identity)
		var grab: Vector2 = _sprite_point(app, identity) - app.world.cell_base(float(object.x), float(object.y))
		var cell: Vector2i = app._cell_at(target - grab)
		var probe = Session.new()
		if probe.restore(app.session.save_data()) and probe.command({"type": "editor_move", "id": identity, "x": cell.x, "y": cell.y}).ok:
			return target
	return rect.get_center()

func _test_rejected_overlay_release(app, source: Vector2, target: Vector2, region_name: String) -> void:
	# Stabilize both canonical save copies so this exercises durable rejection,
	# not merely a renderer ghost or an in-memory object position.
	app.save_now()
	app.save_now()
	var before: Dictionary = app.session.save_data()
	var saved: Dictionary = _save_bytes()
	var selected := _object(app.session.snapshot(), str(before.state.editor.selected_id))
	var grab: Vector2 = source - app.world.cell_base(float(selected.x), float(selected.y))
	var coordinate: Vector2i = app._cell_at(target - grab)
	var probe = Session.new()
	var underlying_tile_accepts: bool = probe.restore(before) and probe.command({"type": "editor_move", "id": before.state.editor.selected_id, "x": coordinate.x, "y": coordinate.y}).ok
	await _touch(app, source, true, 23)
	await _drag(app, source, target, 23)
	_expect(underlying_tile_accepts and not app._floor_drop(target) and not app.world.editor_preview.is_empty() and not app.world.editor_preview.valid, "Selected-object dragging into %s rejects its UI region even though the underlying world tile accepts the move" % region_name)
	await _touch(app, target, false, 23)
	_expect(_same(before, app.session.save_data()) and app.editor_ui.rejection.visible, "Releasing a selected object into %s preserves arrangement, selection and inventory and shows rejection" % region_name)
	_expect(_same(saved, _save_bytes()) and _same(before, app.store.load_session()), "Rejected selected-object release into %s preserves both exact saved copies" % region_name)

func _test_active_clock_and_resume(app) -> void:
	var expected = Session.new()
	_expect(expected.restore(app.session.save_data()), "Active-clock fixture restores the public session")
	expected.advance(0.8)
	app.simulation_enabled = true
	app._process(0.8)
	_expect(_same(expected.snapshot(), app.session.snapshot()), "An ordinary slow foreground frame accounts for all active time rather than discarding time above 250 ms")
	var before_suspend: Dictionary = app.session.snapshot()
	app.notification(Node.NOTIFICATION_APPLICATION_PAUSED)
	app._process(120.0)
	_expect(_same(before_suspend, app.session.snapshot()), "Android suspension does not run restaurant service")
	app.notification(Node.NOTIFICATION_APPLICATION_RESUMED)
	app._process(120.0)
	_expect(_same(before_suspend, app.session.snapshot()), "The first resumed frame does not credit suspended time as offline income")
	expected.advance(0.1)
	app._process(0.1)
	app.simulation_enabled = false
	_expect(_same(expected.snapshot(), app.session.snapshot()), "Normal active service continues after the resumed frame")

func _test_reaction_restore(app) -> void:
	var original: RefCounted = app.session
	var probe = Session.new_session(41)
	var found := {}
	for step in range(3600):
		probe.advance(0.05)
		for customer in probe.snapshot().customers:
			var kind := "restless" if customer.restless else str(customer.preference_phase)
			if not kind in ["active", "satisfied", "expired", "restless"] or found.has(kind):
				continue
			if kind == "satisfied" and float(customer.happy_elapsed) < 0.2:
				continue
			found[kind] = true
			app.session = probe
			app._refresh()
			await _frames()
			var feedback: Dictionary = app.world.customer_feedback(customer)
			var clip: String = app.world.customer_clip(customer)
			var offset: Vector2 = app.world.customer_pose_offset(customer, app.world.cell)
			var restored = Session.new()
			var payload: Dictionary = JSON.parse_string(JSON.stringify(probe.save_data(), "", true, true))
			_expect(restored.restore(payload), "A real %s visit restores through the app's production session boundary" % kind)
			app.session = restored
			app._refresh()
			await _frames()
			var reopened: Dictionary = {}
			for current in app.world.state.customers:
				if current.id == customer.id: reopened = current
			_expect(not reopened.is_empty() and _same(feedback, app.world.customer_feedback(reopened)) and clip == app.world.customer_clip(reopened) and offset.is_equal_approx(app.world.customer_pose_offset(reopened, app.world.cell)), "Native %s feedback resumes the same reaction, timer and body pose after reopening" % kind)
			if kind == "active":
				_expect(not feedback.is_empty() and float(feedback.timer) >= 0.0 and float(feedback.timer) <= 1.0, "The actual waiting customer exposes its saved circular preference countdown")
			if kind == "satisfied":
				_expect(not feedback.is_empty() and str(feedback.clip).begins_with("happy-smile") and offset.y < 0.0, "Matched preferences use the generated happy face and brief body bounce")
			if kind == "restless":
				_expect(clip == "restless", "Unfed waiting resolves to the same customer's native restless action")
		if found.size() == 4: break
	_expect(found.size() == 4, "Normal demonstration play reaches all four feedback states in the actual native renderer")
	app.session = original
	app._refresh()
	await _frames()

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
		_expect(_skin_source(_button_surface(normal)) != _skin_source(_button_surface(pressed)) and _skin_source(_button_surface(normal)) != _skin_source(_button_surface(disabled)), "Normal, pressed and disabled controls render distinct generated atlas regions")
		await _test_optical_pairs(gallery, [_button_ink_pair(normal), _button_ink_pair(pressed), _button_ink_pair(disabled)])
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

func _test_editor_gallery() -> void:
	var gallery = APP.instantiate()
	gallery.show_editor_gallery = true
	gallery.simulation_enabled = false
	root.add_child(gallery)
	await _frames()
	_expect(gallery.editor_ui.visible and gallery.editor_ui.get_script() == load("res://scripts/editor_presentation.gd"), "Shared editor gallery instantiates the same native presentation used by gameplay")
	var pager_visual: Control = gallery.editor_ui.previous.get_meta("visual")
	var pager_surface: Panel = gallery.editor_ui.previous.get_meta("visual_surface")
	_expect(gallery.editor_ui.layers.layout.icon != null and gallery.editor_ui.cards.size() == 4 and gallery.editor_ui.previous.disabled and pager_visual.modulate.a < 1 and pager_surface.get_theme_stylebox("panel") is StyleBoxEmpty, "Shared gallery renders the same four goods, generated category icon and quiet unbacked disabled pager")
	gallery.queue_free()
	await _frames()

func _hud_rects(app) -> Dictionary:
	return {"coin": app.coin.get_global_rect(), "coin_capsule": app.coin_panel.get_global_rect(), "editing_capsule": app.editing_panel.get_global_rect(), "shop": app.shop.get_global_rect(), "edit": app.edit.get_global_rect(), "staff": app.staff.get_global_rect()}

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
		if not app.world.art.objects.has(key):
			continue
		var entry: Dictionary = app.world.art.objects[key]
		var clip_id: String = "static" if entry.clips.has("static") else str(entry.clips.keys()[0])
		var clip_record: Dictionary = entry.clips[clip_id]
		var direction: String = "S" if clip_record.directions.has("S") else str(clip_record.directions.keys()[0])
		var texture: Texture2D = app.world.art.get_texture(key, clip_id, direction, 0.0)
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
