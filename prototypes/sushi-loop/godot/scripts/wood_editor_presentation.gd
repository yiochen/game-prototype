extends "res://scripts/editor_presentation.gd"
## Approved HTML dock, with native controls, accessible labels and clipped goods.
const WoodSkin = preload("res://scripts/wood_skin.gd")
const WOOD_INK := Color("592c10")
var wood = WoodSkin.new()
var backdrop: Control
var scroll_offsets: Dictionary = {}
var header_height := 78.0
var safe_height := 42.0
var wood_font: Font

class Backdrop extends Control:
	var owner_ui
	func _draw() -> void:
		var ui = owner_ui
		var u: float = ui.unit
		var layer := str(ui.state.get("editor",{}).get("layer","layout"))
		var opened := bool(ui.state.get("editor",{}).get("tray_open",true))
		var cap_top: float = ui.header_height-78
		var board_top: float = ui.header_height
		# A real bottom inset can extend the plain maple below the fixed design.
		ui.wood.style("board",u).draw(get_canvas_item(),Rect2(0,board_top*u,size.x,size.y-board_top*u))
		# The gradient is a plain translucent span, with no corners to distort.
		draw_texture_rect_region(ui.wood.texture("tab-backdrop"),Rect2(0,0,size.x,ui.header_height*u),Rect2(32,32,1440,156))
		# Paint the connected cap over the gradient as it is in the HTML stacking.
		if opened:
			ui.wood.draw_asset(self,"connected-"+layer,Vector2(0,cap_top)*u,u)
		else:
			var button: Button = ui.layers[layer]
			ui.wood.style("tab-selected",u).draw(get_canvas_item(),Rect2(button.position+Vector2(0,cap_top)*u,Vector2(button.size.x,78*u)))
		ui.wood.draw_asset(self,"footer-waves",Vector2(28*u,size.y-40*u),u)

func _ready() -> void:
	super._ready()
	wood_font = Typography.body()
	wood_font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"):800}
	backdrop = Backdrop.new()
	backdrop.owner_ui = self
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	backdrop.clip_contents = true
	add_child(backdrop)
	move_child(backdrop,0)
	rail.clip_contents = true
	rail.mouse_filter = Control.MOUSE_FILTER_STOP
	rail.gui_input.connect(func(event: InputEvent):
		_tray_input(event)
		if event is InputEventScreenTouch and event.pressed: item_pointer.emit({},event))
	refresh_layout()

func _is_wood_button(button: Button) -> bool:
	return button == shop or button in layers.values()

func _refresh_button_visual(button: Button) -> void:
	if not _is_wood_button(button) or not button.has_meta("visual"):
		super._refresh_button_visual(button)
		return
	var selected := button != shop and button.button_pressed
	var pressed: bool = button.get_meta("visual_pressed",false)
	var surface: Panel = button.get_meta("visual_surface")
	surface.custom_minimum_size = Vector2.ZERO
	surface.add_theme_stylebox_override("panel",StyleBoxEmpty.new() if selected else wood.style(("shop-" if button == shop else "tab-")+("pressed" if pressed else "normal"),unit))
	var icon: TextureRect = button.get_meta("visual_icon")
	icon.texture = wood.icon("shop" if button == shop else button.text.to_lower())
	icon.modulate = CREAM if button == shop else WOOD_INK
	var caption: Label = button.get_meta("visual_label")
	caption.text = button.text
	caption.add_theme_color_override("font_color",CREAM if button == shop else WOOD_INK)
	if wood_font != null: caption.add_theme_font_override("font",wood_font)
	var focus: Panel = button.get_meta("visual_focus")
	var outline := StyleBoxFlat.new()
	outline.bg_color = Color.TRANSPARENT
	outline.border_color = WOOD_INK
	outline.set_border_width_all(maxi(1,int(2*unit)))
	outline.set_corner_radius_all(int(12*unit))
	focus.add_theme_stylebox_override("panel",outline)
	focus.visible = button.has_focus()

func _press_button_visual(button: Button, pressed: bool) -> void:
	if not _is_wood_button(button):
		super._press_button_visual(button,pressed)
		return
	button.set_meta("visual_pressed",pressed)
	_refresh_button_layout(button)

func _layout_button_visual(button: Button, bounds: Rect2, font_size: float, icon_width: float) -> void:
	if not _is_wood_button(button):
		super._layout_button_visual(button,bounds,font_size,icon_width)
		return
	button.set_meta("visual_layout",{"bounds":bounds,"font_size":font_size,"icon_width":icon_width})
	_refresh_button_visual(button)
	var visual: Control = button.get_meta("visual")
	visual.position = Vector2.ZERO
	visual.size = button.size
	visual.scale = Vector2.ONE
	var surface: Panel = button.get_meta("visual_surface")
	surface.position = Vector2(0,(header_height-78)*unit)
	surface.size = Vector2(button.size.x,78*unit)
	var face := Rect2(0,(header_height-78+14)*unit,button.size.x,60*unit)
	var focus: Panel = button.get_meta("visual_focus")
	focus.position = face.position
	focus.size = face.size
	var icon: TextureRect = button.get_meta("visual_icon")
	var caption: Label = button.get_meta("visual_label")
	var pixels := maxi(1,int((25 if button == shop else 26)*unit))
	var font := caption.get_theme_font("font")
	var width := UISkin.caption_ink(font,caption.text,pixels).size.x
	var total := width+39*unit
	icon.size = Vector2(30,30)*unit
	icon.position = Vector2((button.size.x-total)/2,face.get_center().y-15*unit)
	UISkin.layout_caption(caption,Rect2(icon.position.x+39*unit,face.position.y,width,face.size.y),pixels)
	if button.get_meta("visual_pressed",false):
		icon.position.y += 2*unit
		caption.position.y += 2*unit

func _rebuild_cards() -> void:
	for card in cards:
		rail.remove_child(card)
		card.queue_free()
	cards.clear()
	var layer := str(state.get("editor",{}).get("layer","layout"))
	for item: Dictionary in inventory_items():
		var card := _button("","slot-paper","",str(item.name),rail)
		card.toggle_mode = true
		card.set_meta("entry",item)
		card.button_pressed = active_item == str(item.id)
		card.disabled = not item.get("available",true) or (int(item.get("count",0))<=0 and not item.get("assigned",false))
		card.accessibility_description = "Current floor" if layer == "floor" else "Assigned. Inspect or drag upward to move." if item.get("assigned",false) else "%s available. Swipe sideways to browse; drag upward or select then tap a free floor tile." % int(item.get("count",0))
		var preview := ItemPreview.new()
		preview.trim_goods = true
		preview.art = art
		preview.entry = item
		preview.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(preview)
		var caption := _label(_inventory_caption(item))
		caption.add_theme_color_override("font_color",WOOD_INK)
		card.add_child(caption)
		var badge := Panel.new()
		badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(badge)
		var stock := _label(str(int(item.get("count",0))) if layer == "layout" else "Placed" if item.get("assigned",false) else "Current" if layer == "floor" else "Ready")
		card.add_child(stock)
		card.set_meta("preview",preview)
		card.set_meta("name_label",caption)
		card.set_meta("stock_badge",badge)
		card.set_meta("stock",stock)
		card.gui_input.connect(func(event: InputEvent):
			_tray_input(event)
			item_pointer.emit(item,event)
			if event is InputEventKey and event.pressed and not event.echo and event.keycode in [KEY_ENTER,KEY_KP_ENTER,KEY_SPACE]:
				item_armed.emit(item)
				get_viewport().set_input_as_handled()
			if event is InputEventKey and event.pressed and event.keycode in [KEY_HOME,KEY_END]:
				(cards[0] if event.keycode == KEY_HOME else cards[-1]).grab_focus()
				get_viewport().set_input_as_handled())
		card.focus_entered.connect(func(): reveal_card(card))
		cards.append(card)
	if not scroll_offsets.has(layer):
		scroll_offsets[layer] = float(state.get("editor",{}).get("scrolls",{}).get(layer,int(state.get("editor",{}).get("pages",{}).get(layer,0))*648))

func _tray_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN,MOUSE_BUTTON_WHEEL_LEFT,MOUSE_BUTTON_WHEEL_RIGHT]:
		scroll_by(100*unit*(-1 if event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_LEFT] else 1))
		commit_scroll()
		get_viewport().set_input_as_handled()

func _move_control(control: Control, target: Vector2) -> void:
	# The dock is one joined surface; category changes must not split its pieces.
	control.position = target

func scroll_by(delta: float) -> void:
	var layer := str(state.get("editor",{}).get("layer","layout"))
	var width := 204.0 if layer == "people" else 152.0
	var maximum := maxf(0,(cards.size()*width+maxi(0,cards.size()-1)*10)-688)
	scroll_offsets[layer] = clampf(float(scroll_offsets.get(layer,0))+delta/unit,0,maximum)
	_layout_goods(layer)

func commit_scroll() -> void:
	var layer := str(state.get("editor",{}).get("layer","layout"))
	command_requested.emit({"type":"editor_scroll","offset":float(scroll_offsets.get(layer,0))})

func reveal_card(card: Button) -> void:
	var index := cards.find(card)
	if index<0: return
	var layer := str(state.get("editor",{}).get("layer","layout"))
	var width := 204.0 if layer == "people" else 152.0
	var offset := float(scroll_offsets.get(layer,0))
	var left := index*(width+10)
	if left < offset: scroll_by((left-offset)*unit)
	elif left+width>offset+688: scroll_by((left+width-offset-688)*unit)
	commit_scroll()

func _layout_goods(layer: String) -> void:
	if rail == null: return
	var width := 204.0 if layer == "people" else 152.0
	var content := cards.size()*width+maxi(0,cards.size()-1)*10
	var offset := clampf(float(scroll_offsets.get(layer,0)),0,maxf(0,content-688))
	var start := maxf(0,(688-content)/2) if layer != "layout" else 0.0
	for i in range(cards.size()):
		var card: Button = cards[i]
		card.position = Vector2(start+i*(width+10)-offset,35)*unit
		card.custom_minimum_size = Vector2.ZERO
		card.size = Vector2(width,214)*unit
		if card.get_meta("wood_unit",-1.0) != unit:
			card.set_meta("wood_unit",unit)
			for treatment in ["normal","hover","pressed","disabled"]: card.add_theme_stylebox_override(treatment,StyleBoxEmpty.new())
			var outline := StyleBoxFlat.new()
			outline.bg_color = Color.TRANSPARENT
			outline.border_color = WOOD_INK
			outline.set_border_width_all(maxi(1,int(2*unit)))
			card.add_theme_stylebox_override("focus",outline)
			card.add_theme_stylebox_override("pressed",outline)
		var preview: Control = card.get_meta("preview")
		preview.position = Vector2(12,8)*unit
		if card.button_pressed: preview.position.y -= 4*unit
		preview.size = Vector2(width-24,126)*unit
		preview.modulate.a = 0.4 if card.disabled else 1.0
		var caption: Label = card.get_meta("name_label")
		caption.visible = true
		if wood_font != null: caption.add_theme_font_override("font",wood_font)
		UISkin.layout_caption(caption,Rect2(0,154*unit,width*unit,30*unit),maxi(1,int(25*unit)))
		var badge: Panel = card.get_meta("stock_badge")
		badge.visible = layer == "layout"
		badge.position = Vector2(width-46,101)*unit
		badge.size = Vector2(42,42)*unit
		badge.add_theme_stylebox_override("panel",wood.style("quantity-badge",unit))
		badge.modulate.a = 0.7 if card.disabled else 1.0
		var stock: Label = card.get_meta("stock")
		stock.visible = true
		stock.add_theme_color_override("font_color",CREAM if layer == "layout" else WOOD_INK)
		if wood_font != null: stock.add_theme_font_override("font",wood_font)
		UISkin.layout_caption(stock,Rect2(badge.position,badge.size) if layer == "layout" else Rect2(0,185*unit,width*unit,24*unit),maxi(1,int((24 if layer == "layout" else 19)*unit)))
		stock.modulate.a = 0.7 if card.disabled and layer == "layout" else 1.0
		card.focus_neighbor_left = cards[maxi(0,i-1)].get_path()
		card.focus_neighbor_right = cards[mini(cards.size()-1,i+1)].get_path()

func refresh_layout() -> void:
	if not is_node_ready() or area.size.x<=0: return
	super.refresh_layout()
	var physical_axes := get_viewport_transform().get_scale() * get_global_transform().get_scale()
	var physical_scale := maxf(0.001,minf(physical_axes.x,physical_axes.y))
	header_height = maxf(78,44.01/physical_scale/unit)
	safe_height = 42
	if OS.get_name() in ["Android","iOS"]:
		var bottom := maxf(0,float(get_window().size.y)-Rect2(DisplayServer.get_display_safe_area()).end.y)
		safe_height = maxf(42,bottom/physical_scale/unit+8)
	var opened := bool(state.get("editor",{}).get("tray_open",true))
	var goods_height := 249.0 if opened else 0.0
	category_rail.position = Vector2(area.position.x,area.end.y-(header_height+goods_height+safe_height)*unit)
	category_rail.size = Vector2(area.size.x,header_height*unit)
	category_rod.hide()
	bottom_dock.hide()
	previous.hide()
	next.hide()
	tray.custom_minimum_size = Vector2.ZERO
	tray.add_theme_stylebox_override("panel",StyleBoxEmpty.new())
	tray.position = category_rail.position+Vector2(0,header_height*unit)
	tray.size = Vector2(area.size.x,goods_height*unit)
	rail.position = Vector2(16*unit,0)
	rail.size = Vector2(688*unit,goods_height*unit)
	var layer := str(state.get("editor",{}).get("layer","layout"))
	_layout_goods(layer)
	var x := 14.0
	for i in range(4):
		var button: Button = layers[["people","layout","floor"][i]] if i<3 else shop
		var width: float = 662.0*[1.08,1.36,1.0,0.92][i]/4.36
		button.custom_minimum_size = Vector2.ZERO
		button.position = Vector2(x,0)*unit
		button.size = Vector2(width,header_height)*unit
		_layout_button_visual(button,Rect2(0,0,width,header_height),26,30)
		x += width+10
	_update_inventory_backing()
	if backdrop != null:
		backdrop.position = category_rail.position
		backdrop.size = Vector2(area.size.x,(header_height+goods_height+safe_height)*unit)
		backdrop.queue_redraw()
	_layout_context()

func _update_inventory_backing() -> void:
	if inventory_backing == null or category_rail == null: return
	inventory_backing.color = Color.TRANSPARENT
	inventory_backing.position = category_rail.position
	inventory_backing.size = Vector2(area.size.x,area.end.y-category_rail.position.y)
