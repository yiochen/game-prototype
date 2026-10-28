extends Control
## Native approved maple picker; shared unchanged by restaurant and gallery.
const Book = preload("res://scripts/recipe_book.gd")
const Art = preload("res://scripts/recipe_art.gd")
const Dish = preload("res://scripts/recipe_dish_view.gd")
const Wood = preload("res://scripts/wood_skin.gd")
const UISkin = preload("res://scripts/ui_skin.gd")
const Typography = preload("res://scripts/typography.gd")
const Management = preload("res://scripts/chef_management.gd")
const Dismissal = preload("res://scripts/chef_dismissal.gd")
const Dev = preload("res://scripts/chef_development.gd")
const INK := Color("592c10")
signal inspected(chef_id: String, recipe_id: String)
signal prepared(chef_id: String, recipe_id: String)
signal closed
signal management_requested(value: Dictionary)
signal placement_requested(chef_id: String)
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
var level_label: Label # Retained as a hidden compatibility node; header uses tabs.
var recipe_tab: Button
var manage_tab: Button
var tab := "recipes"
var slide := 0.0
var slide_tween: Tween
var content_clip: Control
var recipe_page: Control
var manage_view: Management
var dismissal: Dismissal
var separator: ColorRect
var tab_marker: ColorRect
var reduced_motion := false
var management_signature := ""
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
	content_clip=Control.new();content_clip.clip_contents=true;content_clip.mouse_filter=MOUSE_FILTER_STOP;panel.add_child(content_clip)
	recipe_page=Control.new();recipe_page.mouse_filter=MOUSE_FILTER_STOP;content_clip.add_child(recipe_page)
	manage_view=Management.new();content_clip.add_child(manage_view)
	manage_view.requested.connect(func(value):
		if tab=="manage" and visible and not dismissal.visible:management_requested.emit(value))
	manage_view.placement_requested.connect(func():
		if tab=="manage" and visible and not dismissal.visible:placement_requested.emit(chef_id))
	manage_view.firing_requested.connect(open_firing)
	catalog_backing = Panel.new()
	catalog_backing.mouse_filter = Control.MOUSE_FILTER_STOP
	catalog_backing.clip_children = CanvasItem.CLIP_CHILDREN_AND_DRAW
	recipe_page.add_child(catalog_backing)
	heading = _label(panel)
	level_label = _label(panel);level_label.hide()
	recipe_tab=_button("Recipes","Recipes tab",panel);manage_tab=_button("Manage","Manage tab",panel)
	recipe_tab.pressed.connect(func():switch_tab("recipes"));manage_tab.pressed.connect(func():switch_tab("manage"))
	tab_marker=ColorRect.new();tab_marker.color=Color("95613c");tab_marker.mouse_filter=MOUSE_FILTER_IGNORE;panel.add_child(tab_marker)
	separator=ColorRect.new();separator.color=Color("d29c5e");separator.mouse_filter=MOUSE_FILTER_IGNORE;panel.add_child(separator)
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
	recipe_page.add_child(details)
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
		if tab=="recipes" and prepare_button.is_visible_in_tree() and not prepare_button.disabled and not dismissal.visible: prepared.emit(chef_id, selected))
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
	dismissal=Dismissal.new();add_child(dismissal)
	dismissal.confirmed.connect(func():management_requested.emit({"type":"fire_chef","chef_id":chef_id}))
	dismissal.canceled.connect(func():switch_tab("manage",false);manage_view.fire.grab_focus())
	dismissal.closed.connect(dismiss)
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
	tab="recipes";slide=0;manage_view.result.text="";management_signature=""
	if is_instance_valid(slide_tween):slide_tween.kill()
	show()
	catalog.scroll_vertical = 0
	_rebuild()
	_refresh_details()
	manage_view.refresh(state,actor)
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
	var next_actor:=_find_chef(state,chef_id)
	if next_actor.is_empty() and dismissal.visible:
		session_state=state
		if state.get("staff",{}).get("dismissed",{}).has(chef_id):dismissal.play_fired()
		return
	if next_actor.is_empty():dismiss();return
	var signature := JSON.stringify([state.recipes, state.recipe_book, next_actor.get("recipe_id", ""), _is_placed(state), next_actor.get("level"),next_actor.get("cooking_speed")])
	var previous := JSON.stringify([session_state.recipes, session_state.recipe_book, actor.get("recipe_id", ""), _is_placed(session_state),actor.get("level"),actor.get("cooking_speed")])
	session_state = state
	actor = next_actor
	var management_key:=JSON.stringify([chef_id,actor.level,actor.level_cap,actor.cooking_speed,actor.growth_rate,state.coins,_is_placed(state)])
	if management_key!=management_signature:
		manage_view.refresh(state,actor);management_signature=management_key
	if signature != previous:
		# Never rebuild the scroll tree for Live preparation progress.
		var offset := catalog.scroll_vertical
		_rebuild()
		catalog.set_deferred("scroll_vertical", offset)
		_refresh_details()

func _is_placed(state: Dictionary = session_state) -> bool:
	return state.get("objects", []).any(func(object): return object.get("kind") == "chef" and object.get("id") == chef_id)

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
	var placed := _is_placed()
	prepare_button.disabled = not placed or not eligible
	prepare_button.visible = placed and not (eligible and str(actor.get("recipe_id", "")) == selected)
	preparing_label.visible = placed and not prepare_button.visible
	details.accessibility_description = "%s. %s. %s. %s" % [detail_name.text, detail_price.text, detail_time.text, detail_requirement.text]

func _text(label: Label, bounds: Rect2, pixels: float) -> void:
	label.position = bounds.position * unit
	label.size = bounds.size * unit
	label.add_theme_font_size_override("font_size", maxi(1, int(pixels * unit)))

func layout(value: Rect2, inset := 0.0) -> void:
	area = value
	safe_top = inset
	if panel == null or area.size.x <= 0: return
	var physical:=maxf(.001,get_viewport_transform().get_scale().x)
	var compact:=size.x>size.y and size.y*physical<600
	if compact:
		var width:=minf(size.x,620.0/physical)
		area=Rect2((size.x-width)*.5,0,width,size.y)
	unit = minf(area.size.x/720.0,390.0/720.0/physical) if compact else area.size.x / 720.0
	var top := maxf(area.position.y, inset) + (34 if compact else 130) * unit
	panel.position = Vector2(area.position.x + 24 * unit, top)
	panel.size = Vector2(area.size.x-48*unit, area.end.y - top - (24 if compact else 110) * unit)
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
	var reference_width:=panel.size.x/unit
	var catalog_width:=reference_width-28
	var header := 136.0 if compact else 178.0
	var footer := (220.0 if _is_placed() else 200.0) if compact else 390.0 if _is_placed() else 286.0
	var detail_top := height - footer
	content_clip.position=Vector2(0,header)*unit
	content_clip.size=Vector2(reference_width,height-header)*unit
	recipe_page.size=content_clip.size
	manage_view.layout(content_clip.size,unit)
	_position_pages(slide)
	catalog_backing.position = Vector2.ZERO
	catalog_backing.size = Vector2(reference_width,detail_top-header+48)*unit
	var cream := _flat(Color("fff3db"),32)
	cream.corner_radius_bottom_left = 0
	cream.corner_radius_bottom_right = 0
	catalog_backing.add_theme_stylebox_override("panel",cream)
	heading.text = ("%s’s recipes" if tab=="recipes" else "%s") % str(actor.get("name", "Chef"))
	_text(heading, Rect2(184, 10 if compact else 32, reference_width-304, 52), 36)
	for i in range(2):
		var button:Button=[recipe_tab,manage_tab][i]
		button.position=Vector2(184+i*146,51 if compact else 89)*unit;button.size=Vector2(126,82)*unit
		button.add_theme_font_size_override("font_size",int(25*unit));button.accessibility_description="Selected tab" if (i==0)==(tab=="recipes") else "";button.toggle_mode=true;button.set_pressed_no_signal((i==0)==(tab=="recipes"))
		for treatment in ["normal","hover","pressed","focus"]:button.add_theme_stylebox_override(treatment,StyleBoxEmpty.new())
		button.add_theme_color_override("font_color",INK if (i==0)==(tab=="recipes") else Color("91633f"))
	tab_marker.position=Vector2(184+(0 if tab=="recipes" else 146),header-16)*unit;tab_marker.size=Vector2(126,4)*unit
	separator.position=Vector2(0,header)*unit;separator.size=Vector2(panel.size.x, maxf(1,unit));separator.visible=tab=="manage"
	portrait.identity = str(actor.get("art_id", "chef-lena"))
	portrait.position = Vector2(16, header - 204.8) * unit
	portrait.size = Vector2(160, 204.8) * unit
	portrait.queue_redraw()
	close_button.position = Vector2(reference_width-120, 12 if compact else 18) * unit
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
	catalog.size = Vector2(catalog_width, maxf(100, detail_top - header)) * unit
	grid.add_theme_constant_override("h_separation", int(16*unit))
	grid.add_theme_constant_override("v_separation", int(16*unit))
	# This inset belongs to the scrolling content and disappears as it scrolls.
	catalog_content.add_theme_constant_override("margin_top",int(24*unit))
	var tile_width := (catalog_width - 16.0) / 2.0
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
	details.position = Vector2(0, detail_top-header)*unit
	details.size = Vector2(reference_width, footer)*unit
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
	prepare_button.size = Vector2(reference_width-64, 100)*unit
	prepare_button.add_theme_font_size_override("font_size", int(35*unit))
	for key in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]: prepare_button.add_theme_color_override(key, Color("fff9e9"))
	for treatment in ["normal", "hover", "pressed", "disabled"]:
		prepare_button.add_theme_stylebox_override(treatment, wood.style("hud-cream-normal" if treatment == "disabled" else "hud-live-pressed" if treatment == "pressed" else "hud-live-normal", unit))
	prepare_button.add_theme_stylebox_override("focus", focus)
	_text(preparing_label, Rect2(32, 260, 608, 100), 28)
	waves.position = Vector2(4, footer-32)*unit
	waves.size = Vector2(reference_width-8, 24)*unit
	waves.queue_redraw()
	if compact:
		detail_dish.position=Vector2(14,4)*unit;detail_dish.size=Vector2(180,180)*unit
		_text(detail_name,Rect2(210,12,reference_width-480,48),30)
		_text(detail_price,Rect2(254,62,reference_width-510,36),28);detail_coin.position=Vector2(210,65)*unit
		_text(detail_time,Rect2(210,110,reference_width-480,42),22)
		_text(detail_requirement,Rect2(210,158,reference_width-480,30),21)
		prepare_button.position=Vector2(reference_width-244,54)*unit;prepare_button.size=Vector2(216,92)*unit
		_text(preparing_label,Rect2(reference_width-250,54,222,92),23)
		if selected.is_empty():
			_text(detail_name,Rect2(30,16,reference_width-300,60),30);_text(detail_time,Rect2(30,80,reference_width-300,64),22)
	for control: Control in [close_button, prepare_button,recipe_tab,manage_tab]:
		control.custom_minimum_size = Vector2.ONE * 44.01 / maxf(0.001, physical)
	if dismissal.visible:dismissal.layout(Rect2(Vector2(area.position.x,maxf(area.position.y,safe_top)),Vector2(area.size.x,area.end.y-maxf(area.position.y,safe_top))))

func _reveal_selected() -> void:
	if tiles.has(selected): catalog.ensure_control_visible(tiles[selected].button)

func _input(event: InputEvent) -> void:
	if not visible: return
	if dismissal.visible:
		if event.is_action_pressed("ui_cancel"):dismissal.back();get_viewport().set_input_as_handled()
		elif event is InputEventKey and event.pressed and event.keycode==KEY_TAB:
			var targets:=dismissal.targets();var current:=targets.find(get_viewport().gui_get_focus_owner());targets[posmod(current+(-1 if event.shift_pressed else 1),targets.size())].grab_focus();get_viewport().set_input_as_handled()
		return
	if tab=="recipes" and event is InputEventScreenTouch and event.pressed and catalog.get_global_rect().has_point(event.position):
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
		if event.keycode in [KEY_LEFT,KEY_RIGHT] and get_viewport().gui_get_focus_owner() in [recipe_tab,manage_tab]:
			switch_tab("manage" if tab=="recipes" else "recipes");(recipe_tab if tab=="recipes" else manage_tab).grab_focus();get_viewport().set_input_as_handled()
		elif event.keycode == KEY_ESCAPE:
			dismiss()
			get_viewport().set_input_as_handled()
		elif event.keycode == KEY_TAB:
			var keyboard_glow := _flat(Color.TRANSPARENT,48)
			keyboard_glow.shadow_color = Color(0.85,0.5,0.18,0.75)
			keyboard_glow.shadow_size = maxi(2,int(5*unit))
			close_button.add_theme_stylebox_override("focus",keyboard_glow)
			var targets: Array[Control] = [recipe_tab,manage_tab,close_button]
			if tab=="recipes":
				for record in tiles.values(): targets.append(record.button)
				if prepare_button.visible and not prepare_button.disabled: targets.append(prepare_button)
			else:
				if manage_view.upgrade.visible and not manage_view.upgrade.disabled:targets.append(manage_view.upgrade)
				targets.append(manage_view.unassign);targets.append(manage_view.fire)
			var current := targets.find(get_viewport().gui_get_focus_owner())
			targets[posmod(current+(-1 if event.shift_pressed else 1), targets.size())].grab_focus()
			get_viewport().set_input_as_handled()

func dismiss() -> void:
	if dismissal.visible:
		dismissal.back();return
	if is_instance_valid(slide_tween):slide_tween.kill()
	touch_index = -1
	touch_dragged = false
	hide()
	if is_instance_valid(focus_before) and focus_before.is_visible_in_tree(): focus_before.grab_focus()
	closed.emit()

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		touch_index = -1
		touch_dragged = false
		var buttons: Array = [close_button, prepare_button,recipe_tab,manage_tab]
		if manage_view!=null:buttons.append_array([manage_view.upgrade,manage_view.unassign,manage_view.fire])
		if dismissal!=null:buttons.append_array([dismissal.close_button,dismissal.cancel_button,dismissal.confirm_button])
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

func switch_tab(value:String,animate:=true)->void:
	if value not in ["recipes","manage"]:return
	for button in [prepare_button,manage_view.upgrade,manage_view.unassign,manage_view.fire]:
		var old_disabled:bool=button.disabled;button.disabled=true;button.disabled=old_disabled
	touch_index=-1;touch_dragged=false;tab=value
	if is_instance_valid(slide_tween):slide_tween.kill()
	layout(area,safe_top)
	var destination:=0.0 if tab=="recipes" else 1.0
	if reduced_motion or not animate:_position_pages(destination)
	else:
		slide_tween=create_tween();slide_tween.tween_method(_position_pages,slide,destination,.26).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
func _position_pages(value:float)->void:
	slide=value
	if content_clip==null:return
	var w:=content_clip.size.x
	recipe_page.position=Vector2(-value*w,0);manage_view.position=Vector2((1-value)*w,0)
	recipe_page.visible=value<.999 or tab=="recipes";manage_view.visible=value>.001 or tab=="manage"
	for record in tiles.values():record.button.mouse_filter=MOUSE_FILTER_STOP if tab=="recipes" else MOUSE_FILTER_IGNORE;record.button.focus_mode=FOCUS_ALL if tab=="recipes" else FOCUS_NONE
	for control in [prepare_button]:control.mouse_filter=MOUSE_FILTER_STOP if tab=="recipes" else MOUSE_FILTER_IGNORE;control.focus_mode=FOCUS_ALL if tab=="recipes" else FOCUS_NONE
	for control in [manage_view.upgrade,manage_view.unassign,manage_view.fire]:
		if control!=null:control.mouse_filter=MOUSE_FILTER_STOP if tab=="manage" else MOUSE_FILTER_IGNORE;control.focus_mode=FOCUS_ALL if tab=="manage" else FOCUS_NONE
	queue_redraw()
func open_firing()->void:
	if actor.is_empty() or tab!="manage" or dismissal.visible:return
	dismissal.reduced_motion=reduced_motion;dismissal.open(actor,Rect2(Vector2(area.position.x,maxf(area.position.y,safe_top)),Vector2(area.size.x,area.end.y-maxf(area.position.y,safe_top))))
func management_result(request:Dictionary,result:Dictionary)->void:
	if not result.get("ok",false):return
	if request.type=="fire_chef":dismissal.play_fired()
	elif request.type=="level_up_chef":
		manage_view.result.text="Level %s · %s recipes unlocked!"%[actor.level,Dev.tier(int(actor.level))] if Dev.tier(int(actor.level))!=Dev.tier(int(request.expected_level)) else "Level %s · Cooking speed %.2f×"%[actor.level,actor.cooking_speed]
