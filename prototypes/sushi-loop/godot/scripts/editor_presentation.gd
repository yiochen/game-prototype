extends Control
## Catalog-derived native editor controls, shared by the restaurant and gallery.
## The caller owns commands, persistence and pointer gestures.

signal command_requested(value: Dictionary)
signal item_pointer(item: Dictionary, event: InputEvent)
signal item_armed(item: Dictionary)

const Typography = preload("res://scripts/typography.gd")
const ArtBook = preload("res://scripts/art_book.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const INK := Color("233d58")
const CREAM := Color("fff3db")
const DRAWER_HEIGHT := 220.0
const CATEGORY_HEIGHT := 100.0
const CARD_HEIGHT := 185.0
const DOCK_HEIGHT := 26.0
const PAGE_SIZE := 3
const LAYOUT_PAGE_SIZE := 4
var state: Dictionary = {}
var area := Rect2()
var unit := 1.0
var live: Button
var layers: Dictionary = {}
var inventory_backing: ColorRect
var category_rail: Panel
var category_rod: Panel
var bottom_dock: Panel
var shop: Button
var context_bubble: Panel
var context_pointer: TextureRect
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
var skin: UISkin
var inspection: ColorRect
var inspection_panel: Panel
var inspection_title: Label
var inspection_details: Label
var inspection_close: Button
var reduced_motion := false
var inspection_preview: ItemPreview
var inspection_preview_panel: Panel

class ItemPreview extends Control:
	const GOODS_MANIFEST := "res://assets/ui/editor-goods/manifest.json"
	static var frame_bounds: Dictionary = {}
	static var goods: Dictionary = {}
	static var goods_texture: Texture2D
	static var goods_loaded := false
	var art
	var entry: Dictionary = {}
	func _load_goods() -> void:
		if goods_loaded: return
		goods_loaded = true
		if not FileAccess.file_exists(GOODS_MANIFEST): return
		var manifest = JSON.parse_string(FileAccess.get_file_as_string(GOODS_MANIFEST))
		if not manifest is Dictionary: return
		goods = manifest.get("sprites", {})
		var atlas_path := str(manifest.get("atlas", ""))
		if atlas_path.is_empty(): return
		if not atlas_path.begins_with("res://"):
			atlas_path = GOODS_MANIFEST.get_base_dir().path_join(atlas_path)
		goods_texture = load(atlas_path)
	func _draw() -> void:
		if entry.is_empty(): return
		var identity := str(entry.get("art_id", ""))
		_load_goods()
		if goods_texture != null and goods.has(identity) and str(entry.get("kind", "")) != "chef":
			var region: Array = goods[identity].get("region", [])
			if region.size() == 4:
				var source := Rect2(float(region[0]), float(region[1]), float(region[2]), float(region[3]))
				draw_texture_rect_region(goods_texture, UISkin.fit_rect(source.size, Rect2(Vector2.ZERO, size)), source)
				return
		if art == null: return
		if identity.is_empty() or not art.objects.has(identity): return
		var clip := "idle" if entry.kind == "chef" or identity == "plant-angular" else "running" if entry.kind == "belt" else "static"
		var data: Dictionary = art.frame_data(identity, clip, "S", 0.0)
		if data.is_empty(): return
		# Inventory and profile art uses one static representative frame. Fit its
		# occupied pixels rather than the production renderer's padded tile frame.
		# Scene registration and pose-to-pose scale remain owned by ArtBook.
		var source: Rect2 = data.region
		var key := "%s:%s" % [data.texture.resource_path, source]
		if not frame_bounds.has(key):
			var pixels: Image = data.texture.get_image()
			var can_crop := pixels != null
			if can_crop and pixels.is_compressed(): can_crop = pixels.decompress() == OK
			if can_crop:
				var occupied := pixels.get_region(Rect2i(source)).get_used_rect()
				frame_bounds[key] = Rect2(source.position + Vector2(occupied.position), Vector2(occupied.size)) if occupied.has_area() else source
			else:
				frame_bounds[key] = source
		source = frame_bounds[key]
		var target := UISkin.fit_rect(source.size, Rect2(Vector2.ZERO, size))
		draw_texture_rect_region(data.texture, target, source)

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	body = Typography.body()
	art.reload()
	skin = UISkin.new()
	live = _button("Live", "control-green", "play", "Return to Live")
	_add_button_visual(live)
	live.pressed.connect(func(): command_requested.emit({"type": "set_mode", "mode": "live"}))
	inventory_backing = ColorRect.new()
	inventory_backing.color = CREAM
	inventory_backing.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(inventory_backing)
	category_rail = Panel.new()
	category_rail.accessibility_name = "Editor categories"
	add_child(category_rail)
	category_rod = Panel.new()
	category_rod.mouse_filter = Control.MOUSE_FILTER_IGNORE
	category_rail.add_child(category_rod)
	for key in ["people", "layout", "floor"]:
		var name_text: String = str(key).capitalize()
		var button := _button(name_text, "tab-idle", str(key), name_text + " layer", category_rail)
		button.toggle_mode = true
		_add_button_visual(button)
		button.pressed.connect(func(): command_requested.emit({"type": "editor_toggle_tray"} if str(state.get("editor", {}).get("layer", "")) == key else {"type": "editor_layer", "layer": key}))
		layers[key] = button
	shop = _button("Shop", "control-wood", "shop", "Shop", category_rail)
	_add_button_visual(shop)
	shop.pressed.connect(func(): command_requested.emit({"type": "editor_shop"}))
	tray = Panel.new()
	add_child(tray)
	title = _label("")
	tray.add_child(title)
	rail = Control.new()
	rail.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tray.add_child(rail)
	previous = _button("", "slot-paper", "caret-left", "Previous inventory page", tray)
	next = _button("", "slot-paper", "caret-right", "Next inventory page", tray)
	_add_button_visual(previous)
	_add_button_visual(next)
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
	bottom_dock = Panel.new()
	bottom_dock.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bottom_dock)
	context_bubble = Panel.new()
	context_bubble.accessibility_name = "Selected object actions"
	add_child(context_bubble)
	context_pointer = TextureRect.new()
	context_pointer.texture = icon_texture("pointer")
	context_pointer.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	context_pointer.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	context_pointer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	context_bubble.add_child(context_pointer)
	rotate = _button("Rotate", "context-action", "rotate", "Rotate selected object", context_bubble)
	remove = _button("Return", "context-action", "remove", "Return selected object to inventory", context_bubble)
	for button in [rotate, remove]:
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	rotate.pressed.connect(func(): command_requested.emit({"type": "editor_rotate", "id": state.editor.selected_id}))
	remove.pressed.connect(func(): command_requested.emit({"type": "editor_remove", "id": state.editor.selected_id}))
	remove.accessibility_description = "Store this owned object in inventory for later placement."
	rotate.accessibility_description = "Turn this object one quarter turn clockwise."
	rejection = _label("")
	rejection.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	rejection.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	rejection.add_theme_color_override("font_color", INK)
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
	inspection.add_child(inspection_panel)
	inspection_title = _label("")
	inspection_title.add_theme_font_override("font", Typography.heading())
	inspection_panel.add_child(inspection_title)
	inspection_details = _label("")
	inspection_details.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	inspection_panel.add_child(inspection_details)
	inspection_preview_panel = Panel.new()
	inspection_preview_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inspection_panel.add_child(inspection_preview_panel)
	inspection_preview = ItemPreview.new()
	inspection_preview.art = art
	inspection_preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
	inspection_panel.add_child(inspection_preview)
	inspection_close = _button("Close", "control-wood", "close", "Close staff details", inspection_panel)
	_add_button_visual(inspection_close)
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

func _notification(what: int) -> void:
	if what not in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_WINDOW_FOCUS_OUT] or not is_node_ready(): return
	# A suspended window may never receive the held finger's release. Clear the
	# native press as well as its artwork so an orphan release cannot activate it.
	var buttons: Array = [live, shop, previous, next, inspection_close]
	buttons.append_array(layers.values())
	for button: Button in buttons:
		if button == null or not button.has_meta("visual"): continue
		var was_disabled := button.disabled
		if not was_disabled:
			button.disabled = true
			button.disabled = false
		if button.toggle_mode:
			button.set_pressed_no_signal(str(button.get_meta("skin_role")) == "tab-active")
		var motion = button.get_meta("visual_tween") if button.has_meta("visual_tween") else null
		if motion is Tween and motion.is_valid(): motion.kill()
		button.set_meta("visual_pressed", false)
		var visual: Control = button.get_meta("visual")
		visual.scale = Vector2.ONE
		_refresh_button_visual(button)

func _label(value: String) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_override("font", body)
	label.add_theme_color_override("font_color", INK)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label

func icon_texture(identity: String) -> Texture2D:
	return skin.icon(identity)

func _button(value: String, role: String, icon_name: String, accessible: String, parent: Node = self) -> Button:
	var button := Button.new()
	button.text = value
	button.expand_icon = true
	button.accessibility_name = accessible
	button.add_theme_font_override("font", body)
	button.set_meta("skin_role", role)
	_style_button(button)
	if not icon_name.is_empty(): button.icon = icon_texture(icon_name)
	parent.add_child(button)
	return button

func _add_button_visual(button: Button) -> void:
	# Native buttons retain their labels, focus and stable touch bounds. Their
	# separate artwork can be inset or pressed without moving those bounds.
	button.self_modulate.a = 0.0
	var visual := Control.new()
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	button.add_child(visual)
	var surface := Panel.new()
	surface.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.add_child(surface)
	var focus := Panel.new()
	focus.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.add_child(focus)
	var icon := TextureRect.new()
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.add_child(icon)
	var caption := _label(button.text)
	caption.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	caption.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	visual.add_child(caption)
	button.set_meta("visual", visual)
	button.set_meta("visual_surface", surface)
	button.set_meta("visual_focus", focus)
	button.set_meta("visual_icon", icon)
	button.set_meta("visual_label", caption)
	button.button_down.connect(func(): _press_button_visual(button, true))
	button.button_up.connect(func(): _press_button_visual(button, false))
	button.mouse_entered.connect(func(): _refresh_button_visual(button))
	button.mouse_exited.connect(func(): _press_button_visual(button, false))
	button.focus_entered.connect(func(): _refresh_button_visual(button))
	button.focus_exited.connect(func(): _refresh_button_visual(button))
	_style_button(button)

func _press_button_visual(button: Button, pressed: bool) -> void:
	button.set_meta("visual_pressed", pressed)
	_refresh_button_visual(button)
	var visual: Control = button.get_meta("visual")
	var previous_tween = button.get_meta("visual_tween") if button.has_meta("visual_tween") else null
	if previous_tween is Tween and previous_tween.is_valid(): previous_tween.kill()
	var target := Vector2.ONE * (0.975 if pressed else 1.0)
	if reduced_motion or not is_visible_in_tree():
		visual.scale = target
		return
	var motion := create_tween()
	motion.tween_property(visual, "scale", target, 0.10 if pressed else 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	button.set_meta("visual_tween", motion)

func _refresh_button_visual(button: Button) -> void:
	if not button.has_meta("visual"): return
	var role := str(button.get_meta("skin_role"))
	var treatment := "disabled" if button.disabled else "pressed" if button.get_meta("visual_pressed", false) else "normal"
	if role in ["tab-idle", "tab-active"] and not button.disabled: treatment = "normal"
	var surface: Panel = button.get_meta("visual_surface")
	skin.apply_panel(surface, role, unit, treatment)
	var focus: Panel = button.get_meta("visual_focus")
	focus.visible = button.has_focus()
	var focus_signature := "%0.6f:%s" % [unit, role in ["tab-idle", "tab-active"]]
	if focus.get_meta("skin_signature", "") != focus_signature:
		var focus_shadow := StyleBoxFlat.new()
		focus_shadow.bg_color = Color.TRANSPARENT
		focus_shadow.shadow_color = Color(0.78, 0.28, 0.15, 0.45)
		focus_shadow.shadow_size = maxi(1, int(4 * unit))
		focus_shadow.set_corner_radius_all(maxi(1, int((8 if role in ["tab-idle", "tab-active"] else 42) * unit)))
		focus.add_theme_stylebox_override("panel", focus_shadow)
		focus.set_meta("skin_signature", focus_signature)
	var icon: TextureRect = button.get_meta("visual_icon")
	icon.texture = button.icon
	var caption: Label = button.get_meta("visual_label")
	caption.text = button.text
	caption.add_theme_color_override("font_color", CREAM if role in ["tab-idle", "tab-active", "control-green"] else INK)
	var visual: Control = button.get_meta("visual")
	visual.modulate.a = 0.45 if button.disabled else 1.0

func _layout_button_visual(button: Button, bounds: Rect2, font_size: float, icon_width: float) -> void:
	_refresh_button_visual(button)
	var visual: Control = button.get_meta("visual")
	visual.position = bounds.position * unit
	visual.size = bounds.size * unit
	visual.pivot_offset = visual.size * 0.5
	for key in ["visual_surface", "visual_focus"]:
		var panel: Control = button.get_meta(key)
		panel.position = Vector2.ZERO
		panel.size = visual.size
	var icon: TextureRect = button.get_meta("visual_icon")
	var caption: Label = button.get_meta("visual_label")
	caption.add_theme_font_size_override("font_size", maxi(1, int(font_size * unit)))
	caption.visible = not button.text.is_empty()
	if button.text.is_empty():
		icon.size = Vector2(icon_width, 32) * unit
		icon.position = (visual.size - icon.size) * 0.5
	else:
		var text_width := body.get_string_size(button.text, HORIZONTAL_ALIGNMENT_LEFT, -1, maxi(1, int(font_size * unit))).x
		var gap := 8 * unit
		var combined := minf(visual.size.x - 16 * unit, text_width + icon_width * unit + gap)
		icon.size = Vector2(icon_width, icon_width) * unit
		icon.position = Vector2((visual.size.x - combined) * 0.5, (visual.size.y - icon.size.y) * 0.5)
		caption.position = Vector2(icon.position.x + icon.size.x + gap, 0)
		caption.size = Vector2(combined - icon.size.x - gap, visual.size.y)

func _style_button(button: Button) -> void:
	var role: String = button.get_meta("skin_role")
	var signature := "%s:%0.6f:%s:%s" % [role, unit, button.toggle_mode and button.button_pressed, button.has_meta("visual")]
	if button.get_meta("skin_signature", "") == signature: return
	button.set_meta("skin_signature", signature)
	var tab := role in ["tab-idle", "tab-active"]
	var primary := role == "control-green"
	for kind in ["normal", "hover", "pressed", "disabled"]:
		var treatment: String = "selected" if kind == "pressed" and button.toggle_mode and button.button_pressed else kind
		# The inset artwork owns its material and corner minimums. The invisible
		# native target must not grow by the pill's radius plus its text height.
		button.add_theme_stylebox_override(kind, StyleBoxEmpty.new() if button.has_meta("visual") else skin.style(role, unit, treatment))
	for kind in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(kind, CREAM if tab or primary else INK)
	button.add_theme_color_override("font_disabled_color", Color("75838c"))
	button.add_theme_color_override("icon_disabled_color", Color("89959d"))
	button.add_theme_constant_override("h_separation", int(8 * unit))
	button.add_theme_constant_override("outline_size", 0)
	# The focus frame belongs to the same generated material family.
	var focus_role := "focus" if skin.manifest.styles.has("focus") else role
	button.add_theme_stylebox_override("focus", StyleBoxEmpty.new() if button.has_meta("visual") else skin.style(focus_role, unit, "pressed"))
	_refresh_button_visual(button)

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

func _inventory_caption(item: Dictionary) -> String:
	# Short visual captions preserve complete saved names and accessible labels.
	match str(item.get("id", "")):
		"belt-tile": return "Belt"
		"stool-plain": return "Stool"
		"plant-angular": return "Plant"
		"barrel-wood": return "Barrel"
		"crate-wood": return "Crate"
	return str(item.get("name", ""))

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
	var count := LAYOUT_PAGE_SIZE if layer == "layout" else PAGE_SIZE
	var entries := inventory_items()
	var page := int(editor.get("page", 0))
	var pages := maxi(1, ceili(float(entries.size()) / count))
	previous.disabled = page <= 0
	next.disabled = page >= pages - 1
	previous.accessibility_name = "Previous %s page" % layer
	next.accessibility_name = "Next %s page" % layer
	page_announcement.text = "%s page %s of %s" % [layer.capitalize(), page + 1, pages]
	page_announcement.accessibility_name = page_announcement.text
	for index in range(page * count, mini((page + 1) * count, entries.size())):
		var item: Dictionary = entries[index]
		var card := _button("", "slot-paper", "", str(item.name), rail)
		card.toggle_mode = true
		card.button_pressed = active_item == str(item.id)
		card.disabled = not item.get("available", true) or (int(item.get("count", 0)) <= 0 and not item.get("assigned", false))
		card.accessibility_description = "Assigned. Drag to move." if item.get("assigned", false) else "%s available. Drag onto the floor, or select then tap a free tile." % int(item.get("count", 0))
		if layer == "floor": card.accessibility_description = "Current floor. Floor customization is not yet available."
		var preview := ItemPreview.new()
		preview.art = art
		preview.entry = item
		preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(preview)
		var name_label := _label(_inventory_caption(item))
		name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		name_label.add_theme_color_override("font_color", INK)
		card.add_child(name_label)
		var stock_badge := Panel.new()
		stock_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(stock_badge)
		var stock := _label("Placed" if item.get("assigned", false) else "Current" if layer == "floor" else "Ready" if layer == "people" else "%s left" % int(item.get("count", 0)))
		stock.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		stock.add_theme_color_override("font_color", INK)
		stock.modulate.a = 0.72
		stock.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		card.add_child(stock)
		card.set_meta("entry", item)
		card.set_meta("preview", preview)
		card.set_meta("name_label", name_label)
		card.set_meta("stock", stock)
		card.set_meta("stock_badge", stock_badge)
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
	var inset_buttons: Array = [live, shop, previous, next, inspection_close]
	inset_buttons.append_array(layers.values())
	for button: Button in inset_buttons:
		button.custom_minimum_size = Vector2(100, 100) * unit
	skin.apply_panel(tray, "container-tray", unit)
	skin.apply_panel(category_rail, "container-tray", unit)
	skin.apply_panel(category_rod, "noren-rod" if skin.manifest.styles.has("noren-rod") else "noren-rail", unit)
	skin.apply_panel(bottom_dock, "noren-dock" if skin.manifest.styles.has("noren-dock") else "control-wood", unit)
	skin.apply_panel(context_bubble, "context-bubble", unit)
	skin.apply_panel(inspection_panel, "container-modal", unit)
	skin.apply_panel(inspection_preview_panel, "slot-paper", unit)
	rejection.add_theme_stylebox_override("normal", skin.style("toast-error", unit))
	var editor: Dictionary = state.get("editor", {})
	var layer: String = str(editor.get("layer", "people"))
	var open: bool = bool(editor.get("tray_open", true))
	var drawer_height := DRAWER_HEIGHT if open else DOCK_HEIGHT
	live.position = area.position + Vector2(area.size.x - 190 * unit, 30 * unit)
	live.size = Vector2(166, 100) * unit
	live.add_theme_font_size_override("font_size", maxi(1, int(32 * unit)))
	live.add_theme_constant_override("icon_max_width", int(32 * unit))
	_layout_button_visual(live, Rect2(0, 0, 166, 100), 32, 32)
	tray.visible = open
	tray.accessibility_name = "%s inventory" % layer.capitalize()
	_move_control(tray, Vector2(area.position.x, area.end.y - drawer_height * unit))
	tray.size = Vector2(area.size.x, DRAWER_HEIGHT * unit)
	_move_control(category_rail, Vector2(area.position.x, area.end.y - (drawer_height + CATEGORY_HEIGHT) * unit))
	category_rail.size = Vector2(area.size.x, CATEGORY_HEIGHT * unit)
	inventory_backing.position = category_rail.position
	inventory_backing.size = Vector2(area.size.x, maxf(0.0, area.end.y - category_rail.position.y))
	category_rod.position = Vector2(0, 4) * unit
	category_rod.size = Vector2(720, 24) * unit
	bottom_dock.position = Vector2(area.position.x, area.end.y - DOCK_HEIGHT * unit)
	bottom_dock.size = Vector2(area.size.x, DOCK_HEIGHT * unit)
	title.visible = false
	previous.position = Vector2(4, 14) * unit
	next.position = Vector2(616, 14) * unit
	previous.size = Vector2(100, CARD_HEIGHT) * unit
	next.size = previous.size
	for button in [previous, next]:
		button.add_theme_constant_override("icon_max_width", int(20 * unit))
		_layout_button_visual(button, Rect2(32, 0, 36, CARD_HEIGHT), 1, 20)
	rail.position = Vector2(108, 14) * unit
	rail.size = Vector2(504, CARD_HEIGHT) * unit
	page_announcement.position = Vector2.ZERO
	page_announcement.size = Vector2.ONE
	var slot_width := 504.0 / (LAYOUT_PAGE_SIZE if layer == "layout" else PAGE_SIZE)
	for index in range(cards.size()):
		var card: Button = cards[index]
		card.position = Vector2(index * slot_width + 4, 0) * unit
		card.size = Vector2(slot_width - 8, CARD_HEIGHT) * unit
		var preview: Control = card.get_meta("preview")
		preview.position = Vector2(13, 9) * unit
		preview.size = Vector2(slot_width - 34, 108) * unit
		var name_label: Label = card.get_meta("name_label")
		name_label.position = Vector2(5, 118) * unit
		name_label.size = Vector2(slot_width - 18, 34) * unit
		name_label.add_theme_font_size_override("font_size", maxi(1, int(24 * unit)))
		name_label.visible = layer != "floor"
		var stock: Label = card.get_meta("stock")
		var stock_badge: Panel = card.get_meta("stock_badge")
		stock.visible = layer != "floor"
		stock_badge.visible = false
		stock_badge.add_theme_stylebox_override("panel", skin.style("stock-badge", unit))
		stock.position = Vector2(5, 152) * unit
		stock.size = Vector2(slot_width - 18, 30) * unit
		stock.add_theme_font_size_override("font_size", maxi(1, int(20 * unit)))
		if layer == "floor":
			preview.position.y = 28 * unit
			preview.size.y = 128 * unit
		_style_button(card)
	var tab_left := 12.0
	for index in range(3):
		var key: String = ["people", "layout", "floor"][index]
		var button: Button = layers[key]
		var tab_width: float = [184.0, 184.0, 152.0][index]
		button.text = key.capitalize()
		button.set_meta("skin_role", "tab-active" if key == layer else "tab-idle")
		button.set_pressed_no_signal(key == layer)
		button.accessibility_description = "Selected, tray %s" % ("open" if open else "closed") if key == layer else "Switch to %s and open its tray" % key
		button.position = Vector2(tab_left, 0) * unit
		button.size = Vector2(tab_width, CATEGORY_HEIGHT) * unit
		button.add_theme_font_size_override("font_size", maxi(1, int(30 * unit)))
		button.add_theme_constant_override("icon_max_width", int(40 * unit))
		_style_button(button)
		_layout_button_visual(button, Rect2(4, 0, tab_width - 8, CATEGORY_HEIGHT), 30, 36)
		tab_left += tab_width
	shop.position = Vector2(532, 0) * unit
	shop.size = Vector2(176, CATEGORY_HEIGHT) * unit
	shop.add_theme_font_size_override("font_size", maxi(1, int(30 * unit)))
	shop.add_theme_constant_override("icon_max_width", int(32 * unit))
	_layout_button_visual(shop, Rect2(8, 0, 160, 100), 30, 32)
	_layout_context()
	for button in [live, previous, next, shop, rotate, remove, inspection_close]: _style_button(button)
	rejection.position = Vector2(area.position.x + 60 * unit, area.position.y + 168 * unit)
	rejection.size = Vector2(600, 110) * unit
	rejection.add_theme_font_size_override("font_size", maxi(1, int(30 * unit)))
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
	inspection_close.add_theme_constant_override("icon_max_width", int(40 * unit))
	_layout_button_visual(inspection_close, Rect2(0, 0, 180, 100), 28, 32)
	inspection_preview_panel.position = Vector2(24, 120) * unit
	inspection_preview_panel.size = Vector2(205, 325) * unit
	inspection_preview.position = Vector2(40, 136) * unit
	inspection_preview.size = Vector2(173, 293) * unit
	inspection_details.position = Vector2(248, 150) * unit
	inspection_details.size = Vector2(365, 300) * unit
	inspection_details.add_theme_font_size_override("font_size", maxi(1, int(32 * unit)))

func _layout_context() -> void:
	# Both labeled actions have 100+ logical-pixel targets. The complete generated
	# capsule stays beside the selection and outside the fixed category drawer.
	var floor_bounds := Rect2(area.position + Vector2(0, 148 * unit), Vector2(area.size.x, maxf(0.0, occlusion_top() - area.position.y - 148 * unit)))
	var contextual := selected_visible and floor_bounds.has_point(target_base)
	context_bubble.visible = contextual
	rotate.visible = contextual
	remove.visible = contextual
	context_bubble.size = Vector2(304, 128) * unit
	context_pointer.position = Vector2(140, 104) * unit
	context_pointer.size = Vector2(24, 22) * unit
	var left := clampf(target_base.x - 152 * unit, area.position.x + 12 * unit, area.end.x - 316 * unit)
	var upper := area.position.y + 148 * unit
	var lower := maxf(upper, occlusion_top() - 168 * unit)
	var top := target_base.y - 236 * unit
	if top < upper and target_base.y + 80 * unit <= lower:
		top = target_base.y + 80 * unit
	context_bubble.position = Vector2(left, clampf(top, upper, lower))
	for index in range(2):
		var button: Button = [rotate, remove][index]
		button.position = Vector2(12 + index * 140, 8) * unit
		button.size = Vector2(140, 112) * unit
		button.add_theme_font_size_override("font_size", maxi(1, int(27 * unit)))
		button.add_theme_constant_override("icon_max_width", int(42 * unit))

func occlusion_top() -> float:
	return category_rail.position.y if category_rail != null else area.end.y

func blocked_rects() -> Array[Rect2]:
	var result: Array[Rect2] = []
	for control in [live, inventory_backing, category_rail, tray, context_bubble]:
		if control != null and control.is_visible_in_tree():
			var bounds: Rect2 = control.get_global_rect()
			if control == context_bubble:
				bounds.size.y += 20 * unit
			result.append(bounds)
	return result

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
	var messages := {"occupied": "That tile is occupied.", "entrance": "Keep the entrance clear.", "customer_busy": "A guest is using this seat.", "customer_path": "Keep an aisle open for guests.", "no_stock": "None left in inventory.", "shop_unavailable": "Shop is not available yet.", "invalid_position": "Place objects on cleared floor."}
	rejection.text = messages.get(reason, "This object cannot go there.")
	rejection.accessibility_name = rejection.text
	rejection.show()
	rejection_seconds = 1.3

func _process(delta: float) -> void:
	# The backing reaches the bottom even while the category row slides. Its
	# cream field is always visible through the separate curtains' loop gaps.
	if category_rail != null and inventory_backing != null:
		inventory_backing.position = category_rail.position
		inventory_backing.size = Vector2(area.size.x, maxf(0.0, area.end.y - category_rail.position.y))
	if rejection_seconds > 0:
		rejection_seconds -= delta
		if rejection_seconds <= 0: rejection.hide()
