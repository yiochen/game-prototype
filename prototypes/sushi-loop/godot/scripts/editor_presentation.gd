extends Control
## Catalog-derived native editor controls, shared by the restaurant and gallery.
## The caller owns commands, persistence and pointer gestures.

signal command_requested(value: Dictionary)
signal item_pointer(item: Dictionary, event: InputEvent)
signal item_armed(item: Dictionary)

const Typography = preload("res://scripts/typography.gd")
const ArtBook = preload("res://scripts/art_book.gd")
const DISABLED_SHADER = preload("res://scripts/shaders/editor_disabled.gdshader")
const DIRECTORY := "res://assets/ui/editor/"
const ICON_REGIONS := {
	"people": Rect2(24, 52, 352, 258), "layout": Rect2(36, 18, 310, 330),
	"floor": Rect2(38, 50, 294, 280), "rotate": Rect2(10, 20, 348, 338),
	"remove": Rect2(30, 0, 346, 318), "caret-left": Rect2(50, 0, 185, 258),
	"caret-right": Rect2(153, 0, 185, 258),
}
const INK := Color("253b3b")
const PAPER := Color("fff0d1")
var state: Dictionary = {}
var area := Rect2()
var unit := 1.0
var live: Button
var layers: Dictionary = {}
var tray: Panel
var title: Label
var previous: Button
var next: Button
var rail: Control
var page_announcement: Label
var cards: Array[Button] = []
var rotate: Button
var remove: Button
var rejection: Label
var rejection_seconds := 0.0
var active_item := ""
var current_signature := ""
var body: Font
var art = ArtBook.new()
var target_base := Vector2.ZERO
var selected_visible := false
var disabled_material: ShaderMaterial
var inspection: ColorRect
var inspection_panel: Panel
var inspection_title: Label
var inspection_details: Label
var inspection_close: Button
var reduced_motion := false
var inspection_preview: ItemPreview

class ItemPreview extends Control:
	var art
	var entry: Dictionary = {}
	func _draw() -> void:
		if art == null or entry.is_empty(): return
		var identity := str(entry.get("art_id", ""))
		if identity.is_empty() or not art.objects.has(identity): return
		var clip := "idle" if entry.kind == "chef" or identity == "plant-angular" else "running" if entry.kind == "belt" else "static"
		var data: Dictionary = art.frame_data(identity, clip, "S", 0.0)
		if data.is_empty(): return
		var registration: Dictionary = art.registration(identity, clip, "S")
		var frame: Array = registration.frame_size
		var scale_factor := minf(size.x / float(frame[0]), size.y / float(frame[1]))
		var rect := Rect2((size - Vector2(float(frame[0]), float(frame[1])) * scale_factor) * 0.5, Vector2(float(frame[0]), float(frame[1])) * scale_factor)
		draw_texture_rect_region(data.texture, rect, data.region)

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	body = Typography.body()
	art.reload()
	disabled_material = ShaderMaterial.new()
	disabled_material.shader = DISABLED_SHADER
	live = _button("Live", "button-live", "", "Return to Live")
	live.pressed.connect(func(): command_requested.emit({"type": "set_mode", "mode": "live"}))
	for key in ["people", "layout", "floor"]:
		var name_text: String = str(key).capitalize()
		var button := _button("", "button-wood", str(key), name_text + " layer")
		button.toggle_mode = true
		button.pressed.connect(func(): command_requested.emit({"type": "editor_toggle_tray"} if str(state.get("editor", {}).get("layer", "")) == key else {"type": "editor_layer", "layer": key}))
		layers[key] = button
	tray = Panel.new()
	var paper := StyleBoxFlat.new()
	paper.bg_color = PAPER
	paper.border_color = Color("664a36")
	paper.set_border_width_all(3)
	paper.border_width_top = 5
	paper.set_corner_radius_all(14)
	paper.corner_radius_bottom_left = 0
	paper.corner_radius_bottom_right = 0
	tray.add_theme_stylebox_override("panel", paper)
	add_child(tray)
	title = _label("")
	tray.add_child(title)
	rail = Control.new()
	rail.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tray.add_child(rail)
	previous = _button("", "button-wood", "caret-left", "Previous inventory page", tray)
	next = _button("", "button-wood", "caret-left", "Next inventory page", tray)
	next.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	next.scale = Vector2.ONE
	previous.pressed.connect(func(): command_requested.emit({"type": "editor_page", "page": maxi(0, int(state.editor.page) - 1)}))
	next.pressed.connect(func(): command_requested.emit({"type": "editor_page", "page": int(state.editor.page) + 1}))
	page_announcement = _label("")
	page_announcement.accessibility_live = AccessibilityServer.LIVE_POLITE
	page_announcement.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# Keep native screen-reader page announcements without visible page numbers.
	page_announcement.modulate.a = 0.0
	tray.add_child(page_announcement)
	rotate = _button("", "button-wood", "rotate", "Rotate selected object")
	remove = _button("", "button-wood", "remove", "Return selected object to inventory")
	rotate.pressed.connect(func(): command_requested.emit({"type": "editor_rotate", "id": state.editor.selected_id}))
	remove.pressed.connect(func(): command_requested.emit({"type": "editor_remove", "id": state.editor.selected_id}))
	rejection = _label("")
	rejection.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rejection.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rejection.add_theme_color_override("font_color", Color("fff7e4"))
	var rejected_paper := StyleBoxFlat.new()
	rejected_paper.bg_color = Color("8f443e")
	rejected_paper.border_color = Color("4d322b")
	rejected_paper.set_border_width_all(3)
	rejected_paper.set_corner_radius_all(14)
	rejected_paper.content_margin_left = 14
	rejected_paper.content_margin_right = 14
	rejected_paper.content_margin_top = 10
	rejected_paper.content_margin_bottom = 10
	rejection.add_theme_stylebox_override("normal", rejected_paper)
	rejection.accessibility_live = AccessibilityServer.LIVE_ASSERTIVE
	add_child(rejection)
	rejection.hide()
	_make_inspection()
	refresh_layout()

func _make_inspection() -> void:
	inspection = ColorRect.new()
	inspection.color = Color(0.05, 0.12, 0.14, 0.48)
	inspection.accessibility_name = "Staff details"
	add_child(inspection)
	inspection.gui_input.connect(func(event: InputEvent):
		if event is InputEventScreenTouch and event.pressed: close_inspection())
	inspection_panel = Panel.new()
	inspection_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	var paper := StyleBoxFlat.new()
	paper.bg_color = PAPER
	paper.border_color = Color("664a36")
	paper.set_border_width_all(5)
	paper.set_corner_radius_all(20)
	paper.shadow_color = Color(0.03, 0.08, 0.08, 0.35)
	paper.shadow_size = 12
	paper.shadow_offset = Vector2(0, 8)
	inspection_panel.add_theme_stylebox_override("panel", paper)
	inspection.add_child(inspection_panel)
	inspection_title = _label("")
	inspection_title.add_theme_font_override("font", Typography.heading())
	inspection_panel.add_child(inspection_title)
	inspection_details = _label("")
	inspection_details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	inspection_panel.add_child(inspection_details)
	inspection_preview = ItemPreview.new()
	inspection_preview.art = art
	inspection_preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inspection_panel.add_child(inspection_preview)
	inspection_close = _button("Close", "button-wood", "", "Close staff details", inspection_panel)
	inspection_close.pressed.connect(close_inspection)
	inspection.hide()

func inspect(item: Dictionary) -> void:
	var recipe: Dictionary = state.get("recipes", {}).get(str(item.get("recipe_id", "")), {})
	inspection_title.text = str(item.get("name", "Chef"))
	inspection_details.text = "%s\nPreparation: %s s\n%s" % [recipe.get("name", str(item.get("recipe_id", "")).replace("_", " ").capitalize()), str(recipe.get("preparation_seconds", "—")), "Assigned" if item.get("assigned", false) else "In your roster · drag to place"]
	inspection_preview.entry = item.duplicate(true)
	inspection_preview.queue_redraw()
	inspection.show()
	inspection_close.grab_focus()
	refresh_layout()

func close_inspection() -> void:
	inspection.hide()
	for card in cards:
		if str(card.get_meta("entry").id) == str(inspection_preview.entry.get("id", "")):
			card.grab_focus()
			break

func _unhandled_key_input(event: InputEvent) -> void:
	if inspection.visible and event.is_action_pressed("ui_cancel"):
		close_inspection()
		get_viewport().set_input_as_handled()

func _label(value: String) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_override("font", body)
	label.add_theme_color_override("font_color", INK)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label

func _style(plate: String, kind: String) -> StyleBox:
	var path := DIRECTORY + plate + ".png"
	if ResourceLoader.exists(path):
		var style := StyleBoxTexture.new()
		style.texture = load(path)
		style.region_rect = Rect2(38, 52, 440, 416) if plate == "button-wood" else Rect2(5, 45, 765, 230)
		style.content_margin_left = 12
		style.content_margin_right = 12
		style.content_margin_top = 8
		style.content_margin_bottom = 10
		style.modulate_color = Color("e4bb7b") if kind == "pressed" else Color.WHITE
		return style
	var style := StyleBoxFlat.new()
	style.bg_color = Color("a97043") if plate == "button-wood" else Color("477e56")
	style.border_color = Color("4d382c")
	style.set_border_width_all(3)
	style.set_corner_radius_all(14)
	return style

func icon_texture(identity: String) -> Texture2D:
	var texture: Texture2D = load(DIRECTORY + identity + ".png")
	if not ICON_REGIONS.has(identity): return texture
	var cropped := AtlasTexture.new()
	cropped.atlas = texture
	cropped.region = ICON_REGIONS[identity]
	cropped.filter_clip = true
	return cropped

func _button(value: String, plate: String, icon_name: String, accessible: String, parent: Node = self) -> Button:
	var button := Button.new()
	button.text = value
	button.expand_icon = true
	button.accessibility_name = accessible
	button.add_theme_font_override("font", body)
	button.add_theme_color_override("font_color", Color("fff5dc"))
	button.add_theme_color_override("font_hover_color", Color("fff9e8"))
	button.add_theme_color_override("font_pressed_color", Color("fff0b9"))
	button.add_theme_color_override("font_disabled_color", Color("b3a992"))
	button.add_theme_color_override("icon_disabled_color", Color("ab9e8a"))
	button.add_theme_constant_override("h_separation", 10)
	button.add_theme_constant_override("outline_size", 3)
	button.add_theme_color_override("font_outline_color", Color("594431"))
	for kind in ["normal", "hover", "pressed", "disabled"]:
		button.add_theme_stylebox_override(kind, _style(plate, kind))
	var focus := StyleBoxFlat.new()
	focus.bg_color = Color.TRANSPARENT
	focus.border_color = Color("fbd77f")
	focus.set_border_width_all(3)
	focus.set_corner_radius_all(14)
	button.add_theme_stylebox_override("focus", focus)
	if ResourceLoader.exists(DIRECTORY + icon_name + ".png"):
		button.icon = icon_texture(icon_name)
	parent.add_child(button)
	return button

func set_state(value: Dictionary, portrait: Rect2) -> void:
	state = value
	area = portrait
	visible = state.get("mode", "live") == "edit"
	if not is_node_ready(): return
	var signature := JSON.stringify([state.get("editor", {}).get("layer"), state.get("editor", {}).get("page"), state.get("inventory", []), active_item])
	if signature != current_signature:
		current_signature = signature
		_rebuild_cards()
	refresh_layout()

func inventory_items() -> Array:
	var result: Array = []
	var layer: String = str(state.get("editor", {}).get("layer", "people"))
	for item in state.get("inventory", []):
		if (layer == "people" and item.kind == "chef") or (layer == "layout" and item.kind in ["belt", "seat", "decor"]) or (layer == "floor" and item.kind == "floor"):
			result.append(item)
	return result

func _rebuild_cards() -> void:
	for card in cards:
		card.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if reduced_motion or not is_visible_in_tree(): card.queue_free()
		else:
			var departing := create_tween()
			departing.tween_property(card, "modulate:a", 0.0, 0.08)
			departing.tween_callback(card.queue_free)
	cards.clear()
	var editor: Dictionary = state.get("editor", {})
	var layer: String = str(editor.get("layer", "people"))
	var count := 3 if layer == "people" else 2
	var entries := inventory_items()
	var page := int(editor.get("page", 0))
	var pages := maxi(1, ceili(float(entries.size()) / count))
	previous.disabled = page <= 0
	next.disabled = page >= pages - 1
	previous.material = disabled_material if previous.disabled else null
	next.material = disabled_material if next.disabled else null
	previous.accessibility_name = "Previous %s page" % layer
	next.accessibility_name = "Next %s page" % layer
	page_announcement.text = "%s page %s of %s" % [layer.capitalize(), page + 1, pages]
	page_announcement.accessibility_name = page_announcement.text
	for index in range(page * count, mini((page + 1) * count, entries.size())):
		var item: Dictionary = entries[index]
		var card := _button("", "button-wood", "", str(item.name), rail)
		card.toggle_mode = true
		card.button_pressed = active_item == str(item.id)
		card.disabled = not item.get("available", true) or (int(item.get("count", 0)) <= 0 and not item.get("assigned", false))
		card.material = disabled_material if card.disabled else null
		card.accessibility_description = "Assigned. Drag to move." if item.get("assigned", false) else "%s available. Drag onto the floor, or select then tap a free tile." % int(item.get("count", 0))
		if layer == "floor": card.accessibility_description = "Current floor. Floor customization is not yet available."
		var preview := ItemPreview.new()
		preview.art = art
		preview.entry = item
		preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(preview)
		var name_label := _label(str(item.name))
		name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		name_label.add_theme_color_override("font_color", Color("fff5dc"))
		card.add_child(name_label)
		var stock := _label("Placed" if item.get("assigned", false) else "Current" if layer == "floor" else "Ready" if layer == "people" else "%s in stock" % int(item.get("count", 0)))
		stock.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		stock.add_theme_color_override("font_color", Color("f1d9ae"))
		card.add_child(stock)
		card.set_meta("entry", item)
		card.set_meta("preview", preview)
		card.set_meta("name_label", name_label)
		card.set_meta("stock", stock)
		card.gui_input.connect(func(event: InputEvent):
			if not card.disabled: item_pointer.emit(item, event))
		card.pressed.connect(func(): item_armed.emit(item))
		cards.append(card)
		if not reduced_motion and is_visible_in_tree():
			card.modulate.a = 0.0
			create_tween().tween_property(card, "modulate:a", 1.0, 0.16).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)

func refresh_layout() -> void:
	if not is_node_ready() or area.size.x <= 0: return
	unit = area.size.x / 720.0
	var editor: Dictionary = state.get("editor", {})
	var layer: String = str(editor.get("layer", "people"))
	var open: bool = bool(editor.get("tray_open", true))
	var tray_height := 292.0 if layer == "people" else 260.0
	if not open: tray_height = 0.0
	live.position = area.position + Vector2(area.size.x - 216 * unit, 30 * unit)
	live.size = Vector2(192, 104) * unit
	live.add_theme_font_size_override("font_size", maxi(1, int(36 * unit)))
	tray.visible = open
	_move_control(tray, Vector2(area.position.x, area.end.y - tray_height * unit))
	tray.size = Vector2(area.size.x, tray_height * unit)
	title.text = "Staff" if layer == "people" else ""
	title.position = Vector2(28, 12) * unit
	title.size = Vector2(500, 40) * unit
	title.add_theme_font_size_override("font_size", maxi(1, int(28 * unit)))
	var rail_top := 56.0 if layer == "people" else 10.0
	previous.position = Vector2(12, rail_top + 22) * unit
	next.position = Vector2(608, rail_top + 22) * unit
	previous.size = Vector2(100, 150) * unit
	next.size = previous.size
	for button in [previous, next]:
		button.add_theme_constant_override("icon_max_width", int(52 * unit))
	if ResourceLoader.exists(DIRECTORY + "caret-right.png"):
		next.icon = icon_texture("caret-right")

	rail.position = Vector2(120, rail_top) * unit
	rail.size = Vector2(480, tray_height - rail_top - 12) * unit
	page_announcement.position = Vector2(0, 0)
	page_announcement.size = Vector2.ONE
	var slots := 3 if layer == "people" else 2
	var slot_width := 480.0 / slots
	for index in range(cards.size()):
		var card: Button = cards[index]
		card.position = Vector2(index * slot_width + 5, 0) * unit
		card.size = Vector2(slot_width - 10, tray_height - rail_top - 12) * unit
		var preview: Control = card.get_meta("preview")
		preview.position = Vector2(12, 2) * unit
		preview.size = Vector2(slot_width - 34, 132 if layer == "people" else 130) * unit
		var name_label: Label = card.get_meta("name_label")
		name_label.position = Vector2(8, 135) * unit
		name_label.size = Vector2(slot_width - 26, 35) * unit
		name_label.add_theme_font_size_override("font_size", maxi(1, int(26 * unit)))
		name_label.visible = layer != "floor"
		var stock: Label = card.get_meta("stock")
		stock.visible = layer != "floor"
		stock.position = Vector2(8, 172) * unit
		stock.size = Vector2(slot_width - 26, 30) * unit
		stock.add_theme_font_size_override("font_size", maxi(1, int((24 if layer == "people" else 22) * unit)))
	for index in range(3):
		var key: String = ["people", "layout", "floor"][index]
		var button: Button = layers[key]
		button.text = key.capitalize() if key == layer else ""
		button.set_pressed_no_signal(key == layer)
		button.accessibility_description = "Selected, tray %s" % ("open" if open else "closed") if key == layer else "Switch to %s and open its tray" % key
		_move_control(button, Vector2(area.end.x - (240 if key == layer else 124) * unit, area.end.y - tray_height * unit - (370 - index * 116) * unit))
		button.size = Vector2(216 if key == layer else 100, 100) * unit
		button.add_theme_font_size_override("font_size", maxi(1, int(28 * unit)))
		button.add_theme_constant_override("icon_max_width", int(52 * unit))
	var tool_left := clampf(target_base.x - 110 * unit, area.position.x + 12 * unit, area.end.x - 236 * unit)
	var tool_top := clampf(target_base.y - 204 * unit, area.position.y + 160 * unit, tray.position.y - 118 * unit)
	var tool_rect := Rect2(Vector2(tool_left, tool_top), Vector2(212, 100) * unit)
	for layer_button in layers.values():
		if tool_rect.intersects(layer_button.get_global_rect()): tool_left = area.position.x + 20 * unit
	for index in range(2):
		var button: Button = [rotate, remove][index]
		button.visible = selected_visible
		button.position = Vector2(tool_left + index * 112 * unit, tool_top)
		button.size = Vector2(100, 100) * unit
		button.add_theme_constant_override("icon_max_width", int(60 * unit))
	rejection.position = Vector2(area.position.x + 60 * unit, area.position.y + 168 * unit)
	rejection.size = Vector2(600, 110) * unit
	rejection.add_theme_font_size_override("font_size", maxi(1, int(28 * unit)))
	inspection.position = area.position
	inspection.size = area.size
	inspection_panel.position = Vector2(34 * unit, area.size.y * 0.32)
	inspection_panel.size = Vector2(652, 500) * unit
	inspection_title.position = Vector2(28, 28) * unit
	inspection_title.size = Vector2(410, 78) * unit
	inspection_title.add_theme_font_size_override("font_size", maxi(1, int(42 * unit)))
	inspection_close.position = Vector2(446, 18) * unit
	inspection_close.size = Vector2(180, 100) * unit
	inspection_close.add_theme_font_size_override("font_size", maxi(1, int(28 * unit)))
	inspection_preview.position = Vector2(24, 120) * unit
	inspection_preview.size = Vector2(205, 325) * unit
	inspection_details.position = Vector2(248, 150) * unit
	inspection_details.size = Vector2(365, 300) * unit
	inspection_details.add_theme_font_size_override("font_size", maxi(1, int(30 * unit)))

func _move_control(control: Control, target: Vector2) -> void:
	if control.has_meta("position_target") and control.get_meta("position_target") == target: return
	if control.has_meta("position_tween"):
		var previous_tween = control.get_meta("position_tween")
		if previous_tween is Tween and previous_tween.is_valid(): previous_tween.kill()
	var animate: bool = control.has_meta("position_target") and not reduced_motion and is_visible_in_tree()
	control.set_meta("position_target", target)
	if not animate:
		control.position = target
		return
	var motion := create_tween()
	motion.tween_property(control, "position", target, 0.20).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	control.set_meta("position_tween", motion)

func set_selection(base: Vector2, show: bool) -> void:
	target_base = base
	selected_visible = show
	refresh_layout()

func reject(reason: String) -> void:
	var messages := {"occupied": "That tile is occupied.", "entrance": "Keep the entrance clear.", "customer_busy": "A guest is using this seat.", "customer_path": "Keep an aisle open for guests.", "no_stock": "None left in inventory.", "invalid_position": "Place objects on cleared floor."}
	rejection.text = messages.get(reason, "This object cannot go there.")
	rejection.accessibility_name = rejection.text
	rejection.show()
	rejection_seconds = 1.3

func _process(delta: float) -> void:
	if rejection_seconds > 0:
		rejection_seconds -= delta
		if rejection_seconds <= 0: rejection.hide()
