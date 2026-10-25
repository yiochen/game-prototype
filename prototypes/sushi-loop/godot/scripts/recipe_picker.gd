extends Control
## Native approved maple picker; shared unchanged by restaurant and gallery.
const Book = preload("res://scripts/recipe_book.gd")
const Art = preload("res://scripts/recipe_art.gd")
const Dish = preload("res://scripts/recipe_dish_view.gd")
const Wood = preload("res://scripts/wood_skin.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const INK := Color("592c10")
signal inspected(chef_id: String, recipe_id: String)
signal prepared(chef_id: String, recipe_id: String)
signal closed
var wood = Wood.new()
var session_state: Dictionary = {}
var actor: Dictionary = {}
var chef_id := ""
var selected := ""
var unit := 1.0
var area := Rect2()
var safe_top := 0.0
var panel: Panel
var maple_face: TextureRect
var catalog_backing: Panel
var heading: Label
var level_label: Label
var portrait: Control
var close_button: Button
var catalog: ScrollContainer
var catalog_content: MarginContainer
var grid: GridContainer
var details: Panel
var detail_dish: Control
var detail_name: Label
var detail_price: Label
var detail_coin: TextureRect
var detail_time: Label
var detail_requirement: Label
var prepare_button: Button
var preparing_label: Label
var waves: Control
var tiles: Dictionary = {}
var font: Font
var focus_before: Control
var touch_index := -1
var touch_origin := Vector2.ZERO
var touch_scroll := 0
var touch_recipe := ""
var touch_dragged := false

class Portrait extends Control:
	const HeadArt = preload("res://scripts/recipe_art.gd")
	var identity := "chef-lena"
	func _draw() -> void:
		var texture := HeadArt.head(identity)
		# Exactly the shared 25:32 crop: trim the bottom, preserve proportions.
		var source := Rect2(Vector2.ZERO, Vector2(texture.get_width(), texture.get_width() * 1.28))
		draw_texture_rect_region(texture, Rect2(Vector2.ZERO, size), source)

class Waves extends Control:
	var wood_skin
	func _draw() -> void:
		var u := size.x / 664.0
		wood_skin.draw_asset(self, "footer-waves", Vector2(0, 0), u)

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	font = Typography.body()
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):850}
	var scrim := ColorRect.new()
	scrim.color = Color(0.25, 0.16, 0.07, 0.20)
	scrim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	scrim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(scrim)
	panel = Panel.new()
	panel.accessibility_name = "Chef recipe picker"
	panel.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(panel)
	maple_face = TextureRect.new()
	maple_face.texture = wood.texture("wood-grain")
	maple_face.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	maple_face.stretch_mode = TextureRect.STRETCH_SCALE
	maple_face.texture_repeat = CanvasItem.TEXTURE_REPEAT_ENABLED
	maple_face.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var maple_material := ShaderMaterial.new()
	maple_material.shader = load("res://scripts/maple_face.gdshader")
	maple_face.material = maple_material
	panel.add_child(maple_face)
	catalog_backing = Panel.new()
	catalog_backing.mouse_filter = Control.MOUSE_FILTER_STOP
	catalog_backing.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	panel.add_child(catalog_backing)
	heading = _label(panel)
	level_label = _label(panel)
	close_button = _button("×", "Close recipes", panel)
	close_button.pressed.connect(dismiss)
	catalog = ScrollContainer.new()
	catalog.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	catalog.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	catalog.follow_focus = true
	catalog.mouse_filter = Control.MOUSE_FILTER_STOP
	catalog.accessibility_name = "Scrollable recipe catalog"
	catalog_backing.add_child(catalog)
	catalog_content = MarginContainer.new()
	catalog_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	catalog.add_child(catalog_content)
	grid = GridContainer.new()
	grid.columns = 2
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	catalog_content.add_child(grid)
	details = Panel.new()
	details.mouse_filter = Control.MOUSE_FILTER_STOP
	details.accessibility_name = "Selected recipe details"
	panel.add_child(details)
	detail_dish = Dish.new()
	details.add_child(detail_dish)
	detail_name = _label(details)
	detail_name.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail_price = _label(details)
	detail_coin = TextureRect.new()
	detail_coin.texture = _coin_texture()
	detail_coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	detail_coin.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	detail_coin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	details.add_child(detail_coin)
	detail_time = _label(details)
	detail_time.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	detail_requirement = _label(details)
	prepare_button = _button("Prepare", "Prepare selected recipe", details)
	prepare_button.pressed.connect(func():
		if not prepare_button.disabled: prepared.emit(chef_id, selected))
	preparing_label = _label(details)
	preparing_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	preparing_label.text = "Preparing · Current recipe"
	preparing_label.accessibility_name = "Preparing current recipe"
	waves = Waves.new()
	waves.wood_skin = wood
	waves.mouse_filter = Control.MOUSE_FILTER_IGNORE
	waves.clip_contents = true
	details.add_child(waves)
	details.move_child(waves,0)
	portrait = Portrait.new()
	portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	portrait.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	panel.add_child(portrait)
	hide()

func _label(parent: Node) -> Label:
	var result := Label.new()
	result.add_theme_font_override("font", font)
	result.add_theme_color_override("font_color", INK)
	result.mouse_filter = Control.MOUSE_FILTER_IGNORE
	result.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	parent.add_child(result)
	return result

func _button(text: String, accessible: String, parent: Node) -> Button:
	var result := Button.new()
	result.text = text
	result.accessibility_name = accessible
	result.add_theme_font_override("font", font)
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]: result.add_theme_color_override(key, INK)
	result.add_theme_color_override("font_disabled_color", Color("8b7359"))
	parent.add_child(result)
	return result

func open(state: Dictionary, id: String) -> void:
	focus_before = get_viewport().gui_get_focus_owner()
	session_state = state
	chef_id = id
	actor = _find_chef(state, id)
	if actor.is_empty(): return
	selected = str(actor.get("recipe_id", ""))
	show()
	catalog.scroll_vertical = 0
	_rebuild()
	_refresh_details()
	layout(area, safe_top)
	close_button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	close_button.grab_focus()
	if not selected.is_empty():
		inspected.emit(chef_id, selected)
		call_deferred("_reveal_selected")

func _find_chef(state: Dictionary, id: String) -> Dictionary:
	for object in state.objects:
		if object.kind == "chef" and object.id == id: return object
	for stock in state.inventory:
		if stock.kind == "chef" and stock.id == id: return stock
	return {}

func refresh(state: Dictionary) -> void:
	if not visible: return
	var signature := JSON.stringify([state.recipes, state.recipe_book, _find_chef(state, chef_id).get("recipe_id", "")])
	var previous := JSON.stringify([session_state.recipes, session_state.recipe_book, actor.get("recipe_id", "")])
	session_state = state
	actor = _find_chef(state, chef_id)
	if signature != previous:
		# Never rebuild the scroll tree for Live preparation progress.
		var offset := catalog.scroll_vertical
		_rebuild()
		catalog.set_deferred("scroll_vertical", offset)
		_refresh_details()

func _known(id: String) -> bool:
	return id in session_state.recipe_book.discovered

func _recipe(id: String) -> Dictionary:
	if id.begins_with("unknown-"): return {"name":"Undiscovered dish", "tier":id.trim_prefix("unknown-"), "food_cell":4}
	return session_state.recipes.get(id, {})

func _eligible(id: String) -> bool:
	return _known(id) and mini(int(actor.get("level", 1)), int(actor.get("level_cap", 12))) >= Book.required_level(_recipe(id))

func _sort_key(id: String) -> int:
	var rank := Art.TIERS.find(str(_recipe(id).tier))
	return -rank if _eligible(id) else 100-rank if _known(id) else 200+rank

func _rebuild() -> void:
	for child in grid.get_children():
		grid.remove_child(child)
		child.queue_free()
	tiles.clear()
	var ids: Array = session_state.recipes.keys()
	for tier_name in Book.catalog().unknown_tiers: ids.append("unknown-" + str(tier_name))
	ids.sort_custom(func(a, b): return _sort_key(a) < _sort_key(b) if _sort_key(a) != _sort_key(b) else str(a) < str(b))
	for id: String in ids:
		var recipe := _recipe(id)
		var known := _known(id)
		var tile := _button("", "Inspect " + (str(recipe.name) if known else "undiscovered dish"), grid)
		tile.accessibility_description = "%s plate, %s rim, requires Level %s%s%s%s" % [recipe.tier, Book.catalog().rim_patterns[maxi(0, Art.TIERS.find(recipe.tier))], Book.required_level(recipe), ", %s coins" % int(recipe.price) if known else "", ", currently preparing" if actor.get("recipe_id") == id else "", ", new discovery" if id in session_state.recipe_book.new else ""]
		tile.set_meta("accessible_base", tile.accessibility_description)
		tile.toggle_mode = true
		tile.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		tile.pressed.connect(func():
			if not touch_dragged and touch_index == -1: inspect(id))
		var dish := Dish.new()
		dish.recipe = recipe
		dish.unknown = not known
		dish.modulate.a = 0.48 if known and not _eligible(id) else 1.0
		tile.add_child(dish)
		var name_label := _label(tile)
		name_label.text = str(recipe.name) if known else "???"
		name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var price := _label(tile)
		price.text = "%s" % int(recipe.price) if known else ""
		price.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var coin := TextureRect.new()
		coin.texture = _coin_texture()
		coin.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		coin.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		coin.mouse_filter = Control.MOUSE_FILTER_IGNORE
		coin.visible = known
		tile.add_child(coin)
		var badge := _label(tile)
		badge.text = "NEW"
		badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		badge.visible = id in session_state.recipe_book.new
		var backing := _flat(Color("ffedc5"), 14)
		backing.border_color = Color("b07b44")
		backing.set_border_width_all(1)
		badge.add_theme_stylebox_override("normal", backing)
		tiles[id] = {"button":tile, "dish":dish, "name":name_label, "price":price, "coin":coin, "badge":badge}
	layout(area, safe_top)

func _flat(color: Color, radius: float) -> StyleBoxFlat:
	var result := StyleBoxFlat.new()
	result.bg_color = color
	result.set_corner_radius_all(maxi(1, int(radius * unit)))
	result.content_margin_left = 0
	result.content_margin_right = 0
	result.content_margin_top = 0
	result.content_margin_bottom = 0
	return result

func inspect(id: String) -> void:
	selected = id
	if _known(id):
		inspected.emit(chef_id, id)
		session_state.recipe_book.new.erase(id)
	_refresh_details()
	layout(area, safe_top)

func _refresh_details() -> void:
	var recipe := _recipe(selected)
	var exists := not recipe.is_empty()
	var known := exists and _known(selected)
	var eligible := known and _eligible(selected)
	detail_dish.visible = exists
	detail_dish.recipe = recipe
	detail_dish.unknown = not known
	detail_dish.queue_redraw()
	detail_name.text = str(recipe.name) if known else "Undiscovered dish" if exists else "Choose a recipe"
	detail_price.text = "%s" % int(recipe.price) if known else ""
	detail_coin.visible = known
	detail_time.text = "Prep with %s   %s" % [str(actor.get("name", "Chef")), "%.1f sec" % Book.seconds(recipe, actor) if eligible else "—"] if known else "Find new creatures on expeditions." if exists else "Pick a dish above to see its details."
	detail_requirement.text = "Requires Lv %s" % Book.required_level(recipe) if known else ""
	prepare_button.disabled = not eligible
	prepare_button.visible = not (eligible and str(actor.get("recipe_id", "")) == selected)
	preparing_label.visible = not prepare_button.visible
	details.accessibility_description = "%s. %s. %s. %s" % [detail_name.text, detail_price.text, detail_time.text, detail_requirement.text]

func _text(label: Label, bounds: Rect2, pixels: float) -> void:
	label.position = bounds.position * unit
	label.size = bounds.size * unit
	label.add_theme_font_size_override("font_size", maxi(1, int(pixels * unit)))

func layout(value: Rect2, inset := 0.0) -> void:
	area = value
	safe_top = inset
	if panel == null or area.size.x <= 0: return
	unit = area.size.x / 720.0
	var top := maxf(area.position.y, inset) + 74 * unit
	panel.position = Vector2(area.position.x + 24 * unit, top)
	panel.size = Vector2(672 * unit, area.end.y - top - 26 * unit)
	var outer_shadow := _flat(Color.TRANSPARENT, 32)
	outer_shadow.shadow_color = Color(0.35, 0.18, 0.05, 0.2)
	outer_shadow.shadow_size = int(8*unit)
	outer_shadow.shadow_offset = Vector2(0,6)*unit
	panel.add_theme_stylebox_override("panel", outer_shadow)
	maple_face.size = panel.size
	var maple_material: ShaderMaterial = maple_face.material
	maple_material.set_shader_parameter("surface_size", panel.size)
	maple_material.set_shader_parameter("corner_radius", 32*unit)
	maple_material.set_shader_parameter("grain_width", 720*unit)
	var height := panel.size.y / unit
	var header := 146.0
	var footer := 390.0
	var detail_top := height - footer
	catalog_backing.position = Vector2(0,header)*unit
	catalog_backing.size = Vector2(672,detail_top-header+48)*unit
	var cream := _flat(Color("fff3db"),32)
	cream.corner_radius_bottom_left = 0
	cream.corner_radius_bottom_right = 0
	catalog_backing.add_theme_stylebox_override("panel",cream)
	heading.text = "%s’s recipes" % str(actor.get("name", "Chef"))
	_text(heading, Rect2(184, 28, 368, 52), 36)
	level_label.text = "Level %s" % int(actor.get("level", 1))
	_text(level_label, Rect2(184, 83, 348, 40), 25)
	portrait.identity = str(actor.get("art_id", "chef-lena"))
	portrait.position = Vector2(16, header - 204.8) * unit
	portrait.size = Vector2(160, 204.8) * unit
	portrait.queue_redraw()
	close_button.position = Vector2(552, 18) * unit
	close_button.size = Vector2(96, 96) * unit
	close_button.add_theme_font_size_override("font_size", int(54 * unit))
	for treatment in ["normal", "hover", "pressed", "disabled"]:
		var close_surface := _flat(Color("f5d39e") if treatment == "pressed" else Color("ffe8bc"), 48)
		close_surface.shadow_color = Color(0.45, 0.25, 0.08, 0.18)
		close_surface.shadow_size = int(5*unit)
		close_surface.shadow_offset = Vector2(0,4)*unit
		close_button.add_theme_stylebox_override(treatment, close_surface)
	var focus := _flat(Color.TRANSPARENT, 30)
	focus.border_color = Color("93633c")
	focus.set_border_width_all(maxi(1, int(3*unit)))
	close_button.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	catalog.position = Vector2(14, 0) * unit
	catalog.size = Vector2(644, maxf(120, detail_top - header)) * unit
	grid.add_theme_constant_override("h_separation", int(16*unit))
	grid.add_theme_constant_override("v_separation", int(16*unit))
	# This inset belongs to the scrolling content and disappears as it scrolls.
	catalog_content.add_theme_constant_override("margin_top",int(24*unit))
	var tile_width := (644.0 - 16.0) / 2.0
	for id in tiles:
		var record: Dictionary = tiles[id]
		var tile: Button = record.button
		tile.custom_minimum_size = Vector2(tile_width, 298) * unit
		tile.set_pressed_no_signal(selected == id)
		tile.accessibility_description = str(tile.get_meta("accessible_base")) + (", selected for inspection" if selected == id else "")
		var background := _flat(Color("fffdf0") if selected == id else Color("faeaca"), 24)
		background.border_color = Color("93633c") if actor.get("recipe_id") == id else Color("e4c99d")
		background.set_border_width_all(maxi(1, int((3 if actor.get("recipe_id") == id else 1)*unit)))
		background.shadow_color = Color(0.57, 0.33, 0.13, 0.20)
		background.shadow_size = maxi(1,int(2*unit))
		background.shadow_offset = Vector2(0, 3)*unit
		for treatment in ["normal", "hover", "pressed", "disabled", "hover_pressed"]: tile.add_theme_stylebox_override(treatment, background)
		tile.add_theme_stylebox_override("focus", focus)
		record.dish.position = Vector2((tile_width-218)/2, 8)*unit
		record.dish.size = Vector2(218, 218)*unit
		_text(record.name, Rect2(7, 218, tile_width-14, 34), 26)
		_text(record.price, Rect2(22, 254, tile_width-22, 36), 29)
		record.coin.position = Vector2(tile_width/2-48, 253)*unit
		record.coin.size = Vector2(34, 34)*unit
		_text(record.badge, Rect2(tile_width-80, 8, 70, 30), 19)
		record.badge.visible = id in session_state.recipe_book.new
	# Full-width details, top corners kept round, padded content inside.
	details.position = Vector2(0, detail_top)*unit
	details.size = Vector2(672, footer)*unit
	details.add_theme_stylebox_override("panel", wood.style("panel-maple", unit))
	detail_dish.position = Vector2(16, 8)*unit
	detail_dish.size = Vector2(260, 238)*unit
	_text(detail_name, Rect2(278, 32, 370, 80), 34)
	_text(detail_price, Rect2(326, 104, 312, 44), 33)
	detail_coin.position = Vector2(278, 107)*unit
	detail_coin.size = Vector2(38, 38)*unit
	_text(detail_time, Rect2(278, 160, 362, 64), 23)
	_text(detail_requirement, Rect2(278, 226, 360, 28), 23)
	detail_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	detail_time.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	if selected.is_empty():
		detail_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		detail_time.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_text(detail_name, Rect2(32, 48, 608, 64), 34)
		_text(detail_time, Rect2(32, 124, 608, 90), 23)
	prepare_button.position = Vector2(32, 260)*unit
	prepare_button.size = Vector2(608, 100)*unit
	prepare_button.add_theme_font_size_override("font_size", int(35*unit))
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]: prepare_button.add_theme_color_override(key, Color("fff9e9"))
	for treatment in ["normal", "hover", "pressed", "disabled"]:
		prepare_button.add_theme_stylebox_override(treatment, wood.style("hud-cream-normal" if treatment == "disabled" else "hud-live-pressed" if treatment == "pressed" else "hud-live-normal", unit))
	prepare_button.add_theme_stylebox_override("focus", focus)
	_text(preparing_label, Rect2(32, 260, 608, 100), 28)
	waves.position = Vector2(4, footer-32)*unit
	waves.size = Vector2(664, 24)*unit
	waves.queue_redraw()
	for control: Control in [close_button, prepare_button]:
		var physical := get_viewport_transform().get_scale().x
		control.custom_minimum_size = Vector2.ONE * 44.01 / maxf(0.001, physical)

func _reveal_selected() -> void:
	if tiles.has(selected): catalog.ensure_control_visible(tiles[selected].button)

func _input(event: InputEvent) -> void:
	if not visible: return
	if event is InputEventScreenTouch and event.pressed and catalog.get_global_rect().has_point(event.position):
		if touch_index == -1:
			touch_index = event.index
			touch_origin = event.position
			touch_scroll = catalog.scroll_vertical
			touch_recipe = ""
			touch_dragged = false
			for id in tiles:
				if tiles[id].button.get_global_rect().has_point(event.position):
					touch_recipe = id
					break
		# Own touch gestures before BaseButton receives a press. This prevents
		# a scroll release from inspecting a tile or leaving a held button.
		get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag and event.index == touch_index:
		var delta: Vector2 = event.position-touch_origin
		if delta.length()>10/maxf(0.001, get_viewport_transform().get_scale().x): touch_dragged = true
		if touch_dragged:
			catalog.scroll_vertical = touch_scroll-int(delta.y)
			get_viewport().set_input_as_handled()
	elif event is InputEventScreenTouch and not event.pressed and event.index == touch_index:
		var pick := touch_recipe
		var dragged := touch_dragged
		touch_index = -1
		if not event.canceled and not dragged and not pick.is_empty() and tiles.has(pick) and tiles[pick].button.get_global_rect().has_point(event.position): inspect(pick)
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE:
			dismiss()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_TAB:
			var keyboard_glow := _flat(Color.TRANSPARENT,48)
			keyboard_glow.shadow_color = Color(0.85,0.5,0.18,0.75)
			keyboard_glow.shadow_size = maxi(2,int(5*unit))
			close_button.add_theme_stylebox_override("focus",keyboard_glow)
			var targets: Array[Control] = [close_button]
			for record in tiles.values(): targets.append(record.button)
			if prepare_button.visible and not prepare_button.disabled: targets.append(prepare_button)
			var current := targets.find(get_viewport().gui_get_focus_owner())
			targets[posmod(current+(-1 if event.shift_pressed else 1), targets.size())].grab_focus()
			get_viewport().set_input_as_handled()

func dismiss() -> void:
	touch_index = -1
	touch_dragged = false
	hide()
	if is_instance_valid(focus_before) and focus_before.is_visible_in_tree(): focus_before.grab_focus()
	closed.emit()

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		touch_index = -1
		touch_dragged = false
		var buttons: Array = [close_button, prepare_button]
		for record in tiles.values(): buttons.append(record.button)
		for button in buttons:
			if button == null: continue
			var disabled: bool = button.disabled
			button.disabled = true
			button.disabled = disabled

func _coin_texture() -> Texture2D:
	var texture := AtlasTexture.new()
	texture.atlas = wood.texture("coin-emblem")
	texture.region = Rect2(32, 32, 108, 108)
	return texture
