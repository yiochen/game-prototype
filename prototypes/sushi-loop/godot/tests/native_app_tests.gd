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
	"plant-angular", "lantern-gold", "barrel-wood", "crate-wood", "entry-finished",
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
	var surfaces: Array = [app.shop.get_theme_stylebox("normal"), app.edit.get_theme_stylebox("normal"), app.staff.get_theme_stylebox("normal"), editor.live.get_meta("visual_surface").get_theme_stylebox("panel"), editor.previous.get_meta("visual_surface").get_theme_stylebox("panel"), editor.tray.get_theme_stylebox("panel"), editor.category_rail.get_theme_stylebox("panel"), editor.context_bubble.get_theme_stylebox("panel"), editor.inspection_panel.get_theme_stylebox("panel"), editor.inspection_preview_panel.get_theme_stylebox("panel"), editor.rejection.get_theme_stylebox("normal"), editor.category_rod.get_theme_stylebox("panel"), editor.bottom_dock.get_theme_stylebox("panel")]
	surfaces.append(app.coin_panel.get_theme_stylebox("panel"))
	surfaces.append(app.editing_panel.get_theme_stylebox("panel"))
	var generated := true
	var calibrated := true
	for surface in surfaces:
		generated = generated and not _skin_source(surface).is_empty()
		calibrated = calibrated and _skin_calibrated(surface, editor.skin, unit)
	_expect(generated, "Every rendered HUD control, hanging rod, bottom dock, drawer, context capsule, profile well, modal and toast uses the coordinated generated B family")
	_expect(calibrated, "Generated surfaces retain their documented fixed corner edges and content insets at the actual viewport scale")
	_expect(_skin_source(surfaces[0]) == _skin_source(surfaces[1]) and _skin_source(surfaces[1]) == _skin_source(surfaces[2]), "Shop, Edit and Staff share the same neutral ceramic native frame")
	_expect(_skin_source(editor.live.get_meta("visual_surface").get_theme_stylebox("panel")) != _skin_source(app.edit.get_theme_stylebox("normal")), "Live has the distinct generated vermilion primary surface")
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

func _test_configured_camera(app) -> void:
	var original: RefCounted = app.session
	app.session = load("res://scripts/session.gd").new_session(41, {"floor": {"viewport_columns": 6, "rows": 30}})
	app._refresh()
	app._layout()
	await _frames()
	_expect(is_equal_approx(app.world.cell, (app.world.portrait.size.x - 48.0) / 6.0), "Configured visible column count determines the actual square cell pitch")
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
	_expect(final_row.y + app.world.cell * 0.5 <= app.editor_ui.occlusion_top() + 0.01 and final_row.y - app.world.cell * 0.5 >= app.world.portrait.position.y + 145.0 * app.editor_ui.unit, "Editor vertical panning reveals the entire final floor row above the rail, including in tall windows with a centered floor")
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
	_expect(horizontal and rail_rect.encloses(app.editor_ui.shop.get_global_rect()) and app.editor_ui.shop.get_global_rect().position.x >= prior_right, "People, Layout, Floor and quiet Shop form one horizontal category rail with all names visible")
	_expect(app.editor_ui.tray.get_global_rect().position.y >= rail_rect.end.y - 0.01, "The compact cream drawer begins below the separate hanging category panels")
	_test_compact_inventory(app)
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
	var closing_backing: Rect2 = app.editor_ui.inventory_backing.get_global_rect()
	var covered_floor := closing_backing.position + closing_backing.size * Vector2(0.15, 0.85)
	_expect(not app._floor_drop(covered_floor), "The moving cream backing blocks floor drops throughout the closing transition")
	var before_backing_gesture: Dictionary = app.session.save_data()
	await _touch(app, covered_floor, true, 26)
	await _drag(app, covered_floor, covered_floor + Vector2(app.world.cell * 0.35, 0), 26)
	await _touch(app, covered_floor + Vector2(app.world.cell * 0.35, 0), false, 26)
	_expect(_same(before_backing_gesture, app.session.save_data()), "A real touch and drag beginning on the moving cream backing cannot pan or select the covered floor")
	await create_timer(0.23).timeout
	_expect(not app.session.snapshot().editor.tray_open and not app.editor_ui.tray.visible and app.editor_ui.category_rail.visible and app.editor_ui.shop.visible, "Tapping the active layer collapses the drawer and keeps the category rail and Shop available")
	_expect(app.editor_ui.inventory_backing.get_global_rect().encloses(app.editor_ui.category_rail.get_global_rect()) and app.editor_ui.bottom_dock.is_visible_in_tree(), "The collapsed category panels still hang over cream with a visible bottom dock")
	_expect(app.editor_ui.category_rail.get_global_rect().end.y <= app.editor_ui.bottom_dock.get_global_rect().position.y + 0.01, "The collapsed curtain row reserves space above the bottom dock so the selected underline remains visible")
	await _tap(app, app.editor_ui.layers.layout.get_global_rect().get_center())
	var seat := _object(app.session.snapshot(), "seat-1")
	if seat.is_empty():
		for candidate in app.session.snapshot().objects:
			if candidate.kind == "seat": seat = candidate; break
	var seat_id: String = str(seat.id)
	var at: Vector2 = app.world.cell_base(float(seat.x), float(seat.y))
	await _touch(app, at, true, 16)
	await _drag(app, at, at - Vector2(app.world.cell, 0), 16)
	await _touch(app, at - Vector2(app.world.cell, 0), false, 16)
	_expect(int(_object(app.session.snapshot(), seat_id).x) == int(seat.x) and float(app.session.snapshot().camera.x) > 0 and str(app.session.snapshot().editor.selected_id).is_empty(), "Dragging an unselected object pans instead of moving it or selecting it")
	app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
	app._refresh()
	await _tap(app, at)
	_expect(app.session.snapshot().editor.selected_id == seat_id and app.editor_ui.rotate.visible and app.editor_ui.remove.visible and app.editor_ui.context_bubble.visible and app.editor_ui.context_bubble.get_global_rect().encloses(app.editor_ui.rotate.get_global_rect()) and app.editor_ui.context_bubble.get_global_rect().encloses(app.editor_ui.remove.get_global_rect()) and app.editor_ui.rotate.text == "Rotate" and app.editor_ui.remove.text == "Return", "Tapping a floor object exposes labelled Rotate and Return in one contextual ceramic capsule")
	var pointer: Rect2 = app.editor_ui.context_pointer.get_global_rect()
	var capsule: Rect2 = app.editor_ui.context_bubble.get_global_rect()
	_expect(pointer.position.y >= capsule.end.y - 28 * app.editor_ui.unit and pointer.end.y <= capsule.end.y + 1 * app.editor_ui.unit, "The context pointer occupies the capsule's lower material edge instead of floating beneath its bounds")
	var destination: Vector2 = app.world.cell_base(3, 5)
	await _touch(app, at, true, 12)
	await _drag(app, at, destination, 12)
	_expect(not app.world.editor_preview.is_empty() and app.world.editor_preview.valid, "An actual selected-object drag shows a valid registered tile preview")
	await _touch(app, destination, false, 12)
	var moved := _object(app.session.snapshot(), seat_id)
	_expect(int(moved.x) == 3 and int(moved.y) == 5 and app.session.snapshot().editor.selected_id == seat_id, "Releasing the selected-object drag moves it and leaves it selected")
	var before_rejection: Dictionary = app.session.save_data()
	var blocked: Vector2 = app.world.cell_base(3, 6)
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
	await _test_rejected_overlay_release(app, app.world.cell_base(3, 5), outside_portrait, "outside the portrait over an otherwise valid world tile")
	app.session.command({"type": "set_camera", "x": 0.0, "y": 0.0})
	app._refresh()
	var facing: String = str(moved.facing)
	await _tap(app, app.editor_ui.rotate.get_global_rect().get_center())
	_expect(_object(app.session.snapshot(), seat_id).facing != facing and app.session.snapshot().editor.selected_id == seat_id, "The native Rotate button turns the selected object without losing selection")
	await _tap(app, app.editor_ui.cards[0].get_global_rect().get_center())
	_expect(str(app.session.snapshot().editor.selected_id).is_empty() and not app.armed_item.is_empty() and not app.editor_ui.rotate.visible and not app.editor_ui.remove.visible, "Arming Layout inventory clears the old floor selection so object tools cannot target a different object")
	await _tap(app, app.editor_ui.layers.people.get_global_rect().get_center())
	await _tap(app, app.editor_ui.layers.layout.get_global_rect().get_center())
	await _tap(app, app.world.cell_base(3, 5))
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
	await _tap(app, app.editor_ui.next.get_global_rect().get_center())
	_expect(int(app.session.snapshot().editor.page) == 1 and app.editor_ui.page_announcement.accessibility_name == "Layout page 2 of 2" and not app.editor_ui.previous.disabled and app.editor_ui.next.disabled and app.editor_ui.cards.size() == 1 and app.editor_ui.cards[0].get_meta("entry").id == "barrel-wood", "The edge caret reaches the fifth good on the final page with correct boundaries and an accessible announcement")
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
	_expect(_skin_calibrated(app.recovery.get_theme_stylebox("panel"), app.skin, app.editor_ui.unit) and _skin_source(app.recovery_retry.get_theme_stylebox("normal")) == _skin_source(app.skin.style("control-green", app.editor_ui.unit)) and _skin_source(app.recovery_close.get_theme_stylebox("normal")) == _skin_source(app.skin.style("control-wood", app.editor_ui.unit)) and app.recovery_title.get_theme_color("font_color") == Color("233d58"), "Save retry uses the same calibrated cream recovery panel, navy type and vermilion primary as the editor")
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
	_expect(app.session.restore(original), "The large-balance HUD probe restores the exact paused restaurant")
	app._refresh()
	app._layout()
	await _frames()

func _test_compact_inventory(app) -> void:
	var editor = app.editor_ui
	var unit: float = editor.unit
	var backing: Rect2 = editor.inventory_backing.get_global_rect()
	_expect(editor.cards.size() == 4 and backing.encloses(editor.category_rail.get_global_rect()) and backing.encloses(editor.tray.get_global_rect()), "One continuous cream backing covers the hanging-panel gaps and the four-good inventory drawer")
	_expect(editor.tray.size.y <= 225 * unit and editor.bottom_dock.is_visible_in_tree() and app.world.portrait.encloses(editor.bottom_dock.get_global_rect()), "The shorter drawer retains its generated dock inside the portrait bottom edge")
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
		accessible = accessible and physical.size.x >= 44 and physical.size.y >= 44 and label.text == captions[index] and card.accessibility_name == str(item.name)
		for pager in [editor.previous, editor.next]:
			independent = independent and not bounds.intersects(pager.get_global_rect())
	_expect(goods_ready, "Every visible Layout good loads its dedicated Blender atlas region instead of a live-scene sprite")
	_expect(compact and accessible, "Four smaller goods, short captions and quiet stock fit their mats while retaining full accessible names and 44-pixel targets")
	for pager in [editor.previous, editor.next]:
		var visual: Control = pager.get_meta("visual")
		var material: Panel = pager.get_meta("visual_surface")
		independent = independent and pager.get_global_rect().encloses(material.get_global_rect()) and material.size.x <= 44 * unit and is_equal_approx(material.size.y, editor.cards[0].size.y) and _skin_source(material.get_theme_stylebox("panel")) == _skin_source(editor.cards[0].get_theme_stylebox("normal"))
	_expect(independent, "Narrow paging surfaces match the goods height and material while their full native touch areas avoid every item")
	var previous_end: float = editor.category_rail.get_global_rect().position.x
	var separated := true
	for layer in ["people", "layout", "floor"]:
		var button: Button = editor.layers[layer]
		var visual: Control = button.get_meta("visual")
		var surface: Control = button.get_meta("visual_surface")
		var rect := surface.get_global_rect()
		separated = separated and button.is_visible_in_tree() and visual.is_visible_in_tree() and button.self_modulate.a == 0 and visual.modulate.a > 0 and visual.get_global_rect().encloses(rect) and rect.position.x > previous_end and backing.encloses(rect)
		previous_end = rect.end.x
	_expect(separated and editor.category_rod.is_visible_in_tree(), "Each curtain is a separate visible artwork panel with cream gaps under one fixed shared rod")
	for button in [editor.live, editor.shop]:
		var visual: Control = button.get_meta("visual")
		_expect(button.get_global_rect().encloses(visual.get_global_rect()) and is_equal_approx(visual.size.y, button.size.y) and visual.size.y >= 100 * unit - 0.01, "%s renders the full-height rounded capsule within its native touch target" % button.text)

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

func _valid_underlay(app, rect: Rect2, identity: String) -> Vector2:
	# Prefer the capsule's pointer/padding outside either action button.
	var samples := [Vector2(0.5, 0.94), Vector2(0.02, 0.5), Vector2(0.98, 0.5)]
	for y in [0.15, 0.5, 0.85]:
		for x in [0.15, 0.5, 0.85]: samples.append(Vector2(x, y))
	for sample in samples:
		var target: Vector2 = rect.position + rect.size * sample
		var cell: Vector2i = app._cell_at(target)
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
	var coordinate: Vector2i = app._cell_at(target)
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
		_expect(_skin_source(normal.get_theme_stylebox("normal")) != _skin_source(pressed.get_theme_stylebox("pressed")) and _skin_source(normal.get_theme_stylebox("normal")) != _skin_source(disabled.get_theme_stylebox("disabled")), "Normal, pressed and disabled controls render distinct generated atlas regions")
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
	_expect(gallery.editor_ui.layers.layout.icon != null and gallery.editor_ui.cards.size() == 4 and gallery.editor_ui.previous.disabled and pager_visual.modulate.a < 1 and _skin_source(pager_surface.get_theme_stylebox("panel")) == _skin_source(gallery.editor_ui.skin.style("slot-paper", gallery.editor_ui.unit, "disabled")), "Shared gallery renders the same four goods, generated category icon and quiet disabled mat pager")
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
