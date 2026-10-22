extends Control

const Session = preload("res://scripts/session.gd")
const Persistence = preload("res://scripts/save_store.gd")
const RestaurantView = preload("res://scripts/restaurant_view.gd")
const Audio = preload("res://scripts/audio.gd")
const Typography = preload("res://scripts/typography.gd")
const EditorPresentation = preload("res://scripts/wood_editor_presentation.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const ScreenLayout = preload("res://scripts/screen_layout.gd")
const INK := Color("233d58")
const CREAM := Color("fff3db")
var session: Session
var store: Persistence
var world: RestaurantView
var world_clip: Control
var audio: Audio
var show_gallery := false
var show_editor_gallery := false
var editor_ui: EditorPresentation
var pointer_start := Vector2.ZERO
var gesture_kind := ""
var gesture_dragged := false
var gesture_object := ""
var gesture_item: Dictionary = {}
var armed_item: Dictionary = {}
var gesture_cell := Vector2i.ZERO
var tap_object := ""
var gesture_grab_offset := Vector2.ZERO # Pointer offset from the object's ground root, in tiles.
var gesture_started_in_tray := false
var previous_selection := ""
var selection_tween: Tween
var simulation_enabled := true
var money: Label
var editing_cue: Label
var coin: TextureRect
var coin_panel: Panel
var editing_panel: Panel
var editing_icon: TextureRect
var shop: Button
var edit: Button
var staff: Button
var gallery_buttons: Array[Button] = []
var autosave_elapsed := 0.0
var pointer := -1
var previous_pointer := Vector2.ZERO
var last_screen_press := Vector2.ZERO
var backgrounded := false
var skip_resume_frame := false
var save_error := ""
var body_font: Font
var display_font: Font
var save_blocked := false
var pending_edit_save := false
var recovery: Panel
var recovery_title: Label
var recovery_message: Label
var recovery_retry: Button
var recovery_close: Button
var skin: UISkin

func _ready() -> void:
	# Godot defaults to quitting on Android Back before modal UI can own it.
	get_tree().quit_on_go_back = false
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	show_gallery = show_gallery or "--gallery" in OS.get_cmdline_user_args()
	show_editor_gallery = show_editor_gallery or "--editor-gallery" in OS.get_cmdline_user_args()
	store = Persistence.new()
	session = Session.new_session(int(Time.get_unix_time_from_system()) % 2147483647)
	if not show_gallery and not show_editor_gallery:
		var saved: Dictionary = store.load_session(_valid_saved_session)
		if not saved.is_empty():
			if not session.restore(saved):
				save_error = "The saved restaurant could not be restored."
		elif not store.last_error.is_empty():
			save_error = store.last_error
			save_blocked = true
	body_font = Typography.body()
	display_font = Typography.heading()
	skin = UISkin.new()
	audio = Audio.new()
	audio.set_muted(show_gallery or show_editor_gallery or save_blocked)
	add_child(audio)
	world = RestaurantView.new()
	world.show_gallery = show_gallery
	world_clip = Control.new()
	world_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	world_clip.clip_contents = true
	add_child(world_clip)
	world_clip.add_child(world)
	world.state = session.snapshot()
	coin_panel = Panel.new()
	coin_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(coin_panel)
	editing_panel = Panel.new()
	editing_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(editing_panel)
	coin = TextureRect.new()
	coin.texture = skin.icon_ink("coin")
	coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	coin.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	coin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(coin)
	money = Label.new()
	money.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	money.add_theme_font_override("font", body_font)
	money.add_theme_color_override("font_color", INK)
	money.add_theme_constant_override("shadow_offset_x", 0)
	money.add_theme_constant_override("shadow_offset_y", 0)
	money.accessibility_name = "Coins"
	money.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(money)
	editing_cue = Label.new()
	editing_cue.text = "Editing"
	editing_cue.add_theme_font_override("font", body_font)
	editing_cue.add_theme_color_override("font_color", INK)
	editing_cue.accessibility_name = "Editing restaurant"
	editing_cue.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(editing_cue)
	editing_icon = TextureRect.new()
	editing_icon.texture = skin.icon_ink("edit")
	editing_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	editing_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	editing_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(editing_icon)
	shop = make_button("Shop", "shop", true)
	edit = make_button("Edit", "edit", false)
	staff = make_button("Staff", "people", true)
	editor_ui = EditorPresentation.new()
	add_child(editor_ui)
	editor_ui.command_requested.connect(_editor_command)
	editor_ui.item_pointer.connect(_inventory_pointer)
	editor_ui.item_armed.connect(_arm_item)
	edit.pressed.connect(func(): _editor_command({"type": "set_mode", "mode": "edit"}))
	if show_editor_gallery:
		session.command({"type": "set_mode", "mode": "edit"})
		session.command({"type": "editor_layer", "layer": "layout"})
	if show_gallery:
		edit.hide()
		staff.hide()
		for mode in ["Normal", "Pressed", "Disabled"]:
			var button := make_button(mode, "shop", mode == "Disabled")
			if mode == "Pressed":
				button.toggle_mode = true
				button.button_pressed = true
			gallery_buttons.append(button)
	if save_blocked:
		_make_recovery()
	resized.connect(_layout)
	_layout()
	_refresh()
	if not show_gallery and not show_editor_gallery:
		save_now()

func make_button(text: String, icon_name: String, disabled := false) -> Button:
	var button := Button.new()
	button.text = text
	button.icon = skin.icon_ink(icon_name)
	button.expand_icon = true
	button.disabled = disabled
	button.accessibility_name = text
	button.add_theme_font_override("font", body_font)
	button.add_theme_color_override("font_color", INK)
	button.add_theme_color_override("font_hover_color", INK)
	button.add_theme_color_override("font_pressed_color", INK)
	button.add_theme_color_override("font_hover_pressed_color", INK)
	button.add_theme_color_override("font_focus_color", INK)
	button.add_theme_color_override("font_disabled_color", Color("75828b"))
	button.add_theme_color_override("icon_disabled_color", Color("8e9ba5"))
	# Native text remains available to accessibility and focus. Its own draw is
	# hidden so generated padding and font line-box reserves cannot offset ink.
	button.self_modulate.a = 0.0
	var visual := Control.new()
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	button.add_child(visual)
	for key in ["visual_surface", "visual_focus"]:
		var panel := Panel.new()
		panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		visual.add_child(panel)
		button.set_meta(key, panel)
	var icon := TextureRect.new()
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.add_child(icon)
	button.set_meta("visual_icon", icon)
	var caption := Label.new()
	caption.add_theme_font_override("font", body_font)
	caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.add_child(caption)
	button.set_meta("visual_label", caption)
	button.set_meta("visual", visual)
	button.button_down.connect(func(): _style_native_button(button, float(button.get_meta("skin_unit", 1.0)), true))
	button.button_up.connect(func(): _style_native_button(button, float(button.get_meta("skin_unit", 1.0)), false))
	button.mouse_exited.connect(func(): _style_native_button(button, float(button.get_meta("skin_unit", 1.0)), false))
	button.focus_entered.connect(func(): _style_native_button(button, float(button.get_meta("skin_unit", 1.0))))
	button.focus_exited.connect(func(): _style_native_button(button, float(button.get_meta("skin_unit", 1.0)), false))
	button.toggled.connect(func(_pressed: bool): _style_native_button(button, float(button.get_meta("skin_unit", 1.0))))
	_style_native_button(button, 1.0)
	add_child(button)
	button.pressed.connect(func(): audio.play_cue("click"))
	return button

func _style_native_button(button: Button, unit: float, held = null) -> void:
	button.set_meta("skin_unit", unit)
	if held is bool: button.set_meta("visual_pressed", held)
	var role := str(button.get_meta("skin_role", "control-wood"))
	for kind in ["normal", "hover", "pressed", "disabled"]:
		button.add_theme_stylebox_override(kind, StyleBoxEmpty.new())
	button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	button.custom_minimum_size = Vector2(100, 100) * unit
	for kind in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(kind, CREAM if role == "control-green" else INK)
	button.add_theme_constant_override("h_separation", int(10 * unit))
	button.add_theme_constant_override("outline_size", 0)
	var treatment := "disabled" if button.disabled else "pressed" if button.get_meta("visual_pressed", false) or (button.toggle_mode and button.button_pressed) else "normal"
	var visual: Control = button.get_meta("visual")
	visual.size = button.size
	visual.modulate.a = 0.45 if button.disabled else 1.0
	var surface: Panel = button.get_meta("visual_surface")
	skin.apply_panel(surface, role, unit, treatment)
	surface.size = visual.size
	var focus_panel: Panel = button.get_meta("visual_focus")
	var focus := StyleBoxFlat.new()
	focus.bg_color = Color.TRANSPARENT
	focus.shadow_color = Color(0.78, 0.28, 0.15, 0.6)
	focus.shadow_size = maxi(2, int(6 * unit))
	focus.set_corner_radius_all(maxi(1, int(42 * unit)))
	focus_panel.add_theme_stylebox_override("panel", focus)
	focus_panel.size = visual.size
	focus_panel.visible = button.has_focus()
	var face := skin.face_rect(role, Rect2(Vector2.ZERO, visual.size), unit, treatment)
	var icon: TextureRect = button.get_meta("visual_icon")
	icon.texture = button.icon
	var icon_width := float(button.get_theme_constant("icon_max_width"))
	var fitted_icon := UISkin.fit_rect(icon.texture.get_size(), Rect2(Vector2.ZERO, Vector2.ONE * icon_width)).size
	var caption: Label = button.get_meta("visual_label")
	caption.text = button.text
	caption.add_theme_color_override("font_color", CREAM if role == "control-green" else INK)
	var font_size := button.get_theme_font_size("font_size")
	var available_width := maxf(0.0, face.size.x - fitted_icon.x - 26 * unit)
	while font_size > maxi(8, int(20 * unit)) and UISkin.caption_ink(body_font, button.text, font_size).size.x > available_width:
		font_size -= 1
	var text_width := UISkin.caption_ink(body_font, button.text, font_size).size.x
	var group_width := fitted_icon.x + 10 * unit + text_width
	var left := face.get_center().x - group_width * 0.5
	icon.position = Vector2(left, face.get_center().y - fitted_icon.y * 0.5)
	icon.size = fitted_icon
	UISkin.layout_caption(caption, Rect2(left + fitted_icon.x + 10 * unit, face.position.y, text_width, face.size.y), font_size)

func _layout_hud(area: Rect2, unit: float) -> void:
	var top: float = area.position.y + (124 * unit if show_gallery else 32 * unit)
	coin_panel.position = Vector2(area.position.x + 24 * unit, top)
	skin.apply_panel(coin_panel, "coin-panel", unit)
	coin_panel.size = Vector2(240, 100) * unit
	var coin_face := skin.face_rect("coin-panel", Rect2(coin_panel.position, coin_panel.size), unit)
	var coin_fit := UISkin.fit_rect(coin.texture.get_size(), Rect2(coin_face.position.x + 10 * unit, coin_face.get_center().y - 27 * unit, 54 * unit, 54 * unit))
	coin.position = coin_fit.position
	coin.size = coin_fit.size
	var money_frame := Rect2(coin_face.position.x + 76 * unit, coin_face.position.y, coin_face.size.x - 90 * unit, coin_face.size.y)
	# A larger earned balance must stay inside its own capsule without covering
	# Editing or Live. Measure the actual typeface rather than counting digits.
	var balance_text := str(session.snapshot().get("coins", 0))
	money.set_meta("full_balance", balance_text)
	money.text = balance_text
	money.accessibility_description = balance_text + " coins"
	var font_size := int(38 * unit)
	while font_size > maxi(8, int(20 * unit)) and body_font.get_string_size(money.text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x > money_frame.size.x:
		font_size -= 1
	if body_font.get_string_size(money.text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x > money_frame.size.x:
		# Preserve the full amount in the save and accessibility description;
		# extremely large earnings use a readable compact caption, not tiny text.
		var magnitude := mini(6, int((balance_text.length() - 1) / 3.0))
		var leading := balance_text.length() - magnitude * 3
		money.text = balance_text.substr(0, leading)
		var decimal := balance_text.substr(leading, 1)
		if not decimal.is_empty() and decimal != "0": money.text += "." + decimal
		money.text += ["", "K", "M", "B", "T", "Qa", "Qi"][magnitude]
	UISkin.layout_caption(money, money_frame, font_size)
	editing_panel.position = Vector2(area.position.x + 280 * unit, top)
	skin.apply_panel(editing_panel, "control-wood", unit)
	editing_panel.size = Vector2(190, 100) * unit
	var editing_face := skin.face_rect("control-wood", Rect2(editing_panel.position, editing_panel.size), unit)
	var editing_font_size := maxi(8, int(28 * unit))
	var caption_width := UISkin.caption_ink(body_font, editing_cue.text, editing_font_size).size.x
	var editing_icon_size := UISkin.fit_rect(editing_icon.texture.get_size(), Rect2(Vector2.ZERO, Vector2.ONE * 30 * unit)).size
	var group_width := editing_icon_size.x + 10 * unit + caption_width
	var group_left := editing_face.get_center().x - group_width * 0.5
	editing_icon.position = Vector2(group_left, editing_face.get_center().y - editing_icon_size.y * 0.5)
	editing_icon.size = editing_icon_size
	UISkin.layout_caption(editing_cue, Rect2(group_left + editing_icon_size.x + 10 * unit, editing_face.position.y, caption_width, editing_face.size.y), editing_font_size)

func _place_native_button(button: Button, bounds: Rect2, unit: float, font_size: float, icon_width: float) -> void:
	# Lower the previous viewport's native minimum before assigning the new
	# rectangle; Control would otherwise clamp a phone pill to its old size.
	button.custom_minimum_size = Vector2(100, 100) * unit
	button.add_theme_font_size_override("font_size", maxi(1, int(font_size * unit)))
	button.add_theme_constant_override("icon_max_width", maxi(1, int(icon_width * unit)))
	button.position = bounds.position
	button.size = bounds.size
	_style_native_button(button, unit)

func _display_safe_top() -> float:
	if OS.get_name() not in ["Android", "iOS"]: return 0.0
	return ScreenLayout.top_inset(Rect2(DisplayServer.get_display_safe_area()), DisplayServer.get_display_cutouts(), get_viewport_transform(), float(get_window().size.y))

func _layout() -> void:
	_layout_for_safe_top(_display_safe_top())

func _layout_for_safe_top(top_inset: float) -> void:
	if world == null:
		return
	world.size = size
	world.safe_top = top_inset
	world.update_layout()
	var scene_area: Rect2 = world.portrait
	# Keep world coordinates identical to the root's input coordinates while the
	# containing control clips adjoining floor in a wide native window.
	world_clip.position = scene_area.position
	world_clip.size = scene_area.size
	world.position = -scene_area.position
	var area: Rect2 = world.hud_area()
	var unit: float = area.size.x / 720.0
	_layout_hud(area, unit)
	_place_native_button(shop, Rect2(Vector2(area.position.x + (440 * unit if show_gallery else 34 * unit), area.position.y + (112 * unit if show_gallery else 145 * unit)), Vector2(224, 108) * unit), unit, 34, 48)
	_place_native_button(edit, Rect2(Vector2(area.position.x + 34 * unit, area.end.y - 156 * unit), Vector2(206, 110) * unit), unit, 34, 48)
	_place_native_button(staff, Rect2(Vector2(area.position.x + 266 * unit, area.end.y - 156 * unit), Vector2(214, 110) * unit), unit, 34, 48)
	for i in range(gallery_buttons.size()):
		var button: Button = gallery_buttons[i]
		_place_native_button(button, Rect2(Vector2(area.position.x + (38 + i * 220) * unit, area.end.y - 185 * unit), Vector2(206, 110) * unit), unit, 34, 38)
	# Editor controls share the same contained portrait and root input coordinates.
	editor_ui.size = size
	editor_ui.set_state(session.snapshot(), area)
	if recovery != null:
		recovery.add_theme_stylebox_override("panel", skin.style("container-modal", unit))
		recovery.position = area.position + Vector2(34 * unit, area.size.y * 0.28)
		recovery.size = Vector2(652, 680) * unit
		recovery_title.position = Vector2(32, 32) * unit
		recovery_title.size = Vector2(588, 120) * unit
		recovery_title.add_theme_font_size_override("font_size", int(44 * unit))
		recovery_message.position = Vector2(32, 170) * unit
		recovery_message.size.x = 588 * unit
		recovery_message.add_theme_font_size_override("font_size", int(36 * unit))
		recovery_message.size = Vector2(588, 300) * unit
		_place_native_button(recovery_retry, Rect2(Vector2(32, 500) * unit, Vector2(288, 110) * unit), unit, 34, 44)
		_place_native_button(recovery_close, Rect2(Vector2(344, 500) * unit, Vector2(276, 110) * unit), unit, 34, 44)

func _process(delta: float) -> void:
	if session == null or backgrounded or save_blocked:
		return
	# An Android resume must not turn the suspended frame into offline income.
	# Ordinary foreground frame delays still belong to the active session.
	if skip_resume_frame:
		skip_resume_frame = false
		return
	if not show_gallery and not show_editor_gallery and simulation_enabled:
		var events: Array = advance_time(delta)
		if not events.is_empty():
			save_now()
		autosave_elapsed += delta
		if autosave_elapsed >= 3.0:
			save_now()
			autosave_elapsed = 0.0
	else:
		world.time += delta
	world.sale_pops = world.sale_pops.filter(func(pop: Dictionary): return world.time - float(pop.time) < 1.0)
	_refresh()

func advance_time(elapsed: float) -> Array:
	if save_blocked:
		return []
	world.time += elapsed
	var events: Array = session.advance(elapsed)
	for event in events:
		audio.play_cue(str(event.type))
		if event.type == "sale":
			world.sale_pops.append({"x": event.x, "y": event.y, "time": world.time})
	_refresh()
	return events

func _refresh() -> void:
	world.state = session.snapshot()
	var coins_text := str(int(world.state.coins))
	if money.get_meta("full_balance", "") != coins_text:
		money.text = coins_text
		money.accessibility_description = "%s coins" % coins_text
		_layout_hud(world.hud_area(), world.portrait.size.x / 720.0)
	var editing: bool = world.state.get("mode", "live") == "edit"
	editing_cue.visible = editing and not show_gallery
	editing_panel.visible = editing_cue.visible
	editing_icon.visible = editing_cue.visible
	shop.visible = show_gallery or not editing
	edit.visible = not show_gallery and not editing
	staff.visible = not show_gallery and not editing
	editor_ui.reduced_motion = world.reduced_motion
	editor_ui.set_state(world.state, world.hud_area())
	var selected_id: String = str(world.state.get("editor", {}).get("selected_id", ""))
	if selected_id != previous_selection:
		previous_selection = selected_id
		if selection_tween != null and selection_tween.is_valid(): selection_tween.kill()
		world.editor_selection_alpha = 1.0 if world.reduced_motion else 0.0
		if not world.reduced_motion:
			selection_tween = create_tween()
			selection_tween.tween_property(world, "editor_selection_alpha", 1.0, 0.14).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	var selected := _selected_object()
	editor_ui.set_selection(world.cell_base(float(selected.get("x", 0)), float(selected.get("y", 0))), editing and not selected.is_empty())
	world.queue_redraw()

func save_now() -> bool:
	if save_blocked:
		return false
	if show_gallery or show_editor_gallery or session == null or store == null:
		return true
	var success: bool = store.save_session(session.save_data())
	save_error = "" if success else store.last_error
	return success

func _selected_object() -> Dictionary:
	var scene: Dictionary = session.snapshot()
	var identity: String = str(scene.get("editor", {}).get("selected_id", ""))
	for object in scene.objects:
		if str(object.id) == identity: return object
	return {}

func _editor_command(value: Dictionary) -> Dictionary:
	if save_blocked: return {"ok": false, "reason": "save_blocked"}
	if value.get("type") == "editor_shop":
		# The drawer shortcut exposes the existing unavailable feature without
		# introducing purchases or mutating the paused restaurant.
		audio.play_cue("click")
		editor_ui.reject("shop_unavailable")
		return {"ok": false, "reason": "shop_unavailable"}
	var result: Dictionary = session.command(value)
	if result.get("ok", false):
		if value.type in ["set_mode", "editor_layer", "editor_remove"]:
			armed_item.clear()
			editor_ui.active_item = ""
		if value.type == "set_mode":
			_cancel_gesture()
		audio.play_cue("click")
		if not save_now(): _block_edit_save()
	else:
		editor_ui.reject(str(result.get("reason", "invalid_position")))
	_refresh()
	return result

func _block_edit_save() -> void:
	# The accepted edit remains in memory. Stop further mutations until the
	# same pending restaurant can be durably written; never reload old data
	# over the unsaved arrangement merely because Retry was pressed.
	pending_edit_save = true
	save_blocked = true
	audio.set_muted(true)
	_cancel_gesture()
	if recovery == null: _make_recovery()
	_layout()

func _arm_item(item: Dictionary) -> void:
	if gesture_dragged: return
	if item.kind == "chef":
		editor_ui.inspect(item)
		return
	_editor_command({"type": "editor_select", "id": null})
	if save_blocked: return
	armed_item = item.duplicate(true)
	editor_ui.active_item = str(item.id)
	_refresh()

func _inventory_pointer(item: Dictionary, event: InputEvent) -> void:
	if not event is InputEventScreenTouch or not event.pressed or pointer != -1: return
	# Defer arming, selection and placement until direction is owned.
	pointer = event.index
	pointer_start = last_screen_press
	previous_pointer = pointer_start
	gesture_kind = "inventory_pending"
	gesture_started_in_tray = true
	gesture_item = item.duplicate(true)
	gesture_dragged = false
	gesture_object = str(item.get("id", "")) if item.get("assigned", false) else ""

func _pickup_allowed() -> bool:
	return not gesture_item.is_empty() and gesture_item.get("available",true) and (int(gesture_item.get("count",0))>0 or gesture_item.get("assigned",false))

func _begin_inventory_pickup() -> void:
	if not str(session.snapshot().editor.selected_id).is_empty():
		_editor_command({"type":"editor_select","id":null})
	armed_item = gesture_item.duplicate(true)
	editor_ui.active_item = str(gesture_item.id)
	_refresh()

func _cell_at(position_value: Vector2) -> Vector2i:
	var camera: Dictionary = session.snapshot().camera
	var coordinate := (_world_position(position_value) - world.floor_origin) / world.cell + Vector2(float(camera.x), float(camera.y))
	return Vector2i(floori(coordinate.x), floori(coordinate.y))

func _world_position(position_value: Vector2) -> Vector2:
	return world.get_global_transform().affine_inverse() * get_global_transform() * position_value

func _placement_cell_at(position_value: Vector2) -> Vector2i:
	if gesture_kind != "object": return _cell_at(position_value)
	var ground := _world_position(position_value) - gesture_grab_offset * world.cell
	var camera: Dictionary = session.snapshot().camera
	var coordinate := (ground - world.floor_origin) / world.cell + Vector2(float(camera.x), float(camera.y))
	return Vector2i(floori(coordinate.x), floori(coordinate.y))

func _object_at(position_value: Vector2) -> Dictionary:
	return world.object_at(_world_position(position_value))

func _unhandled_input(event: InputEvent) -> void:
	if session == null or show_gallery or save_blocked or pointer != -1: return
	if not event is InputEventScreenTouch or not event.pressed: return
	var local: Vector2 = get_global_transform_with_canvas().affine_inverse() * event.position
	if not world.hud_area().has_point(local): return
	pointer = event.index
	pointer_start = local
	previous_pointer = local
	gesture_dragged = false
	gesture_grab_offset = Vector2.ZERO
	gesture_kind = "pan"
	gesture_started_in_tray = false
	if session.snapshot().get("mode", "live") == "edit":
		if not armed_item.is_empty():
			gesture_kind = "inventory"
			gesture_item = armed_item.duplicate(true)
			gesture_object = str(armed_item.id) if armed_item.get("assigned", false) else ""
		else:
			var object := _object_at(local)
			var selected: String = str(session.snapshot().editor.selected_id)
			if not object.is_empty() and str(object.id) == selected:
				gesture_kind = "object"
				gesture_object = str(object.id)
				# Grabbing a head, shelf top or other raised part must not snap its
				# ground root to the finger's tile when dragging begins.
				gesture_grab_offset = (_world_position(local) - world.cell_base(float(object.x), float(object.y))) / world.cell
			else:
				# An object must already be selected before a drag can move it.
				# All other drags pan; a short release selects the tapped object.
				tap_object = str(object.get("id", ""))
				if not selected.is_empty(): _editor_command({"type": "editor_select", "id": null})
	get_viewport().set_input_as_handled()

func _input(event: InputEvent) -> void:
	var inverse := get_global_transform_with_canvas().affine_inverse()
	if event is InputEventScreenTouch and event.pressed:
		last_screen_press = inverse * event.position
	if pointer == -1 or session == null: return
	if event is InputEventScreenDrag and event.index == pointer:
		var local: Vector2 = inverse * event.position
		var change := local - previous_pointer
		previous_pointer = local
		var displacement := local-pointer_start
		var threshold := 10.0/maxf(0.001,get_viewport_transform().get_scale().x)
		if gesture_kind == "inventory_pending" and displacement.length() >= threshold:
			if absf(displacement.x)>absf(displacement.y)*1.3:
				gesture_kind = "inventory_scroll"
			elif displacement.y<0 and absf(displacement.y)>absf(displacement.x)*1.3:
				gesture_kind = "inventory" if _pickup_allowed() else "inventory_cancel"
				if gesture_kind == "inventory": _begin_inventory_pickup()
			elif displacement.y>threshold:
				gesture_kind = "inventory_cancel"
		if not gesture_dragged and displacement.length() >= threshold: gesture_dragged = true
		if gesture_kind == "inventory_scroll":
			editor_ui.scroll_by(-change.x)
		elif gesture_kind == "pan":
			_pan(change)
		elif gesture_dragged and gesture_kind in ["inventory","object"]:
			_update_preview(local)
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenTouch and not event.pressed and event.index == pointer:
		var local: Vector2 = inverse * event.position
		if not event.canceled:
			if gesture_kind == "inventory_scroll":
				editor_ui.commit_scroll()
			elif gesture_kind == "inventory_pending" and not gesture_dragged and _pickup_allowed():
				_arm_item(gesture_item)
			elif gesture_kind == "pan" and not gesture_dragged and not tap_object.is_empty():
				_editor_command({"type": "editor_select", "id": tap_object})
			elif gesture_kind == "object" and gesture_dragged:
				if _floor_drop(local):
					var coordinate := _placement_cell_at(local)
					_editor_command({"type": "editor_move", "id": gesture_object, "x": coordinate.x, "y": coordinate.y})
				else:
					editor_ui.reject("invalid_position")
			elif gesture_kind == "inventory":
				if gesture_started_in_tray and not gesture_dragged and gesture_item.get("kind") == "chef":
					armed_item.clear()
					editor_ui.active_item = ""
					editor_ui.inspect(gesture_item)
				elif _floor_drop(local):
					var coordinate := _cell_at(local)
					var value := {"type": "editor_move", "id": gesture_object, "x": coordinate.x, "y": coordinate.y} if not gesture_object.is_empty() else {"type": "editor_place", "inventory_id": gesture_item.id, "x": coordinate.x, "y": coordinate.y}
					var result := _editor_command(value)
					if result.get("ok", false):
						armed_item.clear()
						editor_ui.active_item = ""
				elif gesture_dragged:
					editor_ui.reject("invalid_position")
		_cancel_gesture()
		save_now()
		_refresh()
		get_viewport().set_input_as_handled()

func _floor_drop(at: Vector2) -> bool:
	if not world.hud_area().has_point(at) or at.y <= world.hud_area().position.y + 145 * editor_ui.unit:
		return false
	if editor_ui.inspection.visible or (recovery != null and recovery.is_visible_in_tree()):
		return false
	for blocked: Rect2 in editor_ui.blocked_rects():
		if blocked.has_point(at): return false
	return true

func _update_preview(at: Vector2) -> void:
	var coordinate := _placement_cell_at(at)
	# Ask an isolated session through the same public save/command boundary as
	# the real drop. A green ghost therefore includes aisle and guest checks,
	# rather than merely looking for an empty cell.
	var probe = Session.new()
	var candidate := {"type": "editor_move", "id": gesture_object, "x": coordinate.x, "y": coordinate.y} if not gesture_object.is_empty() else {"type": "editor_place", "inventory_id": gesture_item.id, "x": coordinate.x, "y": coordinate.y}
	var valid: bool = _floor_drop(at) and probe.restore(session.save_data()) and probe.command(candidate).get("ok", false)
	var source: Dictionary = gesture_item if gesture_kind == "inventory" else _selected_object()
	world.editor_preview = {"x": coordinate.x, "y": coordinate.y, "valid": valid, "source": source}
	world.queue_redraw()

func _cancel_gesture() -> void:
	pointer = -1
	gesture_kind = ""
	gesture_object = ""
	gesture_item.clear()
	gesture_grab_offset = Vector2.ZERO
	tap_object = ""
	gesture_started_in_tray = false
	world.editor_preview.clear()
	world.queue_redraw()

func _pan(change: Vector2) -> void:
	var scene: Dictionary = session.snapshot()
	var camera: Dictionary = scene.camera
	var floor_data: Dictionary = scene.floor
	var visible_columns := float(floor_data.get("viewport_columns", floor_data.columns))
	var limit := maxf(0.0, float(floor_data.world_columns) - visible_columns)
	var x := clampf(float(camera.x) - change.x / world.cell, 0.0, limit)
	var visible_bottom := world.portrait.end.y - 24.0
	if scene.get("mode", "live") == "edit":
		visible_bottom = editor_ui.occlusion_top()
	# Include the rendered floor origin so the final tile can reach the rail.
	var floor_bottom := world.floor_origin.y + float(floor_data.rows) * world.cell
	var vertical_limit := maxf(0.0, (floor_bottom - visible_bottom) / world.cell)
	var y := clampf(float(camera.y) - change.y / world.cell, 0.0, vertical_limit)
	session.command({"type": "set_camera", "x": x, "y": y})
	_refresh()

func _cancel_native_button_presses() -> void:
	var buttons: Array = [shop, edit, staff, recovery_retry, recovery_close]
	buttons.append_array(gallery_buttons)
	for candidate in buttons:
		if not is_instance_valid(candidate) or not candidate.has_meta("visual"): continue
		var button: Button = candidate
		var was_disabled := button.disabled
		var was_pressed := button.button_pressed
		# Cancel BaseButton's actual press ownership as well as its decoration;
		# an orphan release after returning must not activate Edit or Retry.
		if not was_disabled:
			button.disabled = true
			button.disabled = false
		if button.toggle_mode: button.set_pressed_no_signal(was_pressed)
		_style_native_button(button, float(button.get_meta("skin_unit", 1.0)), false)

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED:
		backgrounded = true
		_cancel_native_button_presses()
		if is_instance_valid(world): _cancel_gesture()
		save_now()
	elif what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		_cancel_native_button_presses()
		if is_instance_valid(world): _cancel_gesture()
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		backgrounded = false
		skip_resume_frame = true
		if is_instance_valid(world): _layout()
	elif what in [NOTIFICATION_WM_CLOSE_REQUEST, NOTIFICATION_WM_GO_BACK_REQUEST]:
		if what == NOTIFICATION_WM_GO_BACK_REQUEST and editor_ui != null and editor_ui.inspection.visible:
			editor_ui.close_inspection()
			return
		save_now()
		if what == NOTIFICATION_WM_GO_BACK_REQUEST: get_tree().quit()

func _exit_tree() -> void:
	save_now()

func _valid_saved_session(data: Dictionary) -> bool:
	return Session.new().restore(data)

func _make_recovery() -> void:
	recovery = Panel.new()
	recovery.accessibility_name = "Saved restaurant needs attention"
	# Startup recovery is created before the first world layout. Use the same
	# positive base scale as new buttons; _layout calibrates it before drawing.
	recovery.add_theme_stylebox_override("panel", skin.style("container-modal"))
	add_child(recovery)
	recovery_title = Label.new()
	recovery_title.text = "Your edit needs saving" if pending_edit_save else "Saved restaurant\nneeds attention"
	recovery_title.add_theme_font_override("font", display_font)
	recovery_title.add_theme_color_override("font_color", INK)
	recovery.add_child(recovery_title)
	recovery_message = Label.new()
	# Establish wrap width before assigning long text. A zero-width Label can
	# cache a many-line minimum and retain that inflated height after layout.
	recovery_message.size = Vector2(588, 300)
	recovery_message.add_theme_font_override("font", body_font)
	recovery_message.add_theme_font_size_override("font_size", 36)
	recovery_message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	recovery_message.text = "Your changes are still here. Storage could not be updated. Retry to save this arrangement. Closing keeps the last successfully saved restaurant." if pending_edit_save else "Your restaurant could not be opened. Your save files have been kept. You can try opening them again."
	recovery_message.add_theme_color_override("font_color", INK)
	recovery.add_child(recovery_message)
	recovery_retry = make_button("Retry", "retry")
	recovery_close = make_button("Close", "close")
	recovery_retry.set_meta("skin_role", "control-green")
	recovery_retry.set_meta("skin_unit", -1.0)
	for kind in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		recovery_retry.add_theme_color_override(kind, CREAM)
	recovery_retry.reparent(recovery)
	recovery_close.reparent(recovery)
	recovery_retry.pressed.connect(_retry_restore)
	recovery_close.pressed.connect(func(): get_tree().quit())

func _retry_restore() -> void:
	if pending_edit_save:
		save_blocked = false
		if not save_now():
			save_blocked = true
			return
		pending_edit_save = false
		audio.set_muted(show_gallery or show_editor_gallery)
		recovery.queue_free()
		recovery = null
		_refresh()
		return
	var saved: Dictionary = store.load_session(_valid_saved_session)
	if saved.is_empty() and not store.last_error.is_empty():
		return
	if not saved.is_empty() and not session.restore(saved):
		return
	save_blocked = false
	save_error = ""
	audio.set_muted(show_gallery)
	recovery.queue_free()
	recovery = null
	_refresh()
	save_now()
