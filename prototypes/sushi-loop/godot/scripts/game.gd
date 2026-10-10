extends Control

const Session = preload("res://scripts/session.gd")
const Persistence = preload("res://scripts/save_store.gd")
const RestaurantView = preload("res://scripts/restaurant_view.gd")
const Audio = preload("res://scripts/audio.gd")
const Typography = preload("res://scripts/typography.gd")
var session: Session
var store: Persistence
var world: RestaurantView
var world_clip: Control
var audio: Audio
var show_gallery := false
var simulation_enabled := true
var money: Label
var coin: TextureRect
var shop: Button
var edit: Button
var staff: Button
var gallery_buttons: Array[Button] = []
var autosave_elapsed := 0.0
var pointer := -1
var previous_pointer := Vector2.ZERO
var backgrounded := false
var save_error := ""
var body_font: Font
var display_font: Font
var save_blocked := false
var recovery: Panel
var recovery_title: Label
var recovery_message: Label
var recovery_retry: Button
var recovery_close: Button

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	show_gallery = show_gallery or "--gallery" in OS.get_cmdline_user_args()
	store = Persistence.new()
	session = Session.new_session(int(Time.get_unix_time_from_system()) % 2147483647)
	if not show_gallery:
		var saved: Dictionary = store.load_session(_valid_saved_session)
		if not saved.is_empty():
			if not session.restore(saved):
				save_error = "The saved restaurant could not be restored."
		elif not store.last_error.is_empty():
			save_error = store.last_error
			save_blocked = true
	body_font = Typography.body()
	display_font = Typography.heading()
	audio = Audio.new()
	audio.set_muted(show_gallery or save_blocked)
	add_child(audio)
	world = RestaurantView.new()
	world.show_gallery = show_gallery
	world_clip = Control.new()
	world_clip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	world_clip.clip_contents = true
	add_child(world_clip)
	world_clip.add_child(world)
	world.state = session.snapshot()
	coin = TextureRect.new()
	coin.texture = load("res://assets/ui/coin.svg")
	coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	coin.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	coin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(coin)
	money = Label.new()
	money.add_theme_font_override("font", body_font)
	money.add_theme_color_override("font_color", Color("ffedbf") if show_gallery else Color("253b3b"))
	money.add_theme_color_override("font_shadow_color", Color("263a38") if show_gallery else Color("fff2c8"))
	money.add_theme_constant_override("shadow_offset_x", 1)
	money.add_theme_constant_override("shadow_offset_y", 1)
	money.accessibility_name = "Coins"
	money.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(money)
	shop = make_button("Shop", "shop", true)
	edit = make_button("Edit", "edit", true)
	staff = make_button("Staff", "staff", true)
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
	if not show_gallery:
		save_now()

func make_button(text: String, icon_name: String, disabled := false) -> Button:
	var button := Button.new()
	button.text = text
	button.icon = load("res://assets/ui/" + icon_name + ".svg")
	button.expand_icon = true
	button.disabled = disabled
	button.accessibility_name = text
	button.add_theme_font_override("font", body_font)
	button.add_theme_color_override("font_color", Color("fff4d7"))
	button.add_theme_color_override("font_hover_color", Color("fff9e8"))
	button.add_theme_color_override("font_pressed_color", Color("ffefbb"))
	button.add_theme_color_override("font_disabled_color", Color("c8cbc0"))
	button.add_theme_color_override("icon_disabled_color", Color("a9b9b5"))
	button.add_theme_constant_override("h_separation", 10)
	for kind in ["normal", "hover", "pressed", "disabled", "focus"]:
		button.add_theme_stylebox_override(kind, button_style(kind))
	add_child(button)
	button.pressed.connect(func(): audio.play_cue("click"))
	return button

func button_style(kind: String) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("a5673b")
	style.border_color = Color("523b2e")
	style.set_border_width_all(3)
	style.border_width_bottom = 8
	style.set_corner_radius_all(15)
	style.content_margin_left = 15
	style.content_margin_right = 15
	style.content_margin_top = 8
	style.content_margin_bottom = 12
	style.shadow_color = Color(0.04, 0.13, 0.14, 0.25)
	style.shadow_size = 6
	style.shadow_offset = Vector2(0, 4)
	if kind == "hover":
		style.bg_color = Color("b87e45")
	elif kind == "pressed":
		style.bg_color = Color("885735")
		style.border_color = Color("f2cc6b")
		style.border_width_bottom = 3
		style.shadow_size = 2
	elif kind == "disabled":
		style.bg_color = Color("405e60")
		style.border_color = Color("30494d")
		style.shadow_size = 0
	elif kind == "focus":
		style.bg_color = Color.TRANSPARENT
		style.border_color = Color("ffdd73")
		style.set_border_width_all(4)
		style.shadow_size = 0
	return style

func _layout() -> void:
	if world == null:
		return
	world.size = size
	world.update_layout()
	var area: Rect2 = world.portrait
	# Keep world coordinates identical to the root's input coordinates while the
	# containing control clips adjoining floor in a wide native window.
	world_clip.position = area.position
	world_clip.size = area.size
	world.position = -area.position
	var unit: float = area.size.x / 720.0
	var top: float = 124 * unit if show_gallery else 42 * unit
	coin.position = Vector2(area.position.x + 34 * unit, top)
	coin.size = Vector2.ONE * 54 * unit
	money.position = Vector2(area.position.x + 94 * unit, top - 2 * unit)
	money.size = Vector2(300, 60) * unit
	money.add_theme_font_size_override("font_size", int(43 * unit))
	shop.position = Vector2(area.position.x + (440 * unit if show_gallery else 34 * unit), 112 * unit if show_gallery else 145 * unit)
	shop.size = Vector2(224, 108) * unit
	edit.position = Vector2(area.position.x + 34 * unit, area.end.y - 156 * unit)
	edit.size = Vector2(206, 110) * unit
	staff.position = Vector2(area.position.x + 266 * unit, area.end.y - 156 * unit)
	staff.size = Vector2(214, 110) * unit
	for button in [shop, edit, staff]:
		button.add_theme_font_size_override("font_size", int(34 * unit))
		button.add_theme_constant_override("icon_max_width", int(48 * unit))
	for i in range(gallery_buttons.size()):
		var button: Button = gallery_buttons[i]
		button.position = Vector2(area.position.x + (38 + i * 220) * unit, area.end.y - 185 * unit)
		button.size = Vector2(206, 110) * unit
		button.add_theme_font_size_override("font_size", int(34 * unit))
		button.add_theme_constant_override("icon_max_width", int(38 * unit))
	if recovery != null:
		recovery.position = Vector2(area.position.x + 34 * unit, area.size.y * 0.28)
		recovery.size = Vector2(652, 600) * unit
		recovery_title.position = Vector2(32, 32) * unit
		recovery_title.size = Vector2(588, 120) * unit
		recovery_title.add_theme_font_size_override("font_size", int(44 * unit))
		recovery_message.position = Vector2(32, 170) * unit
		recovery_message.size = Vector2(588, 240) * unit
		recovery_message.add_theme_font_size_override("font_size", int(36 * unit))
		recovery_retry.position = Vector2(32, 452) * unit
		recovery_retry.size = Vector2(288, 110) * unit
		recovery_close.position = Vector2(344, 452) * unit
		recovery_close.size = Vector2(276, 110) * unit
		for button in [recovery_retry, recovery_close]:
			button.add_theme_font_size_override("font_size", int(34 * unit))
			button.add_theme_constant_override("icon_max_width", int(44 * unit))

func _process(delta: float) -> void:
	if session == null or backgrounded or save_blocked:
		return
	if not show_gallery and simulation_enabled:
		var events: Array = advance_time(minf(delta, 0.25))
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
	if money.text != coins_text:
		money.text = coins_text
		money.accessibility_description = "%s coins" % coins_text
	world.queue_redraw()

func save_now() -> bool:
	if save_blocked:
		return false
	if show_gallery or session == null or store == null:
		return true
	var success: bool = store.save_session(session.save_data())
	save_error = "" if success else store.last_error
	return success

func _unhandled_input(event: InputEvent) -> void:
	if session == null or show_gallery or save_blocked:
		return
	var inverse := get_global_transform_with_canvas().affine_inverse()
	if event is InputEventScreenTouch:
		var local: Vector2 = inverse * event.position
		if event.pressed and pointer == -1 and world.portrait.has_point(local):
			pointer = event.index
			previous_pointer = local
		elif not event.pressed and event.index == pointer:
			pointer = -1
			save_now()
	elif event is InputEventScreenDrag and event.index == pointer:
		var local: Vector2 = inverse * event.position
		var change := local - previous_pointer
		previous_pointer = local
		var camera: Dictionary = session.snapshot().camera
		var floor_data: Dictionary = session.snapshot().floor
		var visible_columns := float(floor_data.get("viewport_columns", floor_data.columns))
		var limit := maxf(0.0, float(floor_data.world_columns) - visible_columns)
		var x := clampf(float(camera.x) - change.x / world.cell, 0.0, limit)
		session.command({"type": "set_camera", "x": x, "y": 0.0})
		_refresh()
		get_viewport().set_input_as_handled()

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED:
		backgrounded = true
		pointer = -1
		save_now()
	elif what == NOTIFICATION_APPLICATION_RESUMED:
		backgrounded = false
	elif what in [NOTIFICATION_WM_CLOSE_REQUEST, NOTIFICATION_WM_GO_BACK_REQUEST]:
		save_now()

func _exit_tree() -> void:
	save_now()

func _valid_saved_session(data: Dictionary) -> bool:
	return Session.new().restore(data)

func _make_recovery() -> void:
	recovery = Panel.new()
	recovery.accessibility_name = "Saved restaurant needs attention"
	var paper := StyleBoxFlat.new()
	paper.bg_color = Color("ffefcf")
	paper.border_color = Color("513d32")
	paper.set_border_width_all(4)
	paper.set_corner_radius_all(18)
	recovery.add_theme_stylebox_override("panel", paper)
	add_child(recovery)
	recovery_title = Label.new()
	recovery_title.text = "Saved restaurant\nneeds attention"
	recovery_title.add_theme_font_override("font", display_font)
	recovery_title.add_theme_color_override("font_color", Color("253b3b"))
	recovery.add_child(recovery_title)
	recovery_message = Label.new()
	recovery_message.text = "Your restaurant could not be opened. Your save files have been kept. You can try opening them again."
	recovery_message.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	recovery_message.add_theme_font_override("font", body_font)
	recovery_message.add_theme_color_override("font_color", Color("253b3b"))
	recovery.add_child(recovery_message)
	recovery_retry = make_button("Retry", "arrow")
	recovery_close = make_button("Close", "close")
	recovery_retry.reparent(recovery)
	recovery_close.reparent(recovery)
	recovery_retry.pressed.connect(_retry_restore)
	recovery_close.pressed.connect(func(): get_tree().quit())

func _retry_restore() -> void:
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
